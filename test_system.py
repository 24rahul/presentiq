#!/usr/bin/env python3
"""System test script for PresentIQ."""

import os
import sys
from pathlib import Path


def test_imports():
    print("Testing package imports...")

    required_packages = [
        'streamlit', 'openai', 'pyaudio', 'wave', 'threading',
        'tempfile', 'dotenv', 'json', 'numpy', 'yaml',
    ]

    failed_imports = []
    for package in required_packages:
        try:
            __import__(package)
            print(f"  [OK] {package}")
        except ImportError as e:
            print(f"  [FAIL] {package}: {e}")
            failed_imports.append(package)

    return len(failed_imports) == 0


def test_agent_imports():
    print("\nTesting agent imports...")
    try:
        from agents.base import BaseAgent
        from agents.transcription_qa import TranscriptionQAAgent
        from agents.clinical_content import ClinicalContentAgent
        from agents.clinical_reasoning import ClinicalReasoningAgent
        from agents.structure_delivery import StructureDeliveryAgent
        from agents.communication_professionalism import CommunicationProfessionalismAgent
        from agents.anticipatory_reasoning import AnticipatoryReasoningAgent
        from agents.literature_learning import LiteratureLearningAgent
        from agents.synthesizer import SynthesizerAgent
        print("  [OK] All 8 agents imported")
        return True
    except ImportError as e:
        print(f"  [FAIL] {e}")
        return False


def test_pipeline_imports():
    print("\nTesting pipeline and config loading...")
    try:
        from pipeline import FeedbackPipeline, get_format_options, PRESENTATION_FORMATS

        expected = {"full_hp", "focused_hp", "sbar", "consult", "handoff", "post_op"}
        loaded = set(PRESENTATION_FORMATS.keys())

        if not expected.issubset(loaded):
            print(f"  [FAIL] Missing formats: {expected - loaded}")
            return False

        print(f"  [OK] Pipeline loaded, {len(PRESENTATION_FORMATS)} formats available")
        return True
    except Exception as e:
        print(f"  [FAIL] {e}")
        return False


def test_env_file():
    print("\nTesting environment configuration...")

    if not os.path.exists('.env'):
        print("  [FAIL] .env file not found")
        return False

    from dotenv import load_dotenv
    load_dotenv()

    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("  [FAIL] OPENAI_API_KEY not found in .env")
        return False
    elif api_key == 'your_api_key_here' or len(api_key) < 10:
        print("  [WARN] OPENAI_API_KEY appears to be placeholder")
        return False
    else:
        print("  [OK] OPENAI_API_KEY configured")
        return True


def test_whisper_api():
    print("\nTesting Whisper API...")
    try:
        import openai
        from dotenv import load_dotenv
        load_dotenv()
        client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        print("  [OK] Whisper API client initialized")
        return True
    except Exception as e:
        print(f"  [FAIL] {e}")
        return False


def test_openai_connection():
    print("\nTesting OpenAI API connection...")
    try:
        import openai
        from dotenv import load_dotenv
        load_dotenv()

        client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Say 'API test successful'"}],
            max_tokens=10,
        )

        if response.choices[0].message.content:
            print("  [OK] API connection successful")
            return True
        else:
            print("  [FAIL] Empty response")
            return False
    except Exception as e:
        print(f"  [FAIL] {e}")
        return False


def test_audio_system():
    print("\nTesting audio system...")
    try:
        import pyaudio
        p = pyaudio.PyAudio()

        input_devices = []
        for i in range(p.get_device_count()):
            info = p.get_device_info_by_index(i)
            if info['maxInputChannels'] > 0:
                input_devices.append(info['name'])
        p.terminate()

        if input_devices:
            print(f"  [OK] {len(input_devices)} input device(s) found")
            return True
        else:
            print("  [FAIL] No audio input devices")
            return False
    except Exception as e:
        print(f"  [FAIL] {e}")
        return False


def test_feedback_generator():
    print("\nTesting legacy feedback generation...")
    try:
        from feedback_generator import FeedbackGenerator
        generator = FeedbackGenerator()

        sample = """
        This is a 45-year-old female presenting with chest pain.
        The pain started 2 hours ago and is described as crushing.
        She has a history of hypertension and diabetes.
        Physical exam shows blood pressure 140/90, heart rate 85.
        Assessment is possible acute coronary syndrome.
        Plan includes EKG, chest X-ray, and cardiac enzymes.
        """

        feedback = generator.generate_feedback(sample)

        if isinstance(feedback, dict) and 'overall_assessment' in feedback:
            print(f"  [OK] Score: {feedback.get('overall_score', 'N/A')}/10")
            return True
        else:
            print("  [FAIL] Unexpected response format")
            return False
    except Exception as e:
        print(f"  [FAIL] {e}")
        return False


def main():
    print("PresentIQ - System Test")
    print("=" * 60)

    tests = [
        ("Package Imports", test_imports),
        ("Agent Imports", test_agent_imports),
        ("Pipeline & Config", test_pipeline_imports),
        ("Environment Config", test_env_file),
        ("Whisper API", test_whisper_api),
        ("OpenAI Chat API", test_openai_connection),
        ("Audio System", test_audio_system),
        ("Legacy Feedback", test_feedback_generator),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"  [FAIL] {test_name} crashed: {e}")
            results.append((test_name, False))

    print("\n" + "=" * 60)
    print("RESULTS")
    print("=" * 60)

    passed = 0
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"  [{status}] {test_name}")
        if result:
            passed += 1

    print(f"\n{passed}/{len(results)} tests passed")

    if passed == len(results):
        print("\nAll tests passed. Run the application:")
        print("   streamlit run app.py")
    else:
        print(f"\n{len(results) - passed} test(s) failed. See above for details.")


if __name__ == "__main__":
    main()
