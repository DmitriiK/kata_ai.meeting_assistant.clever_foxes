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
    def __init__(
        self,
        log_file: str = "transcriptions.log",
        session_dir: str = None
    ):
        """
        Initialize logger.
        
        Args:
            log_file: Base name for log file (conversations only)
            session_dir: Optional session directory for saving logs
        """
        self.base_log_file = log_file
        self.session_dir = session_dir
        
        # Track interim text per source
        self.last_interim_text = {}
        
        # Generate timestamp for this application start
        start_timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H%M%S")
        
        # Determine actual log file paths
        if session_dir and os.path.exists(session_dir):
            # Use session directory (for meeting summaries, etc.)
            self.log_file = os.path.join(session_dir, log_file)
            self.system_log_file = os.path.join(
                session_dir, "system_events.log"
            )
        else:
            # Use logs folder with timestamped filenames
            logs_dir = "logs"
            os.makedirs(logs_dir, exist_ok=True)
            
            # Extract base name without extension
            base_name = os.path.splitext(log_file)[0]
            extension = os.path.splitext(log_file)[1] or ".log"
            
            # Create timestamped filenames
            timestamped_name = f"{base_name}_{start_timestamp}{extension}"
            self.log_file = os.path.join(logs_dir, timestamped_name)
            
            system_name = f"system_events_{start_timestamp}.log"
            self.system_log_file = os.path.join(logs_dir, system_name)
        
        # Create conversation log file if it doesn't exist
        if not os.path.exists(self.log_file):
            # Ensure directory exists
            log_dir = os.path.dirname(self.log_file)
            if log_dir:
                os.makedirs(log_dir, exist_ok=True)
            with open(self.log_file, 'w') as f:
                start_time = datetime.datetime.now()
                f.write(f"=== Conversation Log Started at {start_time} ===\n")
        
        # Create system events log file if it doesn't exist
        if not os.path.exists(self.system_log_file):
            sys_log_dir = os.path.dirname(self.system_log_file)
            if sys_log_dir:
                os.makedirs(sys_log_dir, exist_ok=True)
            with open(self.system_log_file, 'w') as f:
                start_time = datetime.datetime.now()
                header = f"=== System Events Log Started at {start_time} ===\n"
                f.write(header)
    
    def update_session_dir(self, session_dir: str):
        """Update the session directory for log file location."""
        self.session_dir = session_dir
        if session_dir:
            new_log_file = os.path.join(session_dir, self.base_log_file)
            new_system_log = os.path.join(session_dir, "system_events.log")
            
            if new_log_file != self.log_file:
                self.log_file = new_log_file
                self.system_log_file = new_system_log
                
                # Create new conversation log file
                if not os.path.exists(self.log_file):
                    log_dir = os.path.dirname(self.log_file)
                    if log_dir:
                        os.makedirs(log_dir, exist_ok=True)
                    with open(self.log_file, 'w') as f:
                        start_time = datetime.datetime.now()
                        header = (f"=== Conversation Log "
                                  f"Started at {start_time} ===\n")
                        f.write(header)
                
                # Create new system events log file
                if not os.path.exists(self.system_log_file):
                    sys_log_dir = os.path.dirname(self.system_log_file)
                    if sys_log_dir:
                        os.makedirs(sys_log_dir, exist_ok=True)
                    with open(self.system_log_file, 'w') as f:
                        start_time = datetime.datetime.now()
                        header = (f"=== System Events Log "
                                  f"Started at {start_time} ===\n")
                        f.write(header)
    
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
            speaker_id: Speaker identifier (e.g., "Speaker 1")
        """
        if not text:
            return
        
        # Create a unique key for this source
        key = f"{source}:{speaker_id if speaker_id else 'unknown'}"
        source_key = key
        
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
    
    def log_system_event(self, message: str):
        """
        Log system event (app starts, device detection, etc).
        Goes to system_events.log only, not to conversation log.
        
        Args:
            message: System event message
        """
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [SYSTEM] {message}"
        print(f"🔧 {log_entry}")
        
        with open(self.system_log_file, 'a', encoding='utf-8') as f:
            f.write(f"{log_entry}\n")
    
    def log_info(self, message: str):
        """
        Log informational message to conversation log.
        Use for session markers, language changes, etc.
        
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
