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
        self.last_interim_text = {}  # Track last interim per source
        
        # Create log file if it doesn't exist
        if not os.path.exists(log_file):
            with open(log_file, 'w') as f:
                start_time = datetime.datetime.now()
                f.write(f"=== Transcription Log Started at {start_time} ===\n")
    
    def log_interim_result(
        self,
        text: str,
        source: str = "microphone",
        speaker_id: Optional[str] = None
    ):
        """
        Log interim/partial transcription result (console only).
        Shows what's being recognized in real-time as user speaks.
        Displays word-by-word sequentially instead of replacing.
        
        Args:
            text: Partial transcribed text
            source: Source of the audio
            speaker_id: Speaker identifier (e.g., "Speaker 1", "Speaker 2")
        """
        if not text:
            return
        
        # Create a unique key for this source
        source_key = f"{source}:{speaker_id if speaker_id else 'unknown'}"
        
        # Get the last interim text for this source
        last_text = self.last_interim_text.get(source_key, "")
        
        # If this is the first interim for this utterance
        if not last_text:
            # Print header for new interim sequence
            speaker_info = f"[{speaker_id}]" if speaker_id else ""
            interim_label = (f"{Fore.YELLOW}⚡ [INTERIM] "
                             f"[{source}]{speaker_info}: ")
            print(f"\n{interim_label}", end="", flush=True)
        
        # Find new words by comparing with last text
        last_words = last_text.split()
        new_words = text.split()
        
        # Print only the new words that were added
        if len(new_words) > len(last_words):
            # Extract new words
            added_words = new_words[len(last_words):]
            for word in added_words:
                print(f"{Fore.YELLOW}{word}{Style.RESET_ALL} ",
                      end="", flush=True)
        elif text != last_text:
            # Text changed but not just appended - print all
            # (handles corrections)
            print(f"\n{Fore.YELLOW}↻ {text}{Style.RESET_ALL}",
                  end="", flush=True)
        
        # Update last interim text
        self.last_interim_text[source_key] = text
    
    def log_transcription(
        self,
        text: Optional[str],
        source: str = "microphone",
        speaker_id: Optional[str] = None
    ):
        """
        Log transcription result to both console and file.
        Only logs when speech is detected (silent when no speech).
        
        Args:
            text: Transcribed text (None if transcription failed)
            source: Source of the audio (e.g., "microphone", "file")
            speaker_id: Speaker identifier (e.g., "Speaker 1", "Speaker 2")
        """
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        if text:
            # Clear interim state for this source
            source_key = f"{source}:{speaker_id if speaker_id else 'unknown'}"
            if source_key in self.last_interim_text:
                del self.last_interim_text[source_key]
            
            # Format speaker info for display
            speaker_info = f"[{speaker_id}]" if speaker_id else ""
            
            # Successful transcription - enhanced console output
            log_entry = f"[{timestamp}] [{source}]{speaker_info} {text}"
            
            # Highly visible colored console output
            header = (f"{Back.GREEN}{Fore.BLACK}🎯 TRANSCRIPTION RESULT "
                      f"{Style.RESET_ALL}")
            print(f"\n{header}")
            
            # Show speaker if available
            if speaker_id:
                speaker_label = (f"{Back.MAGENTA}{Fore.WHITE} "
                                f"👤 {speaker_id} ")
                print(f"{speaker_label}{Style.RESET_ALL}")
            
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
