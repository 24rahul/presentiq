import streamlit as st
import tempfile
import os
from pathlib import Path
import openai
from dotenv import load_dotenv
from feedback_generator import FeedbackGenerator
from simple_recorder import audio_recorder_component

# Load environment variables
load_dotenv()

# Configure page
st.set_page_config(
    page_title="PresentIQ - Medical Presentation Feedback",
    page_icon="🧠",
    layout="wide"
)

# Initialize session state
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

# Simple CSS
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
</style>
""", unsafe_allow_html=True)

def transcribe_audio(file_path, api_key):
    """Transcribe audio using OpenAI Whisper"""
    client = openai.OpenAI(api_key=api_key)
    with open(file_path, "rb") as audio_file:
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file
        )
    return transcript.text

# Title
st.title("🧠 PresentIQ")
st.subheader("Medical Presentation Feedback System")
st.caption("Created by Rahul Gorijavolu and Emily Zhao at the Johns Hopkins University School of Medicine")

# Sidebar for configuration
with st.sidebar:
    st.header("Configuration")
    
    # API Keys
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
    
    # Model selection
    if ai_provider == "OpenAI":
        model = st.selectbox("Model", ["gpt-4o", "gpt-4", "gpt-3.5-turbo"])
    else:
        model = st.selectbox("Model", ["grok-3", "grok-2-1212"])

    # Dynamically get all services grouped by specialty
    feedback_generator_for_services = FeedbackGenerator()
    services_by_specialty = feedback_generator_for_services.get_service_options()
    
    # Flatten for selectbox with group labels
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

# Main interface
st.markdown("---")

# Check if keys are provided
if not openai_key:
    st.warning("⚠️ Please provide OpenAI API key in the sidebar to continue")
elif ai_provider == "xAI (Grok)" and not xai_key:
    st.warning("⚠️ Please provide xAI API key in the sidebar to continue")
else:
    # Initialize feedback generator
    try:
        if ai_provider == "OpenAI":
            os.environ["OPENAI_API_KEY"] = openai_key
        else:
            os.environ["XAI_API_KEY"] = xai_key
        os.environ["AI_MODEL"] = model
        
        feedback_generator = FeedbackGenerator(provider=ai_provider)
        st.sidebar.success(f"✅ {ai_provider} Ready")
        
        # Audio input options with tabs
        tab1, tab2 = st.tabs(["🎤 Record Audio", "📁 Upload File"])
        
        audio_file_path = None
        
        with tab1:
            st.markdown("### Record Your Presentation")
            st.info("💡 **Tip**: Speak clearly and include all required elements: chief complaint, HPI, history, exam, assessment, and plan.")
            
            # Audio recorder component
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
                # Save uploaded file
                with tempfile.NamedTemporaryFile(delete=False, suffix=Path(uploaded_file.name).suffix) as tmp_file:
                    tmp_file.write(uploaded_file.getvalue())
                    audio_file_path = tmp_file.name
                    st.session_state.current_audio_file = tmp_file.name
                
                st.success(f"📁 File uploaded: {uploaded_file.name}")
        
        # Process audio if we have a file
        if st.session_state.current_audio_file and os.path.exists(st.session_state.current_audio_file):
            st.markdown("---")
            
            # Transcription section
            if not st.session_state.transcription:
                if st.session_state.processing_transcription:
                    st.info("🔄 Transcribing audio... Please wait.")
                else:
                    if st.button("🎯 Transcribe Audio", type="primary", use_container_width=True, key="transcribe_btn"):
                        st.session_state.processing_transcription = True
                        st.rerun()
                
                # Handle transcription processing
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
            
            # Show transcription if available
            if st.session_state.transcription:
                with st.expander("📝 View & Edit Transcription", expanded=True):
                    # Initialize edited transcription if not set
                    if st.session_state.edited_transcription is None:
                        st.session_state.edited_transcription = st.session_state.transcription
                    
                    # Editable text area
                    edited_text = st.text_area(
                        "Transcribed Text (Editable)", 
                        value=st.session_state.edited_transcription,
                        height=150, 
                        key="transcription_editor",
                        help="You can edit the transcription to correct any errors before generating feedback."
                    )
                    
                    # Update session state when text changes
                    if edited_text != st.session_state.edited_transcription:
                        st.session_state.edited_transcription = edited_text
                        # Reset feedback if transcription is edited
                        if st.session_state.feedback:
                            st.session_state.feedback = None
                            st.info("💡 Transcription edited. Please generate feedback again to analyze the updated text.")
                
                # Feedback generation section
                if not st.session_state.feedback:
                    if st.session_state.processing_feedback:
                        st.info("🧠 Analyzing presentation... Please wait.")
                    else:
                        if st.button("🚀 Generate Feedback", type="primary", use_container_width=True, key="feedback_btn"):
                            st.session_state.processing_feedback = True
                            st.rerun()
                    
                    # Handle feedback processing
                    if st.session_state.processing_feedback:
                        try:
                            with st.spinner("🧠 Analyzing presentation..."):
                                # Use edited transcription for feedback generation
                                text_to_analyze = st.session_state.edited_transcription or st.session_state.transcription
                                feedback = feedback_generator.generate_feedback(text_to_analyze, service)
                                st.session_state.feedback = feedback
                                st.session_state.processing_feedback = False
                                st.success("🎉 Analysis complete!")
                                st.rerun()
                        except Exception as e:
                            st.session_state.processing_feedback = False
                            st.error(f"❌ Analysis failed: {e}")
                            st.rerun()
                
                # Display feedback if available
                if st.session_state.feedback:
                    feedback = st.session_state.feedback
                    
                    # Score display
                    score = feedback.get('overall_score', 7)
                    if isinstance(score, str):
                        import re
                        score_match = re.search(r'(\d+)', score)
                        score = int(score_match.group(1)) if score_match else 7
                    
                    st.markdown(f"""
                    <div class="score-banner">
                        Performance Score: {score}/10
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Feedback sections
                    st.subheader("📋 Overall Assessment")
                    st.write(feedback.get('overall_assessment', 'No assessment provided.'))
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.subheader("🔬 Clinical Content")
                        st.write(feedback.get('clinical_content', 'No feedback provided.'))
                        
                        if feedback.get('strengths'):
                            st.subheader("✅ Strengths")
                            for strength in feedback['strengths']:
                                st.write(f"• {strength}")
                    
                    with col2:
                        st.subheader("🧠 Clinical Reasoning")
                        st.write(feedback.get('clinical_reasoning', 'No feedback provided.'))
                        
                        if feedback.get('areas_for_improvement'):
                            st.subheader("🔧 Areas for Improvement")
                            for area in feedback['areas_for_improvement']:
                                st.write(f"• {area}")
                    
                    st.subheader("📊 Presentation Structure")
                    st.write(feedback.get('presentation_structure', 'No feedback provided.'))
                    
                    # Download report
                    if st.button("📄 Download Report", use_container_width=True, key="download_btn"):
                        # Create report content
                        report_lines = [
                            "PRESENTIQ - MEDICAL PRESENTATION FEEDBACK REPORT",
                            "=" * 60,
                            "",
                            f"Service: {feedback.get('service', 'General Medicine')}",
                            f"Performance Score: {score}/10",
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
                            "STRENGTHS:"
                        ]
                        
                        # Add strengths
                        for strength in feedback.get('strengths', []):
                            report_lines.append(f"• {strength}")
                        
                        report_lines.extend([
                            "",
                            "AREAS FOR IMPROVEMENT:"
                        ])
                        
                        # Add improvements
                        for area in feedback.get('areas_for_improvement', []):
                            report_lines.append(f"• {area}")
                        
                        report_lines.extend([
                            "",
                            "TRANSCRIPT:",
                            st.session_state.edited_transcription or st.session_state.transcription,
                            "",
                            "Generated by PresentIQ - Created by Rahul Gorijavolu and Emily Zhao at the Johns Hopkins University School of Medicine"
                        ])
                        
                        report = "\n".join(report_lines)
                        
                        st.download_button(
                            "📥 Download Report",
                            data=report,
                            file_name=f"presentiq_report_{service}.txt",
                            mime="text/plain",
                            key="download_report_btn"
                        )
                
                # Reset button
                if st.button("🔄 Start Over", use_container_width=True, key="reset_btn"):
                    # Clean up files
                    if st.session_state.current_audio_file and os.path.exists(st.session_state.current_audio_file):
                        try:
                            os.unlink(st.session_state.current_audio_file)
                        except:
                            pass
                    
                    # Reset session state
                    st.session_state.transcription = None
                    st.session_state.edited_transcription = None
                    st.session_state.feedback = None
                    st.session_state.current_audio_file = None
                    st.session_state.processing_transcription = False
                    st.session_state.processing_feedback = False
                    
                    st.rerun()
                
    except Exception as e:
        st.sidebar.error(f"❌ Setup Error: {e}")
        st.error("Please check your API configuration and try again.")

# Instructions
st.markdown("---")
st.markdown("""
### 📋 How to Use:
1. **Configure**: Enter your API keys in the sidebar
2. **Record or Upload**: Use the "Record Audio" tab to record live, or "Upload File" for existing audio
3. **Transcribe**: Click to convert speech to text
4. **Analyze**: Generate AI feedback on your presentation
5. **Review**: Read detailed feedback and download report
""")

 