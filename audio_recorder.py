"""
Enhanced audio recorder for capturing both microphone and system audio.
"""
import pyaudio
import io
import wave
import threading
from typing import Generator, Dict, List, Tuple, Optional


class AudioRecorder:
    def __init__(self, sample_rate: int = 16000, chunk_size: int = 1024):
        """
        Initialize audio recorder.
        
        Args:
            sample_rate: Audio sample rate (Whisper works well with 16kHz)
            chunk_size: Audio chunk size for streaming
        """
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.audio_format = pyaudio.paInt16
        self.channels = 1  # Mono audio
        
        self.p = pyaudio.PyAudio()
        
    def list_audio_devices(self) -> List[Dict]:
        """
        List all available audio devices with input/output capabilities.
        
        Returns:
            List of device info dictionaries
        """
        devices = []
        default_input = self.p.get_default_input_device_info()
        default_output = self.p.get_default_output_device_info()
        
        for i in range(self.p.get_device_count()):
            device_info = self.p.get_device_info_by_index(i)
            
            # Include devices with input capability or useful output devices
            if (device_info['maxInputChannels'] > 0 or
                    device_info['maxOutputChannels'] > 0):
                
                device_data = {
                    'index': i,
                    'name': device_info['name'],
                    'input_channels': device_info['maxInputChannels'],
                    'output_channels': device_info['maxOutputChannels'],
                    'sample_rate': int(device_info['defaultSampleRate']),
                    'is_default_input': i == default_input['index'],
                    'is_default_output': i == default_output['index'],
                    'can_record': device_info['maxInputChannels'] > 0
                }
                devices.append(device_data)
        return devices
        
    def get_default_output_device(self) -> Optional[int]:
        """Get the default output device index for system audio capture."""
        try:
            default_output = self.p.get_default_output_device_info()
            return default_output['index']
        except Exception:
            return None
    
    def find_best_system_audio_device(self) -> Optional[int]:
        """
        Find the best device for capturing system audio.
        Prioritizes: BlackHole -> SoundFlower -> Default Output
        """
        devices = self.list_audio_devices()
        
        # Look for virtual audio cables first
        virtual_devices = ['blackhole', 'soundflower', 'loopback']
        for device in devices:
            device_name = device['name'].lower()
            if any(vd in device_name for vd in virtual_devices) and device['can_record']:
                print(f"🔊 Found virtual audio device: {device['name']}")
                return device['index']
        
        # Fall back to default output if it supports input
        default_output_idx = self.get_default_output_device()
        if default_output_idx:
            for device in devices:
                if (device['index'] == default_output_idx and 
                    device['can_record']):
                    print(f"🔊 Using default output device: {device['name']}")
                    return device['index']
        
        # Look for any device that mentions system/output audio
        system_keywords = ['system', 'output', 'speaker', 'headphone']
        for device in devices:
            device_name = device['name'].lower()
            if any(kw in device_name for kw in system_keywords) and device['can_record']:
                print(f"🔊 Found system audio device: {device['name']}")
                return device['index']
        
        return None
        
    def print_audio_devices(self):
        """Print available audio devices with capabilities."""
        devices = self.list_audio_devices()
        print("🎤 Available Audio Devices:")
        print("-" * 70)
        for device in devices:
            device_type = []
            if device['input_channels'] > 0:
                device_type.append("🎤 Input")
            if device['output_channels'] > 0:
                device_type.append("🔊 Output")
            
            type_str = " + ".join(device_type)
            default_marker = ""
            if device['is_default_input']:
                default_marker += " [DEFAULT INPUT]"
            if device['is_default_output']:
                default_marker += " [DEFAULT OUTPUT]"
            
            print(f"\n[{device['index']}] {device['name']}")
            print(f"    Type: {type_str}{default_marker}")
            print(f"    Input channels: {device['input_channels']}, "
                  f"Output channels: {device['output_channels']}")
            print(f"    Sample Rate: {device['sample_rate']} Hz")
            can_record = '✅ Yes' if device['can_record'] else '❌ No'
            print(f"    Can record: {can_record}")
        print("\n" + "-" * 70)
        
    def record_dual_sources(
        self,
        duration: float,
        mic_device_index: Optional[int] = None,
        system_device_index: Optional[int] = None
    ) -> Tuple[bytes, bytes]:
        """
        Record from both microphone and system audio simultaneously.
        
        Args:
            duration: Recording duration in seconds
            mic_device_index: Microphone device index (None for default)
            system_device_index: System audio device index (None to skip)
            
        Returns:
            Tuple of (mic_audio_bytes, system_audio_bytes)
        """
        mic_frames = []
        system_frames = []
        
        # Set up microphone stream
        mic_stream = self.p.open(
            format=self.audio_format,
            channels=self.channels,
            rate=self.sample_rate,
            input=True,
            input_device_index=mic_device_index,
            frames_per_buffer=self.chunk_size
        )
        
        # Set up system audio stream (if available)
        system_stream = None
        if system_device_index is not None:
            try:
                system_stream = self.p.open(
                    format=self.audio_format,
                    channels=self.channels,
                    rate=self.sample_rate,
                    input=True,
                    input_device_index=system_device_index,
                    frames_per_buffer=self.chunk_size
                )
            except Exception as e:
                print(f"⚠️  Could not open system audio device: {e}")
                system_stream = None
        
        frames_to_record = int(
            self.sample_rate / self.chunk_size * duration
        )
        
        print(f"🎤 Recording from both sources for {duration} seconds...")
        
        for _ in range(frames_to_record):
            # Record from microphone
            try:
                mic_data = mic_stream.read(
                    self.chunk_size, exception_on_overflow=False
                )
                mic_frames.append(mic_data)
            except Exception as e:
                print(f"⚠️  Microphone read error: {e}")
                
            # Record from system audio
            if system_stream:
                try:
                    system_data = system_stream.read(
                        self.chunk_size, exception_on_overflow=False
                    )
                    system_frames.append(system_data)
                except Exception as e:
                    print(f"⚠️  System audio read error: {e}")
        
        # Stop streams
        mic_stream.stop_stream()
        mic_stream.close()
        if system_stream:
            system_stream.stop_stream()
            system_stream.close()
        
        # Convert to WAV format
        mic_audio = self._frames_to_wav(mic_frames)
        if system_frames:
            system_audio = self._frames_to_wav(system_frames)
        else:
            system_audio = b""
        
        return mic_audio, system_audio
        
    def _frames_to_wav(self, frames: List[bytes]) -> bytes:
        """Convert audio frames to WAV format bytes."""
        if not frames:
            return b""
            
        wav_buffer = io.BytesIO()
        with wave.open(wav_buffer, 'wb') as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(self.p.get_sample_size(self.audio_format))
            wf.setframerate(self.sample_rate)
            wf.writeframes(b''.join(frames))
        
        wav_buffer.seek(0)
        return wav_buffer.read()
        
    def start_recording_stream(self) -> Generator[bytes, None, None]:
        """
        Start streaming audio from microphone.
        
        Yields:
            Audio chunks as bytes
        """
        stream = self.p.open(
            format=self.audio_format,
            channels=self.channels,
            rate=self.sample_rate,
            input=True,
            frames_per_buffer=self.chunk_size
        )
        
        try:
            print("🎤 Recording started... Press Ctrl+C to stop")
            while True:
                data = stream.read(
                    self.chunk_size, exception_on_overflow=False
                )
                yield data
        except KeyboardInterrupt:
            print("🛑 Recording stopped")
        finally:
            stream.stop_stream()
            stream.close()
    
    def record_fixed_duration(self, duration_seconds: float) -> bytes:
        """
        Record audio for a fixed duration.
        
        Args:
            duration_seconds: How long to record
            
        Returns:
            Audio data as WAV bytes
        """
        stream = self.p.open(
            format=self.audio_format,
            channels=self.channels,
            rate=self.sample_rate,
            input=True,
            frames_per_buffer=self.chunk_size
        )
        
        frames = []
        frames_to_record = int(
            self.sample_rate / self.chunk_size * duration_seconds
        )
        
        print(f"🎤 Recording for {duration_seconds} seconds...")
        
        for _ in range(frames_to_record):
            data = stream.read(self.chunk_size, exception_on_overflow=False)
            frames.append(data)
        
        stream.stop_stream()
        stream.close()
        
        # Convert to WAV format in memory
        wav_buffer = io.BytesIO()
        with wave.open(wav_buffer, 'wb') as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(self.p.get_sample_size(self.audio_format))
            wf.setframerate(self.sample_rate)
            wf.writeframes(b''.join(frames))
        
        wav_buffer.seek(0)
        return wav_buffer.read()
    
    def cleanup(self):
        """Clean up PyAudio resources."""
        self.p.terminate()
