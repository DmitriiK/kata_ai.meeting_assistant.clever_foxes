#!/usr/bin/env python3
"""
Streaming Audio Transcription Application

Real-time continuous transcription using Azure Speech Service streaming API.
No chunking delays - transcribes as you speak!

Usage:
    python main_streaming.py

Controls:
    - Press Ctrl+C to stop and exit
"""
import signal
import sys
import pyaudio
import time
from azure_speech_service import AzureSpeechTranscriber
from transcription_logger import TranscriptionLogger
from config import AudioSettings, LogSettings
from audio_recorder import AudioRecorder


class StreamingTranscriptionApp:
    def __init__(self):
        """Initialize the streaming application."""
        print("🚀 Initializing Streaming Transcription App...")
        
        # Initialize components
        self.logger = TranscriptionLogger(log_file=LogSettings.LOG_FILE)
        # VAD removed - Azure has built-in silence detection
        
        # Initialize audio
        self.audio = pyaudio.PyAudio()
        self.sample_rate = AudioSettings.SAMPLE_RATE
        self.chunk_size = AudioSettings.CHUNK_SIZE
        
        # Azure Speech Service instances for each source
        self.mic_transcriber = None
        self.sys_transcriber = None
        
        # Audio streams
        self.mic_stream = None
        self.sys_stream = None
        self.mic_recognizer = None
        self.sys_recognizer = None
        
        # Control flags
        self.is_running = False
        
        # Set up signal handler
        signal.signal(signal.SIGINT, self.signal_handler)
        
        print("✅ Streaming transcription service initialized")
        print("   ☁️  Azure Speech Service in streaming mode")
        print("   ⚡ Real-time transcription with minimal delay!")
        print("   🚀 Direct audio streaming (no VAD filtering)")
        print()
    
    def signal_handler(self, signum, frame):
        """Handle Ctrl+C gracefully."""
        print("\n🛑 Stopping application...")
        self.is_running = False
        self.cleanup()
        sys.exit(0)
    
    def result_callback(self, text: str, source: str):
        """
        Callback for final transcription results.
        
        Args:
            text: Transcribed text
            source: Audio source label
        """
        if text and text.strip():
            self.logger.log_transcription(text, source)
    
    def interim_callback(self, text: str, source: str):
        """
        Callback for interim/partial transcription results.
        Shows what's being transcribed in real-time.
        
        Args:
            text: Partial transcribed text
            source: Audio source label
        """
        if text and text.strip():
            self.logger.log_interim_result(text, source)
    
    def audio_callback_mic(self, in_data, frame_count, time_info, status):
        """Callback for microphone audio stream."""
        if self.is_running and self.mic_stream:
            # Send all audio directly to Azure (no VAD filtering)
            # Azure has built-in silence detection for faster response
            self.mic_stream.write(in_data)
        
        return (in_data, pyaudio.paContinue)
    
    def audio_callback_sys(self, in_data, frame_count, time_info, status):
        """Callback for system audio stream."""
        if self.is_running and self.sys_stream:
            # Send all audio directly to Azure (no VAD filtering)
            # Azure has built-in silence detection for faster response
            self.sys_stream.write(in_data)
        
        return (in_data, pyaudio.paContinue)
    
    def run(self):
        """Run streaming transcription."""
        # Detect audio devices
        recorder = AudioRecorder(
            sample_rate=self.sample_rate,
            chunk_size=self.chunk_size
        )
        devices = recorder.list_audio_devices()
        
        print("\n🔧 Detecting audio devices...")
        
        # Find microphone
        mic_device = None
        for device in devices:
            if device['is_default_input'] and device['can_record']:
                mic_device = device['index']
                print(f"🎤 Microphone: [{device['index']}] {device['name']}")
                break
        
        # Find system audio device
        sys_device = None
        virtual_keywords = [
            'blackhole', 'voicemeeter', 'vb-cable', 'loopback'
        ]
        for device in devices:
            device_name_lower = device['name'].lower()
            has_keyword = any(
                keyword in device_name_lower
                for keyword in virtual_keywords
            )
            if has_keyword and device['can_record']:
                sys_device = device['index']
                sys_name = device['name']
                print(f"🔊 System Audio: [{device['index']}] {sys_name}")
                break
        
        if sys_device is None:
            print("⚠️  No virtual audio device detected!")
            print("   Only microphone will be captured.")
        
        # Initialize Azure transcribers with callbacks
        print("\n🎙️  Starting streaming recognition...")
        
        if mic_device is not None:
            self.mic_transcriber = AzureSpeechTranscriber(
                logger=self.logger
            )
            self.mic_stream, self.mic_recognizer = (
                self.mic_transcriber.start_continuous_recognition(
                    source_label="🎤 MICROPHONE",
                    result_callback=self.result_callback,
                    interim_callback=(
                        self.interim_callback
                        if LogSettings.SHOW_INTERIM_RESULTS else None
                    )
                )
            )
        
        if sys_device is not None:
            self.sys_transcriber = AzureSpeechTranscriber(
                logger=self.logger
            )
            self.sys_stream, self.sys_recognizer = (
                self.sys_transcriber.start_continuous_recognition(
                    source_label="🔊 SYSTEM_AUDIO",
                    result_callback=self.result_callback,
                    interim_callback=(
                        self.interim_callback
                        if LogSettings.SHOW_INTERIM_RESULTS else None
                    )
                )
            )
        
        # Start audio streams
        self.is_running = True
        
        print("\n" + "=" * 60)
        print("🎙️  LIVE STREAMING TRANSCRIPTION")
        print("=" * 60)
        print("📝 Real-time transcription from microphone and system audio")
        print("⚡ No chunking delays - transcribes as you speak!")
        print("🛑 Press Ctrl+C to stop")
        print("=" * 60 + "\n")
        
        # Open PyAudio streams
        mic_audio_stream = None
        sys_audio_stream = None
        
        try:
            if mic_device is not None and self.mic_stream:
                mic_audio_stream = self.audio.open(
                    format=pyaudio.paInt16,
                    channels=1,
                    rate=self.sample_rate,
                    input=True,
                    input_device_index=mic_device,
                    frames_per_buffer=self.chunk_size,
                    stream_callback=self.audio_callback_mic
                )
                mic_audio_stream.start_stream()
                print("✅ Microphone streaming active")
            
            if sys_device is not None and self.sys_stream:
                sys_audio_stream = self.audio.open(
                    format=pyaudio.paInt16,
                    channels=1,
                    rate=self.sample_rate,
                    input=True,
                    input_device_index=sys_device,
                    frames_per_buffer=self.chunk_size,
                    stream_callback=self.audio_callback_sys
                )
                sys_audio_stream.start_stream()
                print("✅ System audio streaming active")
            
            print("\n🎤 Listening... Speak now!\n")
            
            # Keep running until interrupted
            while self.is_running:
                time.sleep(0.1)
                
        except Exception as e:
            print(f"❌ Error: {e}")
        finally:
            # Stop streams
            if mic_audio_stream:
                mic_audio_stream.stop_stream()
                mic_audio_stream.close()
            if sys_audio_stream:
                sys_audio_stream.stop_stream()
                sys_audio_stream.close()
            
            self.cleanup()
    
    def cleanup(self):
        """Clean up resources."""
        print("🧹 Cleaning up...")
        
        if self.mic_transcriber and self.mic_recognizer:
            self.mic_transcriber.stop_continuous_recognition(
                self.mic_recognizer
            )
        
        if self.sys_transcriber and self.sys_recognizer:
            self.sys_transcriber.stop_continuous_recognition(
                self.sys_recognizer
            )
        
        if self.audio:
            self.audio.terminate()
        
        self.logger.log_info("Application stopped")
        print("👋 Goodbye!")


def main():
    """Main entry point."""
    app = StreamingTranscriptionApp()
    app.run()


if __name__ == "__main__":
    main()
