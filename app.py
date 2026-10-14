import os
from contextlib import nullcontext
from html import escape
from uuid import uuid4

import streamlit as st
from dotenv import load_dotenv

from presentiq.reports.archive import create_data_package
from presentiq.web.feedback import display_legacy_feedback, display_multi_agent_feedback

load_dotenv()

from presentiq.access import CapacityError, access_token_valid, study_usage
from presentiq.ai.backend import AIBackend, AnalysisError
from presentiq.ai.legacy import FeedbackGenerator
from presentiq.ai.pipeline import FeedbackPipeline, get_format_options
from presentiq.integrations.sheets import is_logging_configured, log_submission
from presentiq.reports.text import generate_report
from presentiq.services import SERVICE_CONTEXTS
from presentiq.validation import validate_analysis_input
from presentiq.web.portal import (
    load_clerkship_config,
    render_clerkship_selection,
    render_dashboard,
)
from presentiq.web.recorder import audio_recorder_component
from presentiq.web.state import clear_feedback, reset_submission, set_audio, update_transcript

st.set_page_config(
    page_title="PresentIQ - Medical Presentation Feedback", page_icon="P", layout="wide"
)

# Session state defaults
_defaults = {
    "transcription": None,
    "edited_transcription": None,
    "feedback": None,
    "audio_data": None,
    "audio_name": None,
    "audio_signature": None,
    "audio_epoch": 0,
    "page": "select_clerkship",
    "selected_clerkship": None,
    "clerkship_data": None,
    "active_case": None,
    "active_case_index": None,
    "data_logged": False,
    "logging_attempted": False,
    "logging_error": None,
    "submission_id": None,
    "analysis_settings": None,
}
for key, val in _defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val

# Shared CSS
st.markdown(
    """
<style>
    .stButton > button {
        width: 100%;
        background: #3498db;
        color: white;
        border: none;
        padding: 0.5rem;
        border-radius: 5px;
    }
    .score-banner {
        background: linear-gradient(135deg, #3498db, #2980b9);
        color: white;
        padding: 1rem;
        border-radius: 8px;
        text-align: center;
        margin: 1rem 0;
        font-size: 1.2rem;
        font-weight: bold;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: rgba(52, 152, 219, 0.1);
        border-radius: 8px;
        padding: 4px;
    }
    .stTabs [data-baseweb="tab"] {
        background: transparent;
        border-radius: 6px;
        color: #2c3e50;
        font-weight: 500;
    }
    .stTabs [aria-selected="true"] {
        background: #3498db !important;
        color: white !important;
    }
    .thought-bubble {
        background: #f0f7ff;
        border-left: 4px solid #3498db;
        padding: 0.8rem 1rem;
        margin: 0.5rem 0;
        border-radius: 0 8px 8px 0;
    }
    .thought-type-questioning { border-left-color: #e67e22; }
    .thought-type-concerned { border-left-color: #e74c3c; }
    .thought-type-impressed { border-left-color: #27ae60; }
    .thought-type-satisfied { border-left-color: #27ae60; }
    .thought-type-confused { border-left-color: #e74c3c; }
    .thought-type-expecting { border-left-color: #f39c12; }
    .thought-type-noting { border-left-color: #95a5a6; }
</style>
""",
    unsafe_allow_html=True,
)


# Audio transcription helper
def transcribe_audio(audio_data, audio_name, api_key):
    try:
        with AIBackend("OpenAI", api_key=api_key) as backend:
            transcript = backend.client.audio.transcriptions.create(
                model="whisper-1",
                file=(audio_name, audio_data),
            )
        if not transcript.text.strip():
            raise ValueError("Empty transcription")
        return transcript.text
    except Exception as exc:
        raise AnalysisError(
            "Transcription could not be completed. Check your audio and API access, then retry."
        ) from exc


