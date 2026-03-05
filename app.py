import streamlit as st
import tempfile
import os
from pathlib import Path
import openai
from dotenv import load_dotenv
from feedback_generator import FeedbackGenerator
from pipeline import FeedbackPipeline, get_format_options
from simple_recorder import audio_recorder_component

load_dotenv()

st.set_page_config(
    page_title="PresentIQ - Medical Presentation Feedback",
    page_icon="🧠",
    layout="wide"
)

if 'transcription' not in st.session_state:
    st.session_state.transcription = None
if 'edited_transcription' not in st.session_state:
    st.session_state.edited_transcription = None
if 'feedback' not in st.session_state:
    st.session_state.feedback = None
if 'current_audio_file' not in st.session_state:
    st.session_state.current_audio_file = None
if 'processing_transcription' not in st.session_state:
    st.session_state.processing_transcription = False
if 'processing_feedback' not in st.session_state:
    st.session_state.processing_feedback = False
if 'pipeline_step' not in st.session_state:
    st.session_state.pipeline_step = ""

st.markdown("""
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
""", unsafe_allow_html=True)

def transcribe_audio(file_path, api_key):
    client = openai.OpenAI(api_key=api_key)
    with open(file_path, "rb") as audio_file:
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file
        )
    return transcript.text

st.title("🧠 PresentIQ")
st.subheader("Medical Presentation Feedback System")
st.caption("Created by Rahul Gorijavolu and Emily Zhao at the Johns Hopkins University School of Medicine")

with st.sidebar:
    st.header("Configuration")

    openai_key = st.text_input(
        "OpenAI API Key",
        type="password",
        value=os.getenv("OPENAI_API_KEY", ""),
        help="Required for transcription"
    )

    ai_provider = st.selectbox("AI Provider", ["OpenAI", "xAI (Grok)"])

    if ai_provider == "xAI (Grok)":
        xai_key = st.text_input(
            "xAI API Key",
            type="password",
            value=os.getenv("XAI_API_KEY", ""),
            help="Required for Grok analysis"
        )
    else:
        xai_key = None

    if ai_provider == "OpenAI":
        model = st.selectbox("Model", ["gpt-4o", "gpt-4", "gpt-3.5-turbo"])
    else:
        model = st.selectbox("Model", ["grok-3", "grok-2-1212"])

    feedback_generator_for_services = FeedbackGenerator()
    services_by_specialty = feedback_generator_for_services.get_service_options()

    service_options = []
    service_labels = {}
    for specialty, services in services_by_specialty.items():
        for key, name in services.items():
            label = f"{specialty}: {name}"
            service_options.append(key)
            service_labels[key] = label

    service = st.selectbox(
        "Medical Service",
        service_options,
        format_func=lambda x: service_labels.get(x, x.replace("_", " ").title())
    )

    st.markdown("---")

    st.subheader("Presentation Format")
    format_options = get_format_options()
    presentation_format = st.selectbox(
        "Format Type",
        list(format_options.keys()),
        format_func=lambda x: format_options.get(x, x),
        help="Select the type of presentation you are giving"
    )

    from pipeline import PRESENTATION_FORMATS
    fmt = PRESENTATION_FORMATS.get(presentation_format, {})
    if fmt:
        st.caption(fmt.get("description", ""))
        st.caption(f"Expected time: {fmt.get('time_expectation', 'N/A')}")

    st.markdown("---")

    use_multi_agent = st.toggle(
        "Multi-Agent Pipeline",
        value=True,
        help="Use the multi-agent pipeline for detailed, multi-dimensional feedback. Disable for faster single-prompt feedback."
    )

    enable_anticipatory = False
    if use_multi_agent:
        enable_anticipatory = st.toggle(
            "Attending Inner Monologue (Experimental)",
            value=True,
            help="Walk through the transcript with annotations of what an attending would be thinking at each point"
        )

st.markdown("---")

if not openai_key:
    st.warning("⚠️ Please provide OpenAI API key in the sidebar to continue")
elif ai_provider == "xAI (Grok)" and not xai_key:
    st.warning("⚠️ Please provide xAI API key in the sidebar to continue")
