"""Record the student's browser microphone directly into session memory."""

import streamlit as st


def audio_recorder_component(key="presentation_audio"):
    return st.audio_input(
        "Record your presentation",
        key=key,
        sample_rate=16000,
        help="Allow microphone access in your browser, record your presentation, then stop to review it.",
    )
