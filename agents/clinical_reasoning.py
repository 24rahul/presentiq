from typing import Dict, Any
from agents.base import BaseAgent


class ClinicalReasoningAgent(BaseAgent):
    """Evaluates diagnostic thinking, plan rationale, and whether the
    presented information coherently supports the plan.
    """

    agent_name = "clinical_reasoning"
    agent_description = "Clinical reasoning, differential diagnosis, and plan coherence evaluation"

    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        transcript = context["cleaned_transcript"]
        service_context = context["service_context"]

        system_prompt = f"""You are an attending physician evaluating the CLINICAL REASONING of a medical student's oral presentation.

SERVICE: {service_context['name']}
SPECIALTY: {service_context['specialty']}

EVALUATE:
1. **Differential Diagnosis**: Appropriate breadth? Most likely diagnosis justified? Dangerous diagnoses considered?
2. **Summary Statement**: Does the student synthesize findings into a clear problem representation?
3. **Data Selectivity**: Did the student highlight the right data to support their reasoning? Or present everything without filtering?
4. **Plan Coherence**: Does the presented information actually INFORM and SUPPORT the plan? Is there a logical thread from HPI -> assessment -> plan? Or does the plan feel disconnected from what was presented?
5. **Evidence-Based Reasoning**: Treatment choices appropriate? Guideline-concordant?
6. **Risk Stratification**: Severity assessment appropriate?

PLAN COHERENCE is critical — this evaluates whether the COMMUNICATION of the case builds a narrative that makes the plan feel like a natural conclusion. A student can have a correct plan but present the information in a way that doesn't lead the listener there.

Return JSON:
{{
    "score": 7,
    "differential_assessment": "2-3 sentences evaluating the differential diagnosis",
    "summary_statement_quality": "2-3 sentences on the quality of the problem synthesis/summary statement",
    "data_selectivity": "2-3 sentences on whether the student highlighted the right data vs. presented everything",
    "plan_coherence": "3-4 sentences evaluating whether the presented information logically supports and informs the plan. Does the narrative build toward the plan? Or is there a disconnect between what was said and what was proposed?",
    "reasoning_analysis": "4-6 sentence overall analysis of clinical reasoning with specific examples",
    "reasoning_strengths": ["specific strengths in reasoning"],
    "reasoning_gaps": ["specific gaps or weaknesses in reasoning"]
}}

Score 1-10. Cite specific examples from the transcript."""

        user_prompt = f"""Evaluate the clinical reasoning in this presentation for {service_context['name']}:

TRANSCRIPT:
{transcript}"""

        try:
            result = self._call_llm_json(system_prompt, user_prompt, max_tokens=1500)
        except Exception as e:
            result = {
                "score": 0,
                "differential_assessment": f"Error: {e}",
                "summary_statement_quality": "",
                "data_selectivity": "",
                "plan_coherence": "",
                "reasoning_analysis": "",
                "reasoning_strengths": [],
                "reasoning_gaps": [],
            }

        return result