def _researcher_access_allowed():
    if not os.getenv("PRESENTIQ_ACCESS_TOKEN"):
        st.error("Researcher access is not configured. Please contact the study administrator.")
        return False
    token = st.text_input(
        "Researcher access token",
        type="password",
        key="researcher_access_token",
        help="Use the researcher token provided by your study administrator.",
    )
    if not token:
        st.info("Enter your researcher access token to use study-provided AI in Advanced Mode.")
        return False
    if not access_token_valid(token):
        st.error("The researcher access token is incorrect.")
        return False
    return True


def _back_to_dashboard():
    reset_submission(st.session_state)
    st.session_state.page = "dashboard"


def _log_current_submission(case, clerkship_data, settings):
    logged, message = log_submission(
        clerkship=clerkship_data,
        case=case,
        transcript=st.session_state.edited_transcription,
        feedback=st.session_state.feedback,
        score=st.session_state.feedback["overall_score"],
        ai_provider=settings["provider"],
        model=settings["model"],
        submission_id=st.session_state.submission_id,
    )
    st.session_state.data_logged = logged
    st.session_state.logging_attempted = True
    st.session_state.logging_error = None if logged else message


def render_presentiq_app(
    preset_service=None,
    preset_format=None,
    preset_provider=None,
    preset_model=None,
    show_sidebar_config=True,
    portal_mode=False,
):
    st.title("PresentIQ")
    if portal_mode:
        case = st.session_state.get("active_case") or {}
        clerkship_data = st.session_state.get("clerkship_data") or {}
        st.subheader(case.get("title", "Record Presentation"))
        st.button("Back to Dashboard", key="back_to_dash", on_click=_back_to_dashboard)
    else:
        st.subheader("Medical Presentation Feedback System")

    if show_sidebar_config:
        with st.sidebar:
            st.header("Configuration")
            user_openai_key = st.text_input(
                "OpenAI API Key",
                type="password",
                key="user_openai_key",
                help="Supply your own key, or leave blank to use authorized study access.",
            )
            ai_provider = st.selectbox("AI Provider", ["OpenAI", "xAI (Grok)"])
            user_xai_key = ""
            if ai_provider == "xAI (Grok)":
                user_xai_key = st.text_input("xAI API Key", type="password", key="user_xai_key")
            model = st.selectbox(
                "Model",
                ["gpt-5.5", "gpt-4o", "gpt-4", "gpt-3.5-turbo"]
                if ai_provider == "OpenAI"
                else ["grok-3", "grok-2-1212"],
            )
            services_by_specialty = FeedbackGenerator.get_service_options()
            service_labels = {
                key: f"{specialty}: {name}"
                for specialty, services in services_by_specialty.items()
                for key, name in services.items()
            }
            service = st.selectbox(
                "Medical Service", list(service_labels), format_func=service_labels.get
            )
            format_options = get_format_options()
            presentation_format = st.selectbox(
                "Format Type", list(format_options), format_func=format_options.get
            )
            use_multi_agent = st.toggle("Multi-Agent Pipeline", value=True)
            enable_anticipatory = (
                st.toggle("Attending Inner Monologue (Experimental)", value=True)
                if use_multi_agent
                else False
            )
        openai_key = user_openai_key or os.getenv("OPENAI_API_KEY", "")
        analysis_key = (
            openai_key
            if ai_provider == "OpenAI"
            else (user_xai_key or os.getenv("XAI_API_KEY", ""))
        )
        using_study_access = not user_openai_key or (ai_provider != "OpenAI" and not user_xai_key)
    else:
        defaults = load_clerkship_config().get("presentation_defaults", {})
        ai_provider = preset_provider or "OpenAI"
        model = preset_model or "gpt-5.5"
        service = preset_service or "internal_medicine_hospitalist"
        presentation_format = preset_format or "full_hp"
        use_multi_agent = defaults.get("use_multi_agent", True)
        enable_anticipatory = defaults.get("enable_anticipatory", True)
        openai_key = os.getenv("OPENAI_API_KEY", "")
        analysis_key = openai_key if ai_provider == "OpenAI" else os.getenv("XAI_API_KEY", "")
        using_study_access = True

    if not openai_key or not analysis_key:
        st.warning(
            "Provide the required API keys in Advanced Mode, or contact the study administrator to configure study access."
        )
        return
    if using_study_access and not portal_mode and not _researcher_access_allowed():
        return

    settings = {
        "provider": ai_provider,
        "model": model,
        "service": service,
        "presentation_format": presentation_format,
        "multi_agent": use_multi_agent,
        "anticipatory": enable_anticipatory,
    }
    if st.session_state.feedback and st.session_state.analysis_settings != settings:
        clear_feedback(st.session_state)
        st.info("Analysis settings changed. Generate feedback again for these settings.")

    logging_enabled = portal_mode and is_logging_configured()
    st.info(
        f"Your audio is kept in this session and sent to OpenAI for transcription. "
        f"Your transcript is sent to {ai_provider} to generate feedback. "
        + (
            "Completed transcripts, feedback, scores, and case details are saved to the study's Google Sheet. Audio is not saved to the sheet."
            if logging_enabled
            else "Study logging is not enabled. Download your results before leaving this session."
        )
    )
    source = st.radio("Audio source", ["Record Audio", "Upload File"], horizontal=True)
    epoch = st.session_state.audio_epoch
    if source == "Record Audio":
        audio = audio_recorder_component(key=f"recorded_audio_{epoch}")
    else:
        audio = st.file_uploader(
            "Choose audio file",
            type=["wav", "mp3", "m4a", "flac", "ogg"],
            key=f"uploaded_audio_{epoch}",
            help="Maximum size: 25 MB.",
            max_upload_size=25,
        )
    try:
        set_audio(
            st.session_state,
            audio.getvalue() if audio is not None else None,
            audio.name if audio is not None else None,
            source,
        )
    except ValueError as exc:
        reset_submission(st.session_state)
        st.error(str(exc))
        return
    if st.session_state.audio_data is None:
        return

    st.audio(st.session_state.audio_data)
    if st.session_state.transcription is None:
        if st.button("Transcribe Audio", type="primary", key="transcribe_btn"):
            try:
                with study_usage.reserve() if using_study_access else nullcontext():
                    with st.spinner("Transcribing audio..."):
                        text = transcribe_audio(
                            st.session_state.audio_data, st.session_state.audio_name, openai_key
                        )
                st.session_state.transcription = text
                st.session_state.edited_transcription = text
                st.rerun()
            except (AnalysisError, CapacityError) as exc:
                st.error(str(exc))
        return

    with st.expander("View & Edit Transcription", expanded=True):
        edited_text = st.text_area(
            "Transcribed Text (Editable)",
            value=st.session_state.edited_transcription,
            height=150,
            key="transcription_editor",
            help="Correct transcription errors before generating feedback.",
        )
        update_transcript(st.session_state, edited_text)
    valid_text = True
    try:
        validate_analysis_input(edited_text, service, presentation_format)
    except ValueError as exc:
        st.warning(str(exc))
        valid_text = False

    if not st.session_state.feedback:
        label = "Generate Multi-Agent Feedback" if use_multi_agent else "Generate Feedback"
        if st.button(label, type="primary", key="feedback_btn", disabled=not valid_text):
            try:
                with study_usage.reserve() if using_study_access else nullcontext():
                    if use_multi_agent:
                        progress = st.progress(0)
                        status = st.empty()

                        def update_progress(name, step, total):
                            progress.progress((step - 1) / total)
                            status.text(f"Step {step}/{total}: {name}...")

                        with FeedbackPipeline(
                            ai_provider, api_key=analysis_key, model=model
                        ) as pipeline:
                            feedback = pipeline.run(
                                edited_text,
                                service,
                                SERVICE_CONTEXTS,
                                presentation_format=presentation_format,
                                enable_anticipatory=enable_anticipatory,
                                progress_callback=update_progress,
                            )
                        progress.progress(1.0)
                    else:
                        with st.spinner("Analyzing presentation..."):
                            with FeedbackGenerator(
                                ai_provider, api_key=analysis_key, model=model
                            ) as generator:
                                feedback = generator.generate_feedback(
                                    edited_text, service, presentation_format
                                )
                st.session_state.feedback = feedback
                st.session_state.analysis_settings = settings.copy()
                st.session_state.submission_id = uuid4().hex
                st.session_state.data_logged = False
                st.session_state.logging_attempted = False
                st.session_state.logging_error = None
                st.rerun()
            except (AnalysisError, CapacityError, ValueError) as exc:
                st.error(str(exc))

    if st.session_state.feedback:
        feedback = st.session_state.feedback
        score = feedback["overall_score"]
        st.markdown(
            f'<div class="score-banner">Performance Score: {score}/10 | '
            f"Format: {escape(feedback.get('presentation_format', 'Standard'))}</div>",
            unsafe_allow_html=True,
        )
        if "_agent_results" in feedback:
            display_multi_agent_feedback(feedback)
        else:
            display_legacy_feedback(feedback)

        if logging_enabled:
            if not st.session_state.logging_attempted:
                _log_current_submission(case, clerkship_data, settings)
            if not st.session_state.data_logged:
                if st.button("Retry saving to study", key="retry_logging"):
                    _log_current_submission(case, clerkship_data, settings)
                if st.session_state.logging_error:
                    st.warning(
                        f"Your submission has not been confirmed as saved. {st.session_state.logging_error}"
                    )
            if st.session_state.data_logged:
                st.success("Submission saved to the study's Google Sheet.")

        if portal_mode:
            st.markdown("### Download Your Data")
            st.caption(
                "Download your audio and reports before leaving. Audio is only kept in this session. "
                + (
                    "Study records successfully saved to Google Sheets remain there."
                    if logging_enabled
                    else "Study logging is not enabled; keep your download for your records."
                )
            )
            data, filename = create_data_package(
                audio_data=st.session_state.audio_data,
                audio_name=st.session_state.audio_name,
                transcript=st.session_state.transcription,
                edited_transcript=st.session_state.edited_transcription,
                feedback=feedback,
                case=case,
                clerkship_data=clerkship_data,
                ai_provider=ai_provider,
                model=model,
                submission_id=st.session_state.submission_id,
            )
            st.download_button(
                "Download Complete Data Package",
                data=data,
                file_name=filename,
                mime="application/zip",
                key="download_zip_btn",
            )
        else:
            report = generate_report(
                feedback, ai_provider, model, service, st.session_state.edited_transcription
            )
            st.download_button(
                "Download Report",
                data=report,
                file_name=f"presentiq_report_{service}.txt",
                mime="text/plain",
                key="download_report_btn",
            )

    st.button("Start Over", key="reset_btn", on_click=reset_submission, args=(st.session_state,))


# Page router
config = load_clerkship_config()

page = st.session_state.get("page", "select_clerkship")

if page == "select_clerkship":
    render_clerkship_selection(config)

elif page == "dashboard":
    render_dashboard(config)

elif page == "presentiq":
    case = st.session_state.get("active_case", {})
    render_presentiq_app(
        preset_service=case.get("service"),
        preset_format=case.get("presentation_format"),
        preset_provider=config.get("presentation_defaults", {}).get("ai_provider", "OpenAI"),
        preset_model=config.get("presentation_defaults", {}).get("model", "gpt-5.5"),
        show_sidebar_config=False,
        portal_mode=True,
    )

elif page == "advanced":
    render_presentiq_app(show_sidebar_config=True, portal_mode=False)

else:
    render_clerkship_selection(config)
