# PresentIQ - Medical Presentation Feedback System

> **Live Version:** PresentIQ is now integrated into [argosresearch.org/presentiq](https://argosresearch.org/presentiq)
>
> This repository contains the original Streamlit prototype. The production version runs on the ARGOS Research website.

![PresentIQ](https://img.shields.io/badge/PresentIQ-Medical%20AI-blue.svg)
![Python](https://img.shields.io/badge/Python-3.8+-brightgreen.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-Web%20App-red.svg)

Multi-agent feedback system for medical student oral presentations. Uses a pipeline of 7 specialized evaluation agents to provide attending-level analysis across clinical content, reasoning, structure, communication, and more.

## Features

### Audio Processing
- **Live Recording**: Record presentations directly in the browser
- **File Upload**: Support for WAV, MP3, M4A, FLAC, OGG (up to 25MB)
- **Whisper Transcription**: High-accuracy medical speech recognition

### Multi-Agent Evaluation Pipeline
Seven specialized agents evaluate different dimensions of the presentation:

| Agent | What It Evaluates |
|-------|-------------------|
| **Transcription QA** | Cleans speech-to-text artifacts, flags unclear segments |
| **Clinical Content** | Medical accuracy, completeness, service-specific knowledge |
| **Clinical Reasoning** | Differential dx, summary statement, plan coherence, data selectivity |
| **Structure & Delivery** | Format conformance, semantic density (time allocation vs. clinical relevance) |
| **Communication & Professionalism** | Audience adaptation, patient-centered language |
| **Anticipatory Reasoning** *(experimental)* | Attending inner monologue -- what an attending thinks as they listen |
| **Literature & Learning** | Case-specific teaching points and suggested reading |
| **Attending Synthesizer** | Combines all agent outputs into cohesive feedback |

### Pipeline Flow

```
                          Audio Input
                              |
                      [Whisper Transcription]
                              |
                        Raw Transcript
                              |
                   +-----------------------+
                   |  1. Transcription QA  |  Clean speech-to-text artifacts,
                   |                       |  flag unclear segments
                   +-----------------------+
                              |
                      Cleaned Transcript
                              |
                   +-----------------------+
                   |  2. Clinical Content  |  Medical accuracy, completeness,
                   |                       |  service-specific knowledge
                   +-----------------------+
                              |
                   +-----------------------+
                   | 3. Clinical Reasoning |  Differential dx, summary statement,
                   |                       |  plan coherence, data selectivity
                   +-----------------------+
                              |
        +----------+----------+----------+----------+
        |          |          |          |           |
 +-----------+ +---------+ +----------+ +------------------+
 | Structure | | Comms & | | Lit. &   | | Anticipatory     |
 | & Delivery| | Profess.| | Learning | | Reasoning (opt.) |
 +-----------+ +---------+ +----------+ +------------------+
        |          |          |          |
        +----------+----------+----------+   Step 4: PARALLEL
                              |
              +---------------+---------------+
              |                               |
  +---------------------+     +---------------------------+
  | 5a. Debate Agent    |     | 5b. Contrastive Feedback  |
  |                     |     |                           |
  | Generous vs strict  |     | Before/after rewrites     |   Step 5:
  | evaluator argue     |     | for weakest sections      |   PARALLEL
  | over assessment     |     | (flags illustrative data) |
  +---------------------+     +---------------------------+
              |                               |
              +---------------+---------------+
                              |
                +----------------------------+
                | 6. Attending Synthesizer   |  Holistic synthesis informed
                |                            |  by debate deliberation
                |  Resolves conflicts using  |
                |  debate resolutions        |
                +----------------------------+
                              |
                +----------------------------+
                | 7. Synthesis Critic        |  Reviews for contradictions,
                |                            |  vague advice, missed priorities.
                |  If issues found:          |  Auto-revises the synthesis.
                |  → revision loop           |
                +----------------------------+
                              |
                     Final Feedback Report
                    (tabs + downloadable)
```

Agents 1-3 run **sequentially** because each depends on the previous output.
Step 4 runs up to 4 agents **in parallel** (ThreadPoolExecutor) since they all only need the cleaned transcript and reasoning results.
Step 5 runs Debate + Contrastive Feedback **in parallel** — both only need step 4 results.
Step 7 (Synthesis Critic) triggers a **single revision pass** if it finds contradictions, vague advice, or missed priorities.
Anticipatory Reasoning is **optional** (toggled in sidebar).

### Presentation Format Types
Select the type of presentation you are giving for format-specific evaluation:
- **Full H&P** — New admissions, initial consults
- **Focused H&P** — Follow-ups, problem-based rounds
- **SBAR** — Handoffs, urgent communication, calling consults
- **Consult** — Presenting to a consulting service
- **Handoff (Sign-out)** — End-of-shift cross-coverage
- **Post-Operative Update** — Surgical morning rounds

### Dual Provider Support
- **OpenAI**: GPT-4o, GPT-4, GPT-3.5-turbo
- **xAI Grok**: Grok-3, Grok-2-1212

### Medical Specialty Focus
- **Service-Specific Feedback**: Tailored to rotation specialty
- **Comprehensive Coverage**: Internal Medicine, Surgery, OB/GYN, Neurology
- **Subspecialty Support**: Detailed service breakdowns

### Analysis Capabilities
- **Performance Scoring**: 1-10 scale with weighted multi-agent synthesis
- **Plan Coherence**: Does the presented information logically support the plan?
- **Semantic Density**: Is time allocated proportionally to clinical relevance?
- **Attending Inner Monologue**: See what an attending would be thinking at each point
- **Teaching Points**: Case-specific clinical pearls and suggested reading
- **Professional Reports**: Downloadable comprehensive analysis

## Quick Start

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

## Configuration

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

## Usage Workflow

1. **Configure Settings**: Set provider and API keys in sidebar
2. **Select Rotation**: Choose your current medical service
3. **Select Format**: Choose your presentation format (Full H&P, SBAR, Consult, etc.)
4. **Input Audio**: Record live or upload file
5. **Review Transcription**: Verify speech-to-text accuracy
6. **Generate Feedback**: Run the multi-agent pipeline for detailed, multi-dimensional analysis
7. **Explore Results**: Review feedback across tabs — Overview, Clinical Reasoning, Structure & Efficiency, Attending Inner Monologue, Teaching Points
8. **Download Report**: Save comprehensive feedback document

## Interface

### Feedback Tabs (Multi-Agent Mode)
- **Overview**: Synthesized assessment, strengths, improvements, plan coherence, information efficiency
- **Clinical Reasoning**: Detailed differential dx, summary statement quality, data selectivity, plan coherence
- **Structure & Efficiency**: Format conformance, sections present/missing, semantic density analysis
- **Attending Inner Monologue**: Experimental walkthrough of what an attending would think at each point
- **Teaching Points**: Case-specific clinical pearls, suggested reading, learning summary

## Privacy & Security

- No data storage — transcriptions and feedback are session-only
- API keys handled securely
- Local processing where possible
- HIPAA-conscious design (no patient data retention)

## Technical Stack

- **Backend**: Python, Streamlit
- **Models**: OpenAI Whisper, GPT-4o, xAI Grok
- **Agent Pipeline**: 7 specialized agents with parallel execution (ThreadPoolExecutor)
- **Configuration**: YAML-based presentation format definitions
- **Audio Processing**: PyAudio, Wave
- **Frontend**: HTML/CSS, JavaScript
- **Deployment**: Local/Cloud compatible

## Project Structure

```
presentiq/
├── app.py                          # Main Streamlit application
├── pipeline.py                     # Multi-agent pipeline orchestrator
├── feedback_generator.py           # Legacy single-prompt feedback (preserved)
├── agents/                         # Specialized evaluation agents
│   ├── base.py                     # Base agent class
│   ├── transcription_qa.py         # Transcription cleanup
│   ├── clinical_content.py         # Clinical content evaluation
│   ├── clinical_reasoning.py       # Reasoning + plan coherence
│   ├── structure_delivery.py       # Structure + semantic density
│   ├── communication_professionalism.py  # Communication evaluation
│   ├── anticipatory_reasoning.py   # Attending inner monologue (experimental)
│   ├── literature_learning.py      # Teaching points
│   └── synthesizer.py              # Final synthesis agent
├── configs/
│   └── presentation_formats.yaml   # Presentation format definitions
├── simple_recorder.py              # Audio recording component
├── requirements.txt                # Python dependencies
├── IDEAS.md                        # Deferred and experimental feature ideas
└── README.md
```

## Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## License

This project is developed for educational purposes at Johns Hopkins University School of Medicine.

## Support

For issues or questions:
- Create GitHub issue
- Contact: Rahul Gorijavolu and Emily Zhao, JHUSOM

## Acknowledgments

- Johns Hopkins University School of Medicine
- OpenAI for Whisper and GPT models
- xAI for Grok models
- Streamlit community

---

**PresentIQ** — Elevating medical education through intelligent feedback

*Created by Rahul Gorijavolu and Emily Zhao at the Johns Hopkins University School of Medicine*
