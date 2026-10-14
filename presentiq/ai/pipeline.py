"""Multi-agent pipeline orchestrator for PresentIQ.

Pipeline:
1. Transcription QA Agent
2. Clinical Content Agent
3. Clinical Reasoning Agent (with plan coherence)
4. Parallel: Structure, Communication, Literature, Anticipatory (optional)
5. Parallel: Debate (generous vs strict) + Contrastive Feedback
6. Attending Synthesizer Agent (informed by debate + contrastive)
7. Synthesis Critic → optional revision
"""

import json
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Callable, Dict, Optional

import yaml

from presentiq.ai.agents.anticipatory_reasoning import AnticipatoryReasoningAgent
from presentiq.ai.agents.clinical_content import ClinicalContentAgent
from presentiq.ai.agents.clinical_reasoning import ClinicalReasoningAgent
from presentiq.ai.agents.communication_professionalism import CommunicationProfessionalismAgent
from presentiq.ai.agents.contrastive_feedback import ContrastiveFeedbackAgent
from presentiq.ai.agents.debate import DebateAgent
from presentiq.ai.agents.literature_learning import LiteratureLearningAgent
from presentiq.ai.agents.structure_delivery import StructureDeliveryAgent
from presentiq.ai.agents.synthesis_critic import SynthesisCriticAgent
from presentiq.ai.agents.synthesizer import SynthesizerAgent
from presentiq.ai.agents.transcription_qa import TranscriptionQAAgent
from presentiq.ai.backend import AIBackend
from presentiq.paths import CONFIG_DIR
from presentiq.validation import validate_analysis_input

_FORMATS_PATH = CONFIG_DIR / "presentation_formats.yaml"


def load_presentation_formats() -> Dict[str, Any]:
    if _FORMATS_PATH.exists():
        with open(_FORMATS_PATH) as f:
            data = yaml.safe_load(f)
        return data.get("formats", {})
    return {}


PRESENTATION_FORMATS = load_presentation_formats()


