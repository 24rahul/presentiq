"""Keep audio and its derived analysis together in one browser session."""

import hashlib
from pathlib import Path

from presentiq.validation import MAX_AUDIO_BYTES


def clear_feedback(state):
    state["feedback"] = None
    state["analysis_settings"] = None
    state["submission_id"] = None
    state["data_logged"] = False
    state["logging_attempted"] = False
    state["logging_error"] = None


def clear_analysis(state):
    clear_feedback(state)
    state["transcription"] = None
    state["edited_transcription"] = None
    state.pop("transcription_editor", None)


def reset_submission(state):
    clear_analysis(state)
    state["audio_data"] = None
    state["audio_name"] = None
    state["audio_signature"] = None
    # A new widget key releases the old recording/upload on the next render.
    state["audio_epoch"] = state.get("audio_epoch", 0) + 1


def set_audio(state, audio_data, audio_name, source):
    if audio_data is not None:
        if not audio_data:
            raise ValueError("The audio file is empty.")
        if len(audio_data) > MAX_AUDIO_BYTES:
            raise ValueError("Audio must be 25 MB or smaller.")
        if Path(audio_name).suffix.lower() not in {".wav", ".mp3", ".m4a", ".flac", ".ogg"}:
            raise ValueError("Choose a WAV, MP3, M4A, FLAC, or OGG audio file.")
        signature = (source, audio_name, hashlib.sha256(audio_data).hexdigest())
    else:
        signature = None
    if state.get("audio_signature") != signature:
        clear_analysis(state)
        state["audio_data"] = audio_data
        state["audio_name"] = audio_name if audio_data is not None else None
        state["audio_signature"] = signature


def update_transcript(state, text):
    if text != state.get("edited_transcription"):
        clear_feedback(state)
        state["edited_transcription"] = text
