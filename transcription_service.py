"""
Simple transcription service using OpenAI Whisper.
"""
import whisper
import tempfile
import os
from typing import Optional


class TranscriptionService:
    def __init__(self, model_size: str = "base"):
        """
        Initialize transcription service.
        
        Args:
            model_size: Whisper model size (tiny, base, small, medium, large)
        """
        print(f"🤖 Loading Whisper model '{model_size}'...")
        self.model = whisper.load_model(model_size)
        print("✅ Whisper model loaded successfully")
    
    def transcribe_audio_bytes(self, audio_data: bytes) -> Optional[str]:
        """
        Transcribe audio from bytes (WAV format).
        
        Args:
            audio_data: Audio data in WAV format as bytes
            
        Returns:
            Transcribed text or None if transcription fails
        """
        try:
            # Create temporary file in memory-like approach
            with tempfile.NamedTemporaryFile(
                suffix='.wav', delete=False
            ) as tmp_file:
                tmp_file.write(audio_data)
                tmp_file.flush()
                
                # Transcribe the temporary file
                result = self.model.transcribe(tmp_file.name)
                
                # Clean up temporary file
                os.unlink(tmp_file.name)
                
                text = result.get("text", "")
                return text.strip() if isinstance(text, str) else ""
                
        except Exception as e:
            print(f"❌ Transcription error: {e}")
            return None
    
    def transcribe_audio_file(self, file_path: str) -> Optional[str]:
        """
        Transcribe audio from file path.
        
        Args:
            file_path: Path to audio file
            
        Returns:
            Transcribed text or None if transcription fails
        """
        try:
            result = self.model.transcribe(file_path)
            text = result.get("text", "")
            return text.strip() if isinstance(text, str) else ""
        except Exception as e:
            print(f"❌ Transcription error: {e}")
            return None
