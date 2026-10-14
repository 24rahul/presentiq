import copy
import json
import os
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from presentiq.ai.agents.base import BaseAgent
from presentiq.ai.agents.clinical_content import ClinicalContentAgent
from presentiq.ai.agents.schemas import AGENT_SCHEMAS
from presentiq.ai.backend import AIBackend, AnalysisError
from presentiq.ai.legacy import FeedbackGenerator
from presentiq.ai.pipeline import PRESENTATION_FORMATS, FeedbackPipeline
from presentiq.services import SERVICE_CONTEXTS
from tests.fixtures import OUTPUTS, model_response


class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.env = patch.dict(os.environ, {"OPENAI_API_KEY": "test-key", "AI_MODEL": "test-model"})
        self.env.start()
        self.addCleanup(self.env.stop)

    def test_successful_pipeline_validates_all_agents_and_reports_progress(self):
        progress = []
        with (
            patch.object(BaseAgent, "_call_llm", new=model_response),
            FeedbackPipeline() as pipeline,
        ):
            result = pipeline.run(
                "Synthetic presentation",
                "surgery_general",
                SERVICE_CONTEXTS,
                presentation_format="sbar",
                progress_callback=lambda *args: progress.append(args),
            )
        self.assertEqual(result["status"], "complete")
        self.assertEqual(result["overall_score"], 8)
        self.assertEqual(result["presentation_format"], PRESENTATION_FORMATS["sbar"]["name"])
        self.assertEqual([p[1] for p in progress], list(range(1, 8)))
        self.assertEqual(len(result["_agent_results"]), 10)

    def test_total_provider_failure_has_no_fabricated_score(self):
        with (
            patch.object(
                BaseAgent, "_call_llm", side_effect=RuntimeError("secret-key transcription text")
            ) as call,
            FeedbackPipeline() as pipeline,
        ):
            with self.assertRaises(AnalysisError) as exc:
                pipeline.run("Synthetic presentation", "surgery_general", SERVICE_CONTEXTS)
        self.assertEqual(call.call_count, 1)
        self.assertNotIn("secret-key", str(exc.exception))

    def test_critic_failure_is_not_accepted(self):
        def fail_critic(agent, *args, **kwargs):
            if agent.agent_name == "synthesis_critic":
                raise RuntimeError("provider failed")
            return model_response(agent, *args, **kwargs)

        with patch.object(BaseAgent, "_call_llm", new=fail_critic), FeedbackPipeline() as pipeline:
            with self.assertRaises(AnalysisError):
                pipeline.run("Synthetic presentation", "surgery_general", SERVICE_CONTEXTS)

    def test_revised_synthesis_is_validated(self):
        def request_revision(agent, *args, **kwargs):
            if agent.agent_name == "synthesis_critic":
                return json.dumps(
                    {
                        "issues_found": [],
                        "is_acceptable": False,
                        "revision_instructions": "Clarify rationale.",
                    }
                )
            return model_response(agent, *args, **kwargs)

        with (
            patch.object(BaseAgent, "_call_llm", new=request_revision),
            FeedbackPipeline() as pipeline,
        ):
            result = pipeline.run("Synthetic presentation", "surgery_general", SERVICE_CONTEXTS)
        self.assertTrue(result["_revised"])
        self.assertEqual(result["overall_score"], 8)

    def test_legacy_success_and_failure_are_distinct(self):
        with FeedbackGenerator() as generator:
            with patch.object(BaseAgent, "_call_llm", new=model_response):
                feedback = generator.generate_feedback("Synthetic", "surgery_general", "sbar")
                self.assertEqual(feedback["status"], "complete")
                self.assertEqual(feedback["overall_score"], 8)
            with patch.object(BaseAgent, "_call_llm", return_value="Unstructured output"):
                with self.assertRaises(AnalysisError):
                    generator.generate_feedback("Synthetic")

    def test_invalid_json_shapes_rejected_for_every_agent(self):
        for name in AGENT_SCHEMAS:
            agent = BaseAgent(None, "test")
            agent.agent_name = name
            for raw in ["[]", "null", "{}", '"text"']:
                with (
                    self.subTest(agent=name, raw=raw),
                    patch.object(agent, "_call_llm", return_value=raw),
                ):
                    with self.assertRaises(AnalysisError):
                        agent._call_llm_json("system", "user")

    def test_invalid_nested_types_and_scores_rejected(self):
        for score in [0, 11, "8", None, True]:
            payload = {**OUTPUTS["synthesizer"], "overall_score": score}
            agent = BaseAgent(None, "test")
            agent.agent_name = "synthesizer"
            with (
                self.subTest(score=score),
                patch.object(agent, "_call_llm", return_value=json.dumps(payload)),
            ):
                with self.assertRaises(AnalysisError):
                    agent._call_llm_json("system", "user")
        payload = copy.deepcopy(OUTPUTS["structure_delivery"])
        payload["semantic_density"]["analysis"] = None
        agent.agent_name = "structure_delivery"
        with patch.object(agent, "_call_llm", return_value=json.dumps(payload)):
            with self.assertRaises(AnalysisError):
                agent._call_llm_json("system", "user")

    def test_truncated_response_rejected_even_when_json_is_valid(self):
        client = SimpleNamespace(
            chat=SimpleNamespace(
                completions=SimpleNamespace(
                    create=lambda **kwargs: SimpleNamespace(
                        choices=[
                            SimpleNamespace(
                                finish_reason="length",
                                message=SimpleNamespace(
                                    content=json.dumps(OUTPUTS["transcription_qa"])
                                ),
                            )
                        ]
                    )
                )
            )
        )
        agent = BaseAgent(client, "test")
        agent.agent_name = "transcription_qa"
        with self.assertRaises(AnalysisError):
            agent._call_llm_json("system", "user")

    def test_format_reaches_clinical_content_rubric(self):
        agent = ClinicalContentAgent(None, "test")
        prompts = []
        for fmt in ["full_hp", "sbar"]:
            with patch.object(
                agent, "_call_llm", return_value=json.dumps(OUTPUTS["clinical_content"])
            ) as call:
                agent.run(
                    {
                        "cleaned_transcript": "Synthetic",
                        "service_context": SERVICE_CONTEXTS["surgery_general"],
                        "format_config": PRESENTATION_FORMATS[fmt],
                    }
                )
                prompts.append(call.call_args.args[0])
        self.assertNotEqual(prompts[0], prompts[1])
        self.assertIn(PRESENTATION_FORMATS["sbar"]["name"], prompts[1])

    def test_service_options_do_not_construct_provider_client(self):
        with patch("openai.OpenAI", side_effect=AssertionError("Client not needed")):
            self.assertIn("Surgery", FeedbackGenerator.get_service_options())

    def test_explicit_credentials_and_models_do_not_mutate_environment(self):
        before = dict(os.environ)
        with patch("openai.OpenAI") as client:
            with (
                AIBackend(api_key="session-A", model="model-A") as a,
                AIBackend(api_key="session-B", model="model-B") as b,
            ):
                self.assertEqual((a.model, b.model), ("model-A", "model-B"))
            self.assertEqual(
                [c.kwargs["api_key"] for c in client.call_args_list], ["session-A", "session-B"]
            )
        self.assertEqual(dict(os.environ), before)