else:
    try:
        if ai_provider == "OpenAI":
            os.environ["OPENAI_API_KEY"] = openai_key
        else:
            os.environ["XAI_API_KEY"] = xai_key
        os.environ["AI_MODEL"] = model

        feedback_generator = FeedbackGenerator(provider=ai_provider)
        st.sidebar.success(f"✅ {ai_provider} Ready")

        tab1, tab2 = st.tabs(["🎤 Record Audio", "📁 Upload File"])

        audio_file_path = None

        with tab1:
            st.markdown("### Record Your Presentation")
            st.info("💡 **Tip**: Speak clearly and include all required elements for your selected format.")

            recorded_file = audio_recorder_component()
            if recorded_file and os.path.exists(recorded_file):
                audio_file_path = recorded_file
                st.session_state.current_audio_file = recorded_file
                st.success("✅ Recording ready for transcription!")

        with tab2:
            st.markdown("### Upload Audio File")
            uploaded_file = st.file_uploader(
                "Choose audio file",
                type=['wav', 'mp3', 'm4a', 'flac', 'ogg'],
                help="Upload your medical presentation audio file (max 25MB)"
            )

            if uploaded_file:
                with tempfile.NamedTemporaryFile(delete=False, suffix=Path(uploaded_file.name).suffix) as tmp_file:
                    tmp_file.write(uploaded_file.getvalue())
                    audio_file_path = tmp_file.name
                    st.session_state.current_audio_file = tmp_file.name

                st.success(f"📁 File uploaded: {uploaded_file.name}")

        if st.session_state.current_audio_file and os.path.exists(st.session_state.current_audio_file):
            st.markdown("---")

            if not st.session_state.transcription:
                if st.session_state.processing_transcription:
                    st.info("🔄 Transcribing audio... Please wait.")
                else:
                    if st.button("🎯 Transcribe Audio", type="primary", use_container_width=True, key="transcribe_btn"):
                        st.session_state.processing_transcription = True
                        st.rerun()

                if st.session_state.processing_transcription:
                    try:
                        with st.spinner("🔄 Transcribing audio..."):
                            transcription = transcribe_audio(st.session_state.current_audio_file, openai_key)
                            st.session_state.transcription = transcription
                            st.session_state.processing_transcription = False
                            st.success("✅ Transcription complete!")
                            st.rerun()
                    except Exception as e:
                        st.session_state.processing_transcription = False
                        st.error(f"❌ Transcription failed: {e}")
                        st.rerun()

            if st.session_state.transcription:
                with st.expander("📝 View & Edit Transcription", expanded=True):
                    if st.session_state.edited_transcription is None:
                        st.session_state.edited_transcription = st.session_state.transcription

                    edited_text = st.text_area(
                        "Transcribed Text (Editable)",
                        value=st.session_state.edited_transcription,
                        height=150,
                        key="transcription_editor",
                        help="You can edit the transcription to correct any errors before generating feedback."
                    )

                    if edited_text != st.session_state.edited_transcription:
                        st.session_state.edited_transcription = edited_text
                        if st.session_state.feedback:
                            st.session_state.feedback = None
                            st.info("💡 Transcription edited. Please generate feedback again to analyze the updated text.")

                if not st.session_state.feedback:
                    if st.session_state.processing_feedback:
                        if use_multi_agent:
                            st.info(f"🧠 {st.session_state.pipeline_step or 'Running multi-agent pipeline...'}")
                        else:
                            st.info("🧠 Analyzing presentation... Please wait.")
                    else:
                        button_label = "🚀 Generate Multi-Agent Feedback" if use_multi_agent else "🚀 Generate Feedback"
                        if st.button(button_label, type="primary", use_container_width=True, key="feedback_btn"):
                            st.session_state.processing_feedback = True
                            st.rerun()

                    if st.session_state.processing_feedback:
                        try:
                            text_to_analyze = st.session_state.edited_transcription or st.session_state.transcription

                            if use_multi_agent:
                                pipeline = FeedbackPipeline(provider=ai_provider)
                                progress_bar = st.progress(0)
                                status_text = st.empty()

                                def update_progress(step_name, step_num, total):
                                    progress_bar.progress(step_num / total)
                                    status_text.text(f"Step {step_num}/{total}: {step_name}...")
                                    st.session_state.pipeline_step = f"Step {step_num}/{total}: {step_name}..."

                                feedback = pipeline.run(
                                    transcript=text_to_analyze,
                                    service=service,
                                    service_contexts=feedback_generator.service_contexts,
                                    presentation_format=presentation_format,
                                    enable_anticipatory=enable_anticipatory,
                                    progress_callback=update_progress,
                                )
                                progress_bar.progress(1.0)
                                status_text.text("Analysis complete!")
                            else:
                                with st.spinner("🧠 Analyzing presentation..."):
                                    feedback = feedback_generator.generate_feedback(text_to_analyze, service)

                            st.session_state.feedback = feedback
                            st.session_state.processing_feedback = False
                            st.session_state.pipeline_step = ""
                            st.success("🎉 Analysis complete!")
                            st.rerun()
                        except Exception as e:
                            st.session_state.processing_feedback = False
                            st.session_state.pipeline_step = ""
                            st.error(f"❌ Analysis failed: {e}")
                            st.rerun()

                if st.session_state.feedback:
                    feedback = st.session_state.feedback

                    score = feedback.get('overall_score', 7)
                    if isinstance(score, str):
                        import re
                        score_match = re.search(r'(\d+)', score)
                        score = int(score_match.group(1)) if score_match else 7

                    st.markdown(f"""
                    <div class="score-banner">
                        Performance Score: {score}/10 | Format: {feedback.get('presentation_format', 'Standard')}
                    </div>
                    """, unsafe_allow_html=True)

                    if use_multi_agent and "_agent_results" in feedback:
                        _display_multi_agent_feedback(feedback)
                    else:
                        _display_legacy_feedback(feedback)

                    if st.button("📄 Download Report", use_container_width=True, key="download_btn"):
                        report = _generate_report(feedback, ai_provider, model, service,
                                                  st.session_state.edited_transcription or st.session_state.transcription)
                        st.download_button(
                            "📥 Download Report",
                            data=report,
                            file_name=f"presentiq_report_{service}.txt",
                            mime="text/plain",
                            key="download_report_btn"
                        )

                if st.button("🔄 Start Over", use_container_width=True, key="reset_btn"):
                    if st.session_state.current_audio_file and os.path.exists(st.session_state.current_audio_file):
                        try:
                            os.unlink(st.session_state.current_audio_file)
                        except:
                            pass

                    st.session_state.transcription = None
                    st.session_state.edited_transcription = None
                    st.session_state.feedback = None
                    st.session_state.current_audio_file = None
                    st.session_state.processing_transcription = False
                    st.session_state.processing_feedback = False
                    st.session_state.pipeline_step = ""

                    st.rerun()

    except Exception as e:
        st.sidebar.error(f"❌ Setup Error: {e}")
        st.error("Please check your API configuration and try again.")


