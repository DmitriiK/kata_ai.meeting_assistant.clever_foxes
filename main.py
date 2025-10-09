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
        print("   - 🌈 Transcriptions appear in BRIGHT COLORS below!")
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
            
            # Log result
            self.logger.log_transcription(transcription, "single_recording")
            
            print("\n✅ Transcription complete!")
            
        except Exception as e:
            error_msg = f"Error during transcription: {e}"
            self.logger.log_error(error_msg)
            print(f"❌ {error_msg}")
        finally:
            self.recorder.cleanup()
    
    def show_audio_devices(self):
        """Show available audio input devices."""
        self.recorder.print_audio_devices()
        
        # Check for virtual audio devices
        devices = self.recorder.list_audio_devices()
        virtual_keywords = ['blackhole', 'voicemeeter', 'vb-cable', 'loopback']
        has_virtual_audio = any(
            any(keyword in device['name'].lower()
                for keyword in virtual_keywords)
            for device in devices
        )
        
        print("\n💡 For meeting mode, you'll need:")
        print("   - Microphone device (your voice)")
        print("   - Virtual audio device (system/meeting audio)")
        
        if not has_virtual_audio:
            print("\n🚨 No virtual audio device detected!")
            print("📥 Recommended cross-platform solution:")
            print("   🌐 VB-Audio VoiceMeeter (Free)")
            print("   📂 Download: https://vb-audio.com/Voicemeeter/")
            print("   ✅ Works on Windows, Mac, and Linux")
            print("\n🔧 Alternative options:")
            print("   🍎 Mac: BlackHole (https://github.com/ExistentialAudio/BlackHole)")
            print("   🪟 Windows: VB-Cable (https://vb-audio.com/Cable/)")
        else:
            print("✅ Virtual audio device detected - you're ready for meeting mode!")
        
        print("\n🔄 Returning to main menu...\n")
        
    def run_meeting_mode(self, duration: float = 10.0):
        """
        Record from both microphone and system audio for meeting transcription.
        
        Args:
            duration: Duration to record in seconds
        """
        print("🎭 MEETING MODE - Dual Audio Source Recording")
        print("=" * 50)
        
        # Show available devices
        devices = self.recorder.list_audio_devices()
        print("Available audio devices:")
        for device in devices:
            print(f"  [{device['index']}] {device['name']}")
        
        try:
            # Get device selections
            print("\n🎤 Select microphone device:")
            mic_prompt = "Enter device number (or press Enter for default): "
            mic_choice = input(mic_prompt).strip()
            mic_device = int(mic_choice) if mic_choice else None
            
            print("\n🔊 Select system audio device:")
            print("   (For Zoom/Teams audio - may need virtual audio cable)")
            sys_prompt = "Enter device number (or press Enter to skip): "
            sys_choice = input(sys_prompt).strip()
            sys_device = int(sys_choice) if sys_choice else None
            
            if sys_device is None:
                print("\n⚠️  System audio disabled. Only microphone recorded.")
                print("   To capture meeting audio, install BlackHole")
            
            self.logger.log_info(f"Starting meeting mode ({duration}s)")
            print(f"\n🎤 Recording from both sources for {duration} seconds...")
            print("🔊 Start your meeting audio now!\n")
            
            # Record from both sources
            mic_audio, system_audio = self.recorder.record_dual_sources(
                duration, mic_device, sys_device
            )
            
            # Transcribe microphone audio
            if mic_audio:
                print("🤖 Transcribing microphone audio...")
                mic_transcription = self.transcription_service.transcribe_audio_bytes(
                    mic_audio
                )
                self.logger.log_transcription(mic_transcription, "🎤 MICROPHONE")
            
            # Transcribe system audio  
            if system_audio and len(system_audio) > 1000:  # Check if we got audio
                print("🤖 Transcribing system audio...")
                sys_transcription = self.transcription_service.transcribe_audio_bytes(
                    system_audio
                )
                self.logger.log_transcription(sys_transcription, "🔊 SYSTEM_AUDIO")
            else:
                print("🔇 No system audio captured")
                
            print("\n✅ Meeting transcription complete!")
            
        except ValueError:
            print("❌ Invalid device number")
        except Exception as e:
            error_msg = f"Meeting mode error: {e}"
            self.logger.log_error(error_msg)
            print(f"❌ {error_msg}")
        finally:
            self.recorder.cleanup()


def main():
    """Main application entry point."""
    app = AudioTranscriptionApp()
    
    # Show available devices
    print("\n🔧 Detecting audio devices...")
    devices = app.recorder.list_audio_devices()
    
    # Auto-detect microphone
    mic_device = None
    for device in devices:
        if device['is_default_input'] and device['can_record']:
            mic_device = device['index']
            print(f"🎤 Microphone: [{device['index']}] {device['name']}")
            break
    
    # Auto-detect system audio (look for BlackHole or similar)
    sys_device = None
    virtual_keywords = ['blackhole', 'voicemeeter', 'vb-cable', 'loopback']
    for device in devices:
        device_name_lower = device['name'].lower()
        if (any(keyword in device_name_lower for keyword in virtual_keywords)
                and device['can_record']):
            sys_device = device['index']
            print(f"🔊 System Audio: [{device['index']}] {device['name']}")
            break
    
    if sys_device is None:
        print("⚠️  No virtual audio device detected!")
        print("   Only microphone will be captured.")
        print("   Install BlackHole for full meeting transcription.")
        print("   Download: https://github.com/ExistentialAudio/BlackHole")
    
    print("\n" + "=" * 60)
    print("🎙️  CONTINUOUS DUAL AUDIO TRANSCRIPTION")
    print("=" * 60)
    print("📝 Recording both microphone and system audio")
    print("⏱️  10-second chunks with continuous transcription")
    print("🛑 Press Ctrl+C to stop")
    print("=" * 60 + "\n")
    
    try:
        chunk_count = 0
        duration = 10.0
        
        while True:
            chunk_count += 1
            print(f"\n{'=' * 60}")
            print(f"🎬 Chunk #{chunk_count} - Recording {duration}s...")
            print(f"{'=' * 60}")
            
            # Record from both sources
            mic_audio, system_audio = app.recorder.record_dual_sources(
                duration, mic_device, sys_device
            )
            
            # Transcribe microphone audio
            if mic_audio and len(mic_audio) > 1000:
                print("🤖 Transcribing microphone audio...")
                mic_transcription = (
                    app.transcription_service.transcribe_audio_bytes(mic_audio)
                )
                app.logger.log_transcription(mic_transcription, "🎤 MICROPHONE")
            
            # Transcribe system audio
            if system_audio and len(system_audio) > 1000:
                print("🤖 Transcribing system audio...")
                sys_transcription = (
                    app.transcription_service.transcribe_audio_bytes(
                        system_audio
                    )
                )
                app.logger.log_transcription(
                    sys_transcription, "🔊 SYSTEM_AUDIO"
                )
            
    except KeyboardInterrupt:
        print("\n\n� Stopping application...")
        app.logger.log_info("Application stopped by user")
        print("👋 Goodbye!")
    except Exception as e:
        error_msg = f"Error: {e}"
        app.logger.log_error(error_msg)
        print(f"❌ {error_msg}")
    finally:
        app.recorder.cleanup()
        sys.exit(0)


if __name__ == "__main__":
    main()
