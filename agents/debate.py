import json
from typing import Dict, Any
from agents.base import BaseAgent


class DebateAgent(BaseAgent):
    """Runs a generous-vs-strict evaluator deliberation on the agent results.

    Two perspectives argue over the assessment, surfacing nuance that a
    single-pass evaluation tends to miss (e.g., LLMs defaulting to
    generically positive feedback).  The output is a set of "contested
    points" the synthesizer uses to produce more calibrated feedback.
    """

    agent_name = "debate"
    agent_description = "Inter-agent deliberation between generous and strict evaluator perspectives"

    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        service_context = context["service_context"]
        agent_summary = self._build_summary(context)

        system_prompt = f"""You are mediating a deliberation between two attending physicians reviewing a medical student's oral presentation on {service_context['name']} ({service_context['specialty']}).

GENEROUS EVALUATOR: Focuses on what the student did well relative to their level of training. Gives benefit of the doubt. Highlights growth potential.

STRICT EVALUATOR: Holds the student to the standard they will need on clerkship evaluations and real patient care. Points out gaps honestly.

Below are the evaluation results from multiple specialist agents. Your task:

1. For each dimension (content, reasoning, structure, communication), generate a brief exchange where the generous and strict evaluators disagree or add nuance.
2. Identify where the initial evaluations may be TOO GENEROUS (praising something mediocre) or TOO HARSH (penalizing something reasonable for this level).
3. Arrive at a balanced "deliberation conclusion" for each contested point.

AGENT EVALUATIONS:
{agent_summary}

Return JSON:
{{
    "contested_points": [
        {{
            "dimension": "which evaluation dimension this concerns",
            "generous_view": "what the generous evaluator argues",
            "strict_view": "what the strict evaluator argues",
            "resolution": "the balanced conclusion after deliberation",
            "adjustment": "raise | lower | keep — whether initial assessment should be adjusted"
        }}
    ],
    "consensus_strengths": ["points both evaluators agree are genuine strengths"],
    "consensus_weaknesses": ["points both evaluators agree need improvement"],
    "overall_calibration": "2-3 sentences on whether the initial agent evaluations were well-calibrated, too generous, or too strict overall"
}}

Generate 3-5 contested points. Focus on the most impactful disagreements, not trivial ones."""

        user_prompt = "Conduct the deliberation between generous and strict evaluators based on the agent results above."

        try:
            result = self._call_llm_json(system_prompt, user_prompt, max_tokens=2000)
        except Exception as e:
            result = {
                "contested_points": [],
                "consensus_strengths": [],
                "consensus_weaknesses": [],
                "overall_calibration": f"Error during debate: {e}",
            }

        return result

    def _build_summary(self, context: Dict[str, Any]) -> str:
        sections = []

        content = context.get("clinical_content_result", {})
        if content:
            sections.append(f"CLINICAL CONTENT (Score: {content.get('score', 'N/A')}/10):\n{content.get('content_analysis', '')}")

        reasoning = context.get("clinical_reasoning_result", {})
        if reasoning:
            sections.append(f"CLINICAL REASONING (Score: {reasoning.get('score', 'N/A')}/10):\n{reasoning.get('reasoning_analysis', '')}")

        structure = context.get("structure_delivery_result", {})
        if structure:
            sections.append(f"STRUCTURE & DELIVERY (Score: {structure.get('score', 'N/A')}/10):\n{structure.get('format_conformance', '')}\n{structure.get('organization_flow', '')}")

        communication = context.get("communication_professionalism_result", {})
        if communication:
            sections.append(f"COMMUNICATION (Score: {communication.get('score', 'N/A')}/10):\n{communication.get('audience_adaptation', '')}")

        return "\n\n".join(sections)
