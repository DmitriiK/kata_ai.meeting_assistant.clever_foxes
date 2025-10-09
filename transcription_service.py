"""
Hybrid transcription service combining VAD and Azure Speech Service.
"""
from azure_speech_service import AzureSpeechTranscriber
from vad_detector import VADDetector
from typing import Optional


class HybridTranscriptionService:
    """
    Hybrid transcription service.
    Uses local VAD to detect speech, then Azure for transcription.
    """
    
    def __init__(self):
        """Initialize the hybrid transcription service."""
        self.vad = VADDetector()
        self.azure_transcriber = AzureSpeechTranscriber()
        print("✅ Hybrid transcription service initialized")
        print("   📍 Local VAD for speech detection")
        print("   ☁️  Azure Speech Service for transcription")
    
    def transcribe_audio_bytes(
        self,
        audio_data: bytes,
        source_label: str = "audio"
    ) -> Optional[str]:
        """
        Transcribe audio bytes using hybrid approach.
        
        Args:
            audio_data: WAV format audio bytes
            source_label: Label for audio source
            
        Returns:
            Transcribed text or None if no speech detected
        """
        if not audio_data or len(audio_data) < 1000:
            return None
        
        # Step 1: Check if speech is present using local VAD
        has_speech = self.vad.detect_speech_in_chunk(audio_data)
        
        if not has_speech:
            # No speech detected, skip cloud transcription
            return None
        
        # Step 2: Speech detected, send to Azure for transcription
        try:
            transcription = self.azure_transcriber.transcribe_audio_bytes(
                audio_data, source_label
            )
            return transcription
        except Exception as e:
            print(f"⚠️  Transcription error: {e}")
            return None
    
    def transcribe_with_speakers(
        self,
        audio_data: bytes,
        source_label: str = "audio"
    ) -> list:
        """
        Transcribe audio with speaker diarization.
        
        Args:
            audio_data: WAV format audio bytes
            source_label: Label for audio source
            
        Returns:
            List of tuples: [(speaker_id, text), ...]
        """
        if not audio_data or len(audio_data) < 1000:
            return []
        
        # Check for speech with VAD
        has_speech = self.vad.detect_speech_in_chunk(audio_data)
        
        if not has_speech:
            return []
        
        # Use Azure with speaker diarization
        try:
            results = self.azure_transcriber.transcribe_with_diarization(
                audio_data, source_label
            )
            return results
        except Exception as e:
            print(f"⚠️  Speaker diarization error: {e}")
            # Fall back to simple transcription
            simple_text = self.transcribe_audio_bytes(audio_data, source_label)
            if simple_text:
                return [("Speaker", simple_text)]
            return []
