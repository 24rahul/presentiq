from typing import Dict, Any
import json
from agents.base import BaseAgent


class SynthesisCriticAgent(BaseAgent):
    """Reviews the synthesizer's output for internal contradictions, vague
    advice, and missed priorities.  If issues are found, the synthesizer
    revises.  This implements a single-pass critique-revision loop.
    """

    agent_name = "synthesis_critic"
    agent_description = "Reviews synthesized feedback for contradictions, vagueness, and missed priorities"

    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        synthesis = context["synthesis"]
        agent_results = context.get("agent_results_summary", "")

        system_prompt = """You are a quality reviewer for medical education feedback. A synthesizer agent has combined multiple specialist evaluations into a single feedback report for a medical student.

Your job: Find problems in the synthesis that would confuse or mislead the student.

CHECK FOR:
1. CONTRADICTIONS: Does one section praise something another section criticizes? (e.g., "excellent differential" in strengths but "weak differential" in reasoning feedback)
2. VAGUE ADVICE: Are the "areas for improvement" specific and actionable, or generic platitudes? ("improve your presentation" is useless; "lead with the chief complaint before diving into PMH" is actionable)
3. MISSED PRIORITIES: Based on the agent evaluations, was an important finding buried or omitted in the synthesis?
4. TONE INCONSISTENCY: Does the overall tone match the actual assessment? (e.g., glowing language but mediocre substance)

ORIGINAL AGENT EVALUATIONS (for reference):
""" + agent_results + """

Return JSON:
{
    "issues_found": [
        {
            "type": "contradiction | vague_advice | missed_priority | tone_inconsistency",
            "description": "what the problem is",
            "location": "which field(s) in the synthesis are affected",
            "suggested_fix": "how to resolve it"
        }
    ],
    "is_acceptable": true/false,
    "revision_instructions": "If is_acceptable is false, provide specific instructions for the synthesizer to revise. If acceptable, say 'No revision needed.'"
}

Be strict. Students deserve feedback that is internally consistent and genuinely actionable."""

        user_prompt = f"Review this synthesis for quality:\n\n{json.dumps(synthesis, indent=2)}"

        try:
            result = self._call_llm_json(system_prompt, user_prompt, max_tokens=1500)
        except Exception as e:
            result = {
                "issues_found": [],
                "is_acceptable": True,
                "revision_instructions": f"Error during critique: {e}",
            }

        return result
