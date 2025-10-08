"""
Simple audio recorder for capturing microphone input.
"""
import pyaudio
import io
import wave
from typing import Generator


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
