#!/usr/bin/env python3
"""
Simple Audio Transcription Application

Captures audio from microphone, transcribes it using Whisper,
and logs results to console and file.

Usage:
    python main.py

Controls:
    - Press Ctrl+C to stop recording and exit
    - The app records in 5-second chunks and transcribes each chunk
"""
import signal
import sys
from audio_recorder import AudioRecorder
from transcription_service import TranscriptionService
from transcription_logger import TranscriptionLogger


class AudioTranscriptionApp:
    def __init__(self):
        """Initialize the application components."""
        print("🚀 Initializing Audio Transcription App...")
        
        # Initialize components
        self.recorder = AudioRecorder(sample_rate=16000, chunk_size=1024)
        self.transcription_service = TranscriptionService(model_size="base")
        self.logger = TranscriptionLogger()
        
        # Set up signal handler for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        
        print("✅ Application initialized successfully!")
        print("📋 Instructions:")
        print("   - Speak into your microphone")
        print("   - The app records in 5-second chunks")
        print("   - Press Ctrl+C to stop and exit")
        print("   - Transcriptions are logged to 'transcriptions.log'")
        print()
    
    def signal_handler(self, signum, frame):
        """Handle Ctrl+C gracefully."""
        print("\n🛑 Stopping application...")
        self.logger.log_info("Application stopped by user")
        self.recorder.cleanup()
        sys.exit(0)
    
    def run_continuous_transcription(self, chunk_duration: float = 5.0):
        """
        Run continuous transcription in chunks.
        
        Args:
            chunk_duration: Duration of each recording chunk in seconds
        """
        self.logger.log_info("Starting continuous transcription")
        duration_str = f"{chunk_duration}s"
        print(f"🎤 Starting continuous recording in {duration_str} chunks...")
        print("🔊 Speak now! (Press Ctrl+C to stop)\n")
        
        chunk_count = 0
        
        try:
            while True:
                chunk_count += 1
                print(f"📹 Recording chunk #{chunk_count}...")
                
                # Record audio chunk
                audio_data = self.recorder.record_fixed_duration(
                    chunk_duration
                )
                
                # Transcribe the audio
                print("🤖 Transcribing...")
                transcription = (
                    self.transcription_service.transcribe_audio_bytes(
                        audio_data
                    )
                )
                
                # Debug: Show what we got from transcription
                print(f"🔍 DEBUG: Transcription result: '{transcription}'")
                print(f"🔍 DEBUG: Transcription type: {type(transcription)}")
                
                # Log the result
                if transcription and transcription.strip():
                    self.logger.log_transcription(
                        transcription, f"chunk_{chunk_count}"
                    )
                else:
                    print("🔇 No speech detected in this chunk")
                
                print("-" * 50)
                
        except KeyboardInterrupt:
            self.signal_handler(None, None)
        except Exception as e:
            error_msg = f"Unexpected error: {e}"
            self.logger.log_error(error_msg)
            print(f"❌ {error_msg}")
    
    def run_single_transcription(self, duration: float = 10.0):
        """
        Record and transcribe a single audio clip.
        
        Args:
            duration: Duration to record in seconds
        """
        self.logger.log_info(f"Starting single transcription ({duration}s)")
        print(f"🎤 Recording for {duration} seconds...")
        print("🔊 Speak now!\n")
        
        try:
            # Record audio
            audio_data = self.recorder.record_fixed_duration(duration)
            
            # Transcribe
            print("🤖 Transcribing...")
            transcription = self.transcription_service.transcribe_audio_bytes(
                audio_data
            )
            
            # Debug: Show what we got from transcription
            print(f"🔍 DEBUG: Transcription result: '{transcription}'")
            print(f"🔍 DEBUG: Transcription type: {type(transcription)}")
            
            # Log result
            self.logger.log_transcription(transcription, "single_recording")
            
            print("\n✅ Transcription complete!")
            
        except Exception as e:
            error_msg = f"Error during transcription: {e}"
            self.logger.log_error(error_msg)
            print(f"❌ {error_msg}")
        finally:
            self.recorder.cleanup()


def main():
    """Main application entry point."""
    app = AudioTranscriptionApp()
    
    # Simple menu
    print("Select mode:")
    print("1. Continuous transcription (5-second chunks)")
    print("2. Single transcription (10 seconds)")
    print("3. Exit")
    
    try:
        choice = input("\nEnter your choice (1-3): ").strip()
        
        if choice == "1":
            app.run_continuous_transcription()
        elif choice == "2":
            app.run_single_transcription()
        elif choice == "3":
            print("👋 Goodbye!")
            sys.exit(0)
        else:
            print("❌ Invalid choice. Exiting.")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