def _display_multi_agent_feedback(feedback):
    agent_results = feedback.get("_agent_results", {})

    tab_overview, tab_reasoning, tab_structure, tab_monologue, tab_learning = st.tabs([
        "📋 Overview",
        "🧠 Clinical Reasoning",
        "📊 Structure & Efficiency",
        "💭 Attending Inner Monologue",
        "📚 Teaching Points",
    ])

    with tab_overview:
        st.subheader("Overall Assessment")
        st.write(feedback.get('overall_assessment', 'No assessment provided.'))

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Clinical Content")
            st.write(feedback.get('clinical_content', 'No feedback provided.'))

            if feedback.get('strengths'):
                st.subheader("Strengths")
                for strength in feedback['strengths']:
                    st.write(f"• {strength}")

        with col2:
            st.subheader("Clinical Reasoning")
            st.write(feedback.get('clinical_reasoning', 'No feedback provided.'))

            if feedback.get('areas_for_improvement'):
                st.subheader("Areas for Improvement")
                for area in feedback['areas_for_improvement']:
                    st.write(f"• {area}")

        if feedback.get('plan_coherence_summary'):
            st.subheader("Plan Coherence")
            st.write(feedback['plan_coherence_summary'])

        if feedback.get('semantic_density_summary'):
            st.subheader("Information Efficiency")
            st.write(feedback['semantic_density_summary'])

        st.subheader("Communication & Professionalism")
        st.write(feedback.get('communication_professionalism', 'No feedback provided.'))

        if feedback.get('service_specific_feedback'):
            st.subheader("Service-Specific Feedback")
            st.write(feedback['service_specific_feedback'])

    with tab_reasoning:
        reasoning = agent_results.get("clinical_reasoning", {})
        if reasoning:
            st.subheader("Differential Diagnosis")
            st.write(reasoning.get("differential_assessment", "Not available."))

            st.subheader("Summary Statement Quality")
            st.write(reasoning.get("summary_statement_quality", "Not available."))

            st.subheader("Data Selectivity")
            st.write(reasoning.get("data_selectivity", "Not available."))

            st.subheader("Plan Coherence")
            st.info(reasoning.get("plan_coherence", "Not available."))

            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Reasoning Strengths")
                for s in reasoning.get("reasoning_strengths", []):
                    st.write(f"• {s}")
            with col2:
                st.subheader("Reasoning Gaps")
                for g in reasoning.get("reasoning_gaps", []):
                    st.write(f"• {g}")

    with tab_structure:
        structure = agent_results.get("structure_delivery", {})
        if structure:
            st.subheader(f"Format Conformance")
            st.write(structure.get("format_conformance", "Not available."))

            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Sections Present")
                for s in structure.get("sections_present", []):
                    st.write(f"✅ {s}")
            with col2:
                st.subheader("Sections Missing")
                for s in structure.get("sections_missing", []):
                    st.write(f"❌ {s}")

            st.subheader("Organization & Flow")
            st.write(structure.get("organization_flow", "Not available."))

            sd = structure.get("semantic_density", {})
            if sd:
                st.subheader("Semantic Density / Information Efficiency")
                st.write(sd.get("analysis", "Not available."))

                efficiency = sd.get("efficiency_rating", "unknown")
                color_map = {"efficient": "🟢", "mostly efficient": "🟡", "inefficient": "🔴"}
                st.write(f"**Efficiency Rating:** {color_map.get(efficiency, '⚪')} {efficiency}")

                col1, col2 = st.columns(2)
                with col1:
                    if sd.get("over_represented"):
                        st.write("**Over-represented (too much time):**")
                        for item in sd["over_represented"]:
                            st.write(f"• ⬆️ {item}")
                with col2:
                    if sd.get("under_represented"):
                        st.write("**Under-represented (too little time):**")
                        for item in sd["under_represented"]:
                            st.write(f"• ⬇️ {item}")

    with tab_monologue:
        anticipatory = agent_results.get("anticipatory_reasoning", {})
        monologue = anticipatory.get("inner_monologue", [])

        if monologue:
            st.subheader("What an Attending Would Be Thinking")
            st.caption("This experimental feature shows the inner monologue of an experienced attending as they listen to your presentation.")

            for entry in monologue:
                thought_type = entry.get("thought_type", "noting")
                type_icons = {
                    "questioning": "❓",
                    "expecting": "🔮",
                    "satisfied": "✅",
                    "concerned": "⚠️",
                    "confused": "😕",
                    "impressed": "⭐",
                    "noting": "📝",
                }
                icon = type_icons.get(thought_type, "💭")

                st.markdown(f"""<div class="thought-bubble thought-type-{thought_type}">
<strong>{icon} [{thought_type.upper()}]</strong><br>
<em>Hearing:</em> "{entry.get('transcript_segment', '')}"<br><br>
<strong>Attending thinks:</strong> {entry.get('attending_thought', '')}
</div>""", unsafe_allow_html=True)

            unanswered = anticipatory.get("unanswered_questions", [])
            if unanswered:
                st.subheader("Questions Left Unanswered")
                for q in unanswered:
                    st.write(f"• {q}")

            col1, col2 = st.columns(2)
            with col1:
                strengths = anticipatory.get("anticipatory_strengths", [])
                if strengths:
                    st.subheader("Anticipated Well")
                    for s in strengths:
                        st.write(f"• {s}")
            with col2:
                missed = anticipatory.get("missed_anticipations", [])
                if missed:
                    st.subheader("Could Have Anticipated")
                    for m in missed:
                        st.write(f"• {m}")

            if anticipatory.get("overall_impression"):
                st.subheader("Overall Listener Impression")
                st.write(anticipatory["overall_impression"])
        else:
            st.info("Attending Inner Monologue was not enabled for this analysis. Enable it in the sidebar to see this feature.")

    with tab_learning:
        literature = agent_results.get("literature_learning", {})

        if literature.get("case_learning_summary"):
            st.subheader("Case Learning Summary")
            st.write(literature["case_learning_summary"])

        teaching_points = literature.get("teaching_points", [])
        if teaching_points:
            st.subheader("Teaching Points")
            for tp in teaching_points:
                if isinstance(tp, dict):
                    st.markdown(f"**{tp.get('topic', 'Teaching Point')}**")
                    st.write(tp.get("point", ""))
                    if tp.get("relevance"):
                        st.caption(f"Relevance: {tp['relevance']}")
                    st.markdown("---")
                else:
                    st.write(f"• {tp}")

        reading = literature.get("suggested_reading", [])
        if reading:
            st.subheader("Suggested Reading")
            for r in reading:
                st.write(f"• {r}")

        synth_tp = feedback.get("teaching_points", [])
        if synth_tp and synth_tp != teaching_points:
            st.subheader("Key Takeaways")
            for tp in synth_tp:
                st.write(f"• {tp}")


