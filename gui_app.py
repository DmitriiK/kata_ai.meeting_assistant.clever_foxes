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
import os
import threading
import datetime
import time
import pyaudio
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTextEdit, QPushButton, QLabel, QGroupBox, QCheckBox, QComboBox,
    QMessageBox, QTabWidget, QScrollArea, QFrame, QSplitter, QListWidget,
    QListWidgetItem, QDateEdit
)
from PyQt6.QtCore import Qt, pyqtSignal, QObject, QTimer, QDate
from PyQt6.QtGui import QFont, QTextCursor, QColor, QIcon, QMovie, QPixmap
from azure_speech_service import AzureSpeechTranscriber
from transcription_logger import TranscriptionLogger
from config import AudioSettings, LogSettings, SessionSettings
from audio_recorder import AudioRecorder
from translation_tts_controller import TranslationTTSController
from meeting_assistant_service import MeetingAssistantService
import llm_service
import prompts
from queue import Queue, Empty
from audio_mixer import start_mixer, stop_mixer
from pathlib import Path
import json


class SignalEmitter(QObject):
    """Signal emitter for thread-safe GUI updates."""
    append_interim = pyqtSignal(str, str, str)
    append_final = pyqtSignal(str, str, str, str)
    append_translation = pyqtSignal(str, str, str, str)
    update_status = pyqtSignal(bool)
    update_speak_button = pyqtSignal(str, bool)  # text, enabled
    show_warning = pyqtSignal(str)  # error message
    clear_warning = pyqtSignal()
    # AI Insights signals
    append_insight = pyqtSignal(str, str)  # insight_type, content
    update_insights_display = pyqtSignal(dict)  # insights dict
    update_session_list = pyqtSignal()


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
        
        # Session timer and auto-pause
        self.session_start_time = None
        self.session_duration = 0
        self.session_folder = None
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_timer)
        self.last_speech_time = None
        self.auto_pause_timer = QTimer()
        self.auto_pause_timer.timeout.connect(self.check_auto_pause)
        
        # Feature 1: Text Translation
        self.text_translation_enabled = False
        self.translation_queue = Queue()
        self.translation_worker_running = False
        
        # Feature 2: TTS to Microphone
        self.tts_to_mic_enabled = False
        self.tts_enabled_at = 0.0  # Timestamp when TTS was enabled
        self.seen_before_tts = set()  # Text hashes seen before TTS enabled
        self.tts_controller = TranslationTTSController()
        self.tts_controller.on_state_change = self.on_tts_state_change
        
        # Duplicate detection (bidirectional: MIC↔SYSTEM)
        self.recent_mic_transcriptions = []  # [(text, timestamp), ...]
        self.recent_sys_transcriptions = []  # [(text, timestamp), ...]
        self.duplicate_window_seconds = 3.0  # Time window for duplicates
        
        # Translation tracking (to identify SYSTEM texts as translations)
        self.queued_for_translation = []  # [(text, timestamp), ...]
        self.translation_window_seconds = 30.0  # Max time
        
        # Audio Mixer (for routing mic + TTS to virtual device)
        self.mixer_started = False
        print("🔄 Starting audio mixer...")
        if start_mixer():
            self.mixer_started = True
            print("✅ Audio mixer started successfully")
        else:
            print("⚠️ Audio mixer failed to start")
            print("   TTS to Mic feature may not work")
        
        # Error tracking
        self.last_translation_error = None
        self.translation_error_count = 0
        
        # Audio settings
        self.sample_rate = AudioSettings.SAMPLE_RATE
        self.chunk_size = AudioSettings.CHUNK_SIZE
        
        # Logger
        self.logger = TranscriptionLogger(log_file=LogSettings.LOG_FILE)
        
        # Meeting Assistant Service for AI insights
        self.meeting_assistant = MeetingAssistantService()
        self.session_started = False
        
        # Insights viewing mode
        self.viewing_live = True
        self.current_viewed_session = None
        
        # Date filter state
        self.date_filter_enabled = False
        self.filtered_date = None
        
        # Signal emitter for thread-safe updates
        self.signals = SignalEmitter()
        self.signals.append_interim.connect(self.append_interim)
        self.signals.append_final.connect(self.append_final)
        self.signals.append_translation.connect(self.append_translation)
        self.signals.update_status.connect(self.update_status)
        self.signals.update_speak_button.connect(self.update_speak_button)
        self.signals.show_warning.connect(self.show_warning)
        self.signals.clear_warning.connect(self.clear_warning)
        self.signals.append_insight.connect(self.append_insight_to_display)
        self.signals.update_insights_display.connect(self.update_insights_display)
        self.signals.update_session_list.connect(self.refresh_session_list)
        
        # Setup GUI
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the user interface."""
        self.setWindowTitle("🎤 Meeting Transcription Assistant")
        self.setGeometry(100, 100, 1400, 900)
        
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
        
        # Warning indicator for translation errors (initialized here, added to footer later)
        self.warning_label = QLabel("")
        self.warning_label.setStyleSheet(
            "color: orange; font-size: 14pt; font-weight: bold;"
        )
        self.warning_label.setVisible(False)
        
        # Timer (initialized here, added to footer later)
        self.timer_label = QLabel("⏱️ 00:00:00")
        self.timer_label.setStyleSheet("font-size: 12pt;")
        
        header_layout.addStretch()
        
        # Control buttons in vertical layout (left side)
        control_layout = QVBoxLayout()
        
        # Start/Stop button
        self.start_stop_btn = QPushButton("▶ Start Transcription")
        self.start_stop_btn.clicked.connect(self.toggle_transcription)
        self.start_stop_btn.setMinimumWidth(180)
        control_layout.addWidget(self.start_stop_btn)
        
        # Clear Final button
        clear_final_btn = QPushButton("Clear Final")
        clear_final_btn.clicked.connect(self.clear_final)
        clear_final_btn.setMinimumWidth(180)
        control_layout.addWidget(clear_final_btn)
        
        header_layout.addLayout(control_layout)
        
        # Fox icon/animation (top right corner)
        self.fox_label = QLabel()
        self.fox_label.setFixedSize(60, 60)
        self.fox_label.setScaledContents(True)
        
        # Load static fox image
        self.static_fox = QPixmap("static/fox.png")
        self.fox_label.setPixmap(self.static_fox)
        
        # Load animated fox gif
        self.animated_fox = QMovie("static/dancing_fox.gif")
        self.animated_fox.setScaledSize(self.fox_label.size())
        
        header_layout.addWidget(self.fox_label)
        
        main_layout.addLayout(header_layout)
        
        # ===== FEATURE GROUPS LAYOUT =====
        features_layout = QHBoxLayout()
        
        # GROUP 1: Speech to Text Translation
        speech_to_text_group = QGroupBox("📝 Speech to Text Translation")
        speech_to_text_layout = QVBoxLayout()
        
        self.translate_text_checkbox = QCheckBox("Enable Translation")
        self.translate_text_checkbox.stateChanged.connect(
            self.toggle_text_translation
        )
        speech_to_text_layout.addWidget(self.translate_text_checkbox)
        
        lang_layout = QHBoxLayout()
        lang_layout.addWidget(QLabel("Target Language:"))
        self.text_translation_language = QComboBox()
        self.text_translation_language.addItems([
            "English", "Russian", "Turkish"
        ])
        lang_layout.addWidget(self.text_translation_language)
        speech_to_text_layout.addLayout(lang_layout)
        
        speech_to_text_group.setLayout(speech_to_text_layout)
        features_layout.addWidget(speech_to_text_group)
        
        # GROUP 2: Text to Speech Translation
        text_to_speech_group = QGroupBox("🔊 Text to Speech Translation")
        text_to_speech_layout = QVBoxLayout()
        
        self.tts_mic_checkbox = QCheckBox("Enable TTS to Mic")
        self.tts_mic_checkbox.stateChanged.connect(
            self.toggle_tts_to_mic
        )
        text_to_speech_layout.addWidget(self.tts_mic_checkbox)
        
        tts_lang_layout = QHBoxLayout()
        tts_lang_layout.addWidget(QLabel("TTS Language:"))
        self.tts_language_selector = QComboBox()
        self.tts_language_selector.addItems([
            "English", "Russian", "Turkish"
        ])
        self.tts_language_selector.currentTextChanged.connect(
            self.on_tts_language_changed
        )
        tts_lang_layout.addWidget(self.tts_language_selector)
        text_to_speech_layout.addLayout(tts_lang_layout)
        
        self.speak_btn = QPushButton("Speak to Mic")
        self.speak_btn.setEnabled(False)
        self.speak_btn.setMinimumWidth(150)
        self.speak_btn.clicked.connect(self.toggle_speak_translation)
        text_to_speech_layout.addWidget(self.speak_btn)
        
        text_to_speech_group.setLayout(text_to_speech_layout)
        features_layout.addWidget(text_to_speech_group)
        
        main_layout.addLayout(features_layout)
        
        # Create tab widget for main content
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        # ===== TAB 1: TRANSCRIPTION =====
        transcription_tab = QWidget()
        transcription_layout = QVBoxLayout()
        transcription_tab.setLayout(transcription_layout)
        
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
        transcription_layout.addWidget(interim_group)
        
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
        transcription_layout.addWidget(final_group)
        
        # Translation Results Group
        self.translation_group = QGroupBox("🌍 Translation Results")
        translation_result_layout = QVBoxLayout()
        
        self.translation_text = QTextEdit()
        self.translation_text.setReadOnly(True)
        self.translation_text.setFont(QFont("Courier", 10))
        self.translation_text.setStyleSheet(
            "background-color: #E0F0FF; color: #000000;"
        )
        translation_result_layout.addWidget(self.translation_text)
        
        self.translation_group.setLayout(translation_result_layout)
        transcription_layout.addWidget(self.translation_group)
        self.translation_group.hide()  # Hidden by default
        
        # Add transcription tab to tab widget
        self.tab_widget.addTab(transcription_tab, "📝 Transcription")
        
        # ===== TAB 2: AI INSIGHTS =====
        self.setup_insights_tab()
        
        # Connect tab change event to auto-refresh sessions
        self.tab_widget.currentChanged.connect(self.on_tab_changed)
        
        # Footer layout with warning indicator and timer
        footer_layout = QHBoxLayout()
        footer_layout.addWidget(self.warning_label)
        footer_layout.addStretch()
        footer_layout.addWidget(self.timer_label)
        main_layout.addLayout(footer_layout)
        
        # Set window icon (for both window and dock/taskbar)
        try:
            icon = QIcon("static/fox.png")
            self.setWindowIcon(icon)
            # Also set on application for macOS dock icon
            QApplication.instance().setWindowIcon(icon)
        except Exception as e:
            print(f"Could not load icon: {e}")
    
    def on_tab_changed(self, index):
        """Handle tab change - refresh session list when switching to AI Insights tab."""
        # Tab 1 is AI Insights (0 = Transcription, 1 = AI Insights)
        if index == 1:  # AI Insights tab
            self.refresh_session_list()
    
    def setup_insights_tab(self):
        """Setup the AI Insights tab with session browser and insights sections."""
        insights_tab = QWidget()
        insights_main_layout = QHBoxLayout()  # Changed to horizontal for side-by-side
        insights_tab.setLayout(insights_main_layout)
        
        # ===== LEFT PANEL: Session Browser =====
        left_panel = QWidget()
        left_panel_layout = QVBoxLayout()
        left_panel.setLayout(left_panel_layout)
        left_panel.setMaximumWidth(350)
        
        # Live session button (always at top)
        self.live_mode_btn = QPushButton("🔴 LIVE Session")
        self.live_mode_btn.setCheckable(True)
        self.live_mode_btn.setChecked(True)
        self.live_mode_btn.clicked.connect(self.switch_to_live_mode)
        self.live_mode_btn.setMinimumHeight(50)
        self.live_mode_btn.setStyleSheet(
            """
            QPushButton {
                font-size: 14pt;
                font-weight: bold;
                border: 2px solid #4CAF50;
                border-radius: 5px;
                padding: 10px;
            }
            QPushButton:checked {
                background-color: #4CAF50;
                color: white;
            }
            QPushButton:hover {
                background-color: #45a049;
                color: white;
            }
            """
        )
        left_panel_layout.addWidget(self.live_mode_btn)
        
        # Session list header
        session_list_label = QLabel("📁 Past Sessions")
        session_list_label.setStyleSheet("font-size: 12pt; font-weight: bold; margin-top: 10px;")
        left_panel_layout.addWidget(session_list_label)
        
        # Date filter controls
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Filter by date:"))
        
        self.date_filter = QDateEdit()
        self.date_filter.setCalendarPopup(True)
        self.date_filter.setDate(QDate.currentDate())
        self.date_filter.setDisplayFormat("yyyy-MM-dd")
        self.date_filter.setStyleSheet("padding: 3px;")
        self.date_filter.dateChanged.connect(self.apply_date_filter)
        filter_layout.addWidget(self.date_filter)
        
        # Clear filter button
        clear_filter_btn = QPushButton("All")
        clear_filter_btn.setMaximumWidth(50)
        clear_filter_btn.clicked.connect(self.clear_date_filter)
        clear_filter_btn.setToolTip("Show all sessions")
        filter_layout.addWidget(clear_filter_btn)
        
        left_panel_layout.addLayout(filter_layout)
        
        # Filter status label
        self.filter_status_label = QLabel("")
        self.filter_status_label.setStyleSheet("color: #666; font-size: 9pt; font-style: italic;")
        left_panel_layout.addWidget(self.filter_status_label)
        
        # Session list widget
        self.session_list = QListWidget()
        self.session_list.setStyleSheet(
            """
            QListWidget {
                border: 1px solid #ccc;
                border-radius: 5px;
                background-color: white;
                font-size: 10pt;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #e0e0e0;
                color: #333333;
            }
            QListWidget::item:selected {
                background-color: #1976D2;
                color: white;
                font-weight: bold;
            }
            QListWidget::item:hover {
                background-color: #e3f2fd;
                color: #000000;
            }
            """
        )
        self.session_list.itemClicked.connect(self.on_session_clicked)
        self.session_list.setMinimumHeight(300)
        left_panel_layout.addWidget(self.session_list)
        
        # Session info/stats at bottom
        self.session_stats_label = QLabel("Select a session to view insights")
        self.session_stats_label.setStyleSheet(
            "padding: 10px; background-color: #f0f0f0; color: #333333; border-radius: 5px; font-size: 9pt;"
        )
        self.session_stats_label.setWordWrap(True)
        left_panel_layout.addWidget(self.session_stats_label)
        
        insights_main_layout.addWidget(left_panel)
        
        # ===== RIGHT PANEL: Insights Display =====
        right_panel = QWidget()
        right_panel_layout = QVBoxLayout()
        right_panel.setLayout(right_panel_layout)
        # Create a splitter for resizable sections
        splitter = QSplitter(Qt.Orientation.Vertical)
        
        # Key Points Section
        key_points_group = QGroupBox("🔑 Key Points")
        key_points_layout = QVBoxLayout()
        self.key_points_text = QTextEdit()
        self.key_points_text.setReadOnly(True)
        self.key_points_text.setFont(QFont("Arial", 11))
        self.key_points_text.setStyleSheet(
            "background-color: #E8F5E9; color: #1B5E20; padding: 10px; font-weight: 500;"
        )
        self.key_points_text.setPlaceholderText("Key points will appear here as the AI identifies them...")
        key_points_layout.addWidget(self.key_points_text)
        key_points_group.setLayout(key_points_layout)
        splitter.addWidget(key_points_group)
        
        # Decisions Section
        decisions_group = QGroupBox("✅ Decisions")
        decisions_layout = QVBoxLayout()
        self.decisions_text = QTextEdit()
        self.decisions_text.setReadOnly(True)
        self.decisions_text.setFont(QFont("Arial", 11))
        self.decisions_text.setStyleSheet(
            "background-color: #FFF3E0; color: #BF360C; padding: 10px; font-weight: 500;"
        )
        self.decisions_text.setPlaceholderText("Decisions made during the meeting will appear here...")
        decisions_layout.addWidget(self.decisions_text)
        decisions_group.setLayout(decisions_layout)
        splitter.addWidget(decisions_group)
        
        # Action Items Section
        action_items_group = QGroupBox("📋 Action Items")
        action_items_layout = QVBoxLayout()
        self.action_items_text = QTextEdit()
        self.action_items_text.setReadOnly(True)
        self.action_items_text.setFont(QFont("Arial", 11))
        self.action_items_text.setStyleSheet(
            "background-color: #E3F2FD; color: #01579B; padding: 10px; font-weight: 500;"
        )
        self.action_items_text.setPlaceholderText("Action items and tasks will appear here...")
        action_items_layout.addWidget(self.action_items_text)
        action_items_group.setLayout(action_items_layout)
        splitter.addWidget(action_items_group)
        
        # Follow-up Questions Section
        questions_group = QGroupBox("❓ Follow-up Questions")
        questions_layout = QVBoxLayout()
        self.questions_text = QTextEdit()
        self.questions_text.setReadOnly(True)
        self.questions_text.setFont(QFont("Arial", 11))
        self.questions_text.setStyleSheet(
            "background-color: #F3E5F5; color: #4A148C; padding: 10px; font-weight: 500;"
        )
        self.questions_text.setPlaceholderText("AI-suggested follow-up questions will appear here...")
        questions_layout.addWidget(self.questions_text)
        questions_group.setLayout(questions_layout)
        splitter.addWidget(questions_group)
        
        right_panel_layout.addWidget(splitter)
        insights_main_layout.addWidget(right_panel)
        
        # Add insights tab to tab widget
        self.tab_widget.addTab(insights_tab, "🤖 AI Insights")
        
        # Populate session list on startup
        self.refresh_session_list()
    
    def switch_to_live_mode(self):
        """Switch to viewing live session insights."""
        self.viewing_live = True
        self.live_mode_btn.setChecked(True)
        # Clear list selection
        self.session_list.clearSelection()
        self.session_stats_label.setText("📊 Viewing LIVE session")
        self.load_live_insights()
    
    def on_session_clicked(self, item):
        """Handle session list item click."""
        # Get session folder from item data
        session_folder = item.data(Qt.ItemDataRole.UserRole)
        
        if not session_folder:
            return
        
        # Switch to browsing mode
        self.viewing_live = False
        self.live_mode_btn.setChecked(False)
        self.current_viewed_session = session_folder
        
        # Load insights from session folder
        self.load_session_insights(session_folder)
        
        # Update stats label
        self.update_session_stats(session_folder)
    
    def apply_date_filter(self):
        """Apply date filter to session list."""
        self.date_filter_enabled = True
        self.filtered_date = self.date_filter.date().toPyDate()
        self.refresh_session_list()
        
        # Update filter status
        date_str = self.filtered_date.strftime("%Y-%m-%d")
        self.filter_status_label.setText(f"Showing sessions from {date_str}")
    
    def clear_date_filter(self):
        """Clear date filter and show all sessions."""
        self.date_filter_enabled = False
        self.filtered_date = None
        self.filter_status_label.setText("")
        self.refresh_session_list()
    
    def refresh_session_list(self):
        """Refresh the list of available sessions."""
        self.session_list.clear()
        
        sessions_dir = Path("sessions")
        if not sessions_dir.exists():
            item = QListWidgetItem("No sessions directory found")
            item.setForeground(QColor("#666666"))
            self.session_list.addItem(item)
            return
        
        # Get all session folders
        session_folders = [d for d in sessions_dir.iterdir() if d.is_dir() and d.name.startswith("session_")]
        
        if not session_folders:
            item = QListWidgetItem("No past sessions yet\nStart a transcription to create one!")
            item.setForeground(QColor("#666666"))
            self.session_list.addItem(item)
            return
        
        # Sort by modification time (most recent first)
        session_folders.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        
        # Add to list
        items_added = 0
        for session_folder in session_folders:
            folder_name = session_folder.name
            if len(folder_name) == 23:  # session_YYYYMMDD_HHMMSS = 23 chars
                timestamp_str = folder_name[8:]  # Remove "session_"
                try:
                    # Parse timestamp
                    dt = datetime.datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
                    
                    # Apply date filter if enabled
                    if self.date_filter_enabled and self.filtered_date:
                        session_date = dt.date()
                        if session_date != self.filtered_date:
                            continue  # Skip this session
                    
                    # Format display with date and time on one line - simplified for better readability
                    display_name = dt.strftime("%Y-%m-%d %H:%M:%S")
                    
                    # Check if session has summary file
                    has_summary = (session_folder / f"meeting_summary_{timestamp_str}.json").exists()
                    if has_summary:
                        display_name += " ✓"
                    
                    # Create list item
                    item = QListWidgetItem(display_name)
                    item.setData(Qt.ItemDataRole.UserRole, folder_name)  # Store folder name
                    item.setToolTip(f"Session: {folder_name}\nClick to view insights")
                    
                    self.session_list.addItem(item)
                    items_added += 1
                except Exception as e:
                    # If parsing fails, just use folder name
                    print(f"⚠️ Error parsing session {folder_name}: {e}")
                    item = QListWidgetItem(folder_name)
                    item.setData(Qt.ItemDataRole.UserRole, folder_name)
                    self.session_list.addItem(item)
                    items_added += 1
        
        if items_added == 0 and self.date_filter_enabled:
            item = QListWidgetItem(f"No sessions found for {self.filtered_date.strftime('%Y-%m-%d')}")
            item.setForeground(QColor("#666666"))
            self.session_list.addItem(item)
        
        print(f"✅ Loaded {items_added} past sessions")
    
    def update_session_stats(self, session_folder):
        """Update the session stats label with information about the selected session."""
        session_path = Path("sessions") / session_folder
        
        if not session_path.exists():
            self.session_stats_label.setText("Session not found")
            return
        
        # Try to load summary JSON for stats
        timestamp_str = session_folder[8:]  # Remove "session_"
        summary_file = session_path / f"meeting_summary_{timestamp_str}.json"
        
        if summary_file.exists():
            try:
                with open(summary_file, 'r', encoding='utf-8') as f:
                    summary = json.load(f)
                
                stats = summary.get('statistics', {})
                duration = summary.get('duration_minutes', 0)
                
                stats_text = f"""📊 <b>{session_folder}</b><br>
