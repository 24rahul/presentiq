#!/usr/bin/env python3
"""
Setup script for Medical Presentation Feedback System
"""

import os
import sys
import subprocess
import platform

def check_python_version():
    """Check if Python version is compatible"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8 or higher is required")
        print(f"Current version: {version.major}.{version.minor}.{version.micro}")
        return False
    print(f"✅ Python version: {version.major}.{version.minor}.{version.micro}")
    return True

def install_system_dependencies():
    """Install system dependencies"""
    system = platform.system().lower()
    
    print("\n🔧 Installing system dependencies...")
    
    if system == "darwin":  # macOS
        try:
            # Check if Homebrew is installed
            subprocess.run(["brew", "--version"], check=True, capture_output=True)
            print("✅ Homebrew is installed")
            
            # Install PortAudio
            result = subprocess.run(["brew", "install", "portaudio"], capture_output=True, text=True)
            if result.returncode == 0:
                print("✅ PortAudio installed successfully")
            else:
                print(f"⚠️ PortAudio installation: {result.stdout}")
                
        except subprocess.CalledProcessError:
            print("❌ Homebrew not found. Please install Homebrew first:")
            print("   /bin/bash -c \"$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\"")
            return False
            
    elif system == "linux":
        print("For Linux, please install these packages manually:")
        print("   sudo apt-get install portaudio19-dev python3-pyaudio")
        print("   or")
        print("   sudo yum install portaudio-devel python3-pyaudio")
        
    elif system == "windows":
        print("For Windows, PyAudio should install automatically with pip.")
        print("If you encounter issues, you may need to install Visual Studio Build Tools.")
    
    return True

def install_python_dependencies():
    """Install Python dependencies"""
    print("\n📦 Installing Python dependencies...")
    
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
        print("✅ Python dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install Python dependencies: {e}")
        return False

def create_env_file():
    """Create .env file if it doesn't exist"""
    if not os.path.exists(".env"):
        print("\n📝 Creating .env file...")
        
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
            print("✅ .env file created with your API key")
        else:
            print("⚠️ .env file created but you need to add your OpenAI API key")
            print("   Edit .env file and add: OPENAI_API_KEY=your_key_here")
    else:
        print("✅ .env file already exists")

def test_installation():
    """Test if the installation works"""
    print("\n🧪 Testing installation...")
    
    try:
        import streamlit
        import whisper
        import openai
        import pyaudio
        print("✅ All required packages imported successfully")
        
        # Test Whisper model loading
        print("🔄 Testing Whisper model download (this may take a moment)...")
        model = whisper.load_model("base")
        print("✅ Whisper model loaded successfully")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"⚠️ Warning: {e}")
        return True

def main():
    """Main setup function"""
    print("🩺 Medical Presentation Feedback System Setup")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Install system dependencies
    if not install_system_dependencies():
        print("⚠️ Some system dependencies may not be installed correctly")
    
    # Install Python dependencies
    if not install_python_dependencies():
        sys.exit(1)
    
    # Create .env file
    create_env_file()
    
    # Test installation
    if test_installation():
        print("\n🎉 Setup completed successfully!")
        print("\nTo run the application:")
        print("   streamlit run app.py")
        print("\nMake sure to add your OpenAI API key to the .env file if you haven't already.")
    else:
        print("\n❌ Setup completed with errors")
        print("Please check the error messages above and try to resolve them.")

if __name__ == "__main__":
    main() 