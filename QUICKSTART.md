# Quick Start Guide

## Get Started in 5 Minutes

### Step 1: Clone/Download the Project
If you haven't already, download this project to your computer.

### Step 2: Run the Setup Script
Open your terminal and navigate to the project directory, then run:

```bash
python setup.py
```

This will:
- Check your Python version (3.8+ required)
- Install system dependencies (PortAudio for audio recording)
- Install Python packages
- Create a `.env` file for your OpenAI API key

### Step 3: Get Your OpenAI API Key
1. Go to [OpenAI's website](https://platform.openai.com/api-keys)
2. Sign up or log in
3. Create a new API key
4. Copy the key

### Step 4: Add Your API Key
Edit the `.env` file and add your API key:
```
OPENAI_API_KEY=your_actual_api_key_here
```

### Step 5: Run the Application
```bash
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`

## How to Use

### Step 1: Configure Your Session
In the sidebar:
1. Enter your API key(s)
2. Select your **medical service** (e.g., Internal Medicine: Hospitalist)
3. Select your **presentation format** (Full H&P, SBAR, Consult, Handoff, Post-Op)
4. Toggle **Multi-Agent Pipeline** on/off (on by default for detailed analysis)
5. Toggle **Attending Inner Monologue** on/off (experimental feature)

### Step 2: Input Your Presentation

**Option A: Live Recording**
1. Click the "Record Audio" tab
2. Record your presentation
3. Click "Transcribe Audio"

**Option B: Upload Audio File**
1. Click the "Upload File" tab
2. Upload your audio file (WAV, MP3, M4A, FLAC, OGG)
3. Click "Transcribe Audio"

### Step 3: Review & Generate Feedback
1. Review and edit the transcription if needed
2. Click "Generate Multi-Agent Feedback"
3. Watch the pipeline progress through each agent
4. Explore feedback across tabs:
   - **Overview**: Synthesized assessment, strengths, improvements
   - **Clinical Reasoning**: Differential dx, plan coherence, data selectivity
   - **Structure & Efficiency**: Format conformance, semantic density
   - **Attending Inner Monologue**: What an attending would think at each point
   - **Teaching Points**: Case-specific pearls and suggested reading

## What Makes a Good Presentation

The expected elements depend on your **presentation format**:

### Full H&P (New Admissions)
- Chief complaint & HPI, PMH/PSH, Medications & Allergies
- Social/Family history, Review of Systems
- Physical exam, Labs/Imaging
- Assessment with differential diagnosis, Plan with rationale

### SBAR (Handoffs / Urgent Communication)
- **Situation**: What is happening right now
- **Background**: Relevant context
- **Assessment**: What you think is going on
- **Recommendation**: What you think should be done

### Consult
- Clear consult question, brief patient summary
- Relevant history and workup, what has been done so far
- Specific question for the consultant

### Handoff (Sign-out)
- Patient one-liner, active issues and status
- Anticipatory guidance (if-then statements)
- To-do items, code status

See the full format definitions in `configs/presentation_formats.yaml`.

## Example Presentation

*"This is a 65-year-old male with a history of hypertension and diabetes who presents to the ED with acute onset chest pain that started 2 hours ago. The pain is substernal, crushing in nature, radiates to his left arm, and is associated with diaphoresis and nausea. He denies shortness of breath or palpitations. On physical exam, he appears diaphoretic and anxious. Vital signs show blood pressure 160/90, heart rate 95, respiratory rate 18, and oxygen saturation 98% on room air. Cardiovascular exam reveals regular rate and rhythm without murmurs. Lungs are clear bilaterally. My assessment is acute coronary syndrome, most likely STEMI versus NSTEMI. Differential diagnosis includes unstable angina, aortic dissection, and pulmonary embolism. My plan is to obtain a 12-lead EKG, chest X-ray, CBC, basic metabolic panel, troponins, PT/PTT, and lipid panel. I will start aspirin, administer oxygen, establish IV access, and prepare for possible cardiac catheterization."*

## Troubleshooting

### Common Issues:

**"No module named 'pyaudio'"**
- Run: `brew install portaudio` (macOS) or install PortAudio for your system
- Then: `pip install pyaudio`

**"OpenAI API key not found"**
- Make sure your `.env` file exists and contains: `OPENAI_API_KEY=your_key`
- Restart the application after adding the key

**"No speech detected"**
- Check your microphone permissions
- Speak louder and closer to the microphone
- Ensure audio file has clear speech

**Recording button not working**
- Check microphone permissions in your browser/system
- Try uploading a file instead

### Need Help?
- Check the main README.md for detailed setup instructions
- Ensure you have Python 3.8+ installed
- Make sure your OpenAI API key is valid and has credits

## Tips for Best Results

1. **Speak Clearly**: Enunciate medical terms carefully
2. **Good Audio Quality**: Use a quiet environment
3. **Complete Presentations**: Include all standard elements
4. **Medical Terminology**: Use proper medical language
5. **Logical Flow**: Present in a structured order