⏱️ Duration: {duration} minutes<br>
🔑 Key Points: {stats.get('key_points_identified', 0)}<br>
✅ Decisions: {stats.get('decisions_recorded', 0)}<br>
📋 Action Items: {stats.get('action_items_captured', 0)}<br>
❓ Questions: {stats.get('questions_generated', 0)}"""
                
                self.session_stats_label.setText(stats_text)
            except Exception as e:
                self.session_stats_label.setText(f"Viewing: {session_folder}")
        else:
            self.session_stats_label.setText(f"Viewing: {session_folder}\n(No summary available)")
    
    def load_live_insights(self):
        """Load insights from current live session."""
        # Clear all displays
        self.key_points_text.clear()
        self.decisions_text.clear()
        self.action_items_text.clear()
        self.questions_text.clear()
        
        if not self.meeting_assistant.session_active:
            self.key_points_text.setPlaceholderText("No active session. Start transcription to begin.")
            self.decisions_text.setPlaceholderText("No active session.")
            self.action_items_text.setPlaceholderText("No active session.")
            self.questions_text.setPlaceholderText("No active session.")
            return
        
        # Display current insights from meeting assistant
        if self.meeting_assistant.key_points:
            for point in self.meeting_assistant.key_points:
                self.key_points_text.append(f"• {point}\n")
        
        if self.meeting_assistant.decisions:
            for decision in self.meeting_assistant.decisions:
                self.decisions_text.append(f"• {decision}\n")
        
        if self.meeting_assistant.action_items:
            for item in self.meeting_assistant.action_items:
                self.action_items_text.append(f"• {item}\n")
        
        if self.meeting_assistant.suggested_questions:
            for i, question in enumerate(self.meeting_assistant.suggested_questions, 1):
                self.questions_text.append(f"{i}. {question}\n")
    
    def clean_insight_content(self, content: str) -> str:
        """Remove timestamp headers from insight content."""
        lines = content.split('\n')
        cleaned_lines = []
        
        for line in lines:
            # Skip timestamp headers like "=== 2025-10-13 07:10:18 ==="
            if line.strip().startswith('===') and line.strip().endswith('==='):
                continue
            cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines).strip()
    
    def load_session_insights(self, session_folder):
        """Load insights from a past session folder."""
        session_path = Path("sessions") / session_folder
        
        if not session_path.exists():
            return
        
        # Clear all displays
        self.key_points_text.clear()
        self.decisions_text.clear()
        self.action_items_text.clear()
        self.questions_text.clear()
        
        # Load key points
        key_points_file = session_path / "key-points.txt"
        if key_points_file.exists():
            with open(key_points_file, 'r', encoding='utf-8') as f:
                content = self.clean_insight_content(f.read())
                self.key_points_text.setPlainText(content if content else "No key points recorded for this session.")
        else:
            self.key_points_text.setPlainText("No key points recorded for this session.")
        
        # Load decisions
        decisions_file = session_path / "decisions.txt"
        if decisions_file.exists():
            with open(decisions_file, 'r', encoding='utf-8') as f:
                content = self.clean_insight_content(f.read())
                self.decisions_text.setPlainText(content if content else "No decisions recorded for this session.")
        else:
            self.decisions_text.setPlainText("No decisions recorded for this session.")
        
        # Load action items
        action_items_file = session_path / "action-items.txt"
        if action_items_file.exists():
            with open(action_items_file, 'r', encoding='utf-8') as f:
                content = self.clean_insight_content(f.read())
                self.action_items_text.setPlainText(content if content else "No action items recorded for this session.")
        else:
            self.action_items_text.setPlainText("No action items recorded for this session.")
        
        # Load follow-up questions
        questions_file = session_path / "follow-up-questions.txt"
        if questions_file.exists():
            with open(questions_file, 'r', encoding='utf-8') as f:
                content = self.clean_insight_content(f.read())
                self.questions_text.setPlainText(content if content else "No follow-up questions recorded for this session.")
        else:
            self.questions_text.setPlainText("No follow-up questions recorded for this session.")
    
    def append_insight_to_display(self, insight_type: str, content: str):
        """Append a new insight to the appropriate display (thread-safe)."""
        if not self.viewing_live:
            return  # Only update when viewing live
        
        if insight_type == "key_point":
            self.key_points_text.append(f"• {content}\n")
            self.key_points_text.moveCursor(QTextCursor.MoveOperation.End)
        elif insight_type == "decision":
            self.decisions_text.append(f"• {content}\n")
            self.decisions_text.moveCursor(QTextCursor.MoveOperation.End)
        elif insight_type == "action_item":
            self.action_items_text.append(f"• {content}\n")
            self.action_items_text.moveCursor(QTextCursor.MoveOperation.End)
        elif insight_type == "question":
            # Count existing questions
            existing_text = self.questions_text.toPlainText()
            question_count = existing_text.count('\n') + (1 if existing_text.strip() else 0)
            self.questions_text.append(f"{question_count}. {content}\n")
            self.questions_text.moveCursor(QTextCursor.MoveOperation.End)
    
    def update_insights_display(self, insights: dict):
        """Update insights display with a batch of new insights (thread-safe)."""
        if not self.viewing_live:
            return  # Only update when viewing live
        
        # Add new key points
        if "key_points" in insights:
            for point in insights["key_points"]:
                self.signals.append_insight.emit("key_point", point)
        
        # Add new decisions
        if "decisions" in insights:
            for decision in insights["decisions"]:
                self.signals.append_insight.emit("decision", decision)
        
        # Add new action items
        if "action_items" in insights:
            for item in insights["action_items"]:
                self.signals.append_insight.emit("action_item", item)
        
        # Add new questions
        if "questions" in insights:
            for question in insights["questions"]:
                self.signals.append_insight.emit("question", question)
    
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
        """Append text to final results window and clear interim."""
        # Clear interim results since text is now final
        self.interim_text.clear()
        
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
    
    def toggle_text_translation(self, state):
        """Toggle text translation feature on/off."""
        self.text_translation_enabled = bool(state)
        
        if self.text_translation_enabled:
            self.translation_group.show()
        else:
            # Hide translation window if TTS is also disabled
            if not self.tts_to_mic_enabled:
                self.translation_group.hide()
    
    def toggle_tts_to_mic(self, state):
        """Toggle TTS to microphone feature on/off dynamically during session."""
        self.tts_to_mic_enabled = bool(state)
        
        if self.tts_to_mic_enabled:
            # Check if mixer is running
            if not self.mixer_started:
                QMessageBox.warning(
                    self,
                    "Audio Mixer Not Running",
                    "The audio mixer failed to start.\n\n"
                    "TTS to Mic requires the audio mixer to route both "
                    "your microphone and TTS audio to the virtual device.\n\n"
                    "Please check:\n"
                    "1. BlackHole (macOS) or VB-CABLE (Windows) is installed\n"
                    "2. Your microphone device is available\n"
                    "3. Check terminal for error messages"
                )
                self.tts_mic_checkbox.setChecked(False)
                return
            
            self.translation_group.show()
            # Initialize TTS controller with selected language
            self.tts_controller.set_language(
                self.tts_language_selector.currentText()
            )
            
            # Clear any pending translations from before TTS was enabled
            # This prevents rapid buffering/ready cycles that disable button
            queued_count = 0
            while not self.translation_queue.empty():
                try:
                    self.translation_queue.get_nowait()
                    queued_count += 1
                except Exception:
                    break
            if queued_count > 0:
                print(f"🗑️ Cleared {queued_count} pending translations")
            
            # Save all recent transcriptions as "seen before TTS"
            # Include both MIC and SYSTEM texts + items already queued
            for text, _ in self.recent_mic_transcriptions:
                text_hash = text.lower().strip().replace(" ", "")
                self.seen_before_tts.add(text_hash)
            for text, _ in self.recent_sys_transcriptions:
                text_hash = text.lower().strip().replace(" ", "")
                self.seen_before_tts.add(text_hash)
            # Also mark any texts that were queued for translation
            for text, _ in self.queued_for_translation:
                text_hash = text.lower().strip().replace(" ", "")
                self.seen_before_tts.add(text_hash)
            
            print(f"🗑️ Marked {len(self.seen_before_tts)} old texts to skip")
            
            # Start translation worker if not running
            if not self.translation_worker_running:
                self.translation_worker_running = True
                import threading
                worker_thread = threading.Thread(
                    target=self.translation_worker,
                    daemon=True
                )
                worker_thread.start()
                print("🔄 Started translation worker thread")
            
            # Mark the time when TTS was enabled
            import time
            self.tts_enabled_at = time.time()
            print("🌍 Oral translation mode enabled")
            
            # Add system message to Final Results
            timestamp = time.strftime("%H:%M:%S")
            self.signals.append_final.emit(
                "🌍 Oral translation mode ENABLED",
                "SYSTEM",
                "System",
                timestamp
            )
            
            # Button should start DISABLED - will enable after NEW speech
            self.signals.update_speak_button.emit("Speak to Mic", False)
        else:
            # Stop any ongoing TTS playback
            self.tts_controller.stop_speaking()
            # Clear any buffered translations that haven't been spoken
            self.tts_controller.clear_buffer()
            
            # Clear the translation queue
            while not self.translation_queue.empty():
                try:
                    self.translation_queue.get_nowait()
                except:
                    break
            print("🗑️ Cleared translation queue")
            
            # Clear the "seen before" set for next time TTS is enabled
            self.seen_before_tts.clear()
            print("🔇 Oral translation mode disabled")
            
            # Add system message to Final Results
            import time
            timestamp = time.strftime("%H:%M:%S")
            self.signals.append_final.emit(
                "🔇 Oral translation mode DISABLED",
                "SYSTEM",
                "System",
                timestamp
            )
            
            # Disable the speak button
            self.signals.update_speak_button.emit("Speak to Mic", False)
            
            # Hide translation window if text translation is also disabled
            if not self.text_translation_enabled:
                self.translation_group.hide()
    
    def on_tts_language_changed(self, language: str):
        """Handle TTS language selector change."""
        if self.tts_to_mic_enabled:
            self.tts_controller.set_language(language)
            print(f"🌍 TTS language changed to: {language}")
    
    def toggle_speak_translation(self):
        """Handle Speak/Stop Speaking button click."""
        if self.tts_controller.is_speaking():
            # Currently speaking - stop it
            self.tts_controller.stop_speaking()
        else:
            # Not speaking - start if ready
            if self.tts_controller.is_ready():
                self.tts_controller.speak()
            else:
                print("⚠️ No translation audio ready to speak")
    
    def on_tts_state_change(self, state: str):
        """Handle TTS controller state changes."""
        # Update button text and state based on TTS state
        # Button enabled when: transcription running AND TTS enabled AND 
        # state is ready/speaking
        if state == TranslationTTSController.STATE_IDLE:
            self.signals.update_speak_button.emit(
                "Speak to Mic", False
            )
        elif state == TranslationTTSController.STATE_BUFFERING:
            self.signals.update_speak_button.emit(
                "Generating...", False
            )
        elif state == TranslationTTSController.STATE_READY:
            # Enable if: transcription running AND TTS feature enabled
            enabled = self.is_running and self.tts_to_mic_enabled
            print(f"🔘 Button state update: is_running={self.is_running}, "
                  f"tts_enabled={self.tts_to_mic_enabled}, "
                  f"enabled={enabled}")
            self.signals.update_speak_button.emit(
                "Speak to Mic", enabled
            )
        elif state == TranslationTTSController.STATE_SPEAKING:
            # Enable if: transcription running AND TTS feature enabled
            enabled = self.is_running and self.tts_to_mic_enabled
            self.signals.update_speak_button.emit(
                "Stop Speaking", enabled
            )
    
    def update_speak_button(self, text: str, enabled: bool):
        """Update speak button (thread-safe)."""
        print(f"🎛️ Updating button: text='{text}', enabled={enabled}")
        self.speak_btn.setText(text)
        self.speak_btn.setEnabled(enabled)
        print(f"🎛️ Button updated: isEnabled={self.speak_btn.isEnabled()}")
    
    def show_warning(self, message: str):
        """Show warning icon with tooltip (thread-safe)."""
        self.last_translation_error = message
        self.translation_error_count += 1
        
        # Show warning icon with count
        self.warning_label.setText(
            f"⚠️ {self.translation_error_count}"
        )
        self.warning_label.setToolTip(
            f"Translation Errors: {self.translation_error_count}\n"
            f"Click to view details"
        )
        self.warning_label.setVisible(True)
        self.warning_label.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # Make clickable to show details
        self.warning_label.mousePressEvent = lambda e: self.show_error_details()
    
    def show_error_details(self):
        """Show error details dialog and clear warning."""
        if self.last_translation_error:
            msg_box = QMessageBox(self)
            msg_box.setIcon(QMessageBox.Icon.Warning)
            msg_box.setWindowTitle("Translation Errors")
            msg_box.setText(
                f"Translation error count: {self.translation_error_count}"
            )
            msg_box.setDetailedText(
                f"Last error:\n{self.last_translation_error}"
            )
            msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
            msg_box.exec()
            
            # Clear warning after showing details
            self.clear_warning()
    
    def clear_warning(self):
        """Clear warning indicator."""
        self.warning_label.setVisible(False)
        self.warning_label.setText("")
        self.warning_label.setToolTip("")
        self.last_translation_error = None
        self.translation_error_count = 0
    
    def translation_worker(self):
        """Background worker thread for translation."""
        while self.translation_worker_running:
            try:
                # Get item from queue (blocking with timeout)
                item = self.translation_queue.get(timeout=1.0)
                
            except Empty:
                # Queue timeout - this is normal, just continue
                continue
                
            try:
                text, source, speaker_id, timestamp = item
                
                # Determine which language to use
                # If both features enabled, use text translation language
                if self.text_translation_enabled:
                    target_lang = self.text_translation_language.currentText()
                elif self.tts_to_mic_enabled:
                    target_lang = self.tts_language_selector.currentText()
                else:
                    continue  # Neither feature enabled, skip
                
                try:
                    # Get translation prompt
                    prompt = prompts.get_translation_prompt(
                        text, target_lang
                    )
                    
                    # Call LLM for translation (this can fail!)
                    translation = llm_service.chat(prompt)
                    
                    # Emit signal to update GUI (for text translation)
                    if self.text_translation_enabled:
                        self.signals.append_translation.emit(
                            translation, source, speaker_id, timestamp
                        )
                    
                    # Add to TTS buffer if TTS to mic is enabled
                    if self.tts_to_mic_enabled and translation.strip():
                        try:
                            self.tts_controller.add_translation(translation)
                        except Exception as tts_error:
                            error_msg = (
                                f"TTS generation failed:\n{str(tts_error)}"
                            )
                            print(f"❌ {error_msg}")
                            self.signals.show_warning.emit(error_msg)
                    
                except ConnectionError as conn_err:
                    error_msg = (
                        f"Connection Error:\n"
                        f"Cannot reach translation service.\n"
                        f"Check your network/VPN connection.\n\n"
                        f"Details: {str(conn_err)}"
                    )
                    print(f"❌ {error_msg}")
                    self.signals.show_warning.emit(error_msg)
                    
                except TimeoutError as timeout_err:
                    error_msg = (
                        f"Timeout Error:\n"
                        f"Translation service not responding.\n\n"
                        f"Details: {str(timeout_err)}"
                    )
                    print(f"❌ {error_msg}")
                    self.signals.show_warning.emit(error_msg)
                    
                except Exception as translation_error:
                    error_msg = (
                        f"Translation Failed:\n"
                        f"{str(translation_error)}\n\n"
                        f"Text: {text[:50]}..."
                    )
                    print(f"❌ {error_msg}")
                    self.signals.show_warning.emit(error_msg)
                    
            except Exception as e:
                error_msg = (
                    f"Translation worker error:\n{str(e)}\n\n"
                    f"Type: {type(e).__name__}"
                )
                print(f"❌ {error_msg}")
                self.signals.show_warning.emit(error_msg)
    
    def append_translation(
        self, text: str, source: str, speaker_id: str, timestamp: str
    ):
        """Append translated text to translation results window."""
        # Format source icon based on original source
        if "MIC" in source.upper():
            source_icon = "🎤"
        else:
            source_icon = "🔊"
        
        # Format speaker ID with "(translated)" label
        if speaker_id:
            speaker_str = f"[{speaker_id} (translated)]"
        else:
            speaker_str = "[(translated)]"
        
        # Insert formatted text with HTML styling
        self.translation_text.moveCursor(QTextCursor.MoveOperation.End)
        self.translation_text.insertHtml(
            f'<span style="color: #0066CC;">'
            f'[{timestamp}] [{source_icon} {source}]{speaker_str} '
            f'</span>'
            f'<span style="color: #9932CC;">{text}</span><br>'
        )
        
        # Auto-scroll to bottom
        scrollbar = self.translation_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def update_status(self, running: bool):
        """Update status indicator (fox animation) and buttons."""
        if running:
            self.start_stop_btn.setText("⏸ Stop Transcription")
            
            # Start dancing fox animation
            self.fox_label.setMovie(self.animated_fox)
            self.animated_fox.start()
            
            # Clear any previous warnings when starting new session
            self.signals.clear_warning.emit()
            
            # Start translation worker if any feature is enabled
            if (self.text_translation_enabled or self.tts_to_mic_enabled):
                if not self.translation_worker_running:
                    self.translation_worker_running = True
                    worker_thread = threading.Thread(
                        target=self.translation_worker,
                        daemon=True
                    )
                    worker_thread.start()
            
            # Create session folder for logs
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            self.session_folder = f"sessions/session_{timestamp}"
            os.makedirs(self.session_folder, exist_ok=True)
            
            # Start meeting assistant session
            if not self.meeting_assistant.session_active:
                self.meeting_assistant.start_session()
                print("🤖 Meeting Assistant session started")
            
            # Clear insights display for new session
            if self.viewing_live:
                self.key_points_text.clear()
                self.decisions_text.clear()
                self.action_items_text.clear()
                self.questions_text.clear()
                self.key_points_text.setPlaceholderText("Key points will appear here as the AI identifies them...")
                self.decisions_text.setPlaceholderText("Decisions made during the meeting will appear here...")
                self.action_items_text.setPlaceholderText("Action items and tasks will appear here...")
                self.questions_text.setPlaceholderText("AI-suggested follow-up questions will appear here...")
            
            # Start timers
            self.session_start_time = time.time()
            self.last_speech_time = time.time()
            self.timer.start(1000)  # Update every second
            if SessionSettings.ENABLE_AUTO_PAUSE:
                self.auto_pause_timer.start(5000)  # Check every 5 seconds
        else:
            self.start_stop_btn.setText("▶ Start Transcription")
            
            # Stop dancing fox animation and show static image
            self.animated_fox.stop()
            self.fox_label.setPixmap(self.static_fox)
            
            # Stop translation worker thread
            self.translation_worker_running = False
            
            # Stop and clear TTS
            self.tts_controller.stop_speaking()
            
            # End meeting assistant session and generate summary
            if self.meeting_assistant.session_active:
                print("\n📋 Ending meeting session and generating summary...")
                summary_file = self.meeting_assistant.end_session()
                if summary_file:
                    print(f"✅ Meeting summary saved to: {summary_file}")
                self.session_started = False
                
                # Refresh session list to show new session
                self.signals.update_session_list.emit()
            
            # Stop timers
            self.timer.stop()
            self.auto_pause_timer.stop()
    
    def update_timer(self):
        """Update session duration timer."""
        if self.session_start_time:
            elapsed = int(time.time() - self.session_start_time)
            hours = elapsed // 3600
            minutes = (elapsed % 3600) // 60
            seconds = elapsed % 60
            self.timer_label.setText(
                f"⏱️ {hours:02d}:{minutes:02d}:{seconds:02d}"
            )
    
    def check_auto_pause(self):
        """Check if auto-pause should be triggered."""
        if not SessionSettings.ENABLE_AUTO_PAUSE:
            return
        
        if self.last_speech_time:
            silence_duration = time.time() - self.last_speech_time
            auto_pause_duration = SessionSettings.AUTO_PAUSE_SILENCE_DURATION
            if silence_duration >= auto_pause_duration:
                # Auto-pause triggered
                print(
                    f"\n⏸️  Auto-pause: {auto_pause_duration}s "
                    "of silence detected"
                )
                self.signals.append_final.emit(
                    f"Auto-paused after {auto_pause_duration}s of silence",
                    "System",
                    "",
                    ""
                )
                # Trigger stop
                if self.is_running:
                    self.toggle_transcription()
    
    def result_callback(self, text: str, source: str, speaker_id: str = None):
        """Callback for final transcription results."""
        print(f"🔔 result_callback called: source={source}, text={text[:20]}...")
        if text and text.strip():
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            current_time = time.time()
            
            # Update logger session directory if not already done
            if not self.session_started and self.meeting_assistant.session_active:
                session_dir = str(self.meeting_assistant.summary_manager.session_output_dir)
                self.logger.update_session_dir(session_dir)
                self.session_started = True
            
            # FIRST: Bidirectional duplicate detection
            # Normalize text for comparison
            text_normalized = text.lower().strip().replace(
                " ", ""
            ).replace(".", "").replace(",", "")
            
            is_duplicate = False
            
            # Check MIC against recent SYSTEM (SYSTEM came first)
            if "MIC" in source and self.mixer_started:
                for sys_text, sys_time in self.recent_sys_transcriptions:
                    time_diff = current_time - sys_time
                    if time_diff < self.duplicate_window_seconds:
                        sys_normalized = sys_text.lower().strip().replace(
                            " ", ""
                        ).replace(".", "").replace(",", "")
                        if text_normalized == sys_normalized:
                            is_duplicate = True
                            print(f"� Filtered MIC duplicate of SYSTEM: {text[:50]}...")
                            break
            
            # Check SYSTEM against recent MIC (MIC came first)
            if "SYSTEM" in source and self.mixer_started:
                for mic_text, mic_time in self.recent_mic_transcriptions:
                    time_diff = current_time - mic_time
                    if time_diff < self.duplicate_window_seconds:
                        mic_normalized = mic_text.lower().strip().replace(
                            " ", ""
                        ).replace(".", "").replace(",", "")
                        if text_normalized == mic_normalized:
                            is_duplicate = True
                            print(f"🔇 Filtered SYSTEM duplicate of MIC: {text[:50]}...")
                            break
            
            if is_duplicate:
                return
            
            # Track this transcription for future duplicate detection
            if "MIC" in source:
                self.recent_mic_transcriptions.append((text, current_time))
                self.recent_mic_transcriptions = [
                    (t, ts) for t, ts in self.recent_mic_transcriptions
                    if current_time - ts < 10.0
                ]
                print(f"📝 Tracked MIC: {text[:30]}... (total: {len(self.recent_mic_transcriptions)})")
            elif "SYSTEM" in source:
                self.recent_sys_transcriptions.append((text, current_time))
                self.recent_sys_transcriptions = [
                    (t, ts) for t, ts in self.recent_sys_transcriptions
                    if current_time - ts < 10.0
                ]
                print(f"� Tracked SYSTEM: {text[:30]}... (total: {len(self.recent_sys_transcriptions)})")
            
            # THIRD: Check if SYSTEM is actually a TTS translation
            # TTS translations are NOT in the queued list (not MIC audio)
            # and they appear when TTS is active
            if "SYSTEM" in source:
                # Check if this text was from original speech (MIC/SYSTEM)
                was_original_speech = False
                for queued_text, queued_time in self.queued_for_translation:
                    # Check if this matches queued original text
                    if (text.lower().strip().replace(" ", "") ==
                            queued_text.lower().strip().replace(" ", "")):
                        was_original_speech = True
                        break
                
                # If NOT original speech, it must be a translation
                if not was_original_speech and self.tts_to_mic_enabled:
                    # This is a TTS translation - label it differently
                    speaker_id = "🌍 Translated"
                    source = "TTS"
            
            # Emit signal for thread-safe GUI update
            self.signals.append_final.emit(text, source, speaker_id, timestamp)
            
            # Update last speech time for auto-pause
            self.last_speech_time = current_time
            
            # Queue for translation if any translation feature enabled
            translation_needed = (
                self.text_translation_enabled or self.tts_to_mic_enabled
            )
            if translation_needed and text.strip() and source != "TTS":
                # For TTS: Skip OLD speech (seen before TTS was enabled)
                # For text translation: Queue all speech
                should_queue = True
                if self.tts_to_mic_enabled:
                    # When TTS enabled: check if text was seen before TTS
                    text_hash = text.lower().strip().replace(" ", "")
                    if text_hash in self.seen_before_tts:
                        should_queue = False
                        print("⏭️ Skipping old speech from before TTS enable")
                
                if should_queue and self.translation_queue.qsize() < 5:
                    print(f"📤 Queued for translation: {text[:40]}...")
                    self.translation_queue.put(
                        (text, source, speaker_id, timestamp)
                    )
                    # Track that this text was queued for translation
                    self.queued_for_translation.append((text, current_time))
                    # Keep only recent entries
                    self.queued_for_translation = [
                        (t, ts) for t, ts in self.queued_for_translation
                        if current_time - ts < self.translation_window_seconds
                    ]
                elif not should_queue:
                    print(f"⏸️ NOT queued (should_queue=False): {text[:40]}...")
                elif self.translation_queue.qsize() >= 5:
                    print(f"⏸️ NOT queued (queue full): {text[:40]}...")
            
            # Also log to file (translations are NOT logged)
            self.logger.log_transcription(text, source, speaker_id)
            
            # Process with AI meeting assistant for insights
            if source != "TTS":  # Don't analyze TTS translations
                insights = self.meeting_assistant.add_transcription(text, source, timestamp)
                
                # Display AI insights if any were generated
                if insights:
                    print(f"✨ AI Insights generated: {list(insights.keys())}")
                    
                    # Save insights to files (this creates the txt files)
                    self.meeting_assistant.display_insights(insights)
                    
                    # Emit signal to update GUI display
                    self.signals.update_insights_display.emit(insights)
    
    def interim_callback(
        self, text: str, source: str, speaker_id: str = None
    ):
        """Callback for interim transcription results."""
        if text and text.strip():
            # Update last speech time (interim = still speaking!)
            self.last_speech_time = time.time()
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
    
    def flush_interim_to_final(self):
        """Move any remaining interim text to final results."""
        interim_text = self.interim_text.toPlainText().strip()
        if interim_text:
            # Get current timestamp
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Add to final results with system label
            self.signals.append_final.emit(
                interim_text,
                "System",
                "(flushed from interim)",
                timestamp
            )
    
    def stop_transcription(self):
        """Stop transcription."""
        self.is_running = False
        
        # Stop translation worker
        self.translation_worker_running = False
        
        # Flush any remaining interim text to final results
        self.flush_interim_to_final()
        
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
        
        # Cleanup TTS controller
        self.tts_controller.cleanup()
        
        # Stop audio mixer
        if self.mixer_started:
            print("⏹️ Stopping audio mixer...")
            stop_mixer()
            self.mixer_started = False
        
        event.accept()


def main():
    """Main entry point."""
    app = QApplication(sys.argv)
    window = TranscriptionGUI()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
