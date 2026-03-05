from typing import Dict, Any
from agents.base import BaseAgent


class StructureDeliveryAgent(BaseAgent):
    """Evaluates structure, format conformance, and semantic density.
    Format-aware: evaluates against the selected presentation format.
    Semantic density: checks whether time is allocated proportionally to clinical relevance.
    """

    agent_name = "structure_delivery"
    agent_description = "Presentation structure, format conformance, and information efficiency"

    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        transcript = context["cleaned_transcript"]
        service_context = context["service_context"]
        format_config = context.get("format_config", {})

        format_name = format_config.get("name", "Full H&P")
        expected_sections = format_config.get("expected_sections", [])
        time_expectation = format_config.get("time_expectation", "5-8 minutes")
        evaluation_focus = format_config.get("evaluation_focus", [])

        system_prompt = f"""You are an attending physician evaluating the STRUCTURE and DELIVERY of a medical student's oral presentation.

SERVICE: {service_context['name']}
SPECIALTY: {service_context['specialty']}

PRESENTATION FORMAT: {format_name}
EXPECTED SECTIONS: {', '.join(expected_sections) if expected_sections else 'Standard H&P format'}
TIME EXPECTATION: {time_expectation}
FORMAT-SPECIFIC EVALUATION FOCUS: {', '.join(evaluation_focus) if evaluation_focus else 'Standard organization and flow'}

EVALUATE:

1. **Format Conformance**: Did the student follow the expected {format_name} format? Were all expected sections present and in appropriate order?
2. **Organization & Flow**: Logical progression? Smooth transitions? Easy for the listener to follow?
3. **Semantic Density / Information Efficiency**: This is critical —
   - Estimate roughly what PERCENTAGE of the presentation was spent on each major section
   - Identify sections where the student spent disproportionate time on LOW-relevance information
   - Identify sections where the student RUSHED through HIGH-relevance information
   - Was the overall presentation efficient for the clinical context?
4. **Delivery**: Confidence, pacing, clarity (accounting for transcription limitations)
5. **Emphasis**: Were critical findings given appropriate emphasis? Or buried among routine data?

Return JSON:
{{
    "score": 7,
    "format_conformance": "3-4 sentences on how well the student followed the {format_name} format. Which sections were present, missing, or out of order?",
    "sections_present": ["list of expected sections that were included"],
    "sections_missing": ["list of expected sections that were missing"],
    "organization_flow": "3-4 sentences on logical organization and transitions",
    "semantic_density": {{
        "analysis": "3-4 sentences analyzing information efficiency — where was time well-spent vs. wasted?",
        "over_represented": ["topics or sections that received too much time relative to their clinical importance"],
        "under_represented": ["topics or sections that were rushed or skipped despite being clinically important"],
        "efficiency_rating": "efficient | mostly efficient | inefficient"
    }},
    "delivery_notes": "2-3 sentences on verbal delivery quality",
    "structure_strengths": ["specific structural strengths"],
    "structure_improvements": ["specific actionable improvements for structure and efficiency"]
}}

Score 1-10. Cite specific examples."""

        user_prompt = f"""Evaluate the structure and delivery of this {format_name} presentation for {service_context['name']}:

TRANSCRIPT:
{transcript}"""

        try:
            result = self._call_llm_json(system_prompt, user_prompt, max_tokens=1500)
        except Exception as e:
            result = {
                "score": 0,
                "format_conformance": f"Error: {e}",
                "sections_present": [],
                "sections_missing": [],
                "organization_flow": "",
                "semantic_density": {
                    "analysis": "",
                    "over_represented": [],
                    "under_represented": [],
                    "efficiency_rating": "unknown",
                },
                "delivery_notes": "",
                "structure_strengths": [],
                "structure_improvements": [],
            }

        return result