class ModelMigrationTests(unittest.TestCase):
    def test_gpt55_uses_stateless_structured_responses(self):
        from unittest.mock import Mock

        parsed = AGENT_SCHEMAS["transcription_qa"].model_validate(OUTPUTS["transcription_qa"])
        parse = Mock(return_value=SimpleNamespace(status="completed", output_parsed=parsed))
        client = SimpleNamespace(responses=SimpleNamespace(parse=parse))
        agent = BaseAgent(client, "gpt-5.5")
        agent.agent_name = "transcription_qa"
        self.assertEqual(agent._call_llm_json("system", "synthetic"), parsed.model_dump())
        arguments = parse.call_args.kwargs
        self.assertEqual(arguments["reasoning"], {"effort": "low"})
        self.assertFalse(arguments["store"])
        self.assertIs(arguments["text_format"], AGENT_SCHEMAS["transcription_qa"])
        self.assertNotIn("temperature", arguments)
        self.assertNotIn("max_tokens", arguments)

    def test_refused_or_incomplete_responses_never_return_a_score(self):
        from unittest.mock import Mock

        for status in ("completed", "incomplete"):
            client = SimpleNamespace(
                responses=SimpleNamespace(
                    parse=Mock(return_value=SimpleNamespace(status=status, output_parsed=None))
                )
            )
            agent = BaseAgent(client, "gpt-5.5")
            agent.agent_name = "synthesizer"
            with self.subTest(status=status), self.assertRaises(AnalysisError):
                agent._call_llm_json("system", "synthetic")

    def test_openai_default_does_not_override_grok(self):
        with (
            patch.dict(
                os.environ,
                {
                    "AI_MODEL": "gpt-5.5",
                    "GROK_MODEL": "",
                    "OPENAI_API_KEY": "synthetic",
                    "XAI_API_KEY": "synthetic",
                },
            ),
            patch("openai.OpenAI"),
        ):
            self.assertEqual(AIBackend().model, "gpt-5.5")
            self.assertEqual(AIBackend(provider="xAI (Grok)").model, "grok-3")
