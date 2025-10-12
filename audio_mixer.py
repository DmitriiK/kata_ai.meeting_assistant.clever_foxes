"""
Audio Mixer: Routes microphone to virtual device with TTS mixing.

Continuously routes microphone audio to virtual audio device
(BlackHole/VB-CABLE) and mixes in TTS audio on demand.

This solves the problem of using both real voice AND TTS translations:
- Your microphone audio is continuously passed through to virtual device
- When TTS plays, it's mixed with your microphone audio
- Meeting apps capture from Aggregate Device and hear both

Platform Support:
- macOS: Uses BlackHole 2ch as virtual device, Jabra/other mic as input
- Windows: Uses VB-CABLE as virtual device, default mic as input
"""

import pyaudio
import threading
import time
import logging
from typing import Optional
import numpy as np

logger = logging.getLogger(__name__)


class AudioMixer:
    """
    Continuously routes microphone audio to virtual audio device
    with mixing capability.
    """
    
    def __init__(self):
        self.audio = pyaudio.PyAudio()
        self.is_running = False
        self.mixer_thread: Optional[threading.Thread] = None
        
        # Audio configuration
        self.sample_rate = 48000  # 48kHz to match system
        self.channels = 2  # Stereo
        self.chunk_size = 1024  # Frames per buffer
        self.format = pyaudio.paInt16
        
        # Device indices
        self.mic_device_index: Optional[int] = None
        self.virtual_device_index: Optional[int] = None
        
        # TTS mixing
        self.tts_buffer = bytearray()
        self.tts_lock = threading.Lock()
        self.is_tts_playing = False
        
    def _find_microphone_device(self) -> Optional[int]:
        """
        Find the physical microphone device (not virtual devices).
        Priority: Jabra > MacBook Pro Microphone > Default input
        """
        device_count = self.audio.get_device_count()
        
        # Priority list for microphones
        priority_mics = [
            'jabra', 'evolve', 'built-in', 'macbook pro microphone'
        ]
        
        candidates = []
        default_input = self.audio.get_default_input_device_info()
        
        for i in range(device_count):
            try:
                info = self.audio.get_device_info_by_index(i)
                name = info['name'].lower()
                
                # Skip virtual devices
                skip_devices = ['blackhole', 'vb-cable', 'aggregate',
                                'multi-output']
                if any(skip in name for skip in skip_devices):
                    continue
                
                # Must have input channels
                if info['maxInputChannels'] > 0:
                    # Check priority
                    priority = 999
                    for idx, keyword in enumerate(priority_mics):
                        if keyword in name:
                            priority = idx
                            break
                    
                    candidates.append({
                        'index': i,
                        'name': info['name'],
                        'priority': priority,
                        'is_default': (i == default_input['index'])
                    })
                    
            except Exception:
                continue
        
        if not candidates:
            logger.error("❌ No microphone device found!")
            return None
        
        # Sort by priority, then default, then index
        candidates.sort(
            key=lambda x: (x['priority'], not x['is_default'], x['index'])
        )
        
        selected = candidates[0]
        logger.info(
            f"🎤 Selected microphone: {selected['name']} "
            f"(index: {selected['index']})"
        )
        return selected['index']
    
    def _find_virtual_device(self) -> Optional[int]:
        """
        Find the virtual audio device (BlackHole/VB-CABLE).
        """
        device_count = self.audio.get_device_count()
        
        for i in range(device_count):
            try:
                info = self.audio.get_device_info_by_index(i)
                name = info['name'].lower()
                
                # Look for BlackHole (macOS) or VB-CABLE (Windows)
                virtual_keywords = ['blackhole', 'vb-cable', 'vb cable']
                if any(keyword in name for keyword in virtual_keywords):
                    # Must have output channels
                    if info['maxOutputChannels'] >= 2:
                        logger.info(
                            f"✅ Virtual audio device found: {info['name']} "
                            f"(index: {i})"
                        )
                        return i
                        
            except Exception:
                continue
        
        logger.error(
            "❌ Virtual audio device not found! "
            "Install BlackHole (macOS) or VB-CABLE (Windows)"
        )
        return None
    
    def start(self) -> bool:
        """
        Start the audio mixer thread.
        Returns True if started successfully, False otherwise.
        """
        if self.is_running:
            logger.warning("⚠️ Audio mixer already running")
            return True
        
        # Find devices
        self.mic_device_index = self._find_microphone_device()
        self.virtual_device_index = self._find_virtual_device()
        
        if self.mic_device_index is None or self.virtual_device_index is None:
            logger.error("❌ Cannot start mixer: required devices not found")
            return False
        
        # Start mixer thread
        self.is_running = True
        self.mixer_thread = threading.Thread(
            target=self._mixer_loop, daemon=True
        )
        self.mixer_thread.start()
        
        logger.info("✅ Audio mixer started")
        return True
    
    def stop(self):
        """
        Stop the audio mixer thread.
        """
        if not self.is_running:
            return
        
        self.is_running = False
        
        if self.mixer_thread:
            self.mixer_thread.join(timeout=2.0)
        
        logger.info("⏹️ Audio mixer stopped")
    
    def _mixer_loop(self):
        """
        Main mixer loop: read from mic, mix with TTS, write to virtual.
        """
        mic_stream = None
        virtual_stream = None
        
        # Validate before starting
        if self.audio is None:
            logger.error("❌ PyAudio not initialized")
            return
        
        if self.mic_device_index is None or self.virtual_device_index is None:
            logger.error("❌ Required audio devices not found")
            return
        
        try:
            # Open microphone input stream
            mic_stream = self.audio.open(
                format=self.format,
                channels=1,  # Microphone is mono
                rate=self.sample_rate,
                input=True,
                input_device_index=self.mic_device_index,
                frames_per_buffer=self.chunk_size
            )
            
            # Open virtual device output stream
            virtual_stream = self.audio.open(
                format=self.format,
                channels=self.channels,  # Virtual device is stereo
                rate=self.sample_rate,
                output=True,
                output_device_index=self.virtual_device_index,
                frames_per_buffer=self.chunk_size
            )
            
            logger.info("🔄 Mixer loop started: mic → virtual device")
            
            bytes_per_sample = 2  # paInt16 = 2 bytes
            chunk_bytes = self.chunk_size * bytes_per_sample
            
            while self.is_running:
                try:
                    # Read from microphone (mono)
                    mic_data = mic_stream.read(
                        self.chunk_size, exception_on_overflow=False
                    )
                    
                    # Convert to numpy array for mixing
                    mic_array = np.frombuffer(mic_data, dtype=np.int16)
                    
                    # Duplicate mono to stereo (L and R same)
                    stereo_array = np.column_stack(
                        (mic_array, mic_array)
                    ).flatten()
                    
                    # Check if TTS is playing
                    with self.tts_lock:
                        tts_buffer_size = chunk_bytes * self.channels
                        if (self.is_tts_playing and
                                len(self.tts_buffer) >= tts_buffer_size):
                            # Extract TTS chunk
                            tts_chunk = bytes(
                                self.tts_buffer[:tts_buffer_size]
                            )
                            self.tts_buffer = self.tts_buffer[
                                tts_buffer_size:
                            ]
                            
                            # Convert TTS to numpy array
                            tts_array = np.frombuffer(
                                tts_chunk, dtype=np.int16
                            )
                            
                            # Mix: average mic and TTS (prevents clipping)
                            mixed_array = (
                                stereo_array.astype(np.int32) +
                                tts_array.astype(np.int32)
                            ) // 2
                            mixed_array = np.clip(
                                mixed_array, -32768, 32767
                            ).astype(np.int16)
                            
                            output_data = mixed_array.tobytes()
                        
                        elif self.is_tts_playing and len(self.tts_buffer) > 0:
                            # TTS buffer running out, pad with zeros
                            remaining = len(self.tts_buffer)
                            tts_chunk = bytes(self.tts_buffer)
                            self.tts_buffer.clear()
                            
                            # Pad TTS chunk
                            pad_size = chunk_bytes * self.channels - remaining
                            tts_padded = tts_chunk + b'\x00' * pad_size
                            tts_array = np.frombuffer(
                                tts_padded, dtype=np.int16
                            )
                            
                            # Mix
                            mixed_array = (
                                stereo_array.astype(np.int32) +
                                tts_array.astype(np.int32)
                            ) // 2
                            mixed_array = np.clip(
                                mixed_array, -32768, 32767
                            ).astype(np.int16)
                            
                            output_data = mixed_array.tobytes()
                        
                        elif self.is_tts_playing and len(self.tts_buffer) == 0:
                            # TTS finished
                            self.is_tts_playing = False
                            logger.info("✅ TTS mixing complete")
                            output_data = stereo_array.tobytes()
                        
                        else:
                            # No TTS, just pass through mic audio
                            output_data = stereo_array.tobytes()
                    
                    # Write to virtual device
                    virtual_stream.write(output_data)
                    
                except Exception as e:
                    # Only log if we're supposed to be running
                    if self.is_running:
                        logger.error(f"❌ Error in mixer loop: {e}")
                    time.sleep(0.01)
            
        except Exception as e:
            logger.error(f"❌ Fatal error in mixer loop: {e}")
        
        finally:
            # Clean up streams
            if mic_stream:
                try:
                    mic_stream.stop_stream()
                    mic_stream.close()
                except Exception:
                    pass
            
            if virtual_stream:
                try:
                    virtual_stream.stop_stream()
                    virtual_stream.close()
                except Exception:
                    pass
            
            logger.info("🔄 Mixer loop stopped")
    
    def queue_tts_audio(self, audio_data: bytes):
        """
        Queue TTS audio data to be mixed with microphone audio.
        
        Args:
            audio_data: PCM audio data (16-bit, match sample rate/channels)
        """
        with self.tts_lock:
            self.tts_buffer.extend(audio_data)
            self.is_tts_playing = True
            logger.info(
                f"🎵 TTS audio queued: {len(audio_data)} bytes "
                f"(total buffer: {len(self.tts_buffer)} bytes)"
            )
    
    def is_tts_active(self) -> bool:
        """
        Check if TTS is currently playing/mixing.
        """
        with self.tts_lock:
            return self.is_tts_playing
    
    def __del__(self):
        """Cleanup on deletion."""
        self.stop()
        if hasattr(self, 'audio'):
            self.audio.terminate()


# Global mixer instance
_mixer_instance: Optional[AudioMixer] = None


def get_mixer() -> AudioMixer:
    """
    Get the global audio mixer instance (singleton pattern).
    """
    global _mixer_instance
    if _mixer_instance is None:
        _mixer_instance = AudioMixer()
    return _mixer_instance


def start_mixer() -> bool:
    """
    Start the global audio mixer.
    Returns True if started successfully.
    """
    mixer = get_mixer()
    return mixer.start()


def stop_mixer():
    """
    Stop the global audio mixer.
    """
    global _mixer_instance
    if _mixer_instance:
        _mixer_instance.stop()
        _mixer_instance = None
