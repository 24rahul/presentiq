"""Single-prompt feedback generation with validated results."""

from typing import Any, Dict

from presentiq.ai.agents.base import BaseAgent
from presentiq.ai.backend import AIBackend
from presentiq.services import SERVICE_CONTEXTS
from presentiq.validation import validate_analysis_input


class FeedbackGenerator(AIBackend):
    service_contexts = SERVICE_CONTEXTS

    def generate_feedback(
        self,
        transcription: str,
        service: str = "internal_medicine_hospitalist",
        presentation_format: str = "full_hp",
    ) -> Dict[str, Any]:
        from presentiq.ai.pipeline import PRESENTATION_FORMATS

        transcription = validate_analysis_input(transcription, service, presentation_format)
        service_context = self.service_contexts[service]
        format_config = PRESENTATION_FORMATS[presentation_format]
        agent = BaseAgent(self.client, self.model, self.temperature)
        agent.agent_name = "legacy"
        feedback = agent._call_llm_json(
            self._create_system_prompt(service_context, format_config),
            self._create_user_prompt(transcription, service_context),
            max_tokens=2500,
        )
        feedback.update(
            status="complete",
            service=service_context["name"],
            specialty=service_context["specialty"],
            presentation_format=format_config["name"],
        )
        return feedback

    @classmethod
    def get_service_options(cls):
        specialties = {}
        for key, context in cls.service_contexts.items():
            specialties.setdefault(context["specialty"], {})[key] = context["name"]
        return specialties

    def _create_system_prompt(self, service_context: Dict, format_config: Dict) -> str:
        return f"""You are a highly experienced attending physician specializing in {service_context["specialty"]} working on the {service_context["name"]} with over 20 years of clinical experience and medical education expertise. You are evaluating a medical student's oral presentation during rounds.

CRITICAL INSTRUCTIONS:
1. This is a TRANSCRIBED SPEECH presentation - ignore minor transcription errors, grammatical issues, or filler words
2. Focus on MEDICAL CONTENT, CLINICAL REASONING, and PRESENTATION STRUCTURE
3. Do NOT penalize for transcription artifacts or speech-to-text errors
4. Evaluate as if you heard this presentation live during rounds
5. ALWAYS respond with valid JSON format - no additional text before or after the JSON

PRESENTATION FORMAT: {format_config["name"]}
EXPECTED SECTIONS: {", ".join(format_config["expected_sections"])}
Evaluate history depth and completeness against this format. Do not require a full H&P for an SBAR, handoff, consult, or brief update.

SERVICE CONTEXT: {service_context["name"]}
SPECIALTY: {service_context["specialty"]}
CLINICAL FOCUS: {service_context["focus"]}
COMMON PRESENTATIONS: {service_context["common_presentations"]}
SERVICE EXPECTATIONS: {service_context["expectations"]}

EVALUATION CRITERIA:
1. **Clinical Content (40%)** - Analyze in detail:
   - Medical terminology accuracy and appropriate usage
   - Completeness and relevance of history of present illness
   - Appropriateness of past medical history, medications, allergies
   - Physical examination findings and their clinical significance
   - Differential diagnosis breadth and appropriateness for {service_context["specialty"]}
   - Understanding of disease pathophysiology and clinical manifestations
   - Service-specific knowledge relevant to {service_context["name"]}

2. **Clinical Reasoning (30%)** - Evaluate thoroughly:
   - Logical progression from symptoms to differential diagnosis
   - Risk stratification and severity assessment
   - Evidence-based diagnostic approach and test selection
   - Treatment plan rationale and appropriateness
   - Understanding of prognosis and follow-up needs
   - Integration of patient factors (comorbidities, social determinants)
   - Service-specific protocols and guidelines application

3. **Presentation Structure (20%)** - Assess comprehensively:
   - Logical organization and flow of information
   - Inclusion of the selected format's required sections: {", ".join(format_config["expected_sections"])}
   - Efficiency and conciseness appropriate for rounds
   - Clear communication of key clinical points
   - Appropriate emphasis on critical findings
   - Professional presentation style and confidence

4. **Professionalism (10%)**:
   - Confident delivery (accounting for transcription limitations)
   - Appropriate medical language
   - Patient-centered approach

RESPONSE FORMAT - Return ONLY valid JSON (no markdown, no additional text):
{{
    "overall_score": 6,
    "overall_assessment": "2-3 sentence summary focusing on clinical strengths and areas for improvement",
    "clinical_content": "DETAILED 4-6 sentence analysis of medical accuracy, terminology usage, differential diagnosis appropriateness, history-taking completeness, physical exam relevance, and service-specific clinical knowledge. Include specific examples from the presentation.",
    "clinical_reasoning": "DETAILED 4-6 sentence evaluation of diagnostic thinking process, risk stratification, evidence-based decision making, understanding of pathophysiology, logical flow from symptoms to diagnosis to treatment, and service-specific protocols. Cite specific reasoning examples.",
    "presentation_structure": "DETAILED 4-6 sentence assessment of information organization, inclusion of required elements, efficiency for rounds setting, logical flow, completeness of case presentation, and communication clarity. Reference specific structural strengths and gaps.",
    "service_specific_feedback": "DETAILED 3-4 sentence feedback specific to {service_context["name"]} expectations, protocols, and standards",
    "strengths": ["List 3-4 specific clinical and presentation strengths with examples"],
    "areas_for_improvement": ["List 3-4 specific, actionable recommendations with examples"],
    "teaching_points": ["Key learning points or clinical pearls relevant to this case and {service_context["specialty"]}"]
}}

CRITICAL REQUIREMENTS:
- Each feedback section (clinical_content, clinical_reasoning, presentation_structure) must be 4-6 detailed sentences with specific examples from the presentation
- The overall_score must be an integer from 1-10 (not a string or fraction)
- Return ONLY the JSON object, no markdown formatting or additional text
- Ensure all JSON strings are properly escaped

Be constructive, specific, and focused on helping the student improve their clinical presentation skills for {service_context["specialty"]} rotations, specifically {service_context["name"]}."""

    def _create_user_prompt(self, transcription: str, service_context: Dict) -> str:
        return f"""Please evaluate this medical student presentation for {service_context["name"]} rounds in the {service_context["specialty"]} department.

IMPORTANT: This is a transcribed oral presentation. Focus on the medical content and clinical reasoning, not transcription errors or speech patterns.

PRESENTATION TRANSCRIPT:
{transcription}

Evaluate this presentation considering:
- Service background to include when relevant to the selected format: {", ".join(service_context["key_elements"])}
- Service-specific focus: {service_context["focus"]}
- Clinical reasoning appropriate for {service_context["specialty"]} patients
- Presentation efficiency for rounds setting

Provide specific, actionable feedback that will help this student excel on their {service_context["specialty"]} rotation, specifically on the {service_context["name"]}."""
