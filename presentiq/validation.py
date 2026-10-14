"""Input limits shared by the API and interactive application."""

from presentiq.services import SERVICE_CONTEXTS

MAX_TRANSCRIPT_CHARS = 12000
MAX_AUDIO_BYTES = 25 * 1024 * 1024


def validate_analysis_input(transcript, service, presentation_format):
    from presentiq.ai.pipeline import PRESENTATION_FORMATS

    if not isinstance(transcript, str) or not transcript.strip():
        raise ValueError("Enter a non-empty presentation transcript.")
    transcript = transcript.strip()
    if len(transcript) > MAX_TRANSCRIPT_CHARS:
        raise ValueError(f"Limit the transcript to {MAX_TRANSCRIPT_CHARS:,} characters.")
    if service not in SERVICE_CONTEXTS:
        raise ValueError("Unknown medical service.")
    if presentation_format not in PRESENTATION_FORMATS:
        raise ValueError("Unknown presentation format.")
    return transcript
