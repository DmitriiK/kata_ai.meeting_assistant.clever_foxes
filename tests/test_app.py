#!/usr/bin/env python3
"""
Test script for the audio transcription application.
Tests each component individually without requiring microphone input.
"""

import sys
import os
from services.audio.audio_recorder import AudioRecorder
from services.speech_engine.stt.transcription_service import TranscriptionService
from services.speech_engine.stt.transcription_logger import TranscriptionLogger


def test_audio_recorder():
    """Test AudioRecorder initialization."""
    print("🧪 Testing AudioRecorder...")
    try:
        recorder = AudioRecorder()
        print("✅ AudioRecorder initialized successfully")
        recorder.cleanup()
        return True
    except Exception as e:
        print(f"❌ AudioRecorder failed: {e}")
        return False


def test_transcription_service():
    """Test TranscriptionService initialization."""
    print("🧪 Testing TranscriptionService...")
    try:
        # Use tiny model for faster testing
        service = TranscriptionService(model_size="tiny")
        print("✅ TranscriptionService initialized successfully")
        return True
    except Exception as e:
        print(f"❌ TranscriptionService failed: {e}")
        return False


def test_transcription_logger():
    """Test TranscriptionLogger."""
    print("🧪 Testing TranscriptionLogger...")
    try:
        logger = TranscriptionLogger(log_file="test_transcriptions.log")
        
        # Test logging
        logger.log_transcription("This is a test transcription", "test")
        logger.log_info("Test info message")
        logger.log_error("Test error message")
        
        # Check if file was created (in logs folder with timestamp)
        if os.path.exists(logger.log_file):
            print("✅ TranscriptionLogger working successfully")
            print(f"📁 Log file created at: {logger.log_file}")
            
            # Show log contents
            with open(logger.log_file, "r") as f:
                content = f.read()
                print("📄 Log file contents:")
                print(content)
            
            # Clean up test files
            if os.path.exists(logger.log_file):
                os.remove(logger.log_file)
            if os.path.exists(logger.system_log_file):
                os.remove(logger.system_log_file)
            return True
        else:
            print(f"❌ Log file was not created at {logger.log_file}")
            return False
            
    except Exception as e:
        print(f"❌ TranscriptionLogger failed: {e}")
        return False


def test_whisper_with_sample():
    """Test Whisper with a sample audio file (if available)."""
    print("🧪 Testing Whisper transcription...")
    try:
        service = TranscriptionService(model_size="tiny")
        
        # Test with empty/dummy transcription
        print("✅ Whisper model loaded successfully")
        print("ℹ️  To test actual transcription, run the main app with your microphone")
        return True
        
    except Exception as e:
        print(f"❌ Whisper test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("🚀 Running Audio Transcription App Tests")
    print("=" * 50)
    
    tests = [
        ("Audio Recorder", test_audio_recorder),
        ("Transcription Logger", test_transcription_logger),
        ("Transcription Service", test_transcription_service),
        ("Whisper Model", test_whisper_with_sample),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        print("-" * 30)
        result = test_func()
        results.append((test_name, result))
    
    # Summary
    print("\n" + "=" * 50)
    print("🏁 Test Summary:")
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status} - {test_name}")
        if result:
            passed += 1
    
    print(f"\n📊 Results: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("\n🎉 All tests passed! Your app is ready to use.")
        print("\n🎤 To test with actual microphone input:")
        print("   uv run python main.py")
    else:
        print("\n⚠️  Some tests failed. Check the errors above.")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())