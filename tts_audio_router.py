"""
TTS Audio Router
Routes buffered TTS audio to virtual microphone device via audio mixer.
Supports playback control (start/stop).
"""
import pyaudio
from threading import Thread, Event, Lock
from typing import Optional
import time
import numpy as np
from audio_mixer import get_mixer


class TTSAudioRouter:
    """
    Routes buffered TTS audio to virtual microphone device.
    Supports controlled playback with start/stop.
    """
    
    def __init__(self, virtual_device_name: str = "BlackHole"):
        """
        Initialize TTS audio router.
        
        Args:
            virtual_device_name: Name of virtual audio device to route to
        """
        self.virtual_device_name = virtual_device_name
        self.virtual_device_index: Optional[int] = None
        
        # Playback state
        self.is_playing = False
        self.playback_lock = Lock()
        self.stop_event = Event()
        
        # PyAudio
        self.audio = pyaudio.PyAudio()
        
        # Find virtual device
        self._find_virtual_device()
        
    def _find_virtual_device(self):
        """Find the virtual audio device for output."""
        try:
            for i in range(self.audio.get_device_count()):
                info = self.audio.get_device_info_by_index(i)
                device_name = info['name'].lower()
                
                # Check if device name contains target keyword
                if (
                    self.virtual_device_name.lower() in device_name
                    and info['maxOutputChannels'] > 0
                ):
                    self.virtual_device_index = i
                    print(
                        f"✅ Virtual audio device found: {info['name']} "
                        f"(index: {i})"
                    )
                    return
            
            print(
                f"⚠️ Virtual device '{self.virtual_device_name}' not found"
            )
            print("Available output devices:")
            for i in range(self.audio.get_device_count()):
                info = self.audio.get_device_info_by_index(i)
                if info['maxOutputChannels'] > 0:
                    print(f"  [{i}] {info['name']}")
                    
        except Exception as e:
            print(f"❌ Error finding virtual device: {e}")
    
    def play_audio(
        self,
        audio_data: bytes,
        on_complete: Optional[callable] = None,
        on_stopped: Optional[callable] = None
    ):
        """
        Play audio data via mixer (mixed with microphone).
        Routes to virtual device to act as microphone input.
        
        The audio mixer continuously routes your microphone to BlackHole
        and mixes in TTS audio when playing. This allows peers to hear
        BOTH your real voice AND TTS translations.
        
        Args:
            audio_data: Audio data to play (16kHz, mono, PCM16)
            on_complete: Optional callback when playback completes
            on_stopped: Optional callback when playback is stopped
        """
        mixer = get_mixer()
        
        if not mixer.is_running:
            print("❌ Cannot play: audio mixer not running")
            print("   Call audio_mixer.start_mixer() first")
            if on_stopped:
                on_stopped()
            return
        
        if self.is_playing:
            print("⚠️ Already playing audio")
            return
        
        def _play():
            with self.playback_lock:
                self.is_playing = True
                self.stop_event.clear()
                
                try:
                    # Convert 16kHz mono to 48kHz stereo for mixer
                    print(
                        f"🎵 Queuing {len(audio_data)} bytes "
                        f"TTS to mixer..."
                    )
                    
                    # Convert bytes to numpy array
                    audio_16khz = np.frombuffer(
                        audio_data, dtype=np.int16
                    )
                    
                    # Resample from 16kHz to 48kHz (mixer's rate)
                    # Simple linear interpolation (3x upsampling)
                    audio_48khz = np.repeat(audio_16khz, 3)
                    
                    # Convert mono to stereo (duplicate to L and R)
                    audio_stereo = np.column_stack(
                        (audio_48khz, audio_48khz)
                    ).flatten()
                    
                    # Convert back to bytes
                    audio_resampled = audio_stereo.astype(np.int16).tobytes()
                    
                    # Queue to mixer
                    mixer.queue_tts_audio(audio_resampled)
                    
                    print(
                        f"✅ TTS queued to mixer "
                        f"({len(audio_resampled)} bytes at 48kHz stereo)"
                    )
                    
                    # Wait for TTS to finish playing
                    while mixer.is_tts_active():
                        if self.stop_event.is_set():
                            print("⏹️ Playback stopped by user")
                            self.is_playing = False
                            
                            if on_stopped:
                                on_stopped()
                            return
                        
                        time.sleep(0.1)
                    
                    print("✅ TTS playback complete")
                    
                    if on_complete:
                        on_complete()
                        
                except Exception as e:
                    print(f"❌ Playback error: {e}")
                    
                    if on_stopped:
                        on_stopped()
                        
                finally:
                    self.is_playing = False
        
        # Start playback thread
        thread = Thread(target=_play, daemon=True)
        thread.start()
    
    def stop_playback(self):
        """Stop current playback."""
        if self.is_playing:
            self.stop_event.set()
            print("🛑 Stopping playback...")
        else:
            print("⚠️ No playback in progress")
    
    def is_busy(self) -> bool:
        """
        Check if playback is in progress.
        
        Returns:
            True if playing audio
        """
        return self.is_playing
    
    def cleanup(self):
        """Clean up audio resources."""
        if self.is_playing:
            self.stop_playback()
            # Wait briefly for playback to stop
            time.sleep(0.5)
        
        self.audio.terminate()


# Test module
if __name__ == "__main__":
    from audio_mixer import start_mixer, stop_mixer
    
    print("🧪 Testing TTS Audio Router with Mixer\n")
    
    # Start mixer first
    print("Starting audio mixer...")
    if not start_mixer():
        print("❌ Failed to start mixer")
        exit(1)
    
    time.sleep(1)  # Let mixer initialize
    
    router = TTSAudioRouter()
    
    # Generate test audio (440 Hz tone for 2 seconds)
    print("Test: Playing 440 Hz tone for 2 seconds...")
    
    sample_rate = 16000
    duration = 2
    frequency = 440
    
    t = np.linspace(0, duration, int(sample_rate * duration))
    samples = np.sin(2 * np.pi * frequency * t)
    
    # Convert to 16-bit PCM
    audio_data = (samples * 32767).astype(np.int16).tobytes()
    
    def on_complete():
        print("✅ Test complete!")
    
    def on_stopped():
        print("⏹️ Test stopped early")
    
    router.play_audio(audio_data, on_complete, on_stopped)
    
    # Wait for playback
    time.sleep(4)
    
    router.cleanup()
    stop_mixer()
    print("\n✅ Test finished")