class FeedbackPipeline(AIBackend):
    def __init__(self, provider: str = "OpenAI", *, api_key=None, model=None):
        super().__init__(provider, api_key=api_key, model=model)

        kwargs = dict(client=self.client, model=self.model, temperature=self.temperature)
        self.transcription_qa = TranscriptionQAAgent(**kwargs)
        self.clinical_content = ClinicalContentAgent(**kwargs)
        self.clinical_reasoning = ClinicalReasoningAgent(**kwargs)
        self.structure_delivery = StructureDeliveryAgent(**kwargs)
        self.communication_prof = CommunicationProfessionalismAgent(**kwargs)
        self.anticipatory_reasoning = AnticipatoryReasoningAgent(**kwargs)
        self.literature_learning = LiteratureLearningAgent(**kwargs)
        self.debate = DebateAgent(**kwargs)
        self.contrastive_feedback = ContrastiveFeedbackAgent(**kwargs)
        self.synthesizer = SynthesizerAgent(**kwargs)
        self.synthesis_critic = SynthesisCriticAgent(**kwargs)

    def run(
        self,
        transcript: str,
        service: str,
        service_contexts: Dict[str, Dict],
        presentation_format: str = "full_hp",
        enable_anticipatory: bool = True,
        progress_callback: Optional[Callable[[str, int, int], None]] = None,
    ) -> Dict[str, Any]:
        transcript = validate_analysis_input(transcript, service, presentation_format)
        service_context = service_contexts[service]
        format_config = PRESENTATION_FORMATS[presentation_format]

        total_steps = 7

        def _progress(name, step):
            if progress_callback:
                progress_callback(name, step, total_steps)

        context = {
            "transcript": transcript,
            "service_context": service_context,
            "format_config": format_config,
        }

        _progress("Cleaning transcription", 1)
        qa_result = self.transcription_qa.run(context)
        context["transcription_qa_result"] = qa_result
        context["cleaned_transcript"] = qa_result.get("cleaned_transcript", transcript)

        _progress("Evaluating clinical content", 2)
        content_result = self.clinical_content.run(context)
        context["clinical_content_result"] = content_result

        _progress("Evaluating clinical reasoning", 3)
        reasoning_result = self.clinical_reasoning.run(context)
        context["clinical_reasoning_result"] = reasoning_result

        _progress("Running parallel evaluations", 4)
        parallel_agents = {
            "structure": self.structure_delivery,
            "communication": self.communication_prof,
            "literature": self.literature_learning,
        }
        if enable_anticipatory:
            parallel_agents["anticipatory"] = self.anticipatory_reasoning

        with ThreadPoolExecutor(max_workers=len(parallel_agents)) as executor:
            futures = {
                key: executor.submit(agent.run, context) for key, agent in parallel_agents.items()
            }
            results = {key: future.result() for key, future in futures.items()}

        structure_result = results["structure"]
        communication_result = results["communication"]
        literature_result = results["literature"]

        context["structure_delivery_result"] = structure_result
        context["communication_professionalism_result"] = communication_result
        context["literature_learning_result"] = literature_result
        context["anticipatory_reasoning_result"] = results.get("anticipatory", {})

        # Step 5: Debate + Contrastive Feedback in parallel
        _progress("Deliberating and generating rewrites", 5)
        with ThreadPoolExecutor(max_workers=2) as executor:
            future_debate = executor.submit(self.debate.run, context)
            future_contrastive = executor.submit(self.contrastive_feedback.run, context)

            debate_result = future_debate.result()
            contrastive_result = future_contrastive.result()

        context["debate_result"] = debate_result
        context["contrastive_feedback_result"] = contrastive_result

        # Step 6: Synthesis (informed by debate deliberation)
        _progress("Synthesizing feedback", 6)
        synthesis = self.synthesizer.run(context)

        # Step 7: Critique-revision loop
        _progress("Quality review", 7)
        critic_context = {
            "synthesis": synthesis,
            "agent_results_summary": self.synthesizer._compile_agent_summaries(
                content_result,
                reasoning_result,
                structure_result,
                communication_result,
                context.get("anticipatory_reasoning_result", {}),
                literature_result,
            ),
            "service_context": service_context,
        }
        critic_result = self.synthesis_critic.run(critic_context)

        if not critic_result.get("is_acceptable", True) and critic_result.get(
            "revision_instructions"
        ):
            synthesis = self._revise_synthesis(synthesis, critic_result, context)

        synthesis["_agent_results"] = {
            "transcription_qa": qa_result,
            "clinical_content": content_result,
            "clinical_reasoning": reasoning_result,
            "structure_delivery": structure_result,
            "communication_professionalism": communication_result,
            "anticipatory_reasoning": context.get("anticipatory_reasoning_result", {}),
            "literature_learning": literature_result,
            "debate": debate_result,
            "contrastive_feedback": contrastive_result,
            "synthesis_critic": critic_result,
        }

        synthesis["service"] = service_context.get("name", "Unknown")
        synthesis["specialty"] = service_context.get("specialty", "Unknown")
        synthesis["presentation_format"] = format_config.get("name", "Standard")

        synthesis["status"] = "complete"
        return synthesis

    def _revise_synthesis(
        self, synthesis: Dict[str, Any], critic_result: Dict[str, Any], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Ask the synthesizer to revise based on critic feedback."""
        service_context = context["service_context"]

        system_prompt = f"""You are a senior attending physician on {service_context["name"]}. You previously produced a feedback synthesis for a medical student's presentation, but a quality reviewer found issues.

ORIGINAL SYNTHESIS:
{json.dumps(synthesis, indent=2)}

CRITIC FEEDBACK:
{json.dumps(critic_result.get("issues_found", []), indent=2)}

REVISION INSTRUCTIONS:
{critic_result.get("revision_instructions", "Address the issues found.")}

Produce a REVISED version of the synthesis JSON that fixes the identified issues. Keep the same JSON structure. Only change what needs fixing — don't rewrite sections that were fine."""

        user_prompt = "Revise the synthesis to address the critic's feedback."

        revised = self.synthesizer._call_llm_json(system_prompt, user_prompt, max_tokens=2500)
        revised["_revised"] = True
        return revised


def get_format_options() -> Dict[str, str]:
    return {key: config["name"] for key, config in PRESENTATION_FORMATS.items()}
