"""
Voice Activity Detection (VAD) using WebRTC VAD.
Detects when speech is present in audio to optimize transcription.
"""
import webrtcvad
from typing import Generator
from config import VADSettings, AudioSettings


class VADDetector:
    """Voice Activity Detection for audio streams."""
    
    def __init__(
        self,
        sample_rate: int = AudioSettings.SAMPLE_RATE,
        aggressiveness: int = VADSettings.AGGRESSIVENESS
    ):
        """
        Initialize VAD detector.
        
        Args:
            sample_rate: Audio sample rate (must be 8000, 16000, 32000, 48000)
            aggressiveness: VAD aggressiveness (0-3)
        """
        self.sample_rate = sample_rate
        self.vad = webrtcvad.Vad(aggressiveness)
        self.frame_duration_ms = VADSettings.FRAME_DURATION_MS
        
        # Calculate frame size
        self.frame_size = int(
            sample_rate * self.frame_duration_ms / 1000
        )
        self.frame_bytes = self.frame_size * 2  # 16-bit audio
    
    def is_speech(self, audio_bytes: bytes) -> bool:
        """
        Check if audio bytes contain speech.
        
        Args:
            audio_bytes: Raw PCM audio bytes
            
        Returns:
            True if speech detected, False otherwise
        """
        try:
            # Ensure audio is correct length
            if len(audio_bytes) != self.frame_bytes:
                return False
            
            return self.vad.is_speech(audio_bytes, self.sample_rate)
        except Exception:
            return False
    
    def detect_speech_in_chunk(self, audio_chunk: bytes) -> bool:
        """
        Detect if speech is present in an audio chunk.
        
        Args:
            audio_chunk: Audio chunk (may be longer than frame size)
            
        Returns:
            True if speech detected in any frame
        """
        # Skip WAV header if present (44 bytes)
        if audio_chunk[:4] == b'RIFF':
            audio_chunk = audio_chunk[44:]
        
        speech_frames = 0
        total_frames = 0
        
        # Process chunk in frames
        chunk_len = len(audio_chunk) - self.frame_bytes
        for i in range(0, chunk_len, self.frame_bytes):
            frame = audio_chunk[i:i + self.frame_bytes]
            if len(frame) == self.frame_bytes:
                total_frames += 1
                if self.is_speech(frame):
                    speech_frames += 1
        
        # Consider speech if at least 30% of frames contain speech
        if total_frames > 0:
            speech_ratio = speech_frames / total_frames
            return speech_ratio > 0.3
        
        return False
    
    def get_speech_segments(
        self,
        audio_data: bytes,
        min_speech_duration: float = VADSettings.MIN_SPEECH_DURATION
    ) -> Generator[tuple[int, int], None, None]:
        """
        Get speech segments from audio data.
        
        Args:
            audio_data: Full audio data
            min_speech_duration: Minimum speech duration in seconds
            
        Yields:
            Tuples of (start_byte, end_byte) for speech segments
        """
        # Skip WAV header if present
        if audio_data[:4] == b'RIFF':
            audio_data = audio_data[44:]
        
        min_frames = int(
            min_speech_duration * 1000 / self.frame_duration_ms
        )
        
        speech_frames = []
        current_segment_start = None
        
        # Process audio in frames
        data_len = len(audio_data) - self.frame_bytes
        for i in range(0, data_len, self.frame_bytes):
            frame = audio_data[i:i + self.frame_bytes]
            
            if len(frame) == self.frame_bytes:
                is_speech_frame = self.is_speech(frame)
                
                if is_speech_frame:
                    if current_segment_start is None:
                        current_segment_start = i
                    speech_frames.append(i)
                else:
                    # End of speech segment
                    if current_segment_start is not None:
                        segment_frames = len(speech_frames)
                        if segment_frames >= min_frames:
                            yield (current_segment_start, i)
                        current_segment_start = None
                        speech_frames = []
        
        # Handle final segment
        if (current_segment_start is not None and
                len(speech_frames) >= min_frames):
            yield (current_segment_start, len(audio_data))
