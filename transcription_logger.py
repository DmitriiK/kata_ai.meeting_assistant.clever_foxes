"""
Simple logger for transcription results.
Logs to both console and file with timestamps.
"""
import datetime
import os
from typing import Optional
from colorama import Fore, Back, Style, init

# Initialize colorama for cross-platform colored output
init(autoreset=True)


class TranscriptionLogger:
    def __init__(self, log_file: str = "transcriptions.log"):
        """
        Initialize logger.
        
        Args:
            log_file: Path to log file
        """
        self.log_file = log_file
        self.display_file = "transcription_display.txt"
        
        # Create log file if it doesn't exist
        if not os.path.exists(log_file):
            with open(log_file, 'w') as f:
                start_time = datetime.datetime.now()
                f.write(f"=== Transcription Log Started at {start_time} ===\n")
        
        # Create/clear the live display file
        with open(self.display_file, 'w') as f:
            f.write("🎤 LIVE TRANSCRIPTION DISPLAY 🎤\n")
            f.write("=" * 50 + "\n")
            f.write("Waiting for transcriptions...\n\n")
    
    def log_transcription(
        self, text: Optional[str], source: str = "microphone"
    ):
        """
        Log transcription result to both console and file.
        
        Args:
            text: Transcribed text (None if transcription failed)
            source: Source of the audio (e.g., "microphone", "file")
        """
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        if text:
            # Successful transcription - enhanced console output
            log_entry = f"[{timestamp}] [{source}] {text}"
            
            # Highly visible colored console output
            header = f"{Back.GREEN}{Fore.BLACK}🎯 TRANSCRIPTION RESULT {Style.RESET_ALL}"
            print(f"\n{header}")
            
            speech_label = f"{Back.CYAN}{Fore.BLACK} 💬 SPEECH TEXT: "
            print(f"{speech_label}{Style.RESET_ALL}")
            
            print(f"{Fore.CYAN}{Style.BRIGHT}{text}{Style.RESET_ALL}")
            
            time_label = f"{Fore.YELLOW}⏰ {timestamp} | 🎤 {source}"
            print(f"{time_label}{Style.RESET_ALL}")
            
            print(f"{Fore.GREEN}{'=' * 60}{Style.RESET_ALL}")
            
            # Write to main log file (simple format)
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(f"{log_entry}\n")
            
            # Write to live display file (formatted for separate terminal)
            with open(self.display_file, 'a', encoding='utf-8') as f:
                f.write(f"\n🎯 NEW TRANSCRIPTION [{timestamp}]:\n")
                f.write(f"💬 {text}\n")
                f.write(f"🎤 Source: {source}\n")
                f.write("-" * 60 + "\n")
        else:
            # Failed transcription
            error_entry = f"[{timestamp}] [{source}] ❌ Transcription failed"
            
            # Colored failure output
            fail_label = f"{Back.RED}{Fore.WHITE}🚫 TRANSCRIPTION FAILED "
            print(f"\n{fail_label}{Style.RESET_ALL}")
            
            error_msg = "❌ No speech detected or transcription error"
            print(f"{Fore.RED}{error_msg}{Style.RESET_ALL}")
            
            time_label = f"{Fore.YELLOW}⏰ {timestamp} | 🎤 {source}"
            print(f"{time_label}{Style.RESET_ALL}")
            
            print(f"{Fore.RED}{'-' * 50}{Style.RESET_ALL}")
            
            # Write to main log file
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(f"{error_entry}\n")
            
            # Write to live display file
            with open(self.display_file, 'a', encoding='utf-8') as f:
                f.write(f"\n🚫 FAILED TRANSCRIPTION [{timestamp}]:\n")
                f.write("❌ No speech detected or transcription error\n")
                f.write(f"🎤 Source: {source}\n")
                f.write("-" * 60 + "\n")
    
    def log_info(self, message: str):
        """
        Log informational message.
        
        Args:
            message: Info message to log
        """
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [INFO] {message}"
        print(f"ℹ️ {log_entry}")
        
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(f"{log_entry}\n")
    
    def log_error(self, error_message: str):
        """
        Log error message.
        
        Args:
            error_message: Error message to log
        """
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [ERROR] {error_message}"
        print(f"❌ {log_entry}")
        
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(f"{log_entry}\n")
