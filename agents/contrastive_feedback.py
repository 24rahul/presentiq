from typing import Dict, Any
from agents.base import BaseAgent


class ContrastiveFeedbackAgent(BaseAgent):
    """Generates targeted 'before/after' rewrites for the weakest parts of
    the presentation.  Shows concretely how a section could be improved,
    rather than giving abstract advice.

    IMPORTANT: When the rewrite requires clinical details not present in
    the original transcript, the agent must flag that the example is
    illustrative / not patient-specific.
    """

    agent_name = "contrastive_feedback"
    agent_description = "Targeted before/after rewrites showing how weak sections could be improved"

    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        transcript = context["cleaned_transcript"]
        service_context = context["service_context"]

        # Gather weakness signals from all agents
        weaknesses = self._collect_weaknesses(context)

        system_prompt = f"""You are an attending physician on {service_context['name']} ({service_context['specialty']}). You have listened to a medical student's presentation and identified several weak areas.

Your task: For each weak area, find the specific segment of the transcript and write a CONCRETE REWRITE showing how it could be improved.

RULES:
1. Quote the EXACT original text from the transcript, then provide your improved version.
2. Keep rewrites SHORT — 1-3 sentences. This is a targeted fix, not a model presentation.
3. CRITICAL: If your rewrite adds clinical details that were NOT in the original transcript (because the student omitted them), you MUST mark those details as illustrative. Use brackets like [e.g., 2L NC] or [e.g., troponin 0.04] to signal that the specific values are examples, not the patient's actual data. Add a note: "Specific values are illustrative — substitute the patient's actual data."
4. If the rewrite only reorganizes or rephrases what was already said (no new clinical data needed), no disclaimer is needed.
5. Focus on the 2-4 MOST IMPACTFUL improvements. Quality over quantity.

KNOWN WEAKNESSES:
{weaknesses}

TRANSCRIPT:
{transcript}

Return JSON:
{{
    "rewrites": [
        {{
            "area": "short label for what this improves (e.g., 'HPI opening', 'Assessment framing')",
            "original": "exact quote from transcript",
            "improved": "your rewritten version",
            "why_better": "1 sentence explaining the improvement",
            "uses_illustrative_data": true/false
        }}
    ],
    "note": "A brief overall note on the approach taken — 1-2 sentences"
}}

Provide 2-4 rewrites targeting the highest-impact improvements."""

        user_prompt = "Generate contrastive before/after rewrites for the weakest sections of this presentation."

        try:
            result = self._call_llm_json(system_prompt, user_prompt, max_tokens=2000)
        except Exception as e:
            result = {
                "rewrites": [],
                "note": f"Error during contrastive feedback: {e}",
            }

        return result

    def _collect_weaknesses(self, context: Dict[str, Any]) -> str:
        items = []

        content = context.get("clinical_content_result", {})
        for missing in content.get("elements_missing", []):
            items.append(f"[Content] Missing element: {missing}")
        for issue in content.get("terminology_issues", []):
            items.append(f"[Content] Terminology issue: {issue}")

        reasoning = context.get("clinical_reasoning_result", {})
        for gap in reasoning.get("reasoning_gaps", []):
            items.append(f"[Reasoning] Gap: {gap}")

        structure = context.get("structure_delivery_result", {})
        sd = structure.get("semantic_density", {})
        for over in sd.get("over_represented", []):
            items.append(f"[Structure] Over-represented: {over}")
        for under in sd.get("under_represented", []):
            items.append(f"[Structure] Under-represented: {under}")
        for missing in structure.get("sections_missing", []):
            items.append(f"[Structure] Missing section: {missing}")

        communication = context.get("communication_professionalism_result", {})
        if communication.get("patient_centered_language"):
            items.append(f"[Communication] {communication['patient_centered_language']}")

        if not items:
            items.append("No specific weaknesses flagged — focus on the areas with most room for improvement.")

        return "\n".join(items)
