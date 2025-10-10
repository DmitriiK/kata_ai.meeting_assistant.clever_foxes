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
    def __init__(self, log_file: str = "transcriptions.log", session_dir: str = None):
        """
        Initialize logger.
        
        Args:
            log_file: Base name for log file
            session_dir: Optional session directory for saving logs
        """
        self.base_log_file = log_file
        self.session_dir = session_dir
        
        # Determine actual log file path
        if session_dir and os.path.exists(session_dir):
            self.log_file = os.path.join(session_dir, log_file)
        else:
            self.log_file = log_file
        
        # Create log file if it doesn't exist
        if not os.path.exists(self.log_file):
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.log_file), exist_ok=True) if os.path.dirname(self.log_file) else None
            with open(self.log_file, 'w') as f:
                start_time = datetime.datetime.now()
                f.write(f"=== Transcription Log Started at {start_time} ===\n")
    
    def update_session_dir(self, session_dir: str):
        """Update the session directory for log file location."""
        self.session_dir = session_dir
        if session_dir:
            new_log_file = os.path.join(session_dir, self.base_log_file)
            if new_log_file != self.log_file:
                self.log_file = new_log_file
                # Create new log file if it doesn't exist
                if not os.path.exists(self.log_file):
                    os.makedirs(os.path.dirname(self.log_file), exist_ok=True) if os.path.dirname(self.log_file) else None
                    with open(self.log_file, 'w') as f:
                        start_time = datetime.datetime.now()
                        f.write(f"=== Transcription Log Started at {start_time} ===\n")
    
    def log_interim_result(self, text: str, source: str = "microphone"):
        """
        Log interim/partial transcription result (console only).
        Shows what's being recognized in real-time as user speaks.
        
        Args:
            text: Partial transcribed text
            source: Source of the audio
        """
        if text:
            # Show interim result on console only (not in log file)
            interim_label = f"{Fore.YELLOW}⚡ [INTERIM] [{source}]"
            print(f"\r{interim_label} {text}{Style.RESET_ALL}", end="")
    
    def log_transcription(
        self, text: Optional[str], source: str = "microphone"
    ):
        """
        Log transcription result to both console and file.
        Only logs when speech is detected (silent when no speech).
        
        Args:
            text: Transcribed text (None if transcription failed)
            source: Source of the audio (e.g., "microphone", "file")
        """
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        if text:
            # Clear any interim result line
            print("\r" + " " * 100 + "\r", end="")
            
            # Successful transcription - enhanced console output
            log_entry = f"[{timestamp}] [{source}] {text}"
            
            # Highly visible colored console output
            header = (f"{Back.GREEN}{Fore.BLACK}🎯 TRANSCRIPTION RESULT "
                      f"{Style.RESET_ALL}")
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
        # If no text, do nothing (silent mode)
    
    def log_language_change(self, language: str, source: str = ""):
        """
        Log language detection/change.
        
        Args:
            language: Detected language (e.g., "en-US", "ru-RU", "tr-TR")
            source: Audio source label
        """
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        lang_map = {
            "en-US": "🇺🇸 English",
            "ru-RU": "🇷🇺 Russian",
            "tr-TR": "🇹🇷 Turkish"
        }
        lang_name = lang_map.get(language, language)
        
        log_entry = f"[{timestamp}] [LANG] {lang_name}"
        if source:
            log_entry += f" [{source}]"
        
        # Write to log file
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(f"{log_entry}\n")
    
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
