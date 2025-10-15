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
from services.speech_engine.azure_speech_service import AzureSpeechTranscriber
from services.speech_engine.stt.transcription_logger import TranscriptionLogger
from config import AudioSettings, LogSettings
from services.audio.audio_recorder import AudioRecorder
from services.llm.meeting_assistant_service import MeetingAssistantService


class StreamingTranscriptionApp:
    def __init__(self):
        """Initialize the streaming application."""
        print("🚀 Initializing AI-Powered Meeting Assistant...")
        
        # Initialize components
        self.logger = TranscriptionLogger(log_file=LogSettings.LOG_FILE)
        self.meeting_assistant = MeetingAssistantService()
        
        # Update logger with session directory once meeting starts
        self.session_started = False
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
        
        print("✅ AI Meeting Assistant initialized")
        print("   ☁️  Azure Speech Service in streaming mode")
        print("   🤖 AI-powered meeting insights and assistance")
        print("   ⚡ Real-time transcription with minimal delay!")
        print("   🚀 Direct audio streaming (no VAD filtering)")
        print("✅ Conversation transcription service initialized")
        print("   ☁️  Azure Conversation Transcriber API")
        print("   👥 Speaker diarization enabled")
        print("   🌍 Multi-language support")
        print("   ⚠️  ~1-3 second delay for speaker identification")
        print()
    
    def signal_handler(self, signum, frame):
        """Handle Ctrl+C gracefully."""
        print("\n🛑 Stopping application...")
        self.is_running = False
        
        # End meeting session and generate summary
        print("\n📋 Ending meeting session and generating summary...")
        summary_file = self.meeting_assistant.end_session()
        if summary_file:
            print(f"✅ Meeting summary saved to: {summary_file}")
        
        self.cleanup()
        sys.exit(0)
    
    def result_callback(self, text: str, source: str, speaker_id: str = None):
        """
        Callback for final transcription results.
        
        Args:
            text: Transcribed text
            source: Audio source label
            speaker_id: Speaker identifier
        """
        if text and text.strip():
            # Update logger session directory if not already done
            if not self.session_started and self.meeting_assistant.session_active:
                session_dir = str(self.meeting_assistant.summary_manager.session_output_dir)
                self.logger.update_session_dir(session_dir)
                self.session_started = True
            
            self.logger.log_transcription(text, source)
            
            # Process with AI meeting assistant
            import datetime
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            insights = self.meeting_assistant.add_transcription(text, source, timestamp)
            
            # Display AI insights if any were generated
            if insights:
                self.meeting_assistant.display_insights(insights)
    
    def interim_callback(
        self, text: str, source: str, speaker_id: str = None
    ):
        """
        Callback for interim/partial transcription results.
        Shows what's being transcribed in real-time.
        
        Args:
            text: Partial transcribed text
            source: Audio source label
            speaker_id: Speaker identifier
        """
        if text and text.strip():
            self.logger.log_interim_result(text, source, speaker_id)
    
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
        print("\n🎙️  Starting conversation transcription with speaker "
              "diarization...")
        
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
        print("🤖 AI-POWERED MEETING ASSISTANT")
        print("=" * 60)
        print("📝 Real-time transcription from microphone and system audio")
        print("🤖 AI-powered follow-up questions and meeting insights")
        print("📋 Automatic summarization of key points and decisions")
        print("⚡ No chunking delays - transcribes as you speak!")
        print("🛑 Press Ctrl+C to stop and generate meeting summary")
        print("🎙️  LIVE CONVERSATION TRANSCRIPTION")
        print("=" * 60)
        print("📝 Transcription with speaker identification")
        print("👥 Distinguishes between multiple speakers")
        print("⏱️  ~1-3 second delay for speaker diarization")
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
