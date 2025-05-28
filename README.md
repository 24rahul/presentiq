# PresentIQ - Medical Presentation Feedback System

![PresentIQ](https://img.shields.io/badge/PresentIQ-Medical%20AI-blue.svg)
![Python](https://img.shields.io/badge/Python-3.8+-brightgreen.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-Web%20App-red.svg)

**Developed by Rahul Gorijavolu, Johns Hopkins University School of Medicine**

Advanced AI-powered feedback system for medical student presentations with expert attending-level analysis.

## 🎯 Features

### 🔊 Audio Processing
- **Live Recording**: Record presentations directly in the browser
- **File Upload**: Support for WAV, MP3, M4A, FLAC, OGG (up to 25MB)
- **Whisper Transcription**: High-accuracy medical speech recognition

### 🤖 Dual AI Provider Support
- **OpenAI**: GPT-4o, GPT-4.1, GPT-4, GPT-3.5-turbo
- **xAI Grok**: Grok-3, Grok-3-Fast, Grok-2-1212
- **Smart API Management**: Automatic key validation and provider switching

### 🏥 Medical Specialty Focus
- **Service-Specific Feedback**: Tailored to rotation specialty
- **Comprehensive Coverage**: Internal Medicine, Surgery, OB/GYN, Neurology
- **Subspecialty Support**: Detailed service breakdowns

### 📊 Expert Analysis
- **Performance Scoring**: 1-10 scale with detailed breakdowns
- **Multi-Dimensional Feedback**: Clinical content, reasoning, structure
- **Actionable Insights**: Strengths and improvement areas
- **Professional Reports**: Downloadable comprehensive analysis

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- OpenAI API key (required for Whisper transcription)
- xAI API key (optional, for Grok analysis)

### Installation

1. **Clone Repository**:
   ```bash
   git clone https://github.com/your-username/presentiq.git
   cd presentiq
   ```

2. **Create Virtual Environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **macOS Audio Setup** (if needed):
   ```bash
   brew install portaudio
   ```

### Running the Application

```bash
source venv/bin/activate
streamlit run app.py
```

Navigate to `http://localhost:8501` in your browser.

## 🔧 Configuration

### API Keys
- **OpenAI**: Always required for Whisper transcription
- **xAI**: Required only when using Grok models
- Keys can be configured in the sidebar or pre-set in the application

### Medical Services
Choose your current rotation for specialty-specific feedback:
- Internal Medicine (Hospitalist, ICU, Cardiology, etc.)
- Surgery (General, Trauma, Orthopedics, etc.)
- OB/GYN (Labor & Delivery, Gynecology, etc.)
- Neurology (General, Stroke, Epilepsy, etc.)

## 📋 Usage Workflow

1. **Configure Settings**: Set AI provider and API keys in sidebar
2. **Select Rotation**: Choose your current medical service
3. **Input Audio**: Record live or upload file
4. **Review Transcription**: Verify speech-to-text accuracy
5. **Generate Feedback**: Get expert AI analysis
6. **Download Report**: Save comprehensive feedback document

## 🎨 Interface

### Clean Professional Design
- Modern tech aesthetic with medical professionalism
- Intuitive sidebar configuration
- Tabbed feedback sections for easy navigation
- Responsive design for various screen sizes

### Feedback Categories
- **Overall Assessment**: Comprehensive performance overview
- **Clinical Content**: Medical accuracy and knowledge
- **Clinical Reasoning**: Diagnostic and therapeutic thinking
- **Presentation Structure**: Organization and communication

## 🔒 Privacy & Security

- No data storage - transcriptions and feedback are session-only
- API keys handled securely
- Local processing where possible
- HIPAA-conscious design (no patient data retention)

## 🛠️ Technical Stack

- **Backend**: Python, Streamlit
- **AI Models**: OpenAI Whisper, GPT-4o, xAI Grok
- **Audio Processing**: PyAudio, Wave
- **Frontend**: HTML/CSS, JavaScript
- **Deployment**: Local/Cloud compatible

## 📁 Project Structure

```
presentiq/
├── app.py                 # Main Streamlit application
├── feedback_generator.py  # AI feedback generation logic
├── simple_recorder.py     # Audio recording component
├── requirements.txt       # Python dependencies
├── README.md             # This file
├── .gitignore           # Git ignore patterns
└── venv/                # Virtual environment
```

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📄 License

This project is developed for educational purposes at Johns Hopkins University School of Medicine.

## 🆘 Support

For issues or questions:
- Create GitHub issue
- Contact: Rahul Gorijavolu, JHUSOM

## 🙏 Acknowledgments

- Johns Hopkins University School of Medicine
- OpenAI for Whisper and GPT models
- xAI for Grok models
- Streamlit community

---

**PresentIQ** - Elevating medical education through intelligent feedback

*Developed by Rahul Gorijavolu, Johns Hopkins University School of Medicine* 