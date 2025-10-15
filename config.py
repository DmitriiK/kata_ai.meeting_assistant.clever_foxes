"""
Configuration settings for the Audio Transcription Application.
"""
import os
from dotenv import load_dotenv

load_dotenv()


# Audio Recording Settings
class AudioSettings:
    """Audio recording and processing configuration."""
    # Chunk duration: shorter = more real-time, longer = better accuracy
    CHUNK_DURATION = 5.0  # seconds
    SAMPLE_RATE = 16000  # Hz - 16kHz for Azure Speech Service
    CHUNK_SIZE = 1024  # Audio buffer size
    MIN_AUDIO_LENGTH = 1000  # Minimum audio bytes to attempt transcription


# Voice Activity Detection Settings
class VADSettings:
    """Voice Activity Detection configuration."""
    AGGRESSIVENESS = 3  # 0-3, higher = more aggressive filtering
    FRAME_DURATION_MS = 30  # Frame duration in milliseconds (10, 20, or 30)
    MIN_SPEECH_DURATION = 0.5  # Minimum speech duration in seconds


# Logging Settings
class LogSettings:
    """Logging and output configuration."""
    # Main transcription log file (configurable via environment variable)
    # Note: Logger will create timestamped files in logs/ folder
    LOG_FILE = os.getenv("TRANSCRIPTION_LOG_FILE", "transcriptions.log")
    # Show intermediate/partial results as user speaks
    SHOW_INTERIM_RESULTS = True


# Session Settings
class SessionSettings:
    """Session management configuration."""
    # Auto-pause after silence (seconds)
    AUTO_PAUSE_SILENCE_DURATION = 60  # 1 minute of silence
    # Enable auto-pause feature
    ENABLE_AUTO_PAUSE = True


# Azure OpenAI Settings (legacy - not currently used)
class AzureOpenAI:
    """Azure OpenAI API configuration (for future LLM integration)."""
    AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
    AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
    OPENAI_API_VERSION = "2025-01-01-preview"
    MODEL_NAME = "gpt-4.1-2025-04-14"


class AzureSpeechService:
    """Azure Speech Service configuration."""
    AZURE_SPEECH_SERVICE_KEY = os.getenv("AZURE_SPEECH_SERVICE_KEY")
    AZURE_SPEECH_SERVICE_REGION = os.getenv("AZURE_SPEECH_SERVICE_REGION")
    
    # Language configuration
    # Options: "en-US", "ru-RU", "tr-TR", "auto" (auto-detect)
    SPEECH_LANGUAGE = os.getenv("SPEECH_LANGUAGE", "auto")
    
    # For auto-detection, list candidate languages
    # More languages = slower but more accurate detection
    CANDIDATE_LANGUAGES = ["en-US", "ru-RU", "tr-TR"]
    
    # Enable speaker diarization (identify different speakers)
    ENABLE_DIARIZATION = True
    # Number of expected speakers (None = auto-detect)
    MIN_SPEAKERS = 2
    MAX_SPEAKERS = 10
