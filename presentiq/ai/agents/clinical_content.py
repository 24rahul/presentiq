from typing import Any, Dict

from presentiq.ai.agents.base import BaseAgent


class ClinicalContentAgent(BaseAgent):
    agent_name = "clinical_content"
    agent_description = "Clinical content accuracy and completeness evaluation"

    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        transcript = context["cleaned_transcript"]
        service_context = context["service_context"]

        system_prompt = f"""You are an attending physician evaluating the CLINICAL CONTENT of a medical student's oral presentation.

SERVICE: {service_context["name"]}
SPECIALTY: {service_context["specialty"]}
CLINICAL FOCUS: {service_context["focus"]}

EVALUATE:
1. Medical terminology — accurate and appropriate?
2. HPI completeness — pertinent positives and negatives included?
3. History elements — PMH, meds, allergies, social/family hx relevant and complete?
4. Physical exam — appropriate findings reported? Key findings highlighted?
5. Data interpretation — labs, imaging referenced correctly?
6. Service-specific knowledge — does content reflect understanding of {service_context["name"]}?

Service background elements (require only those relevant to this presentation format): {", ".join(service_context["key_elements"])}

Return JSON:
{{
    "score": 7,
    "elements_present": ["list of key elements that were included"],
    "elements_missing": ["list of key elements that were missing or inadequate"],
    "terminology_issues": ["any medical terminology errors or misuse"],
    "content_analysis": "4-6 sentence detailed analysis of the clinical content with specific examples from the presentation",
    "service_specific_notes": "2-3 sentences on how well the content matches {service_context["name"]} expectations"
}}

Score 1-10. Be specific — cite examples from the transcript."""

        system_prompt += "\n\n" + self.format_guidance(context)

        user_prompt = f"""Evaluate the clinical content of this presentation for {service_context["name"]}:

TRANSCRIPT:
{transcript}"""

        return self._call_llm_json(system_prompt, user_prompt, max_tokens=1500)