def _display_legacy_feedback(feedback):
    st.subheader("Overall Assessment")
    st.write(feedback.get('overall_assessment', 'No assessment provided.'))

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Clinical Content")
        st.write(feedback.get('clinical_content', 'No feedback provided.'))

        if feedback.get('strengths'):
            st.subheader("Strengths")
            for strength in feedback['strengths']:
                st.write(f"• {strength}")

    with col2:
        st.subheader("Clinical Reasoning")
        st.write(feedback.get('clinical_reasoning', 'No feedback provided.'))

        if feedback.get('areas_for_improvement'):
            st.subheader("Areas for Improvement")
            for area in feedback['areas_for_improvement']:
                st.write(f"• {area}")

    st.subheader("Presentation Structure")
    st.write(feedback.get('presentation_structure', 'No feedback provided.'))


def _generate_report(feedback, ai_provider, model, service, transcript_text):
    report_lines = [
        "PRESENTIQ - MEDICAL PRESENTATION FEEDBACK REPORT",
        "=" * 60,
        "",
        f"Service: {feedback.get('service', 'General Medicine')}",
        f"Presentation Format: {feedback.get('presentation_format', 'Standard')}",
        f"Performance Score: {feedback.get('overall_score', 'N/A')}/10",
        f"AI Provider: {ai_provider}",
        f"AI Model: {model}",
        "",
        "OVERALL ASSESSMENT:",
        feedback.get('overall_assessment', 'No assessment provided.'),
        "",
        "CLINICAL CONTENT:",
        feedback.get('clinical_content', 'No feedback provided.'),
        "",
        "CLINICAL REASONING:",
        feedback.get('clinical_reasoning', 'No feedback provided.'),
        "",
        "PRESENTATION STRUCTURE:",
        feedback.get('presentation_structure', 'No feedback provided.'),
        "",
    ]

    if feedback.get('plan_coherence_summary'):
        report_lines.extend([
            "PLAN COHERENCE:",
            feedback['plan_coherence_summary'],
            "",
        ])

    if feedback.get('semantic_density_summary'):
        report_lines.extend([
            "INFORMATION EFFICIENCY:",
            feedback['semantic_density_summary'],
            "",
        ])

    if feedback.get('communication_professionalism'):
        report_lines.extend([
            "COMMUNICATION & PROFESSIONALISM:",
            feedback['communication_professionalism'],
            "",
        ])

    report_lines.append("STRENGTHS:")
    for strength in feedback.get('strengths', []):
        report_lines.append(f"• {strength}")

    report_lines.extend(["", "AREAS FOR IMPROVEMENT:"])
    for area in feedback.get('areas_for_improvement', []):
        report_lines.append(f"• {area}")

    tp = feedback.get("teaching_points", [])
    if tp:
        report_lines.extend(["", "TEACHING POINTS:"])
        for point in tp:
            report_lines.append(f"• {point}")

    agent_results = feedback.get("_agent_results", {})
    anticipatory = agent_results.get("anticipatory_reasoning", {})
    if anticipatory.get("overall_impression"):
        report_lines.extend([
            "",
            "ATTENDING INNER MONOLOGUE - OVERALL IMPRESSION:",
            anticipatory["overall_impression"],
        ])
        unanswered = anticipatory.get("unanswered_questions", [])
        if unanswered:
            report_lines.append("")
            report_lines.append("UNANSWERED QUESTIONS:")
            for q in unanswered:
                report_lines.append(f"• {q}")

    report_lines.extend([
        "",
        "TRANSCRIPT:",
        transcript_text,
        "",
        "Generated by PresentIQ - Created by Rahul Gorijavolu and Emily Zhao at the Johns Hopkins University School of Medicine",
    ])

    return "\n".join(report_lines)


st.markdown("---")
st.markdown("""
### How to Use
1. **Configure**: Enter your API keys and select your medical service in the sidebar
2. **Select Format**: Choose your presentation format (Full H&P, SBAR, Consult, Handoff, etc.)
3. **Record or Upload**: Use the "Record Audio" tab to record live, or "Upload File" for existing audio
4. **Transcribe**: Click to convert speech to text
5. **Analyze**: Generate feedback — the multi-agent pipeline provides detailed, multi-dimensional analysis
6. **Review**: Explore feedback across tabs including the experimental Attending Inner Monologue
""")
