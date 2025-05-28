import streamlit as st
import pyaudio
import wave
import threading
import time
import tempfile
import os

class SimpleRecorder:
    def __init__(self):
        self.chunk = 1024
        self.format = pyaudio.paInt16
        self.channels = 1
        self.rate = 44100
        self.recording = False
        self.frames = []
        
    def start_recording(self):
        """Start recording audio"""
        self.recording = True
        self.frames = []
        
        def record():
            p = pyaudio.PyAudio()
            
            try:
                stream = p.open(
                    format=self.format,
                    channels=self.channels,
                    rate=self.rate,
                    input=True,
                    frames_per_buffer=self.chunk
                )
                
                while self.recording:
                    data = stream.read(self.chunk, exception_on_overflow=False)
                    self.frames.append(data)
                
                stream.stop_stream()
                stream.close()
                
            except Exception as e:
                st.error(f"Recording error: {str(e)}")
            finally:
                p.terminate()
        
        # Start recording in a separate thread
        self.record_thread = threading.Thread(target=record)
        self.record_thread.daemon = True
        self.record_thread.start()
    
    def stop_recording(self):
        """Stop recording and return audio data"""
        self.recording = False
        
        if hasattr(self, 'record_thread'):
            self.record_thread.join(timeout=2)
        
        if self.frames:
            return b''.join(self.frames)
        return None
    
    def save_audio(self, audio_data, filename):
        """Save audio data to file"""
        try:
            with wave.open(filename, 'wb') as wf:
                wf.setnchannels(self.channels)
                wf.setsampwidth(pyaudio.get_sample_size(self.format))
                wf.setframerate(self.rate)
                wf.writeframes(audio_data)
            return True
        except Exception as e:
            st.error(f"Failed to save audio: {str(e)}")
            return False

def audio_recorder_component():
    """Streamlit component for audio recording with clean styling"""
    
    # Initialize recorder in session state
    if 'recorder' not in st.session_state:
        st.session_state.recorder = SimpleRecorder()
    
    if 'recording_state' not in st.session_state:
        st.session_state.recording_state = 'idle'  # idle, recording, completed
    
    if 'start_time' not in st.session_state:
        st.session_state.start_time = None
    
    recorder = st.session_state.recorder
    
    # Recording interface with clean styling
    if st.session_state.recording_state == 'idle':
        if st.button("🎤 Start Recording", type="primary", use_container_width=True):
            recorder.start_recording()
            st.session_state.recording_state = 'recording'
            st.session_state.start_time = time.time()
            st.rerun()
    
    elif st.session_state.recording_state == 'recording':
        # Show recording status with clean styling
        if st.session_state.start_time:
            duration = time.time() - st.session_state.start_time
            st.markdown(f"""
            <div style="
                background: #fff3cd;
                border: 1px solid #ffeaa7;
                border-left: 4px solid #ff9500;
                border-radius: 12px;
                padding: 1.5rem;
                text-align: center;
                margin: 1rem 0;
                color: #8b4513;
            ">
                <div style="display: flex; align-items: center; justify-content: center; margin-bottom: 1rem;">
                    <div style="
                        width: 12px; height: 12px; background: #ff3b30; border-radius: 50%;
                        animation: pulse 1.5s infinite; margin-right: 10px;
                    "></div>
                    <strong>🎤 Recording in Progress</strong>
                </div>
                <div style="font-size: 1.2rem; font-weight: 600;">
                    Duration: {duration:.1f} seconds
                </div>
                <div style="font-size: 0.9rem; opacity: 0.8; margin-top: 0.5rem;">
                    Speak clearly for best results
                </div>
            </div>
            <style>
                @keyframes pulse {{
                    0% {{ transform: scale(0.95); box-shadow: 0 0 0 0 rgba(255, 59, 48, 0.7); }}
                    70% {{ transform: scale(1); box-shadow: 0 0 0 10px rgba(255, 59, 48, 0); }}
                    100% {{ transform: scale(0.95); box-shadow: 0 0 0 0 rgba(255, 59, 48, 0); }}
                }}
            </style>
            """, unsafe_allow_html=True)
        
        if st.button("⏹️ Stop Recording", type="secondary", use_container_width=True):
            audio_data = recorder.stop_recording()
            if audio_data:
                # Save to temporary file
                with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
                    if recorder.save_audio(audio_data, tmp_file.name):
                        st.session_state.recorded_file = tmp_file.name
                        st.session_state.recording_state = 'completed'
                        st.rerun()
            else:
                st.session_state.recording_state = 'idle'
                st.rerun()
        
        # Auto-refresh every second during recording
        time.sleep(1)
        st.rerun()
    
    elif st.session_state.recording_state == 'completed':
        st.markdown("""
        <div style="
            background: #f0fff4;
            border: 1px solid #c3e6cb;
            border-left: 4px solid #34c759;
            border-radius: 12px;
            padding: 1.5rem;
            text-align: center;
            margin: 1rem 0;
            color: #1b5e20;
        ">
            <div style="font-size: 1.1rem; font-weight: 600; margin-bottom: 0.5rem;">
                ✅ Recording Complete
            </div>
            <div style="font-size: 0.9rem; opacity: 0.8;">
                Audio file ready for analysis
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔄 Record Again", use_container_width=True):
                # Clean up previous recording
                if hasattr(st.session_state, 'recorded_file') and os.path.exists(st.session_state.recorded_file):
                    os.unlink(st.session_state.recorded_file)
                st.session_state.recording_state = 'idle'
                st.rerun()
        
        with col2:
            if st.button("🚀 Process Recording", type="primary", use_container_width=True):
                # Return the recorded file path for processing
                if hasattr(st.session_state, 'recorded_file'):
                    return st.session_state.recorded_file
    
    return None 