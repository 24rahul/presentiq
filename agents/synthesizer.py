from typing import Dict, Any
from agents.base import BaseAgent


class SynthesizerAgent(BaseAgent):
    """Combines all agent outputs into a cohesive feedback report that reads
    like it comes from a single attending, not a committee.
    """

    agent_name = "synthesizer"
    agent_description = "Synthesizes all agent outputs into cohesive attending-level feedback"

    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        service_context = context["service_context"]
        format_config = context.get("format_config", {})

        # Collect all agent results
        qa_result = context.get("transcription_qa_result", {})
        content_result = context.get("clinical_content_result", {})
        reasoning_result = context.get("clinical_reasoning_result", {})
        structure_result = context.get("structure_delivery_result", {})
        communication_result = context.get("communication_professionalism_result", {})
        anticipatory_result = context.get("anticipatory_reasoning_result", {})
        literature_result = context.get("literature_learning_result", {})

        # Build the synthesis input
        agent_summaries = self._compile_agent_summaries(
            content_result, reasoning_result, structure_result,
            communication_result, anticipatory_result, literature_result
        )

        system_prompt = f"""You are a senior attending physician on {service_context['name']} ({service_context['specialty']}). You have just listened to a medical student's oral presentation and multiple specialist evaluators have provided their analyses.

Your job is to SYNTHESIZE these into a single, cohesive feedback report that reads as if it comes from one experienced attending — not a committee.

RULES:
1. Do NOT just concatenate the agent outputs. Synthesize them into a coherent narrative.
2. If agents DISAGREE, use your clinical judgment to resolve the conflict.
3. Prioritize the 3-4 MOST IMPORTANT pieces of feedback. Students can't improve everything at once.
4. Lead with strengths, then constructive feedback.
5. End with specific, actionable next steps.
6. The overall score should reflect your holistic clinical judgment across all dimensions -- do not use a formula or fixed weights. Consider the full picture the way an attending would.

Presentation format: {format_config.get('name', 'Standard')}

AGENT EVALUATIONS:
{agent_summaries}

Return JSON:
{{
    "overall_score": 7,
    "overall_assessment": "3-4 sentence cohesive summary — the kind of feedback an attending would give verbally after a presentation",
    "clinical_content": "4-6 sentence synthesis of clinical content feedback",
    "clinical_reasoning": "4-6 sentence synthesis of reasoning feedback, including plan coherence",
    "presentation_structure": "4-6 sentence synthesis of structure, format conformance, and information efficiency",
    "communication_professionalism": "3-4 sentence synthesis of communication feedback",
    "service_specific_feedback": "2-3 sentences specific to {service_context['name']}",
    "strengths": ["top 3-4 specific strengths across all dimensions"],
    "areas_for_improvement": ["top 3-4 prioritized, actionable improvements"],
    "teaching_points": ["2-3 highest-yield teaching points from this case"],
    "suggested_reading": ["1-3 specific topics to review"],
    "semantic_density_summary": "1-2 sentences on information efficiency — was time well allocated?",
    "plan_coherence_summary": "1-2 sentences on whether the presentation built a narrative that supported the plan"
}}

The overall_score must be an integer 1-10. Be honest but constructive."""

        user_prompt = "Synthesize the agent evaluations above into a single cohesive feedback report."

        try:
            result = self._call_llm_json(system_prompt, user_prompt, max_tokens=2500)
            # Ensure score is valid integer
            result["overall_score"] = self._clean_score(result.get("overall_score", 7))
        except Exception as e:
            result = self._create_fallback_synthesis(
                content_result, reasoning_result, structure_result,
                communication_result, str(e)
            )

        return result

    def _compile_agent_summaries(self, content, reasoning, structure, communication, anticipatory, literature) -> str:
        sections = []

        if content:
            sections.append(f"""CLINICAL CONTENT (Score: {content.get('score', 'N/A')}/10):
{content.get('content_analysis', 'No analysis')}
Elements missing: {', '.join(content.get('elements_missing', [])) or 'None'}
Service notes: {content.get('service_specific_notes', '')}""")

        if reasoning:
            sections.append(f"""CLINICAL REASONING (Score: {reasoning.get('score', 'N/A')}/10):
{reasoning.get('reasoning_analysis', 'No analysis')}
Differential: {reasoning.get('differential_assessment', '')}
Summary statement: {reasoning.get('summary_statement_quality', '')}
Plan coherence: {reasoning.get('plan_coherence', '')}
Data selectivity: {reasoning.get('data_selectivity', '')}""")

        if structure:
            sd = structure.get('semantic_density', {})
            sections.append(f"""STRUCTURE & DELIVERY (Score: {structure.get('score', 'N/A')}/10):
Format conformance: {structure.get('format_conformance', '')}
Organization: {structure.get('organization_flow', '')}
Semantic density: {sd.get('analysis', '')}
Over-represented: {', '.join(sd.get('over_represented', [])) or 'None'}
Under-represented: {', '.join(sd.get('under_represented', [])) or 'None'}
Efficiency: {sd.get('efficiency_rating', 'N/A')}""")

        if communication:
            sections.append(f"""COMMUNICATION & PROFESSIONALISM (Score: {communication.get('score', 'N/A')}/10):
Audience adaptation: {communication.get('audience_adaptation', '')}
Patient-centered language: {communication.get('patient_centered_language', '')}
Confidence: {communication.get('confidence_assessment', '')}""")

        if anticipatory and anticipatory.get("inner_monologue"):
            unanswered = anticipatory.get("unanswered_questions", [])
            strengths = anticipatory.get("anticipatory_strengths", [])
            missed = anticipatory.get("missed_anticipations", [])
            sections.append(f"""ANTICIPATORY REASONING (Experimental):
Overall impression: {anticipatory.get('overall_impression', '')}
Anticipatory strengths: {', '.join(strengths) or 'None noted'}
Missed anticipations: {', '.join(missed) or 'None noted'}
Unanswered questions: {', '.join(unanswered) or 'None'}""")

        if literature and literature.get("teaching_points"):
            tp_strs = [f"- {tp.get('topic', '')}: {tp.get('point', '')}" for tp in literature["teaching_points"][:3]]
            sections.append(f"""TEACHING POINTS:
{chr(10).join(tp_strs)}
Suggested reading: {', '.join(literature.get('suggested_reading', [])) or 'None'}""")

        return "\n\n".join(sections)

    def _clean_score(self, score) -> int:
        try:
            if isinstance(score, str):
                import re
                match = re.search(r'(\d+)', score)
                score = int(match.group(1)) if match else 7
            score = int(score)
            return max(1, min(10, score))
        except (ValueError, TypeError):
            return 7

    def _create_fallback_synthesis(self, content, reasoning, structure, communication, error) -> Dict[str, Any]:
        scores = []
        for r in [content, reasoning, structure, communication]:
            if r and isinstance(r.get("score"), (int, float)) and r["score"] > 0:
                scores.append(r["score"])
        avg_score = round(sum(scores) / len(scores)) if scores else 7

        return {
            "overall_score": avg_score,
            "overall_assessment": f"Synthesis encountered an error ({error}). Individual agent scores averaged to {avg_score}/10.",
            "clinical_content": content.get("content_analysis", "See individual agent output.") if content else "Not available.",
            "clinical_reasoning": reasoning.get("reasoning_analysis", "See individual agent output.") if reasoning else "Not available.",
            "presentation_structure": structure.get("format_conformance", "See individual agent output.") if structure else "Not available.",
            "communication_professionalism": communication.get("audience_adaptation", "See individual agent output.") if communication else "Not available.",
            "service_specific_feedback": "See individual agent outputs.",
            "strengths": [],
            "areas_for_improvement": [],
            "teaching_points": [],
            "suggested_reading": [],
            "semantic_density_summary": "",
            "plan_coherence_summary": "",
        }
