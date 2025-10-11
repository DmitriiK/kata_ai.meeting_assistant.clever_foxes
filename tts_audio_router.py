"""
TTS Audio Router
Routes buffered TTS audio to virtual microphone device.
Supports playback control (start/stop).
"""
import pyaudio
from threading import Thread, Event, Lock
from typing import Optional
import time


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
        Play audio data to both virtual device and default output.
        This allows you to hear the translation while routing to mic.
        
        Args:
            audio_data: Audio data to play (16kHz, mono, PCM16)
            on_complete: Optional callback when playback completes normally
            on_stopped: Optional callback when playback is stopped early
        """
        if self.virtual_device_index is None:
            print("❌ Cannot play: virtual device not found")
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
                    # Open TWO streams: one to virtual mic, one to speakers
                    virtual_stream = self.audio.open(
                        format=pyaudio.paInt16,
                        channels=1,
                        rate=16000,  # Azure TTS outputs at 16kHz
                        output=True,
                        output_device_index=self.virtual_device_index,
                        frames_per_buffer=1024
                    )
                    
                    # Open stream to default output (your speakers/headphones)
                    speaker_stream = self.audio.open(
                        format=pyaudio.paInt16,
                        channels=1,
                        rate=16000,
                        output=True,
                        frames_per_buffer=1024
                    )
                    
                    # Play audio in chunks to BOTH streams simultaneously
                    chunk_size = 1024 * 2  # 2 bytes per sample (16-bit)
                    offset = 0
                    
                    while offset < len(audio_data):
                        # Check if stop requested
                        if self.stop_event.is_set():
                            print("⏹️ Playback stopped by user")
                            virtual_stream.stop_stream()
                            virtual_stream.close()
                            speaker_stream.stop_stream()
                            speaker_stream.close()
                            self.is_playing = False
                            
                            if on_stopped:
                                on_stopped()
                            return
                        
                        # Get chunk
                        chunk = audio_data[offset:offset + chunk_size]
                        
                        # Write to BOTH streams (virtual mic + speakers)
                        virtual_stream.write(chunk)
                        speaker_stream.write(chunk)
                        
                        offset += chunk_size
                    
                    # Cleanup both streams
                    virtual_stream.stop_stream()
                    virtual_stream.close()
                    speaker_stream.stop_stream()
                    speaker_stream.close()
                    
                    print(
                        f"✅ Playback complete to both outputs "
                        f"({len(audio_data)} bytes played)"
                    )
                    
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
    import numpy as np
    
    print("🧪 Testing TTS Audio Router\n")
    
    router = TTSAudioRouter()
    
    if router.virtual_device_index is None:
        print("❌ Cannot test: virtual device not found")
        print("Please install BlackHole or similar virtual audio device")
    else:
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
        time.sleep(3)
        
        router.cleanup()
