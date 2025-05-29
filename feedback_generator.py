import openai
import os
import json
from typing import Dict, Any
import streamlit as st

class FeedbackGenerator:
    def __init__(self, provider="OpenAI"):
        self.provider = provider
        
        if provider == "OpenAI":
            self.client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            self.model = os.getenv("AI_MODEL", "gpt-4")
        else:  # xAI (Grok)
            # Use OpenAI client with xAI base URL and API key
            self.client = openai.OpenAI(
                api_key=os.getenv("XAI_API_KEY"),
                base_url="https://api.x.ai/v1"
            )
            self.model = os.getenv("AI_MODEL", "grok-3")
            
        self.temperature = float(os.getenv("FEEDBACK_TEMPERATURE", "0.3"))
        
        # Service-specific contexts organized by specialty
        self.service_contexts = {
            # Internal Medicine Services
            "internal_medicine_hospitalist": {
                "specialty": "Internal Medicine",
                "name": "Internal Medicine - Hospitalist Service",
                "focus": "acute medical conditions, chronic disease exacerbations, medication reconciliation, discharge planning, complex medical decision-making",
                "key_elements": ["chief complaint", "HPI with pertinent positives/negatives", "past medical history", "medications with doses", "allergies", "social history", "family history", "review of systems", "physical exam", "assessment with differential", "plan with rationale"],
                "common_presentations": "heart failure exacerbations, COPD exacerbations, diabetes management, hypertension crisis, pneumonia, UTIs, sepsis, electrolyte abnormalities, acute kidney injury",
                "expectations": "thorough medical reasoning, consideration of comorbidities, medication interactions, social determinants of health, discharge planning"
            },
            "internal_medicine_icu": {
                "specialty": "Internal Medicine",
                "name": "Internal Medicine - Medical ICU",
                "focus": "critically ill patients, ventilator management, vasopressor support, multi-organ failure, sedation management",
                "key_elements": ["chief complaint", "HPI", "past medical history", "medications", "allergies", "physical exam", "ventilator settings", "drips/pressors", "labs/ABG", "assessment", "ICU-specific plan"],
                "common_presentations": "respiratory failure, septic shock, cardiogenic shock, acute respiratory distress syndrome, overdose, diabetic ketoacidosis, status epilepticus",
                "expectations": "critical care reasoning, understanding of ICU interventions, hemodynamic monitoring, ventilator management"
            },
            
            # Surgery Services
            "surgery_general": {
                "specialty": "Surgery",
                "name": "Surgery - General/Acute Care Surgery",
                "focus": "emergency surgical conditions, trauma, appendicitis, cholecystitis, bowel obstruction, hernias",
                "key_elements": ["chief complaint", "HPI", "past surgical history", "medications", "allergies", "physical exam with surgical findings", "imaging results", "labs", "assessment", "surgical vs conservative plan"],
                "common_presentations": "acute abdomen, appendicitis, cholecystitis, bowel obstruction, hernias, trauma, perforated viscus, GI bleeding",
                "expectations": "clear surgical indications, operative vs conservative management, risk stratification, post-operative care planning"
            },
            "surgery_transplant": {
                "specialty": "Surgery",
                "name": "Surgery - Transplant Surgery", 
                "focus": "organ transplant evaluation, post-transplant care, immunosuppression management, transplant complications",
                "key_elements": ["chief complaint", "HPI", "transplant history", "immunosuppressive regimen", "rejection history", "infections", "physical exam", "labs including drug levels", "assessment", "plan"],
                "common_presentations": "transplant evaluation, acute rejection, chronic rejection, post-transplant infections, immunosuppression toxicity, transplant complications",
                "expectations": "understanding of immunosuppression, rejection surveillance, infection risk, long-term complications"
            },
            "surgery_oncology": {
                "specialty": "Surgery", 
                "name": "Surgery - Surgical Oncology",
                "focus": "cancer staging, surgical resection planning, perioperative oncology care, multidisciplinary cancer care",
                "key_elements": ["chief complaint", "HPI", "oncologic history", "staging", "prior treatments", "performance status", "physical exam", "imaging", "pathology", "assessment", "surgical plan"],
                "common_presentations": "newly diagnosed cancers, metastatic disease, post-operative complications, cancer recurrence, palliative procedures",
                "expectations": "cancer staging knowledge, multidisciplinary approach, surgical oncology principles, palliative care integration"
            },
            
            # OB/GYN Services
            "obgyn_obstetrics": {
                "specialty": "Obstetrics & Gynecology",
                "name": "OB/GYN - Obstetrics",
                "focus": "pregnancy care, labor and delivery, pregnancy complications, prenatal care, postpartum care",
                "key_elements": ["chief complaint", "HPI", "obstetric history (G/P/A)", "LMP/EGA", "prenatal course", "medications", "allergies", "physical exam", "fetal assessment", "assessment", "obstetric plan"],
                "common_presentations": "pregnancy complications, preterm labor, preeclampsia, gestational diabetes, fetal growth restriction, labor management, postpartum hemorrhage",
                "expectations": "obstetric history taking, fetal assessment, pregnancy-related physiology, labor management, emergency obstetric care"
            },
            "obgyn_gynecology": {
                "specialty": "Obstetrics & Gynecology", 
                "name": "OB/GYN - Gynecology",
                "focus": "gynecologic conditions, reproductive health, contraception, gynecologic surgery, reproductive endocrinology",
                "key_elements": ["chief complaint", "HPI", "gynecologic history", "menstrual history", "sexual history", "contraceptive use", "pap history", "physical exam", "pelvic exam", "assessment", "plan"],
                "common_presentations": "abnormal uterine bleeding, pelvic pain, contraception counseling, STI screening, gynecologic cancers, infertility, menopause",
                "expectations": "reproductive health knowledge, gynecologic exam skills, contraceptive counseling, cancer screening protocols"
            },
            
            # Neurology Services
            "neurology_general": {
                "specialty": "Neurology",
                "name": "Neurology - General Neurology",
                "focus": "neurological conditions, seizure disorders, headaches, movement disorders, neuropathy, dementia",
                "key_elements": ["chief complaint", "HPI with neurologic timeline", "past medical history", "medications", "neurologic exam", "mental status", "cranial nerves", "motor/sensory exam", "coordination", "gait", "assessment with localization", "plan"],
                "common_presentations": "seizures, headaches, altered mental status, movement disorders, neuropathy, dementia, multiple sclerosis, Parkinson's disease",
                "expectations": "detailed neurologic exam, anatomic localization, neurologic differential diagnosis, understanding of neuroimaging"
            },
            "neurology_stroke": {
                "specialty": "Neurology",
                "name": "Neurology - Stroke Team",
                "focus": "acute stroke care, TIA evaluation, stroke prevention, thrombolysis, thrombectomy, stroke rehabilitation",
                "key_elements": ["chief complaint", "HPI with time of onset", "past medical history", "medications", "NIHSS", "neurologic exam", "imaging review", "assessment with stroke type", "acute stroke plan"],
                "common_presentations": "acute stroke, TIA, intracerebral hemorrhage, subarachnoid hemorrhage, stroke in evolution, post-stroke complications",
                "expectations": "stroke protocols, time windows for intervention, NIHSS scoring, stroke imaging interpretation, acute stroke management"
            },
            "neurology_icu": {
                "specialty": "Neurology",
                "name": "Neurology - Neurocritical Care",
                "focus": "critically ill neurologic patients, intracranial pressure management, status epilepticus, brain death evaluation",
                "key_elements": ["chief complaint", "HPI", "neurologic history", "medications", "neuro exam", "ICP monitoring", "ventilator settings", "imaging", "EEG results", "assessment", "neuro-ICU plan"],
                "common_presentations": "status epilepticus, traumatic brain injury, subarachnoid hemorrhage, brain death evaluation, post-operative neurosurgical patients",
                "expectations": "neurocritical care principles, ICP management, seizure management, neurologic monitoring, brain death protocols"
            }
        }
        
    def generate_feedback(self, transcription: str, service: str = "internal_medicine_hospitalist") -> Dict[str, Any]:
        """Generate expert physician feedback on the medical presentation"""
        
        service_context = self.service_contexts.get(service, self.service_contexts["internal_medicine_hospitalist"])
        
        # Create the expert physician prompt
        system_prompt = self._create_system_prompt(service_context)
        user_prompt = self._create_user_prompt(transcription, service_context)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=self.temperature,
                max_tokens=2500
            )
            
            # Parse the response
            feedback_text = response.choices[0].message.content.strip()
            
            # Clean up the response - remove markdown formatting if present
            if feedback_text.startswith('```json'):
                feedback_text = feedback_text.replace('```json', '').replace('```', '').strip()
            elif feedback_text.startswith('```'):
                feedback_text = feedback_text.replace('```', '').strip()
            
            # Try to parse as JSON with improved error handling
            try:
                feedback = json.loads(feedback_text)
                
                # Validate and clean the feedback structure
                feedback = self._validate_and_clean_feedback(feedback)
                
            except json.JSONDecodeError as e:
                st.warning(f"AI returned non-JSON response. Attempting to parse structured text...")
                feedback = self._parse_unstructured_feedback(feedback_text)
            
            # Add service context to feedback
            feedback['service'] = service_context['name']
            feedback['specialty'] = service_context['specialty']
            
            return feedback
            
        except Exception as e:
            st.error(f"Error generating feedback: {str(e)}")
            return self._create_error_feedback(str(e))
    
    def _create_system_prompt(self, service_context: Dict) -> str:
        """Create the system prompt for the expert physician"""
        return f"""You are a highly experienced attending physician specializing in {service_context['specialty']} working on the {service_context['name']} with over 20 years of clinical experience and medical education expertise. You are evaluating a medical student's oral presentation during rounds.

CRITICAL INSTRUCTIONS:
1. This is a TRANSCRIBED SPEECH presentation - ignore minor transcription errors, grammatical issues, or filler words
2. Focus on MEDICAL CONTENT, CLINICAL REASONING, and PRESENTATION STRUCTURE
3. Do NOT penalize for transcription artifacts like "um," repeated words, or minor speech-to-text errors
4. Evaluate as if you heard this presentation live during rounds
5. ALWAYS respond with valid JSON format - no additional text before or after the JSON

SERVICE CONTEXT: {service_context['name']}
SPECIALTY: {service_context['specialty']}
CLINICAL FOCUS: {service_context['focus']}
COMMON PRESENTATIONS: {service_context['common_presentations']}
SERVICE EXPECTATIONS: {service_context['expectations']}

EVALUATION CRITERIA:
1. **Clinical Content (40%)** - Analyze in detail:
   - Medical terminology accuracy and appropriate usage
   - Completeness and relevance of history of present illness
   - Appropriateness of past medical history, medications, allergies
   - Physical examination findings and their clinical significance
   - Differential diagnosis breadth and appropriateness for {service_context['specialty']}
   - Understanding of disease pathophysiology and clinical manifestations
   - Service-specific knowledge relevant to {service_context['name']}

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
   - Inclusion of all required elements: {', '.join(service_context['key_elements'])}
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
    "service_specific_feedback": "DETAILED 3-4 sentence feedback specific to {service_context['name']} expectations, protocols, and standards",
    "strengths": ["List 3-4 specific clinical and presentation strengths with examples"],
    "areas_for_improvement": ["List 3-4 specific, actionable recommendations with examples"],
    "teaching_points": ["Key learning points or clinical pearls relevant to this case and {service_context['specialty']}"]
}}

CRITICAL REQUIREMENTS:
- Each feedback section (clinical_content, clinical_reasoning, presentation_structure) must be 4-6 detailed sentences with specific examples from the presentation
- The overall_score must be an integer from 1-10 (not a string or fraction)
- Return ONLY the JSON object, no markdown formatting or additional text
- Ensure all JSON strings are properly escaped

Be constructive, specific, and focused on helping the student improve their clinical presentation skills for {service_context['specialty']} rotations, specifically {service_context['name']}."""

    def _create_user_prompt(self, transcription: str, service_context: Dict) -> str:
        """Create the user prompt with the transcription"""
        return f"""Please evaluate this medical student presentation for {service_context['name']} rounds in the {service_context['specialty']} department.

IMPORTANT: This is a transcribed oral presentation. Focus on the medical content and clinical reasoning, not transcription errors or speech patterns.

PRESENTATION TRANSCRIPT:
{transcription}

Evaluate this presentation considering:
- Required elements for {service_context['name']}: {', '.join(service_context['key_elements'])}
- Service-specific focus: {service_context['focus']}
- Clinical reasoning appropriate for {service_context['specialty']} patients
- Presentation efficiency for rounds setting

Provide specific, actionable feedback that will help this student excel on their {service_context['specialty']} rotation, specifically on the {service_context['name']}."""

    def _parse_unstructured_feedback(self, feedback_text: str) -> Dict[str, Any]:
        """Parse unstructured feedback text into a structured format"""
        
        # Basic fallback structure
        feedback = {
            "overall_score": 7,
            "overall_assessment": "",
            "clinical_content": "",
            "clinical_reasoning": "",
            "presentation_structure": "",
            "service_specific_feedback": "",
            "strengths": [],
            "areas_for_improvement": [],
            "teaching_points": []
        }
        
        # Try to extract sections based on common patterns
        sections = feedback_text.split('\n\n')
        
        for i, section in enumerate(sections):
            section_lower = section.lower()
            
            if 'overall' in section_lower and i == 0:
                feedback["overall_assessment"] = section
            elif 'clinical content' in section_lower or 'medical' in section_lower:
                feedback["clinical_content"] = section
            elif 'reasoning' in section_lower:
                feedback["clinical_reasoning"] = section
            elif 'structure' in section_lower or 'organization' in section_lower:
                feedback["presentation_structure"] = section
            elif 'service' in section_lower or 'specific' in section_lower:
                feedback["service_specific_feedback"] = section
        
        # If we couldn't parse sections, put everything in overall assessment
        if not any(feedback[key] for key in ["overall_assessment", "clinical_content", "clinical_reasoning"]):
            feedback["overall_assessment"] = feedback_text
        
        return feedback
    
    def _create_error_feedback(self, error_message: str) -> Dict[str, Any]:
        """Create error feedback when API call fails"""
        return {
            "overall_score": 0,
            "overall_assessment": f"Unable to generate feedback due to an error: {error_message}",
            "clinical_content": "Feedback unavailable due to technical error.",
            "clinical_reasoning": "Feedback unavailable due to technical error.",
            "presentation_structure": "Feedback unavailable due to technical error.",
            "service_specific_feedback": "Feedback unavailable due to technical error.",
            "strengths": [],
            "areas_for_improvement": ["Technical issue prevented feedback generation"],
            "teaching_points": ["Please try again or check your API configuration"]
        }
    
    def get_service_options(self) -> Dict[str, Dict[str, str]]:
        """Get available service options organized by specialty"""
        services_by_specialty = {}
        for key, context in self.service_contexts.items():
            specialty = context['specialty']
            if specialty not in services_by_specialty:
                services_by_specialty[specialty] = {}
            services_by_specialty[specialty][key] = context['name']
        return services_by_specialty
    
    def get_service_description(self, service: str) -> str:
        """Get description for a service"""
        context = self.service_contexts.get(service, {})
        return f"**Focus:** {context.get('focus', 'General medical care')}\n**Common Cases:** {context.get('common_presentations', 'Various medical conditions')}"

    def _validate_and_clean_feedback(self, feedback: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and clean the feedback structure"""
        
        # Ensure overall_score is an integer
        if 'overall_score' in feedback:
            try:
                # Handle various score formats
                score_value = feedback['overall_score']
                if isinstance(score_value, str):
                    # Extract number from strings like "6/10", "6", "6.0"
                    import re
                    score_match = re.search(r'(\d+)', score_value)
                    if score_match:
                        feedback['overall_score'] = int(score_match.group(1))
                    else:
                        feedback['overall_score'] = 7  # Default fallback
                elif isinstance(score_value, float):
                    feedback['overall_score'] = int(score_value)
                elif not isinstance(score_value, int):
                    feedback['overall_score'] = 7  # Default fallback
                    
                # Ensure score is within valid range
                if feedback['overall_score'] < 1:
                    feedback['overall_score'] = 1
                elif feedback['overall_score'] > 10:
                    feedback['overall_score'] = 10
                    
            except (ValueError, TypeError):
                feedback['overall_score'] = 7  # Default fallback
        else:
            feedback['overall_score'] = 7  # Default if missing
        
        # Ensure required fields exist with defaults
        required_fields = {
            'overall_assessment': 'Assessment not provided.',
            'clinical_content': 'Clinical content feedback not provided.',
            'clinical_reasoning': 'Clinical reasoning feedback not provided.',
            'presentation_structure': 'Presentation structure feedback not provided.',
            'service_specific_feedback': 'Service-specific feedback not provided.',
            'strengths': [],
            'areas_for_improvement': [],
            'teaching_points': []
        }
        
        for field, default_value in required_fields.items():
            if field not in feedback or not feedback[field]:
                feedback[field] = default_value
        
        # Ensure list fields are actually lists
        list_fields = ['strengths', 'areas_for_improvement', 'teaching_points']
        for field in list_fields:
            if not isinstance(feedback[field], list):
                feedback[field] = [str(feedback[field])] if feedback[field] else []
        
        return feedback 