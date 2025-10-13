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
    QListWidgetItem, QDateEdit, QLineEdit
)
from PyQt6.QtCore import Qt, pyqtSignal, QObject, QTimer, QDate
from PyQt6.QtGui import QFont, QTextCursor, QColor, QIcon, QMovie, QPixmap
# Import our modern EPAM-inspired styles
from epam_style import (
    COLORS, FONTS, apply_modern_styles, get_textedit_style,
    PRIMARY_BUTTON_STYLE, SECONDARY_BUTTON_STYLE, ACTION_BUTTON_STYLE,
    TITLE_STYLE, TIMER_LABEL_STYLE, WARNING_LABEL_STYLE, LIVE_MODE_BUTTON_STYLE
)
# Import modern icons and professional text
from modern_icons import MODERN_BUTTON_TEXT, MODERN_HEADERS, MODERN_CHAT_BUTTONS
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
from private_chat_service import PrivateChatService


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
    # Private Chat signals
    append_chat_message = pyqtSignal(str, str, str, str)  # timestamp, type, question, answer
    update_chat_buttons = pyqtSignal(bool)  # enable/disable
    show_chat_error = pyqtSignal(str)  # error message
    set_api_status = pyqtSignal(str)  # API operation status


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
        print("[REFRESH] Starting audio mixer...")
        if start_mixer():
            self.mixer_started = True
            print("[OK] Audio mixer started successfully")
        else:
            print("[WARNING] Audio mixer failed to start")
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
        
        # Private AI Chat
        self.chat_service = PrivateChatService()
        self.chat_queue = Queue()
        self.chat_worker_running = False
        
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
        self.signals.append_chat_message.connect(self.append_chat_message)
        self.signals.update_chat_buttons.connect(self.update_chat_buttons)
        self.signals.show_chat_error.connect(self.show_chat_error)
        self.signals.set_api_status.connect(self.set_api_status)
        
        # Setup GUI
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the user interface with modern EPAM-inspired design."""
        self.setWindowTitle("Meeting Transcription Assistant")
        self.setGeometry(100, 100, 1500, 1000)
        
        # Apply modern styles to the entire application
        apply_modern_styles(self)
        
        # Central widget
        central_widget = QWidget()
        central_widget.setStyleSheet(f"background-color: {COLORS['bg_primary']};")
        self.setCentralWidget(central_widget)
        
        # Main layout with proper spacing
        main_layout = QVBoxLayout()
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(24, 24, 24, 24)
        central_widget.setLayout(main_layout)
        
        # Header with controls
        header_layout = QHBoxLayout()
        header_layout.setSpacing(24)
        
        # Title with modern styling - clean and professional
        title_label = QLabel("Meeting Transcription Assistant")
        title_label.setStyleSheet(TITLE_STYLE)
        header_layout.addWidget(title_label)
        
        # Warning indicator for translation errors (initialized here, added to footer later)
        self.warning_label = QLabel("")
        self.warning_label.setStyleSheet(WARNING_LABEL_STYLE)
        self.warning_label.setVisible(False)
        
        # Timer (initialized here, added to footer later) - professional format
        self.timer_label = QLabel("00:00:00")
        self.timer_label.setStyleSheet(TIMER_LABEL_STYLE)
        
        # API Status indicator with modern styling
        self.api_status_label = QLabel("")
        self.api_status_label.setStyleSheet(f"""
            QLabel {{
                color: {COLORS['text_muted']};
                font-family: {FONTS['primary']};
                font-size: 12px;
                font-style: italic;
                padding: 4px 8px;
                background-color: {COLORS['bg_secondary']};
                border-radius: 4px;
            }}
        """)
        self.api_status_label.setVisible(False)
        
        header_layout.addStretch()
        
        # Control buttons in vertical layout (left side)
        control_layout = QVBoxLayout()
        control_layout.setSpacing(12)
        
        # Start/Stop button with primary styling - professional text
        self.start_stop_btn = QPushButton(MODERN_BUTTON_TEXT['start_transcription'])
        self.start_stop_btn.setObjectName("primary_button")
        self.start_stop_btn.setStyleSheet(PRIMARY_BUTTON_STYLE)
        self.start_stop_btn.clicked.connect(self.toggle_transcription)
        self.start_stop_btn.setMinimumWidth(200)
        self.start_stop_btn.setMinimumHeight(45)
        control_layout.addWidget(self.start_stop_btn)
        
        # Clear Final button with secondary styling - professional text
        clear_final_btn = QPushButton(MODERN_BUTTON_TEXT['clear_final'])
        clear_final_btn.setObjectName("secondary_button")
        clear_final_btn.setStyleSheet(SECONDARY_BUTTON_STYLE)
        clear_final_btn.clicked.connect(self.clear_final)
        clear_final_btn.setMinimumWidth(200)
        clear_final_btn.setMinimumHeight(40)
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
        features_layout.setSpacing(20)
        
        # GROUP 1: Speech to Text Translation (Modern Card) - professional header
        speech_to_text_group = QGroupBox(MODERN_HEADERS['speech_translation'])
        speech_to_text_layout = QVBoxLayout()
        speech_to_text_layout.setSpacing(16)
        speech_to_text_layout.setContentsMargins(20, 20, 20, 20)
        
        self.translate_text_checkbox = QCheckBox("Enable Translation")
        speech_to_text_layout.addWidget(self.translate_text_checkbox)
        
        lang_layout = QHBoxLayout()
        lang_label = QLabel("Target Language:")
        lang_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-weight: 500;")
        lang_layout.addWidget(lang_label)
        self.text_translation_language = QComboBox()
        self.text_translation_language.addItems([
            "English", "Russian", "Turkish"
        ])
        lang_layout.addWidget(self.text_translation_language)
        speech_to_text_layout.addLayout(lang_layout)
        
        speech_to_text_group.setLayout(speech_to_text_layout)
        features_layout.addWidget(speech_to_text_group)
        
        # GROUP 2: Text to Speech Translation (Modern Card) - professional header
        text_to_speech_group = QGroupBox(MODERN_HEADERS['tts_translation'])
        text_to_speech_layout = QVBoxLayout()
        text_to_speech_layout.setSpacing(16)
        text_to_speech_layout.setContentsMargins(20, 20, 20, 20)
        
        self.tts_mic_checkbox = QCheckBox("Enable TTS to Mic")
        text_to_speech_layout.addWidget(self.tts_mic_checkbox)
        
        tts_lang_layout = QHBoxLayout()
        tts_label = QLabel("TTS Language:")
        tts_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-weight: 500;")
        tts_lang_layout.addWidget(tts_label)
        self.tts_language_selector = QComboBox()
        self.tts_language_selector.addItems([
            "English", "Russian", "Turkish"
        ])
        self.tts_language_selector.currentTextChanged.connect(
            self.on_tts_language_changed
        )
        tts_lang_layout.addWidget(self.tts_language_selector)
        text_to_speech_layout.addLayout(tts_lang_layout)
        
        self.speak_btn = QPushButton(MODERN_BUTTON_TEXT['speak_to_mic'])
        self.speak_btn.setObjectName("action_button")
        self.speak_btn.setStyleSheet(ACTION_BUTTON_STYLE)
        self.speak_btn.setEnabled(False)
        self.speak_btn.setMinimumWidth(160)
        self.speak_btn.setMinimumHeight(35)
        self.speak_btn.clicked.connect(self.toggle_speak_translation)
        text_to_speech_layout.addWidget(self.speak_btn)
        
        # Connect checkboxes to their handlers after styling
        self.translate_text_checkbox.stateChanged.connect(
            self.toggle_text_translation
        )
        self.tts_mic_checkbox.stateChanged.connect(
            self.toggle_tts_to_mic
        )
        
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
        
        # Interim Results Group (single line) with modern styling - professional header
        interim_group = QGroupBox(MODERN_HEADERS['interim_results'])
        interim_layout = QVBoxLayout()
        interim_layout.setContentsMargins(16, 16, 16, 16)
        
        self.interim_text = QTextEdit()
        self.interim_text.setReadOnly(True)
        self.interim_text.setStyleSheet(get_textedit_style(COLORS['accent_warning']))
        # Set fixed height for single row
        self.interim_text.setMaximumHeight(60)
        interim_layout.addWidget(self.interim_text)
        
        interim_group.setLayout(interim_layout)
        transcription_layout.addWidget(interim_group)
        
        # Final Results Group with modern styling - professional header
        final_group = QGroupBox(MODERN_HEADERS['final_results'])
        final_layout = QVBoxLayout()
        final_layout.setContentsMargins(16, 16, 16, 16)
        
        self.final_text = QTextEdit()
        self.final_text.setReadOnly(True)
        self.final_text.setStyleSheet(get_textedit_style(COLORS['accent_success']))
        final_layout.addWidget(self.final_text)
        
        final_group.setLayout(final_layout)
        transcription_layout.addWidget(final_group)
        
        # Translation Results Group with modern styling - professional header
        self.translation_group = QGroupBox(MODERN_HEADERS['translation_results'])
        translation_result_layout = QVBoxLayout()
        translation_result_layout.setContentsMargins(16, 16, 16, 16)
        
        self.translation_text = QTextEdit()
        self.translation_text.setReadOnly(True)
        self.translation_text.setStyleSheet(get_textedit_style(COLORS['accent_info']))
        translation_result_layout.addWidget(self.translation_text)
        
        self.translation_group.setLayout(translation_result_layout)
        transcription_layout.addWidget(self.translation_group)
        self.translation_group.hide()  # Hidden by default
        
        # ===== PRIVATE AI CHAT SECTION =====
        self.setup_private_chat_ui(transcription_layout)
        
        # Add transcription tab to tab widget - professional name
        self.tab_widget.addTab(transcription_tab, MODERN_HEADERS['transcription_tab'])
        
        # ===== TAB 2: AI INSIGHTS =====
        self.setup_insights_tab()
        
        # Connect tab change event to auto-refresh sessions
        self.tab_widget.currentChanged.connect(self.on_tab_changed)
        
        # Footer layout with modern spacing and styling
        footer_layout = QHBoxLayout()
        footer_layout.setSpacing(16)
        footer_layout.setContentsMargins(0, 12, 0, 0)
        footer_layout.addWidget(self.warning_label)
        footer_layout.addWidget(self.api_status_label)
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
        
        # Live session button (always at top) with modern styling - professional text
        self.live_mode_btn = QPushButton(MODERN_BUTTON_TEXT['live_session'])
        self.live_mode_btn.setCheckable(True)
        self.live_mode_btn.setChecked(True)
        self.live_mode_btn.setObjectName("live_mode_button")
        self.live_mode_btn.setStyleSheet(LIVE_MODE_BUTTON_STYLE)
        self.live_mode_btn.clicked.connect(self.switch_to_live_mode)
        self.live_mode_btn.setMinimumHeight(55)
        left_panel_layout.addWidget(self.live_mode_btn)
        
        # Session list header with modern styling - professional text
        session_list_label = QLabel(MODERN_HEADERS['past_sessions'])
        session_list_label.setStyleSheet(f"""
            QLabel {{
                font-family: {FONTS['primary']};
                font-size: 16px;
                font-weight: 600;
                color: {COLORS['epam_dark']};
                margin-top: 16px;
                margin-bottom: 8px;
            }}
        """)
        left_panel_layout.addWidget(session_list_label)
        
        # Date filter controls with modern styling
        filter_layout = QHBoxLayout()
        filter_layout.setSpacing(8)
        
        filter_label = QLabel("Filter by date:")
        filter_label.setStyleSheet(f"""
            QLabel {{
                font-family: {FONTS['primary']};
                font-size: 13px;
                color: {COLORS['text_secondary']};
            }}
        """)
        filter_layout.addWidget(filter_label)
        
        self.date_filter = QDateEdit()
        self.date_filter.setCalendarPopup(True)
        self.date_filter.setDate(QDate.currentDate())
        self.date_filter.setDisplayFormat("yyyy-MM-dd")
        self.date_filter.dateChanged.connect(self.apply_date_filter)
        filter_layout.addWidget(self.date_filter)
        
        # Clear filter button with modern styling - professional text
        clear_filter_btn = QPushButton(MODERN_BUTTON_TEXT['all_sessions'])
        clear_filter_btn.setObjectName("action_button")
        clear_filter_btn.setStyleSheet(ACTION_BUTTON_STYLE)
        clear_filter_btn.setMaximumWidth(90)
        clear_filter_btn.setMinimumHeight(32)
        clear_filter_btn.clicked.connect(self.clear_date_filter)
        clear_filter_btn.setToolTip("Show all sessions")
        filter_layout.addWidget(clear_filter_btn)
        
        left_panel_layout.addLayout(filter_layout)
        
        # Filter status label with modern styling
        self.filter_status_label = QLabel("")
        self.filter_status_label.setStyleSheet(f"""
            QLabel {{
                color: {COLORS['text_muted']};
                font-family: {FONTS['primary']};
                font-size: 11px;
                font-style: italic;
                margin-bottom: 8px;
            }}
        """)
        left_panel_layout.addWidget(self.filter_status_label)
        
        # Session list widget with modern styling
        self.session_list = QListWidget()
        self.session_list.itemClicked.connect(self.on_session_clicked)
        self.session_list.setMinimumHeight(350)
        left_panel_layout.addWidget(self.session_list)
        
        # Session info/stats at bottom with modern card styling
        self.session_stats_label = QLabel("Select a session to view insights")
        self.session_stats_label.setStyleSheet(f"""
            QLabel {{
                padding: 16px;
                background-color: {COLORS['bg_card']};
                color: {COLORS['text_primary']};
                border: 1px solid {COLORS['border_light']};
                border-radius: 8px;
                font-family: {FONTS['primary']};
                font-size: 12px;
                line-height: 1.4;
            }}
        """)
        self.session_stats_label.setWordWrap(True)
        left_panel_layout.addWidget(self.session_stats_label)
        
        insights_main_layout.addWidget(left_panel)
        
        # ===== RIGHT PANEL: Insights Display =====
        right_panel = QWidget()
        right_panel_layout = QVBoxLayout()
        right_panel.setLayout(right_panel_layout)
        # Create a splitter for resizable sections
        splitter = QSplitter(Qt.Orientation.Vertical)
        
        # Key Points Section with modern styling - professional header
        key_points_group = QGroupBox(MODERN_HEADERS['key_points'])
        key_points_layout = QVBoxLayout()
        key_points_layout.setContentsMargins(16, 16, 16, 16)
        self.key_points_text = QTextEdit()
        self.key_points_text.setReadOnly(True)
        self.key_points_text.setStyleSheet(get_textedit_style(COLORS['accent_success']))
        self.key_points_text.setPlaceholderText("Key points will appear here as the AI identifies them...")
        key_points_layout.addWidget(self.key_points_text)
        key_points_group.setLayout(key_points_layout)
        splitter.addWidget(key_points_group)
        
        # Decisions Section with modern styling - professional header
        decisions_group = QGroupBox(MODERN_HEADERS['decisions'])
        decisions_layout = QVBoxLayout()
        decisions_layout.setContentsMargins(16, 16, 16, 16)
        self.decisions_text = QTextEdit()
        self.decisions_text.setReadOnly(True)
        self.decisions_text.setStyleSheet(get_textedit_style(COLORS['accent_warning']))
        self.decisions_text.setPlaceholderText("Decisions made during the meeting will appear here...")
        decisions_layout.addWidget(self.decisions_text)
        decisions_group.setLayout(decisions_layout)
        splitter.addWidget(decisions_group)
        
        # Action Items Section with modern styling - professional header
        action_items_group = QGroupBox(MODERN_HEADERS['action_items'])
        action_items_layout = QVBoxLayout()
        action_items_layout.setContentsMargins(16, 16, 16, 16)
        self.action_items_text = QTextEdit()
        self.action_items_text.setReadOnly(True)
        self.action_items_text.setStyleSheet(get_textedit_style(COLORS['accent_info']))
        self.action_items_text.setPlaceholderText("Action items and tasks will appear here...")
        action_items_layout.addWidget(self.action_items_text)
        action_items_group.setLayout(action_items_layout)
        splitter.addWidget(action_items_group)
        
        # Follow-up Questions Section with modern styling - professional header
        questions_group = QGroupBox(MODERN_HEADERS['follow_up_questions'])
        questions_layout = QVBoxLayout()
        questions_layout.setContentsMargins(16, 16, 16, 16)
        self.questions_text = QTextEdit()
        self.questions_text.setReadOnly(True)
        self.questions_text.setStyleSheet(get_textedit_style(COLORS['accent_neutral']))
        self.questions_text.setPlaceholderText("AI-suggested follow-up questions will appear here...")
        questions_layout.addWidget(self.questions_text)
        questions_group.setLayout(questions_layout)
        splitter.addWidget(questions_group)
        
        right_panel_layout.addWidget(splitter)
        insights_main_layout.addWidget(right_panel)
        
        # Add insights tab to tab widget - professional name
        self.tab_widget.addTab(insights_tab, MODERN_HEADERS['insights_tab'])
        
        # Populate session list on startup
        self.refresh_session_list()
    
    def setup_private_chat_ui(self, transcription_layout):
        """Setup the private AI chat interface at bottom of transcription tab."""
        
        # Main chat group with modern styling - professional header
        self.chat_group = QGroupBox(MODERN_HEADERS['private_chat'])
        chat_layout = QVBoxLayout()
        chat_layout.setSpacing(16)
        chat_layout.setContentsMargins(20, 20, 20, 20)
        
        # Chat history display with modern styling
        self.chat_history_text = QTextEdit()
        self.chat_history_text.setReadOnly(True)
        self.chat_history_text.setMaximumHeight(280)
        self.chat_history_text.setStyleSheet(f"""
            QTextEdit {{
                background-color: {COLORS['bg_secondary']};
                border: 1px solid {COLORS['border_light']};
                border-radius: 8px;
                padding: 16px;
                font-family: {FONTS['primary']};
                font-size: 13px;
                line-height: 1.5;
                color: {COLORS['text_primary']};
            }}
        """)
        self.chat_history_text.setPlaceholderText(
            "💬 Ask questions about the meeting transcript...\n\n"
            "Start transcription to enable chat."
        )
        chat_layout.addWidget(self.chat_history_text)
        
        # Common questions buttons with modern styling
        common_q_label = QLabel("Quick Questions:")
        common_q_label.setStyleSheet(f"""
            QLabel {{
                font-family: {FONTS['primary']};
                font-size: 14px;
                font-weight: 600;
                color: {COLORS['text_primary']};
                margin-top: 8px;
                margin-bottom: 8px;
            }}
        """)
        chat_layout.addWidget(common_q_label)
        
        # Create button grid (2 rows) with modern styling
        button_container = QWidget()
        button_grid = QVBoxLayout()
        button_grid.setSpacing(12)
        button_container.setLayout(button_grid)
        
        # First row of buttons
        button_row1 = QHBoxLayout()
        button_row1.setSpacing(12)
        self.chat_buttons = {}
        
        buttons_row1 = [
            ("last_said", MODERN_CHAT_BUTTONS['last_said']),
            ("who_spoke", MODERN_CHAT_BUTTONS['who_spoke']),
            ("action_items", MODERN_CHAT_BUTTONS['action_items']),
            ("main_topic", MODERN_CHAT_BUTTONS['main_topic']),
        ]
        
        for btn_id, btn_text in buttons_row1:
            btn = QPushButton(btn_text)
            btn.setObjectName("action_button")
            btn.setStyleSheet(ACTION_BUTTON_STYLE)
            btn.setMinimumHeight(40)
            btn.clicked.connect(lambda checked, id=btn_id: self.ask_common_question(id))
            btn.setEnabled(False)  # Disabled until transcription starts
            self.chat_buttons[btn_id] = btn
            button_row1.addWidget(btn)
        
        button_grid.addLayout(button_row1)
        
        # Second row of buttons
        button_row2 = QHBoxLayout()
        button_row2.setSpacing(12)
        buttons_row2 = [
            ("concerns", MODERN_CHAT_BUTTONS['concerns']),
            ("next_steps", MODERN_CHAT_BUTTONS['next_steps']),
            ("decisions", MODERN_CHAT_BUTTONS['decisions']),
        ]
        
        for btn_id, btn_text in buttons_row2:
            btn = QPushButton(btn_text)
            btn.setObjectName("action_button")
            btn.setStyleSheet(ACTION_BUTTON_STYLE)
            btn.setMinimumHeight(40)
            btn.clicked.connect(lambda checked, id=btn_id: self.ask_common_question(id))
            btn.setEnabled(False)  # Disabled until transcription starts
            self.chat_buttons[btn_id] = btn
            button_row2.addWidget(btn)
        
        button_grid.addLayout(button_row2)
        chat_layout.addWidget(button_container)
        
        # Custom question input with modern styling
        custom_layout = QHBoxLayout()
        custom_layout.setSpacing(12)
        
        custom_label = QLabel("Custom Question:")
        custom_label.setStyleSheet(f"""
            QLabel {{
                font-family: {FONTS['primary']};
                font-size: 14px;
                font-weight: 500;
                color: {COLORS['text_secondary']};
            }}
        """)
        custom_layout.addWidget(custom_label)
        
        self.chat_input = QLineEdit()
        self.chat_input.setPlaceholderText("Type your question here...")
        self.chat_input.setMinimumHeight(40)
        self.chat_input.returnPressed.connect(self.ask_custom_question)
        self.chat_input.setEnabled(False)  # Disabled until transcription starts
        custom_layout.addWidget(self.chat_input)
        
        self.chat_ask_btn = QPushButton(MODERN_BUTTON_TEXT['ask'])
        self.chat_ask_btn.setObjectName("secondary_button")
        self.chat_ask_btn.setStyleSheet(SECONDARY_BUTTON_STYLE)
        self.chat_ask_btn.setMinimumHeight(40)
        self.chat_ask_btn.setMinimumWidth(90)
        self.chat_ask_btn.clicked.connect(self.ask_custom_question)
        self.chat_ask_btn.setEnabled(False)  # Disabled until transcription starts
        custom_layout.addWidget(self.chat_ask_btn)
        
        self.chat_clear_btn = QPushButton(MODERN_BUTTON_TEXT['clear'])
        self.chat_clear_btn.setObjectName("action_button")
        self.chat_clear_btn.setStyleSheet(ACTION_BUTTON_STYLE)
        self.chat_clear_btn.setMinimumHeight(40)
        self.chat_clear_btn.setMinimumWidth(90)
        self.chat_clear_btn.clicked.connect(lambda: self.chat_input.clear())
        custom_layout.addWidget(self.chat_clear_btn)
        
        chat_layout.addLayout(custom_layout)
        self.chat_group.setLayout(chat_layout)
        
        # Add to transcription tab
        transcription_layout.addWidget(self.chat_group)
        self.chat_group.hide()  # Hidden until transcription starts
    
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
                    
                    # Create list item
                    item = QListWidgetItem(display_name)
                    item.setData(Qt.ItemDataRole.UserRole, folder_name)  # Store folder name
                    item.setToolTip(f"Session: {folder_name}\nClick to view insights")
                    
                    self.session_list.addItem(item)
                    items_added += 1
                except Exception as e:
                    # If parsing fails, just use folder name
                    print(f"[WARNING] Error parsing session {folder_name}: {e}")
                    item = QListWidgetItem(folder_name)
                    item.setData(Qt.ItemDataRole.UserRole, folder_name)
                    self.session_list.addItem(item)
                    items_added += 1
        
        if items_added == 0 and self.date_filter_enabled:
            item = QListWidgetItem(f"No sessions found for {self.filtered_date.strftime('%Y-%m-%d')}")
            item.setForeground(QColor("#666666"))
            self.session_list.addItem(item)
        
        print(f"[OK] Loaded {items_added} past sessions")
    
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
            # Clear chat history too
            self.chat_history_text.clear()
            self.chat_history_text.setPlaceholderText(
                "💬 Ask questions about the meeting transcript...\n\n"
                "Start transcription to enable chat."
            )
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
        
        # Load current session's chat history if it exists
        if self.session_folder:
            self.load_session_chat_history(self.session_folder.replace("sessions/", ""))
    
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
        
        # Load private chat history
        self.load_session_chat_history(session_folder)
    
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
            target_lang = self.text_translation_language.currentText()
            self.logger.log_system_event(
                f"Text translation ENABLED (target: {target_lang})"
            )
        else:
            # Hide translation window if TTS is also disabled
            if not self.tts_to_mic_enabled:
                self.translation_group.hide()
            self.logger.log_system_event("Text translation DISABLED")
    
    def toggle_tts_to_mic(self, state):
        """Toggle TTS to microphone feature on/off dynamically during session."""
        self.tts_to_mic_enabled = bool(state)
        
        if self.tts_to_mic_enabled:
            target_lang = self.tts_language_selector.currentText()
            self.logger.log_system_event(
                f"TTS to microphone ENABLED (target: {target_lang})"
            )
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
                print(f"[CLEAR] Cleared {queued_count} pending translations")
            
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
            
            print(f"[CLEAR] Marked {len(self.seen_before_tts)} old texts to skip")
            
            # Start translation worker if not running
            if not self.translation_worker_running:
                self.translation_worker_running = True
                import threading
                worker_thread = threading.Thread(
                    target=self.translation_worker,
                    daemon=True
                )
                worker_thread.start()
                print("[REFRESH] Started translation worker thread")
            
            # Mark the time when TTS was enabled
            import time
            self.tts_enabled_at = time.time()
            print("🌍 Oral translation mode enabled")
            self.logger.log_system_event("Oral translation mode enabled")
            
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
            self.logger.log_system_event("TTS to microphone DISABLED")
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
            print("[CLEAR] Cleared translation queue")
            
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
            self.logger.log_system_event(
                f"TTS target language changed to: {language}"
            )
    
    def toggle_speak_translation(self):
        """Handle Speak/Stop Speaking button click."""
        if self.tts_controller.is_speaking():
            # Currently speaking - stop it
            self.logger.log_system_event("TTS playback stopped by user")
            self.tts_controller.stop_speaking()
        else:
            # Not speaking - start if ready
            if self.tts_controller.is_ready():
                self.logger.log_system_event("TTS playback started")
                self.tts_controller.speak()
            else:
                print("[WARNING] No translation audio ready to speak")
    
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
        print(f"[CONTROL] Updating button: text='{text}', enabled={enabled}")
        # Use modern button text mapping
        if text == "Speak to Mic":
            text = MODERN_BUTTON_TEXT['speak_to_mic']
        elif text == "Stop Speaking":
            text = MODERN_BUTTON_TEXT['stop_speaking']
        self.speak_btn.setText(text)
        self.speak_btn.setEnabled(enabled)
        print(f"[CONTROL] Button updated: isEnabled={self.speak_btn.isEnabled()}")
    
    def set_api_status(self, message: str):
        """Update API status label (thread-safe via signal)."""
        if message:
            self.api_status_label.setText(f"⏳ {message}")
            self.api_status_label.setVisible(True)
        else:
            self.api_status_label.setVisible(False)
    
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
                    text_preview = text[:50] if len(text) > 50 else text
                    self.logger.log_system_event(
                        f"LLM translate: '{text_preview}...' -> {target_lang}"
                    )
                    self.signals.set_api_status.emit(
                        f"Translating to {target_lang}..."
                    )
                    translation = llm_service.chat(prompt)
                    self.signals.set_api_status.emit("")
                    trans_preview = (translation[:50] if len(translation) > 50
                                     else translation)
                    self.logger.log_system_event(
                        f"LLM response: '{trans_preview}...'"
                    )
                    
                    # Emit signal to update GUI (for text translation)
                    if self.text_translation_enabled:
                        self.signals.append_translation.emit(
                            translation, source, speaker_id, timestamp
                        )
                    
                    # Add to TTS buffer if TTS to mic is enabled
                    if self.tts_to_mic_enabled and translation.strip():
                        try:
                            trans_preview = (translation[:40]
                                             if len(translation) > 40
                                             else translation)
                            self.logger.log_system_event(
                                f"TTS generation: '{trans_preview}...'"
                            )
                            self.signals.set_api_status.emit(
                                "Generating TTS audio..."
                            )
                            self.tts_controller.add_translation(translation)
                            self.signals.set_api_status.emit("")
                            self.logger.log_system_event(
                                "TTS audio added to buffer"
                            )
                        except Exception as tts_error:
                            error_msg = (
                                f"TTS generation failed:\n{str(tts_error)}"
                            )
                            print(f"[ERROR] {error_msg}")
                            self.signals.show_warning.emit(error_msg)
                    
                except ConnectionError as conn_err:
                    error_msg = (
                        f"Connection Error:\n"
                        f"Cannot reach translation service.\n"
                        f"Check your network/VPN connection.\n\n"
                        f"Details: {str(conn_err)}"
                    )
                    print(f"[ERROR] {error_msg}")
                    self.signals.show_warning.emit(error_msg)
                    
                except TimeoutError as timeout_err:
                    error_msg = (
                        f"Timeout Error:\n"
                        f"Translation service not responding.\n\n"
                        f"Details: {str(timeout_err)}"
                    )
                    print(f"[ERROR] {error_msg}")
                    self.signals.show_warning.emit(error_msg)
                    
                except Exception as translation_error:
                    error_msg = (
                        f"Translation Failed:\n"
                        f"{str(translation_error)}\n\n"
                        f"Text: {text[:50]}..."
                    )
                    print(f"[ERROR] {error_msg}")
                    self.signals.show_warning.emit(error_msg)
                    
            except Exception as e:
                error_msg = (
                    f"Translation worker error:\n{str(e)}\n\n"
                    f"Type: {type(e).__name__}"
                )
                print(f"[ERROR] {error_msg}")
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
            self.start_stop_btn.setText(MODERN_BUTTON_TEXT['stop_transcription'])
            
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
            
            # Show and enable chat UI
            self.chat_group.show()
            self.chat_history_text.clear()
            self.chat_history_text.setPlaceholderText(
                "💬 Ask questions about the meeting transcript..."
            )
            
            # Start chat worker thread
            if not self.chat_worker_running:
                self.chat_worker_running = True
                chat_thread = threading.Thread(
                    target=self.chat_worker,
                    daemon=True
                )
                chat_thread.start()
                print("🔄 Chat worker thread started")
            
            # Enable chat buttons
            self.signals.update_chat_buttons.emit(True)
        else:
            self.start_stop_btn.setText(MODERN_BUTTON_TEXT['start_transcription'])
            self.logger.log_system_event("Transcription session paused")
            
            # Stop dancing fox animation and show static image
            self.animated_fox.stop()
            self.fox_label.setPixmap(self.static_fox)
            
            # Stop translation worker thread
            self.translation_worker_running = False
            
            # Stop and clear TTS
            self.tts_controller.stop_speaking()
            
            # Stop chat worker thread
            self.chat_worker_running = False
            
            # Disable chat buttons
            self.signals.update_chat_buttons.emit(False)
            
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
                f"{hours:02d}:{minutes:02d}:{seconds:02d}"
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
        # Clear STT status when final result received
        self.signals.set_api_status.emit("")
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
            # Show STT status
            self.signals.set_api_status.emit(
                f"Recognizing speech ({source})..."
            )
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
                    self.logger.log_system_event(
                        "Starting Azure Speech STT for microphone"
                    )
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
                    self.logger.log_system_event(
                        "Azure Speech STT for microphone started successfully"
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
                    self.logger.log_system_event(
                        "Starting Azure Speech STT for system audio"
                    )
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
                    self.logger.log_system_event(
                        "Azure Speech STT for system audio started"
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
    
    # ===== PRIVATE CHAT METHODS =====
    
    def ask_common_question(self, question_type: str):
        """Handle common question button click."""
        if not self.is_running:
            QMessageBox.warning(
                self, "No Active Session",
                "Please start transcription before asking questions."
            )
            return
        
        # Get the question text
        question_text = self.chat_service.get_question_text(question_type)
        
        # Add visual indicator
        self.chat_history_text.append(
            f"\n{'=' * 60}\n"
            f"🤔 Processing: {question_text}\n"
            f"{'=' * 60}\n"
        )
        self.chat_history_text.moveCursor(QTextCursor.MoveOperation.End)
        
        # Queue the question
        self.chat_queue.put((question_type, question_text))
        
        # Disable buttons while processing
        self.signals.update_chat_buttons.emit(False)
        
        print(f"💬 Chat question queued: [{question_type}] {question_text}")
    
    def ask_custom_question(self):
        """Handle custom question input."""
        question = self.chat_input.text().strip()
        if not question:
            return
        
        if not self.is_running:
            QMessageBox.warning(
                self, "No Active Session",
                "Please start transcription before asking questions."
            )
            return
        
        # Add visual indicator
        self.chat_history_text.append(
            f"\n{'=' * 60}\n"
            f"🤔 Processing: {question}\n"
            f"{'=' * 60}\n"
        )
        self.chat_history_text.moveCursor(QTextCursor.MoveOperation.End)
        
        # Queue the question
        self.chat_queue.put(("custom", question))
        
        # Clear input
        self.chat_input.clear()
        
        # Disable buttons while processing
        self.signals.update_chat_buttons.emit(False)
        
        print(f"💬 Custom chat question queued: {question}")
    
    def chat_worker(self):
        """Background worker for processing chat questions."""
        print("🔄 Chat worker thread started")
        
        while self.chat_worker_running:
            try:
                # Get item from queue (blocking with timeout)
                item = self.chat_queue.get(timeout=1.0)
                question_type, question_text = item
                
                print(f"🤖 Processing chat question: [{question_type}] {question_text[:50]}...")
                
                try:
                    # Get transcript context
                    context = self.chat_service.get_transcript_context(
                        self.meeting_assistant.conversation_history
                    )
                    
                    print(f"📋 Context length: {len(context)} chars")
                    
                    # Generate prompt
                    prompt = self.chat_service.generate_prompt(
                        question_type, question_text, context
                    )
                    
                    # Call LLM
                    answer = llm_service.chat(prompt, max_tokens=400)
                    
                    if answer and not answer.startswith("Error:"):
                        # Emit signal with result
                        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        self.signals.append_chat_message.emit(
                            timestamp, question_type, question_text, answer
                        )
                        
                        # Save to history file
                        if self.session_folder:
                            self.chat_service.save_to_history(
                                question_text, answer, question_type, self.session_folder
                            )
                        
                        print(f"✅ Chat answer generated successfully")
                    else:
                        # Error from LLM
                        error_msg = f"LLM Error: {answer}"
                        self.signals.show_chat_error.emit(error_msg)
                        print(f"[ERROR] {error_msg}")
                
                except Exception as e:
                    error_msg = f"Chat processing error: {str(e)}"
                    self.signals.show_chat_error.emit(error_msg)
                    print(f"[ERROR] {error_msg}")
                    import traceback
                    traceback.print_exc()
                
            except Empty:
                # Queue timeout - this is normal, just continue
                continue
            except Exception as e:
                print(f"❌ Chat worker error: {e}")
                import traceback
                traceback.print_exc()
        
        print("🛑 Chat worker thread stopped")
    
    def append_chat_message(self, timestamp: str, q_type: str, question: str, answer: str):
        """Append chat message to display (thread-safe)."""
        # Remove the "Processing..." message by getting current text and removing last entry
        current_text = self.chat_history_text.toPlainText()
        if "🤔 Processing:" in current_text:
            # Find and remove the last processing message
            lines = current_text.split('\n')
            filtered_lines = []
            skip_count = 0
            for i in range(len(lines) - 1, -1, -1):
                if skip_count > 0:
                    skip_count -= 1
                    continue
                if "🤔 Processing:" in lines[i]:
                    skip_count = 2  # Skip this line and the separator lines
                    continue
                filtered_lines.insert(0, lines[i])
            self.chat_history_text.setPlainText('\n'.join(filtered_lines))
        
        # Append new message with nice formatting
        self.chat_history_text.append(
            f"\n{'=' * 60}\n"
            f"[{timestamp}] [{q_type}]\n"
            f"{'=' * 60}\n"
            f"Q: {question}\n\n"
            f"A: {answer}\n"
        )
        
        # Auto-scroll to bottom
        self.chat_history_text.moveCursor(QTextCursor.MoveOperation.End)
        
        # Re-enable buttons
        self.signals.update_chat_buttons.emit(True)
        
        print(f"💬 Chat message appended to display")
    
    def update_chat_buttons(self, enabled: bool):
        """Enable/disable chat buttons (thread-safe)."""
        # Update all common question buttons
        for btn in self.chat_buttons.values():
            btn.setEnabled(enabled)
        
        # Update custom question controls
        self.chat_input.setEnabled(enabled)
        self.chat_ask_btn.setEnabled(enabled)
    
    def show_chat_error(self, error_msg: str):
        """Show chat error in the display (thread-safe)."""
        self.chat_history_text.append(
            f"\n⚠️ Error: {error_msg}\n"
        )
        self.chat_history_text.moveCursor(QTextCursor.MoveOperation.End)
        
        # Re-enable buttons
        self.signals.update_chat_buttons.emit(True)
    
    def load_session_chat_history(self, session_folder: str):
        """Load private chat history for a session."""
        session_path = Path("sessions") / session_folder
        
        # Load chat history using service
        chat_content = self.chat_service.load_history(str(session_path))
        
        if chat_content:
            self.chat_history_text.setPlainText(chat_content)
        else:
            self.chat_history_text.clear()
            self.chat_history_text.setPlaceholderText(
                "No chat history for this session."
            )
    
    def closeEvent(self, event):
        """Handle window closing."""
        if self.is_running:
            self.stop_transcription()
        
        # Stop chat worker
        self.chat_worker_running = False
        
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
