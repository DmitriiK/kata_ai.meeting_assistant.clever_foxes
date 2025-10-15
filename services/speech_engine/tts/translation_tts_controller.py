"""
Translation TTS Controller
Coordinates the translation → TTS → playback pipeline.
Manages state and provides unified API for GUI.
"""
from typing import Optional, Callable
from threading import Lock
from .tts_audio_buffer import TTSAudioBuffer
from .tts_audio_router import TTSAudioRouter


class TranslationTTSController:
    """
    Coordinates translation TTS feature.
    Manages buffer, router, and playback state.
    """
    
    # State constants
    STATE_IDLE = "idle"
    STATE_BUFFERING = "buffering"
    STATE_READY = "ready"
    STATE_SPEAKING = "speaking"
    
    def __init__(self, virtual_device_name: str = "BlackHole"):
        """
        Initialize translation TTS controller.
        
        Args:
            virtual_device_name: Name of virtual audio device
        """
        # Components
        self.buffer = TTSAudioBuffer()
        self.router = TTSAudioRouter(virtual_device_name)
        
        # State
        self.state = self.STATE_IDLE
        self.state_lock = Lock()
        
        # Callbacks
        self.on_state_change: Optional[Callable[[str], None]] = None
        
    def set_language(self, language_name: str):
        """
        Set target language for TTS.
        
        Args:
            language_name: Friendly language name 
                          ("English", "Russian", "Turkish")
        """
        self.buffer.set_voice_by_language(language_name)
    
    def add_translation(self, text: str):
        """
        Add translated text to TTS buffer.
        Generates audio asynchronously.
        
        Args:
            text: Translated text to convert to speech
        """
        if not text or not text.strip():
            print("⚠️ Empty translation text, skipping")
            return
        
        # Update state
        self._set_state(self.STATE_BUFFERING)
        
        # Generate audio
        def on_complete(success: bool, message: str):
            if success:
                self._set_state(self.STATE_READY)
            else:
                self._set_state(self.STATE_IDLE)
        
        self.buffer.generate_async(text, on_complete)
    
    def speak(self):
        """
        Start speaking buffered audio.
        Routes audio to virtual microphone.
        
        Returns:
            True if playback started, False otherwise
        """
        # Check state and get audio data
        with self.state_lock:
            # Check if we have audio
            if not self.buffer.has_audio():
                print("⚠️ No audio in buffer to speak")
                return False
            
            # Check if already playing
            if self.state == self.STATE_SPEAKING:
                print("⚠️ Already speaking")
                return False
            
            # Get audio data
            audio_data = self.buffer.get_buffer()
        
        # Update state (outside lock to avoid deadlock)
        self._set_state(self.STATE_SPEAKING)
        
        # Start playback
        def on_complete():
            # Playback finished normally
            self.buffer.clear_buffer()
            self._set_state(self.STATE_IDLE)
        
        def on_stopped():
            # Playback stopped early
            self.buffer.clear_buffer()
            self._set_state(self.STATE_IDLE)
        
        self.router.play_audio(audio_data, on_complete, on_stopped)
        return True
    
    def stop_speaking(self):
        """
        Stop current playback and clear buffer.
        """
        # Stop playback
        self.router.stop_playback()
        
        # Clear buffer
        self.buffer.clear_buffer()
        
        # Update state
        self._set_state(self.STATE_IDLE)
    
    def clear_buffer(self):
        """
        Clear buffered audio without stopping playback.
        Useful when disabling TTS feature mid-session.
        """
        # Clear buffer
        self.buffer.clear_buffer()
        
        # Update state to idle if not speaking
        if self.get_state() != self.STATE_SPEAKING:
            self._set_state(self.STATE_IDLE)
    
    def get_state(self) -> str:
        """
        Get current state.
        
        Returns:
            One of: STATE_IDLE, STATE_BUFFERING, 
                   STATE_READY, STATE_SPEAKING
        """
        with self.state_lock:
            return self.state
    
    def is_ready(self) -> bool:
        """
        Check if ready to speak.
        
        Returns:
            True if audio is buffered and ready
        """
        return self.get_state() == self.STATE_READY
    
    def is_speaking(self) -> bool:
        """
        Check if currently speaking.
        
        Returns:
            True if audio is playing
        """
        return self.get_state() == self.STATE_SPEAKING
    
    def is_busy(self) -> bool:
        """
        Check if busy (buffering or speaking).
        
        Returns:
            True if not idle
        """
        state = self.get_state()
        return state in (
            self.STATE_BUFFERING,
            self.STATE_SPEAKING
        )
    
    def _set_state(self, new_state: str):
        """
        Update state and notify callback.
        
        Args:
            new_state: New state value
        """
        with self.state_lock:
            if self.state != new_state:
                old_state = self.state
                self.state = new_state
                
                print(f"🔄 State: {old_state} → {new_state}")
                
                # Notify callback
                if self.on_state_change:
                    self.on_state_change(new_state)
    
    def get_buffer_info(self) -> dict:
        """
        Get buffer information.
        
        Returns:
            Dict with buffer stats
        """
        return {
            'size': self.buffer.get_buffer_size(),
            'has_audio': self.buffer.has_audio(),
            'is_generating': self.buffer.is_busy()
        }
    
    def cleanup(self):
        """Clean up resources."""
        self.stop_speaking()
        self.router.cleanup()


# Test module
if __name__ == "__main__":
    import time
    
    print("🧪 Testing Translation TTS Controller\n")
    
    controller = TranslationTTSController()
    
    # Set up state change callback
    def on_state_change(state):
        print(f"  📢 State changed to: {state}")
    
    controller.on_state_change = on_state_change
    
    # Test 1: English translation
    print("Test 1: Adding English translation...")
    controller.set_language("English")
    controller.add_translation(
        "Hello, this is a test of the translation TTS system."
    )
    
    # Wait for buffering
    print("  Waiting for audio generation...")
    time.sleep(3)
    
    print(f"  State: {controller.get_state()}")
    print(f"  Ready: {controller.is_ready()}")
    print(f"  Buffer: {controller.get_buffer_info()}")
    
    # Test 2: Speak
    if controller.is_ready():
        print("\nTest 2: Speaking...")
        if controller.speak():
            print("  Playback started")
            
            # Wait for playback
            time.sleep(5)
        else:
            print("  Failed to start playback")
    
    # Test 3: Russian translation with interruption
    print("\nTest 3: Russian translation with stop...")
    controller.set_language("Russian")
    controller.add_translation("Привет, это тест системы перевода.")
    
    time.sleep(3)
    
    if controller.is_ready():
        controller.speak()
        print("  Playing for 1 second, then stopping...")
        time.sleep(1)
        controller.stop_speaking()
    
    print(f"\nFinal state: {controller.get_state()}")
    
    controller.cleanup()
