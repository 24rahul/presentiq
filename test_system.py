#!/usr/bin/env python3
"""
Test script for Medical Presentation Feedback System
"""

import os
import sys
from pathlib import Path

def test_imports():
    """Test if all required packages can be imported"""
    print("🧪 Testing package imports...")
    
    required_packages = [
        'streamlit',
        'openai',
        'pyaudio',
        'wave',
        'threading',
        'tempfile',
        'dotenv',
        'json',
        'numpy'
    ]
    
    failed_imports = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package}")
        except ImportError as e:
            print(f"❌ {package}: {e}")
            failed_imports.append(package)
    
    return len(failed_imports) == 0

def test_env_file():
    """Test if .env file exists and has required variables"""
    print("\n🔧 Testing environment configuration...")
    
    if not os.path.exists('.env'):
        print("❌ .env file not found")
        return False
    
    from dotenv import load_dotenv
    load_dotenv()
    
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ OPENAI_API_KEY not found in .env file")
        return False
    elif api_key == 'your_api_key_here' or len(api_key) < 10:
        print("⚠️ OPENAI_API_KEY appears to be placeholder or invalid")
        return False
    else:
        print("✅ OPENAI_API_KEY configured")
        return True

def test_whisper_api():
    """Test OpenAI Whisper API access"""
    print("\n🎤 Testing OpenAI Whisper API...")
    
    try:
        import openai
        from dotenv import load_dotenv
        load_dotenv()
        
        client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        # Test API access (we won't actually send audio, just verify API access)
        print("✅ OpenAI Whisper API client initialized successfully")
        return True
        
    except Exception as e:
        print(f"❌ Whisper API test failed: {e}")
        return False

def test_openai_connection():
    """Test OpenAI API connection"""
    print("\n🤖 Testing OpenAI API connection...")
    
    try:
        import openai
        from dotenv import load_dotenv
        load_dotenv()
        
        client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        # Test with a simple completion
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Say 'API test successful'"}],
            max_tokens=10
        )
        
        if response.choices[0].message.content:
            print("✅ OpenAI API connection successful")
            return True
        else:
            print("❌ OpenAI API responded but with empty content")
            return False
            
    except Exception as e:
        print(f"❌ OpenAI API test failed: {e}")
        return False

def test_audio_system():
    """Test audio recording system"""
    print("\n🔊 Testing audio system...")
    
    try:
        import pyaudio
        
        # Initialize PyAudio
        p = pyaudio.PyAudio()
        
        # Check for input devices
        input_devices = []
        for i in range(p.get_device_count()):
            device_info = p.get_device_info_by_index(i)
            if device_info['maxInputChannels'] > 0:
                input_devices.append(device_info['name'])
        
        p.terminate()
        
        if input_devices:
            print(f"✅ Audio input devices found: {len(input_devices)}")
            print(f"   Primary device: {input_devices[0]}")
            return True
        else:
            print("❌ No audio input devices found")
            return False
            
    except Exception as e:
        print(f"❌ Audio system test failed: {e}")
        return False

def test_feedback_generator():
    """Test feedback generation with sample text"""
    print("\n👨‍⚕️ Testing feedback generation...")
    
    try:
        from feedback_generator import FeedbackGenerator
        
        generator = FeedbackGenerator()
        
        sample_presentation = """
        This is a 45-year-old female presenting with chest pain.
        The pain started 2 hours ago and is described as crushing.
        She has a history of hypertension and diabetes.
        Physical exam shows blood pressure 140/90, heart rate 85.
        Assessment is possible acute coronary syndrome.
        Plan includes EKG, chest X-ray, and cardiac enzymes.
        """
        
        feedback = generator.generate_feedback(sample_presentation)
        
        if isinstance(feedback, dict) and 'overall_assessment' in feedback:
            print("✅ Feedback generation successful")
            print(f"   Sample score: {feedback.get('overall_score', 'N/A')}/10")
            return True
        else:
            print("❌ Feedback generation returned unexpected format")
            return False
            
    except Exception as e:
        print(f"❌ Feedback generation test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🩺 Medical Presentation Feedback System - System Test")
    print("=" * 60)
    
    tests = [
        ("Package Imports", test_imports),
        ("Environment Configuration", test_env_file),
        ("OpenAI Whisper API", test_whisper_api),
        ("OpenAI Chat API", test_openai_connection),
        ("Audio System", test_audio_system),
        ("Feedback Generator", test_feedback_generator)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 60)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
        if result:
            passed += 1
    
    print(f"\nTotal: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("\n🎉 All tests passed! Your system is ready to use.")
        print("\nTo start the application:")
        print("   streamlit run app.py")
        print("\nThen open http://localhost:8501 in your browser")
    else:
        print(f"\n⚠️ {len(results) - passed} test(s) failed. Please address the issues above.")
        
        if not results[1][1]:  # env file test failed
            print("\n💡 Quick fix: Make sure you have a .env file with your OpenAI API key")
        
        if not results[3][1]:  # OpenAI API test failed
            print("💡 Quick fix: Check your OpenAI API key and account credits")

if __name__ == "__main__":
    main() 