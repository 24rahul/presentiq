from typing import Dict, Any
from agents.base import BaseAgent


class ClinicalContentAgent(BaseAgent):
    """Agent 2: Evaluates the medical accuracy and completeness of the presentation.

    Checks terminology, history completeness, physical exam relevance,
    and service-specific clinical knowledge.
    """

    agent_name = "clinical_content"
    agent_description = "Clinical content accuracy and completeness evaluation"

    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        transcript = context["cleaned_transcript"]
        service_context = context["service_context"]

        system_prompt = f"""You are an attending physician evaluating the CLINICAL CONTENT of a medical student's oral presentation.

SERVICE: {service_context['name']}
SPECIALTY: {service_context['specialty']}
CLINICAL FOCUS: {service_context['focus']}

EVALUATE:
1. Medical terminology — accurate and appropriate?
2. HPI completeness — pertinent positives and negatives included?
3. History elements — PMH, meds, allergies, social/family hx relevant and complete?
4. Physical exam — appropriate findings reported? Key findings highlighted?
5. Data interpretation — labs, imaging referenced correctly?
6. Service-specific knowledge — does content reflect understanding of {service_context['name']}?

Required elements for this service: {', '.join(service_context['key_elements'])}

Return JSON:
{{
    "score": 7,
    "elements_present": ["list of key elements that were included"],
    "elements_missing": ["list of key elements that were missing or inadequate"],
    "terminology_issues": ["any medical terminology errors or misuse"],
    "content_analysis": "4-6 sentence detailed analysis of the clinical content with specific examples from the presentation",
    "service_specific_notes": "2-3 sentences on how well the content matches {service_context['name']} expectations"
}}

Score 1-10. Be specific — cite examples from the transcript."""

        user_prompt = f"""Evaluate the clinical content of this presentation for {service_context['name']}:

TRANSCRIPT:
{transcript}"""

        try:
            result = self._call_llm_json(system_prompt, user_prompt, max_tokens=1500)
        except Exception as e:
            result = {
                "score": 0,
                "elements_present": [],
                "elements_missing": [],
                "terminology_issues": [],
                "content_analysis": f"Error during clinical content analysis: {e}",
                "service_specific_notes": "",
            }

        return result
