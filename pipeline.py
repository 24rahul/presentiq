"""Multi-agent pipeline orchestrator for PresentIQ.

Replaces the monolithic single-prompt approach with a pipeline of
specialized agents that each evaluate a different dimension.

Pipeline:
1. Transcription QA Agent
2. Clinical Content Agent
3. Clinical Reasoning Agent (with plan coherence)
4a. Structure & Delivery Agent (parallel with 4b)
4b. Communication & Professionalism Agent (parallel with 4a)
5. Anticipatory Reasoning Agent (experimental)
6. Literature & Learning Agent
7. Attending Synthesizer Agent
"""

import openai
import os
import yaml
from typing import Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from agents.transcription_qa import TranscriptionQAAgent
from agents.clinical_content import ClinicalContentAgent
from agents.clinical_reasoning import ClinicalReasoningAgent
from agents.structure_delivery import StructureDeliveryAgent
from agents.communication_professionalism import CommunicationProfessionalismAgent
from agents.anticipatory_reasoning import AnticipatoryReasoningAgent
from agents.literature_learning import LiteratureLearningAgent
from agents.synthesizer import SynthesizerAgent


_FORMATS_PATH = Path(__file__).parent / "configs" / "presentation_formats.yaml"


def load_presentation_formats() -> Dict[str, Any]:
    if _FORMATS_PATH.exists():
        with open(_FORMATS_PATH) as f:
            data = yaml.safe_load(f)
        return data.get("formats", {})
    return {}


PRESENTATION_FORMATS = load_presentation_formats()


class FeedbackPipeline:
    def __init__(self, provider: str = "OpenAI"):
        self.provider = provider

        if provider == "OpenAI":
            self.client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            self.model = os.getenv("AI_MODEL", "gpt-4")
        else:
            self.client = openai.OpenAI(
                api_key=os.getenv("XAI_API_KEY"),
                base_url="https://api.x.ai/v1",
            )
            self.model = os.getenv("AI_MODEL", "grok-3")

        self.temperature = float(os.getenv("FEEDBACK_TEMPERATURE", "0.3"))

        kwargs = dict(client=self.client, model=self.model, temperature=self.temperature)
        self.transcription_qa = TranscriptionQAAgent(**kwargs)
        self.clinical_content = ClinicalContentAgent(**kwargs)
        self.clinical_reasoning = ClinicalReasoningAgent(**kwargs)
        self.structure_delivery = StructureDeliveryAgent(**kwargs)
        self.communication_prof = CommunicationProfessionalismAgent(**kwargs)
        self.anticipatory_reasoning = AnticipatoryReasoningAgent(**kwargs)
        self.literature_learning = LiteratureLearningAgent(**kwargs)
        self.synthesizer = SynthesizerAgent(**kwargs)

    def run(
        self,
        transcript: str,
        service: str,
        service_contexts: Dict[str, Dict],
        presentation_format: str = "full_hp",
        enable_anticipatory: bool = True,
        progress_callback: Optional[callable] = None,
    ) -> Dict[str, Any]:
        service_context = service_contexts.get(
            service, service_contexts.get("internal_medicine_hospitalist", {})
        )
        format_config = PRESENTATION_FORMATS.get(presentation_format, {})

        total_steps = 6 if enable_anticipatory else 5

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

        _progress("Evaluating structure and communication", 4)
        with ThreadPoolExecutor(max_workers=2) as executor:
            future_structure = executor.submit(self.structure_delivery.run, context)
            future_communication = executor.submit(self.communication_prof.run, context)

            structure_result = future_structure.result()
            communication_result = future_communication.result()

        context["structure_delivery_result"] = structure_result
        context["communication_professionalism_result"] = communication_result

        if enable_anticipatory:
            _progress("Generating attending inner monologue", 5)
            anticipatory_result = self.anticipatory_reasoning.run(context)
            context["anticipatory_reasoning_result"] = anticipatory_result
        else:
            context["anticipatory_reasoning_result"] = {}

        step_num = 6 if enable_anticipatory else 5
        _progress("Identifying teaching points", step_num)
        literature_result = self.literature_learning.run(context)
        context["literature_learning_result"] = literature_result

        _progress("Synthesizing feedback", step_num)
        synthesis = self.synthesizer.run(context)

        synthesis["_agent_results"] = {
            "transcription_qa": qa_result,
            "clinical_content": content_result,
            "clinical_reasoning": reasoning_result,
            "structure_delivery": structure_result,
            "communication_professionalism": communication_result,
            "anticipatory_reasoning": context.get("anticipatory_reasoning_result", {}),
            "literature_learning": literature_result,
        }

        synthesis["service"] = service_context.get("name", "Unknown")
        synthesis["specialty"] = service_context.get("specialty", "Unknown")
        synthesis["presentation_format"] = format_config.get("name", "Standard")

        return synthesis


def get_format_options() -> Dict[str, str]:
    return {key: config["name"] for key, config in PRESENTATION_FORMATS.items()}
