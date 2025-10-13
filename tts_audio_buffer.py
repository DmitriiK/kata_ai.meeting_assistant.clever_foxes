"""
TTS Audio Buffer
Generates TTS audio using Azure Speech Service and buffers it in memory.
Supports async generation and controlled playback.
"""
import azure.cognitiveservices.speech as speechsdk
from typing import Optional, Callable
from threading import Lock, Thread
from config import AzureSpeechService
from tts_voice_manager import TTSVoiceManager


class TTSAudioBuffer:
    """
    Generates TTS audio and buffers it in memory.
    Supports async generation and controlled playback.
    """
    
    def __init__(self):
        """Initialize TTS audio buffer."""
        self.voice_manager = TTSVoiceManager()
        
        # Audio buffer
        self.audio_buffer: bytes = b''
        self.buffer_lock = Lock()
        
        # Generation state
        self.is_generating = False
        self.generation_lock = Lock()
        
        # Azure Speech config
        self.speech_config = speechsdk.SpeechConfig(
            subscription=AzureSpeechService.AZURE_SPEECH_SERVICE_KEY,
            region=AzureSpeechService.AZURE_SPEECH_SERVICE_REGION
        )
        
        # Default voice
        self.current_voice = "en-US-JennyNeural"
        self.speech_config.speech_synthesis_voice_name = self.current_voice
        
    def set_voice_by_language(
        self, language_name: str, sex: Optional[str] = None
    ):
        """
        Set TTS voice based on language name.
        
        Args:
            language_name: Friendly language name 
                          ("English", "Russian", "Turkish")
            sex: Optional sex preference ("male" or "female")
        """
        # Get language code
        lang_code = self.voice_manager.get_language_code(language_name)
        
        if not lang_code:
            print(f"[WARNING] Language '{language_name}' not found")
            return
        
        # Get voice
        voice = self.voice_manager.get_voice(lang_code, sex)
        
        if voice:
            self.current_voice = voice.name
            self.speech_config.speech_synthesis_voice_name = voice.name
            print(f"[MIC] Voice set to: {voice.name} ({voice.language})")
        else:
            print(f"[WARNING] No voice found for {language_name}")
    
    def generate_async(
        self,
        text: str,
        callback: Optional[Callable[[bool, str], None]] = None
    ):
        """
        Generate TTS audio asynchronously and add to buffer.
        
        Args:
            text: Text to convert to speech
            callback: Optional callback(success, message) 
                     when generation completes
        """
        def _generate():
            with self.generation_lock:
                self.is_generating = True
                
                try:
                    # Create synthesizer
                    synthesizer = speechsdk.SpeechSynthesizer(
                        speech_config=self.speech_config,
                        audio_config=None  # We'll handle audio manually
                    )
                    
                    # Generate speech
                    result = synthesizer.speak_text_async(text).get()
                    
                    if result.reason == (
                        speechsdk.ResultReason.SynthesizingAudioCompleted
                    ):
                        # Add to buffer
                        audio_data = result.audio_data
                        
                        with self.buffer_lock:
                            self.audio_buffer += audio_data
                        
                        print(
                            f"✅ TTS generated: {len(audio_data)} bytes "
                            f"(buffer: {len(self.audio_buffer)} bytes)"
                        )
                        
                        if callback:
                            callback(True, "TTS generation successful")
                    else:
                        error_msg = f"TTS failed: {result.reason}"
                        print(f"[ERROR] {error_msg}")
                        
                        if callback:
                            callback(False, error_msg)
                            
                except Exception as e:
                    error_msg = f"TTS generation error: {e}"
                    print(f"[ERROR] {error_msg}")
                    
                    if callback:
                        callback(False, error_msg)
                        
                finally:
                    self.is_generating = False
        
        # Start generation thread
        thread = Thread(target=_generate, daemon=True)
        thread.start()
    
    def get_buffer(self) -> bytes:
        """
        Get current audio buffer.
        
        Returns:
            Audio data as bytes
        """
        with self.buffer_lock:
            return self.audio_buffer
    
    def get_buffer_size(self) -> int:
        """
        Get current buffer size in bytes.
        
        Returns:
            Buffer size
        """
        with self.buffer_lock:
            return len(self.audio_buffer)
    
    def clear_buffer(self):
        """Clear audio buffer."""
        with self.buffer_lock:
            old_size = len(self.audio_buffer)
            self.audio_buffer = b''
            print(f"🗑️ Buffer cleared ({old_size} bytes removed)")
    
    def has_audio(self) -> bool:
        """
        Check if buffer has audio data.
        
        Returns:
            True if buffer is not empty
        """
        with self.buffer_lock:
            return len(self.audio_buffer) > 0
    
    def is_busy(self) -> bool:
        """
        Check if generation is in progress.
        
        Returns:
            True if generating audio
        """
        return self.is_generating


# Test module
if __name__ == "__main__":
    import time
    
    print("🧪 Testing TTS Audio Buffer\n")
    
    buffer = TTSAudioBuffer()
    
    # Test 1: Generate English audio
    print("Test 1: Generating English audio...")
    buffer.set_voice_by_language("English", sex="female")
    
    def test_callback(success, message):
        print(f"  Callback: {message}")
    
    buffer.generate_async("Hello, this is a test.", test_callback)
    
    # Wait for generation
    time.sleep(3)
    
    print(f"  Buffer size: {buffer.get_buffer_size()} bytes")
    print(f"  Has audio: {buffer.has_audio()}")
    
    # Test 2: Generate Russian audio
    print("\nTest 2: Generating Russian audio...")
    buffer.set_voice_by_language("Russian", sex="female")
    buffer.generate_async("Привет, это тест.", test_callback)
    
    time.sleep(3)
    print(f"  Buffer size: {buffer.get_buffer_size()} bytes")
    
    # Test 3: Clear buffer
    print("\nTest 3: Clearing buffer...")
    buffer.clear_buffer()
    print(f"  Buffer size: {buffer.get_buffer_size()} bytes")
    print(f"  Has audio: {buffer.has_audio()}")
