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

# Pre-configured API keys
DEFAULT_OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
DEFAULT_XAI_API_KEY = os.getenv("XAI_API_KEY", "")

# Configure page
st.set_page_config(
    page_title="PresentIQ - Medical Presentation Feedback",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Clean, modern CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    .main-container {
        background: linear-gradient(135deg, #1a1d29 0%, #2c3e50 50%, #34495e 100%);
        min-height: 100vh;
        padding: 0;
    }
    
    .hero-section {
        background: linear-gradient(135deg, #2c3e50 0%, #3498db 50%, #5dade2 100%);
        padding: 2rem;
        text-align: center;
        color: white;
        border-radius: 0 0 16px 16px;
        margin-bottom: 2rem;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
    }
    
    .hero-title {
        font-size: 2.5rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
        color: white;
    }
    
    .hero-subtitle {
        font-size: 1.1rem;
        opacity: 0.9;
        margin-bottom: 1rem;
    }
    
    .developer-credit {
        font-size: 0.85rem;
        opacity: 0.8;
        margin-top: 1rem;
    }
    
    .card {
        background: #2c3e50;
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        color: #ecf0f1;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
    }
    
    .config-card {
        background: #34495e;
        border: 1px solid rgba(93, 173, 226, 0.2);
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
        color: #ecf0f1;
    }
    
    .config-card h4 {
        color: #5dade2;
        margin-bottom: 0.5rem;
        font-weight: 600;
        font-size: 1rem;
    }
    
    .status-success {
        background: linear-gradient(135deg, rgba(39, 174, 96, 0.1) 0%, rgba(39, 174, 96, 0.05) 100%);
        border: 1px solid rgba(39, 174, 96, 0.3);
        color: #2ecc71;
        padding: 0.75rem;
        border-radius: 8px;
        margin: 0.5rem 0;
    }
    
    .status-error {
        background: linear-gradient(135deg, rgba(231, 76, 60, 0.1) 0%, rgba(231, 76, 60, 0.05) 100%);
        border: 1px solid rgba(231, 76, 60, 0.3);
        color: #e74c3c;
        padding: 0.75rem;
        border-radius: 8px;
        margin: 0.5rem 0;
    }
    
    .quick-start {
        background: #34495e;
        border: 1px solid rgba(149, 165, 166, 0.2);
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
        color: #ecf0f1;
    }
    
    .quick-start h4 {
        color: #95a5a6;
        margin-bottom: 0.5rem;
    }
    
    .quick-start ol {
        margin: 0;
        padding-left: 1.2rem;
    }
    
    .quick-start li {
        margin-bottom: 0.3rem;
        color: #bdc3c7;
    }
    
    /* Selectbox styling */
    .stSelectbox > div > div {
        background: #34495e !important;
        border: 1px solid rgba(149, 165, 166, 0.3) !important;
        border-radius: 6px !important;
        color: #ecf0f1 !important;
        min-height: 44px !important;
        font-size: 14px !important;
    }
    
    .stSelectbox > div > div:focus-within {
        border-color: #5dade2 !important;
        box-shadow: 0 0 6px rgba(93, 173, 226, 0.3) !important;
    }
    
    .stSelectbox label {
        color: #ecf0f1 !important;
        font-weight: 500 !important;
    }
    
    /* Text input styling */
    .stTextInput > div > div > input {
        background: #34495e !important;
        border: 1px solid rgba(149, 165, 166, 0.3) !important;
        border-radius: 6px !important;
        color: #ecf0f1 !important;
        font-size: 14px !important;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #5dade2 !important;
        box-shadow: 0 0 6px rgba(93, 173, 226, 0.3) !important;
    }
    
    .stTextInput label {
        color: #ecf0f1 !important;
        font-weight: 500 !important;
    }
    
    /* Ensure markdown text is visible */
    .stMarkdown p, .stMarkdown strong {
        color: #000000 !important;
    }
    
    /* Sidebar text visibility */
    .sidebar .stMarkdown p, .sidebar .stMarkdown strong {
        color: #000000 !important;
    }
    
    .sidebar .element-container p, .sidebar .element-container strong {
        color: #000000 !important;
    }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(135deg, #3498db 0%, #2980b9 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 6px !important;
        font-weight: 600 !important;
        padding: 0.6rem 1.5rem !important;
        transition: all 0.2s ease !important;
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, #5dade2 0%, #3498db 100%) !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 12px rgba(52, 152, 219, 0.3) !important;
    }
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 4px;
        background: #2c3e50;
        border-radius: 8px;
        padding: 0.3rem;
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 6px;
        padding: 0.5rem 1rem;
        color: #bdc3c7;
        background: transparent;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #3498db 0%, #2980b9 100%) !important;
        color: white !important;
    }
    
    /* File uploader styling */
    .stFileUploader > div {
        background: #34495e !important;
        border: 2px dashed rgba(149, 165, 166, 0.3) !important;
        border-radius: 8px !important;
        color: #ecf0f1 !important;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display:none;}
    header {visibility: hidden;}
    
    /* Score display */
    .score-display {
        background: linear-gradient(135deg, #3498db 0%, #2980b9 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 12px;
        text-align: center;
        font-size: 1.3rem;
        font-weight: 600;
        margin: 1rem 0;
        box-shadow: 0 4px 15px rgba(52, 152, 219, 0.2);
    }
    
    /* Feedback sections */
    .feedback-section {
        background: #2c3e50;
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 8px;
        padding: 1.5rem;
        margin: 1rem 0;
        color: #ecf0f1;
    }
    
    .feedback-section h3 {
        color: #5dade2;
        margin-bottom: 1rem;
    }
    
    /* Text area styling */
    .stTextArea > div > div > textarea {
        background: #34495e !important;
        border: 1px solid rgba(149, 165, 166, 0.3) !important;
        border-radius: 6px !important;
        color: #ecf0f1 !important;
    }
    
    /* Expander styling */
    .streamlit-expanderHeader {
        background: #34495e !important;
        color: #5dade2 !important;
        border-radius: 6px !important;
    }
    
    /* Download button */
    .stDownloadButton > button {
        background: linear-gradient(135deg, #27ae60 0%, #2ecc71 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 6px !important;
        font-weight: 600 !important;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def init_feedback_generator(api_key=None, model=None, provider="OpenAI"):
    if api_key:
        if provider == "OpenAI":
            os.environ["OPENAI_API_KEY"] = api_key
        else:  # xAI
            os.environ["XAI_API_KEY"] = api_key
    if model:
        os.environ["AI_MODEL"] = model
    return FeedbackGenerator(provider=provider)

def transcribe_audio(file_path, api_key):
    """Transcribe audio using OpenAI's Whisper API"""
    client = openai.OpenAI(api_key=api_key)
    with open(file_path, "rb") as audio_file:
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file
        )
    return transcript.text

def main():
    # Hero Section
    st.markdown("""
    <div class="hero-section">
        <h1 class="hero-title">PresentIQ</h1>
        <p class="hero-subtitle">Advanced Medical Presentation Feedback</p>
        <div class="developer-credit">Developed by Rahul Gorijavolu, JHUSOM</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar Configuration
    with st.sidebar:
        st.markdown("""
        <div class="config-card">
            <h4>⚙️ Configuration</h4>
        </div>
        """, unsafe_allow_html=True)
        
        # AI Provider
        ai_provider = st.selectbox(
            "AI Provider",
            options=["OpenAI", "xAI (Grok)"],
            index=0
        )
        
        # OpenAI API Key (always required)
        st.markdown("**🔑 OpenAI API Key (Required for Transcription)**")
        openai_key = st.text_input(
            "OpenAI API Key (Required for Transcription)",
            type="password",
            value=DEFAULT_OPENAI_API_KEY,
            help="Required for audio transcription via Whisper",
            label_visibility="collapsed"
        )
        
        # xAI API Key (only for Grok)
        xai_key = None
        if ai_provider == "xAI (Grok)":
            st.markdown("**🔑 xAI API Key (Required for Grok Analysis)**")
            xai_key = st.text_input(
                "xAI API Key (Required for Grok Analysis)", 
                type="password",
                value=DEFAULT_XAI_API_KEY,
                help="Required for Grok AI analysis",
                label_visibility="collapsed"
            )
        
        # Model Selection
        if ai_provider == "OpenAI":
            model_options = {
                "gpt-4o": "GPT-4o (Latest)",
                "gpt-4.1": "GPT-4.1 (Enhanced)",
                "gpt-4": "GPT-4 (Classic)",
                "gpt-3.5-turbo": "GPT-3.5 Turbo"
            }
        else:
            model_options = {
                "grok-3": "Grok-3 (Latest)",
                "grok-3-fast": "Grok-3 Fast", 
                "grok-2-1212": "Grok-2"
            }
        
        selected_model = st.selectbox(
            "Model",
            options=list(model_options.keys()),
            format_func=lambda x: model_options[x]
        )
        
        # Check API keys
        keys_ready = openai_key and len(openai_key) > 10
        if ai_provider == "xAI (Grok)":
            keys_ready = keys_ready and xai_key and len(xai_key) > 10
        
        # Status
        if keys_ready:
            st.markdown(f"""
            <div class="status-success">
                ✅ {ai_provider} Ready
            </div>
            """, unsafe_allow_html=True)
        else:
            missing = ["OpenAI"] if not openai_key or len(openai_key) <= 10 else []
            if ai_provider == "xAI (Grok)" and (not xai_key or len(xai_key) <= 10):
                missing.append("xAI")
            st.markdown(f"""
            <div class="status-error">
                ❌ Missing: {', '.join(missing)}
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Service Selection
        if keys_ready:
            api_key_for_init = openai_key if ai_provider == "OpenAI" else xai_key
            feedback_generator = init_feedback_generator(api_key_for_init, selected_model, ai_provider)
            services = feedback_generator.get_service_options()
            
            # Flatten services for selectbox
            service_options = []
            service_map = {}
            for specialty, specialty_services in services.items():
                service_options.append(f"── {specialty} ──")
                for key, name in specialty_services.items():
                    clean_name = f"   {name.split(' - ', 1)[-1]}"
                    service_options.append(clean_name)
                    service_map[clean_name] = key
            
            selected_service_display = st.selectbox(
                "Current Rotation",
                options=service_options,
                index=1
            )
            
            selected_service = service_map.get(selected_service_display, "internal_medicine_hospitalist")
        
        else:
            selected_service = None
    
    # Quick Start Guide
    st.markdown("""
    <div class="quick-start">
        <h4>📋 Quick Start</h4>
        <ol>
            <li>Configure API keys in sidebar</li>
            <li>Select your medical rotation</li>
            <li>Record or upload presentation</li>
            <li>Get expert feedback</li>
        </ol>
    </div>
    """, unsafe_allow_html=True)
    
    # Main Interface
    if not keys_ready:
        st.markdown("""
        <div class="card">
            <h2 style="text-align: center;">🔐 Setup Required</h2>
            <p style="text-align: center; opacity: 0.8;">Please configure your API keys in the sidebar to continue.</p>
        </div>
        """, unsafe_allow_html=True)
        return
    
    # Tabs for recording/upload
    tab1, tab2 = st.tabs(["🎤 Record", "📁 Upload"])
    
    with tab1:
        col1, col2 = st.columns([2, 1])
        
        with col1:
            recorded_file = audio_recorder_component()
            if recorded_file and os.path.exists(recorded_file):
                st.success("✅ Recording complete!")
                process_audio(recorded_file, feedback_generator, selected_service, openai_key, ai_provider, selected_model)
        
        with col2:
            st.markdown("""
            <div class="card">
                <h4>📋 Tips</h4>
                <p><strong>Include:</strong> Chief complaint, HPI, history, exam, assessment, plan</p>
                <p><strong>Speak:</strong> Clearly with proper medical terms</p>
            </div>
            """, unsafe_allow_html=True)
    
    with tab2:
        uploaded_file = st.file_uploader(
            "Choose audio file",
            type=['wav', 'mp3', 'm4a', 'flac', 'ogg'],
            help="Max 25MB"
        )
        
        if uploaded_file:
            file_size = len(uploaded_file.getvalue())
            if file_size > 25 * 1024 * 1024:
                st.error("⚠️ File too large (max 25MB)")
                return
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded_file.name.split('.')[-1]}") as tmp:
                tmp.write(uploaded_file.getvalue())
                tmp_path = tmp.name
            
            st.success(f"📊 File uploaded: {uploaded_file.name}")
            process_audio(tmp_path, feedback_generator, selected_service, openai_key, ai_provider, selected_model)
            os.unlink(tmp_path)

def process_audio(file_path, feedback_generator, selected_service, openai_key, ai_provider, selected_model):
    """Process audio file - transcribe and analyze"""
    
    st.markdown("---")
    
    # Transcription
    with st.spinner("🔄 Transcribing audio..."):
        try:
            transcription = transcribe_audio(file_path, openai_key)
            if not transcription.strip():
                st.error("❌ No speech detected")
                return
            
            st.success("✅ Transcription complete")
            with st.expander("🔍 View Transcription", expanded=True):
                st.text_area("Transcribed Text", transcription, height=150)
            
        except Exception as e:
            st.error(f"❌ Transcription error: {str(e)}")
            return
    
    # Generate Feedback
    if st.button("🚀 Generate Feedback", type="primary", use_container_width=True):
        with st.spinner("🧠 Analyzing presentation..."):
            try:
                feedback = feedback_generator.generate_feedback(transcription, selected_service)
                st.success("🎉 Analysis complete!")
                display_feedback(feedback, ai_provider, selected_model, transcription)
                
            except Exception as e:
                st.error(f"❌ Analysis error: {str(e)}")

def display_feedback(feedback, ai_provider, selected_model, transcription):
    """Display feedback in clean format"""
    
    # Overall Score
    if feedback.get('overall_score', 0) > 0:
        score = feedback['overall_score']
        performance_levels = {
            9: ("Outstanding", "#27ae60"),
            8: ("Excellent", "#2ecc71"), 
            7: ("Good", "#3498db"),
            6: ("Satisfactory", "#f39c12"),
            5: ("Needs Improvement", "#e67e22"),
            0: ("Requires Development", "#e74c3c")
        }
        
        performance, color = next((v for k, v in performance_levels.items() if score >= k), 
                                  performance_levels[0])
        
        st.markdown(f"""
        <div class="score-display" style="background: linear-gradient(135deg, {color} 0%, #2980b9 100%);">
            Performance Score: {score}/10 - {performance}
        </div>
        """, unsafe_allow_html=True)
    
    # Feedback Tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📋 Overall", "🔬 Clinical", "🧠 Reasoning", "📊 Structure"])
    
    with tab1:
        st.markdown(f"""
        <div class="feedback-section">
            <h3>📋 Overall Assessment</h3>
            <p>{feedback.get('overall_assessment', 'No assessment provided.')}</p>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            if feedback.get('strengths'):
                st.markdown("### ✅ Strengths")
                for strength in feedback['strengths']:
                    st.markdown(f"• {strength}")
        
        with col2:
            if feedback.get('areas_for_improvement'):
                st.markdown("### 🔧 Areas for Improvement")
                for area in feedback['areas_for_improvement']:
                    st.markdown(f"• {area}")
    
    with tab2:
        st.markdown(f"""
        <div class="feedback-section">
            <h3>🔬 Clinical Content</h3>
            <p>{feedback.get('clinical_content', 'No feedback provided.')}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with tab3:
        st.markdown(f"""
        <div class="feedback-section">
            <h3>🧠 Clinical Reasoning</h3>
            <p>{feedback.get('clinical_reasoning', 'No feedback provided.')}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with tab4:
        st.markdown(f"""
        <div class="feedback-section">
            <h3>📊 Presentation Structure</h3>
            <p>{feedback.get('presentation_structure', 'No feedback provided.')}</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Download Report
    st.markdown("---")
    if st.button("📄 Generate Report", use_container_width=True):
        report = generate_report(feedback, transcription, ai_provider, selected_model)
        st.download_button(
            "📥 Download Report",
            data=report,
            file_name=f"presentiq_report_{ai_provider.lower().replace(' ', '_')}_{selected_model}.txt",
            mime="text/plain",
            use_container_width=True
        )

def generate_report(feedback, transcription, ai_provider, model):
    """Generate downloadable report"""
    service = feedback.get('service', 'General Medicine')
    score = feedback.get('overall_score', 'N/A')
    
    report = f"""PRESENTIQ - MEDICAL PRESENTATION FEEDBACK REPORT
{'='*60}

ANALYSIS SUMMARY
Service: {service}
Performance Score: {score}/10
AI Provider: {ai_provider}
AI Model: {model}
Developed by: Rahul Gorijavolu, JHUSOM

{'='*60}

OVERALL ASSESSMENT:
{feedback.get('overall_assessment', 'No assessment provided.')}

CLINICAL CONTENT:
{feedback.get('clinical_content', 'No feedback provided.')}

CLINICAL REASONING:
{feedback.get('clinical_reasoning', 'No feedback provided.')}

PRESENTATION STRUCTURE:
{feedback.get('presentation_structure', 'No feedback provided.')}

STRENGTHS:
"""
    
    if feedback.get('strengths'):
        for strength in feedback['strengths']:
            report += f"• {strength}\n"
    
    report += "\nAREAS FOR IMPROVEMENT:\n"
    if feedback.get('areas_for_improvement'):
        for area in feedback['areas_for_improvement']:
            report += f"• {area}\n"
    
    report += f"""

PRESENTATION TRANSCRIPT:
{'-'*40}
{transcription}

{'='*60}
Generated by PresentIQ
Powered by {ai_provider} ({model})
Developed by Rahul Gorijavolu, Johns Hopkins University School of Medicine
"""
    
    return report

if __name__ == "__main__":
    main() 