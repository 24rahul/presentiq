from typing import Dict, Any
from agents.base import BaseAgent


class AnticipatoryReasoningAgent(BaseAgent):
    """Walks through the transcript and annotates what an attending would be
    thinking at each point. Helps students understand how their presentation
    lands in the listener's mind.
    """

    agent_name = "anticipatory_reasoning"
    agent_description = "Experimental: Attending inner monologue tracking through the presentation"

    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        transcript = context["cleaned_transcript"]
        service_context = context["service_context"]

        system_prompt = f"""You are a highly experienced attending physician on {service_context['name']} ({service_context['specialty']}). You are listening to a medical student's oral presentation.

YOUR TASK: Provide a running inner monologue — what you would be THINKING as you listen to each part of the presentation. Walk through the transcript sequentially and annotate your thought process.

For each segment of the presentation, capture:
- What questions arise in your mind
- What you expect to hear next
- When your expectations are met or violated
- When you feel confused, satisfied, concerned, or impressed
- When critical information is missing and you notice its absence
- When the student anticipates your questions vs. when you have to wonder

THIS IS NOT A RUBRIC EVALUATION. This is a real-time cognitive walkthrough — what goes through an attending's head as they listen.

Write in first person. Be authentic — attendings are sometimes impatient, sometimes impressed, sometimes confused. Capture that honestly.

Return JSON:
{{
    "inner_monologue": [
        {{
            "transcript_segment": "the chunk of transcript this thought responds to",
            "attending_thought": "what the attending is thinking at this moment",
            "thought_type": "questioning | expecting | satisfied | concerned | confused | impressed | noting"
        }}
    ],
    "unanswered_questions": ["questions the attending still has at the END of the presentation that were never addressed"],
    "anticipatory_strengths": ["moments where the student anticipated and preemptively addressed what the attending would wonder"],
    "missed_anticipations": ["moments where the student should have anticipated the attending's question but didn't"],
    "overall_impression": "2-3 sentences on how this presentation felt from the listener's perspective"
}}

Aim for 6-12 inner monologue entries that cover the key moments of the presentation. Focus on the most important cognitive inflection points — not every sentence."""

        user_prompt = f"""Walk through this presentation as if you're hearing it live on {service_context['name']} rounds. Provide your inner monologue:

TRANSCRIPT:
{transcript}"""

        try:
            result = self._call_llm_json(system_prompt, user_prompt, max_tokens=2500)
        except Exception as e:
            result = {
                "inner_monologue": [],
                "unanswered_questions": [],
                "anticipatory_strengths": [],
                "missed_anticipations": [],
                "overall_impression": f"Error during anticipatory reasoning analysis: {e}",
            }

        return result
