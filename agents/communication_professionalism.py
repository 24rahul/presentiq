from typing import Dict, Any
from agents.base import BaseAgent


class CommunicationProfessionalismAgent(BaseAgent):
    """Agent 4b: Evaluates communication quality and professionalism.

    Runs in parallel with StructureDeliveryAgent.
    Focuses on audience adaptation, patient-centered language, and
    professional communication standards.
    """

    agent_name = "communication_professionalism"
    agent_description = "Communication quality and professionalism evaluation"

    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        transcript = context["cleaned_transcript"]
        service_context = context["service_context"]

        system_prompt = f"""You are an attending physician evaluating the COMMUNICATION and PROFESSIONALISM of a medical student's oral presentation.

SERVICE: {service_context['name']}
SPECIALTY: {service_context['specialty']}

NOTE: This is a transcribed oral presentation. Do NOT penalize for transcription artifacts.

EVALUATE:
1. **Audience Adaptation**: Is the presentation calibrated for the audience (attending rounds vs. intern handoff vs. calling a consult)? Appropriate level of detail and language?
2. **Patient-Centered Language**: Does the student refer to the patient respectfully? Use person-first language? Avoid reductive descriptions?
3. **Medical Language Appropriateness**: Correct use of medical terminology without over-reliance on jargon where plain language would be clearer?
4. **Confidence and Assertiveness**: Does the student sound confident in their assessment? Or excessively hedging? (Account for transcription limitations)
5. **Professional Tone**: Appropriate clinical detachment while maintaining empathy?

Return JSON:
{{
    "score": 7,
    "audience_adaptation": "2-3 sentences on how well the presentation was calibrated for the audience and setting",
    "patient_centered_language": "2-3 sentences on respectful, person-centered communication",
    "language_appropriateness": "2-3 sentences on medical terminology use",
    "confidence_assessment": "2-3 sentences on confidence and assertiveness",
    "communication_strengths": ["specific strengths"],
    "communication_improvements": ["specific actionable improvements"]
}}

Score 1-10. Cite specific examples from the transcript."""

        user_prompt = f"""Evaluate the communication and professionalism of this presentation for {service_context['name']}:

TRANSCRIPT:
{transcript}"""

        try:
            result = self._call_llm_json(system_prompt, user_prompt, max_tokens=1200)
        except Exception as e:
            result = {
                "score": 0,
                "audience_adaptation": f"Error: {e}",
                "patient_centered_language": "",
                "language_appropriateness": "",
                "confidence_assessment": "",
                "communication_strengths": [],
                "communication_improvements": [],
            }

        return result
