#!/usr/bin/env python3
"""Setup script for PresentIQ."""

import os
import sys
import subprocess
import platform


def check_python_version():
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(f"[FAIL] Python 3.8+ required (found {version.major}.{version.minor}.{version.micro})")
        return False
    print(f"[OK] Python {version.major}.{version.minor}.{version.micro}")
    return True


def install_system_dependencies():
    system = platform.system().lower()
    print("\nInstalling system dependencies...")

    if system == "darwin":
        try:
            subprocess.run(["brew", "--version"], check=True, capture_output=True)
            result = subprocess.run(["brew", "install", "portaudio"], capture_output=True, text=True)
            if result.returncode == 0:
                print("[OK] PortAudio installed")
            else:
                print(f"[WARN] PortAudio: {result.stdout}")
        except subprocess.CalledProcessError:
            print("[FAIL] Homebrew not found. Install it first:")
            print('   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"')
            return False
    elif system == "linux":
        print("For Linux, install these packages manually:")
        print("   sudo apt-get install portaudio19-dev python3-pyaudio")
        print("   or")
        print("   sudo yum install portaudio-devel python3-pyaudio")
    elif system == "windows":
        print("For Windows, PyAudio should install automatically with pip.")

    return True


def install_python_dependencies():
    print("\nInstalling Python dependencies...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
        print("[OK] Python dependencies installed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[FAIL] {e}")
        return False


def create_env_file():
    if not os.path.exists(".env"):
        print("\nCreating .env file...")
        api_key = input("Enter your OpenAI API key (or press Enter to skip): ").strip()

        env_content = f"""# OpenAI API Configuration
OPENAI_API_KEY={api_key}

# Optional: Customize the model (default: gpt-4)
OPENAI_MODEL=gpt-4

# Optional: Adjust temperature for feedback generation (0.0-1.0)
FEEDBACK_TEMPERATURE=0.3
"""
        with open(".env", "w") as f:
            f.write(env_content)

        if api_key:
            print("[OK] .env file created with your API key")
        else:
            print("[WARN] .env file created — add your API key: OPENAI_API_KEY=your_key_here")
    else:
        print("[OK] .env file already exists")


def test_installation():
    print("\nTesting installation...")
    try:
        import streamlit
        import whisper
        import openai
        import pyaudio
        import yaml
        print("[OK] All required packages imported")

        from agents.base import BaseAgent
        from pipeline import FeedbackPipeline, PRESENTATION_FORMATS
        print(f"[OK] Agent pipeline loaded ({len(PRESENTATION_FORMATS)} presentation formats)")

        print("Loading Whisper model (may take a moment)...")
        model = whisper.load_model("base")
        print("[OK] Whisper model loaded")

        return True
    except ImportError as e:
        print(f"[FAIL] Import error: {e}")
        return False
    except Exception as e:
        print(f"[WARN] {e}")
        return True


def main():
    print("PresentIQ Setup")
    print("=" * 50)

    if not check_python_version():
        sys.exit(1)

    if not install_system_dependencies():
        print("[WARN] Some system dependencies may not be installed correctly")

    if not install_python_dependencies():
        sys.exit(1)

    create_env_file()

    if test_installation():
        print("\nSetup complete! Run the application:")
        print("   streamlit run app.py")
        print("\nMake sure to add your OpenAI API key to .env if you haven't already.")
    else:
        print("\nSetup completed with errors. Check the messages above.")


if __name__ == "__main__":
    main()
