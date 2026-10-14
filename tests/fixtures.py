"""Synthetic model outputs; no patient data or external requests."""

import json

SYNTHESIS = {
    "overall_score": 8,
    "overall_assessment": "Synthetic assessment.",
    "clinical_content": "Synthetic content.",
    "clinical_reasoning": "Synthetic reasoning.",
    "presentation_structure": "Synthetic structure.",
    "service_specific_feedback": "Synthetic service feedback.",
    "strengths": ["Clear summary"],
    "areas_for_improvement": ["Prioritize the plan"],
    "teaching_points": ["Explain the rationale"],
    "communication_professionalism": "Respectful language.",
    "suggested_reading": ["Case review"],
    "semantic_density_summary": "Concise.",
    "plan_coherence_summary": "Connected plan.",
}
OUTPUTS = {
    "transcription_qa": {
        "cleaned_transcript": "Synthetic presentation.",
        "corrections_made": [],
        "unclear_segments": [],
        "transcript_quality": "good",
    },
    "clinical_content": {
        "score": 8,
        "elements_present": ["History"],
        "elements_missing": [],
        "terminology_issues": [],
        "content_analysis": "Relevant content.",
        "service_specific_notes": "Appropriate.",
    },
    "clinical_reasoning": {
        "score": 8,
        "differential_assessment": "Appropriate differential.",
        "summary_statement_quality": "Clear.",
        "data_selectivity": "Focused.",
        "plan_coherence": "Connected.",
        "reasoning_analysis": "Clear reasoning.",
        "reasoning_strengths": ["Clear"],
        "reasoning_gaps": [],
    },
    "structure_delivery": {
        "score": 8,
        "format_conformance": "Appropriate format.",
        "sections_present": ["Situation"],
        "sections_missing": [],
        "organization_flow": "Logical.",
        "semantic_density": {
            "analysis": "Concise.",
            "over_represented": [],
            "under_represented": [],
            "efficiency_rating": "efficient",
        },
        "delivery_notes": "Text only.",
        "structure_strengths": [],
        "structure_improvements": [],
    },
    "communication_professionalism": {
        "score": 8,
        "audience_adaptation": "Appropriate.",
        "patient_centered_language": "Respectful.",
        "language_appropriateness": "Clear.",
        "confidence_assessment": "Text only.",
        "communication_strengths": [],
        "communication_improvements": [],
    },
    "anticipatory_reasoning": {
        "inner_monologue": [
            {
                "transcript_segment": "Synthetic presentation",
                "attending_thought": "What is the plan?",
                "thought_type": "questioning",
            }
        ],
        "unanswered_questions": [],
        "anticipatory_strengths": [],
        "missed_anticipations": [],
        "overall_impression": "Clear.",
    },
    "literature_learning": {
        "teaching_points": [
            {"topic": "Rationale", "point": "Explain your plan.", "relevance": "Planning."}
        ],
        "suggested_reading": ["Case review"],
        "case_learning_summary": "Review rationale.",
    },
    "debate": {
        "contested_points": [
            {
                "dimension": "Content",
                "generous_view": "Clear.",
                "strict_view": "More detail.",
                "resolution": "Keep focused.",
                "adjustment": "keep",
            }
        ],
        "consensus_strengths": ["Clear"],
        "consensus_weaknesses": [],
        "overall_calibration": "Balanced.",
    },
    "contrastive_feedback": {
        "rewrites": [
            {
                "area": "Opening",
                "original": "Synthetic presentation",
                "improved": "Synthetic case summary",
                "why_better": "Concise.",
                "uses_illustrative_data": False,
            }
        ],
        "note": "Rephrased.",
    },
    "synthesizer": SYNTHESIS,
    "legacy": {
        key: value
        for key, value in SYNTHESIS.items()
        if key
        not in {
            "communication_professionalism",
            "suggested_reading",
            "semantic_density_summary",
            "plan_coherence_summary",
        }
    },
    "synthesis_critic": {
        "issues_found": [],
        "is_acceptable": True,
        "revision_instructions": "No revision needed.",
    },
}


def model_response(agent, system_prompt, user_prompt, max_tokens=1500):
    return json.dumps(OUTPUTS[agent.agent_name])
