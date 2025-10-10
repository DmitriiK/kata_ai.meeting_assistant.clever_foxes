#!/usr/bin/env python3
"""
GUI Application for Meeting Transcription
Cross-platform GUI using PyQt6 for Mac and Windows

Features:
- Start/Stop transcription button
- Separate windows for interim and final results
- Real-time updates with speaker identification
- Auto-scroll to latest results
"""
import sys
import threading
import datetime
import pyaudio
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTextEdit, QPushButton, QLabel, QGroupBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QObject
from PyQt6.QtGui import QFont, QTextCursor, QColor
from azure_speech_service import AzureSpeechTranscriber
from transcription_logger import TranscriptionLogger
from config import AudioSettings, LogSettings
from audio_recorder import AudioRecorder


class SignalEmitter(QObject):
    """Signal emitter for thread-safe GUI updates."""
    append_interim = pyqtSignal(str, str, str)
    append_final = pyqtSignal(str, str, str, str)
    update_status = pyqtSignal(bool)


class TranscriptionGUI(QMainWindow):
    def __init__(self):
        """Initialize the GUI application."""
        super().__init__()
        
        # State variables
        self.is_running = False
        self.audio = None
        self.mic_transcriber = None
        self.sys_transcriber = None
        self.mic_stream = None
        self.sys_stream = None
        self.mic_recognizer = None
        self.sys_recognizer = None
        self.mic_audio_stream = None
        self.sys_audio_stream = None
        
        # Audio settings
        self.sample_rate = AudioSettings.SAMPLE_RATE
        self.chunk_size = AudioSettings.CHUNK_SIZE
        
        # Logger
        self.logger = TranscriptionLogger(log_file=LogSettings.LOG_FILE)
        
        # Signal emitter for thread-safe updates
        self.signals = SignalEmitter()
        self.signals.append_interim.connect(self.append_interim)
        self.signals.append_final.connect(self.append_final)
        self.signals.update_status.connect(self.update_status)
        
        # Setup GUI
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the user interface."""
        self.setWindowTitle("🎤 Meeting Transcription Assistant")
        self.setGeometry(100, 100, 1200, 800)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)
        
        # Header with controls
        header_layout = QHBoxLayout()
        
        # Title
        title_label = QLabel("🎤 Meeting Transcription Assistant")
        title_font = QFont("Arial", 16, QFont.Weight.Bold)
        title_label.setFont(title_font)
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Status indicator
        self.status_label = QLabel("● Stopped")
        self.status_label.setStyleSheet("color: red; font-size: 12pt;")
        header_layout.addWidget(self.status_label)
        
        # Start/Stop button
        self.start_stop_btn = QPushButton("▶ Start Transcription")
        self.start_stop_btn.clicked.connect(self.toggle_transcription)
        self.start_stop_btn.setMinimumWidth(180)
        header_layout.addWidget(self.start_stop_btn)
        
        # Clear buttons
        clear_interim_btn = QPushButton("Clear Interim")
        clear_interim_btn.clicked.connect(self.clear_interim)
        clear_interim_btn.setMinimumWidth(120)
        header_layout.addWidget(clear_interim_btn)
        
        clear_final_btn = QPushButton("Clear Final")
        clear_final_btn.clicked.connect(self.clear_final)
        clear_final_btn.setMinimumWidth(120)
        header_layout.addWidget(clear_final_btn)
        
        main_layout.addLayout(header_layout)
        
        # Interim Results Group (single line)
        interim_group = QGroupBox("⚡ Interim Results (Live Transcription)")
        interim_layout = QVBoxLayout()
        
        self.interim_text = QTextEdit()
        self.interim_text.setReadOnly(True)
        self.interim_text.setFont(QFont("Courier", 10))
        self.interim_text.setStyleSheet(
            "background-color: #FFFACD; color: #000000;"
        )
        # Set fixed height for single row
        self.interim_text.setMaximumHeight(50)
        interim_layout.addWidget(self.interim_text)
        
        interim_group.setLayout(interim_layout)
        main_layout.addWidget(interim_group)
        
        # Final Results Group
        final_group = QGroupBox(
            "🎯 Final Results (Confirmed Transcriptions)"
        )
        final_layout = QVBoxLayout()
        
        self.final_text = QTextEdit()
        self.final_text.setReadOnly(True)
        self.final_text.setFont(QFont("Courier", 10))
        self.final_text.setStyleSheet(
            "background-color: #E0FFE0; color: #000000;"
        )
        final_layout.addWidget(self.final_text)
        
        final_group.setLayout(final_layout)
        main_layout.addWidget(final_group)
    
    def append_interim(self, text: str, source: str, speaker_id: str):
        """Append text to interim results window."""
        self.interim_text.clear()
        
        if speaker_id:
            self.interim_text.insertHtml(
                f'<span style="color: #0066CC; font-weight: bold;">'
                f'[{speaker_id}]</span> '
            )
        if source:
            self.interim_text.insertHtml(
                f'<span style="color: #666666;">[{source}]</span> '
            )
        
        self.interim_text.insertPlainText(text)
        self.interim_text.moveCursor(QTextCursor.MoveOperation.End)
    
    def append_final(
        self, text: str, source: str, speaker_id: str, timestamp: str
    ):
        """Append text to final results window."""
        # Add separator
        self.final_text.insertHtml(
            '<span style="color: #999999;">'
            + '─' * 80 + '</span><br>'
        )
        
        # Add timestamp
        if timestamp:
            self.final_text.insertHtml(
                f'<span style="color: #999999;">⏰ {timestamp}</span><br>'
            )
        
        # Add speaker
        if speaker_id:
            self.final_text.insertHtml(
                f'<span style="color: #CC0066; font-weight: bold;">'
                f'👤 {speaker_id}</span> '
            )
        
        # Add source
        if source:
            self.final_text.insertHtml(
                f'<span style="color: #666666;">| {source}</span><br>'
            )
        
        # Add text
        self.final_text.insertHtml(
            f'<span style="color: #000000;">💬 {text}</span><br><br>'
        )
        
        # Auto-scroll to bottom
        self.final_text.moveCursor(QTextCursor.MoveOperation.End)
    
    def clear_interim(self):
        """Clear interim results window."""
        self.interim_text.clear()
    
    def clear_final(self):
        """Clear final results window."""
        self.final_text.clear()
    
    def update_status(self, running: bool):
        """Update status indicator."""
        if running:
            self.status_label.setText("● Recording")
            self.status_label.setStyleSheet(
                "color: green; font-size: 12pt;"
            )
            self.start_stop_btn.setText("⏸ Stop Transcription")
        else:
            self.status_label.setText("● Stopped")
            self.status_label.setStyleSheet("color: red; font-size: 12pt;")
            self.start_stop_btn.setText("▶ Start Transcription")
    
    def result_callback(self, text: str, source: str, speaker_id: str = None):
        """Callback for final transcription results."""
        if text and text.strip():
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Emit signal for thread-safe GUI update
            self.signals.append_final.emit(text, source, speaker_id, timestamp)
            
            # Also log to file
            self.logger.log_transcription(text, source, speaker_id)
    
    def interim_callback(
        self, text: str, source: str, speaker_id: str = None
    ):
        """Callback for interim transcription results."""
        if text and text.strip():
            # Emit signal for thread-safe GUI update
            self.signals.append_interim.emit(text, source, speaker_id)
    
    def audio_callback_mic(self, in_data, frame_count, time_info, status):
        """Callback for microphone audio stream."""
        if self.is_running and self.mic_stream:
            self.mic_stream.write(in_data)
        return (in_data, pyaudio.paContinue)
    
    def audio_callback_sys(self, in_data, frame_count, time_info, status):
        """Callback for system audio stream."""
        if self.is_running and self.sys_stream:
            self.sys_stream.write(in_data)
        return (in_data, pyaudio.paContinue)
    
    def start_transcription(self):
        """Start transcription in background thread."""
        def run():
            try:
                # Initialize PyAudio
                self.audio = pyaudio.PyAudio()
                
                # Detect audio devices
                recorder = AudioRecorder(
                    sample_rate=self.sample_rate,
                    chunk_size=self.chunk_size
                )
                devices = recorder.list_audio_devices()
                
                # Find microphone
                mic_device = None
                for device in devices:
                    if device['is_default_input'] and device['can_record']:
                        mic_device = device['index']
                        self.signals.append_final.emit(
                            f"Microphone: {device['name']}",
                            "System",
                            "",
                            ""
                        )
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
                        self.signals.append_final.emit(
                            f"System Audio: {device['name']}",
                            "System",
                            "",
                            ""
                        )
                        break
                
                # Initialize transcribers
                if mic_device is not None:
                    self.mic_transcriber = AzureSpeechTranscriber(
                        logger=self.logger
                    )
                    self.mic_stream, self.mic_recognizer = (
                        self.mic_transcriber.start_continuous_recognition(
                            source_label="🎤 MIC",
                            result_callback=self.result_callback,
                            interim_callback=self.interim_callback
                        )
                    )
                    
                    # Start audio stream
                    self.mic_audio_stream = self.audio.open(
                        format=pyaudio.paInt16,
                        channels=1,
                        rate=self.sample_rate,
                        input=True,
                        input_device_index=mic_device,
                        frames_per_buffer=self.chunk_size,
                        stream_callback=self.audio_callback_mic
                    )
                    self.mic_audio_stream.start_stream()
                
                if sys_device is not None:
                    self.sys_transcriber = AzureSpeechTranscriber(
                        logger=self.logger
                    )
                    self.sys_stream, self.sys_recognizer = (
                        self.sys_transcriber.start_continuous_recognition(
                            source_label="🔊 SYSTEM",
                            result_callback=self.result_callback,
                            interim_callback=self.interim_callback
                        )
                    )
                    
                    # Start audio stream
                    self.sys_audio_stream = self.audio.open(
                        format=pyaudio.paInt16,
                        channels=1,
                        rate=self.sample_rate,
                        input=True,
                        input_device_index=sys_device,
                        frames_per_buffer=self.chunk_size,
                        stream_callback=self.audio_callback_sys
                    )
                    self.sys_audio_stream.start_stream()
                
                self.signals.append_final.emit(
                    "Transcription started with speaker diarization",
                    "System",
                    "",
                    ""
                )
                
            except Exception as e:
                self.signals.append_final.emit(
                    f"Error: {e}",
                    "Error",
                    "",
                    ""
                )
                self.is_running = False
                self.signals.update_status.emit(False)
        
        # Start in background thread
        thread = threading.Thread(target=run, daemon=True)
        thread.start()
    
    def stop_transcription(self):
        """Stop transcription."""
        self.is_running = False
        
        # Stop audio streams
        if self.mic_audio_stream:
            self.mic_audio_stream.stop_stream()
            self.mic_audio_stream.close()
            self.mic_audio_stream = None
        
        if self.sys_audio_stream:
            self.sys_audio_stream.stop_stream()
            self.sys_audio_stream.close()
            self.sys_audio_stream = None
        
        # Stop transcribers
        if self.mic_transcriber and self.mic_recognizer:
            self.mic_transcriber.stop_continuous_recognition(
                self.mic_recognizer
            )
            self.mic_transcriber = None
            self.mic_recognizer = None
        
        if self.sys_transcriber and self.sys_recognizer:
            self.sys_transcriber.stop_continuous_recognition(
                self.sys_recognizer
            )
            self.sys_transcriber = None
            self.sys_recognizer = None
        
        # Terminate PyAudio
        if self.audio:
            self.audio.terminate()
            self.audio = None
        
        self.signals.append_final.emit(
            "Transcription stopped", "System", "", ""
        )
    
    def toggle_transcription(self):
        """Toggle transcription on/off."""
        if not self.is_running:
            self.is_running = True
            self.signals.update_status.emit(True)
            self.start_transcription()
        else:
            self.signals.update_status.emit(False)
            self.stop_transcription()
    
    def closeEvent(self, event):
        """Handle window closing."""
        if self.is_running:
            self.stop_transcription()
        event.accept()


def main():
    """Main entry point."""
    app = QApplication(sys.argv)
    window = TranscriptionGUI()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
