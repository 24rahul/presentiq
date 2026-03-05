from typing import Dict, Any
from agents.base import BaseAgent


class LiteratureLearningAgent(BaseAgent):
    """Agent 6: Identifies key learning opportunities from the case and
    provides targeted teaching points.

    In future iterations, this agent will integrate with PubMed and
    specialty handbooks via RAG. For now, it uses the LLM's medical
    knowledge to generate relevant teaching points and learning resources.
    """

    agent_name = "literature_learning"
    agent_description = "Teaching points and learning resource identification"

    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        transcript = context["cleaned_transcript"]
        service_context = context["service_context"]
        # Pull reasoning gaps from the clinical reasoning agent if available
        reasoning_result = context.get("clinical_reasoning_result", {})
        reasoning_gaps = reasoning_result.get("reasoning_gaps", [])

        system_prompt = f"""You are a medical educator on {service_context['name']} ({service_context['specialty']}). Based on a medical student's oral presentation, identify the most valuable LEARNING OPPORTUNITIES from this case.

Focus on:
1. Clinical pearls directly relevant to the case presented
2. Knowledge gaps revealed by the presentation (if any)
3. High-yield concepts for {service_context['specialty']} that this case illustrates
4. Connections to broader clinical principles

{"KNOWN REASONING GAPS FROM THIS PRESENTATION: " + '; '.join(reasoning_gaps) if reasoning_gaps else ""}

Do NOT be generic. Teaching points must be SPECIFIC to this case and this student's presentation.

Return JSON:
{{
    "teaching_points": [
        {{
            "topic": "short title",
            "point": "the teaching point — 2-3 sentences, specific and actionable",
            "relevance": "why this matters for this case specifically"
        }}
    ],
    "suggested_reading": ["specific topics or guidelines the student should review, relevant to gaps in this presentation"],
    "case_learning_summary": "3-4 sentences summarizing what makes this case educationally valuable and what the student should take away"
}}

Provide 3-5 teaching points. Quality over quantity."""

        user_prompt = f"""Based on this presentation for {service_context['name']}, identify key learning opportunities:

TRANSCRIPT:
{transcript}"""

        try:
            result = self._call_llm_json(system_prompt, user_prompt, max_tokens=1500)
        except Exception as e:
            result = {
                "teaching_points": [],
                "suggested_reading": [],
                "case_learning_summary": f"Error during literature analysis: {e}",
            }

        return result
