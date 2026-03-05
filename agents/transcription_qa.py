from typing import Dict, Any
from agents.base import BaseAgent


class TranscriptionQAAgent(BaseAgent):
    """Cleans transcription artifacts while preserving medical content.
    Fixes speech-to-text errors without altering meaning or reasoning.
    """

    agent_name = "transcription_qa"
    agent_description = "Transcription quality assurance and cleanup"

    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        transcript = context["transcript"]

        system_prompt = """You are a medical transcription QA specialist. Your job is to clean up a speech-to-text transcript of a medical student's oral presentation.

RULES:
1. Fix obvious speech-to-text errors in medical terminology (e.g., "hyper tension" -> "hypertension", "bee pap" -> "BiPAP")
2. Do NOT change the student's actual words, reasoning, or medical content
3. Do NOT add information that wasn't said
4. Flag segments that seem garbled or unclear as [UNCLEAR]
5. Preserve filler words and speech patterns — they are relevant for delivery analysis

Return JSON:
{
    "cleaned_transcript": "the cleaned transcript text",
    "corrections_made": ["list of corrections: 'original' -> 'corrected'"],
    "unclear_segments": ["list of segments that could not be confidently interpreted"],
    "transcript_quality": "good | fair | poor"
}"""

        user_prompt = f"""Clean up this medical presentation transcript:

{transcript}"""

        try:
            result = self._call_llm_json(system_prompt, user_prompt, max_tokens=2000)
        except Exception:
            # If parsing fails, pass through the original transcript
            result = {
                "cleaned_transcript": transcript,
                "corrections_made": [],
                "unclear_segments": [],
                "transcript_quality": "unknown",
            }

        return result
