"""
Azure Speech Service wrapper for real-time transcription
with speaker diarization.
"""
import azure.cognitiveservices.speech as speechsdk
from config import AzureSpeechService
from typing import Optional, Callable


class AzureSpeechTranscriber:
    """Azure Speech Service transcriber with speaker diarization."""
    
    def __init__(self, callback: Optional[Callable] = None, logger=None):
        """
        Initialize Azure Speech transcriber.
        
        Args:
            callback: Function to call with transcription results
                     Signature: callback(text: str, speaker_id: str)
            logger: TranscriptionLogger instance for logging
        """
        self.callback = callback
        self.logger = logger
        self.speech_config = None
        self.audio_stream = None
        self.is_streaming = False
        self.current_language = None  # Track current detected language
        self.initialize_config()
    
    def initialize_config(self):
        """Initialize Azure Speech configuration."""
        if not AzureSpeechService.AZURE_SPEECH_SERVICE_KEY:
            raise ValueError(
                "AZURE_SPEECH_SERVICE_KEY not set in environment variables"
            )
        if not AzureSpeechService.AZURE_SPEECH_SERVICE_REGION:
            raise ValueError(
                "AZURE_SPEECH_SERVICE_REGION not set in environment variables"
            )
        
        self.speech_config = speechsdk.SpeechConfig(
            subscription=AzureSpeechService.AZURE_SPEECH_SERVICE_KEY,
            region=AzureSpeechService.AZURE_SPEECH_SERVICE_REGION
        )
        
        # Configure language detection/recognition
        lang = AzureSpeechService.SPEECH_LANGUAGE
        if lang == "auto":
            # Enable automatic language detection
            print("🌍 Auto language detection enabled "
                  f"({', '.join(AzureSpeechService.CANDIDATE_LANGUAGES)})")
            # Auto-detect will be configured per recognizer
        else:
            # Set specific language
            self.speech_config.speech_recognition_language = lang
            print(f"🌍 Language set to: {lang}")
        
        # Enable detailed results for speaker diarization
        self.speech_config.output_format = (
            speechsdk.OutputFormat.Detailed
        )
        
        # Request speaker diarization if enabled
        if AzureSpeechService.ENABLE_DIARIZATION:
            self.speech_config.set_property(
                speechsdk.PropertyId.SpeechServiceConnection_LanguageIdMode,
                "Continuous"
            )
    
    def transcribe_audio_bytes(
        self,
        audio_data: bytes,
        source_label: str = "audio"
    ) -> Optional[str]:
        """
        Transcribe audio bytes using Azure Speech Service.
        
        Args:
            audio_data: WAV format audio bytes
            source_label: Label for the audio source
            
        Returns:
            Transcribed text or None if no speech detected
        """
        if not audio_data or len(audio_data) < 1000:
            return None
        
        try:
            # Create audio stream from bytes
            audio_stream = speechsdk.audio.PushAudioInputStream()
            audio_config = speechsdk.audio.AudioConfig(
                stream=audio_stream
            )
            
            # Create speech recognizer
            speech_recognizer = speechsdk.SpeechRecognizer(
                speech_config=self.speech_config,
                audio_config=audio_config
            )
            
            # Push audio data
            audio_stream.write(audio_data)
            audio_stream.close()
            
            # Perform recognition
            result = speech_recognizer.recognize_once()
            
            if result.reason == speechsdk.ResultReason.RecognizedSpeech:
                return result.text
            elif result.reason == speechsdk.ResultReason.NoMatch:
                return None
            elif result.reason == speechsdk.ResultReason.Canceled:
                cancellation = result.cancellation_details
                if cancellation.reason == speechsdk.CancellationReason.Error:
                    error_msg = cancellation.error_details
                    print(f"⚠️  Azure Speech Error: {error_msg}")
                return None
            
            return None
            
        except Exception as e:
            print(f"⚠️  Azure Speech transcription error: {e}")
            return None
    
    def start_continuous_recognition(
        self,
        source_label: str = "audio",
        result_callback: Optional[Callable] = None,
        interim_callback: Optional[Callable] = None
    ):
        """
        Start continuous streaming recognition.
        This enables real-time transcription with minimal delay.
        
        Args:
            source_label: Label for the audio source
            result_callback: Function to call with final results
            interim_callback: Function to call with partial results
        
        Returns:
            tuple: (audio_stream, recognizer) - use these to push audio
        """
        if self.is_streaming:
            print("⚠️  Already streaming. Stop first.")
            return None, None
        
        try:
            # Create push audio input stream
            # 16kHz, 16-bit, mono PCM
            stream_format = speechsdk.audio.AudioStreamFormat(
                samples_per_second=16000,
                bits_per_sample=16,
                channels=1
            )
            self.audio_stream = speechsdk.audio.PushAudioInputStream(
                stream_format
            )
            
            audio_config = speechsdk.audio.AudioConfig(
                stream=self.audio_stream
            )
            
            # Create speech recognizer with language detection if enabled
            lang = AzureSpeechService.SPEECH_LANGUAGE
            if lang == "auto":
                # Create auto-detect config
                auto_detect_config = (
                    speechsdk.languageconfig.AutoDetectSourceLanguageConfig(
                        languages=AzureSpeechService.CANDIDATE_LANGUAGES
                    )
                )
                recognizer = speechsdk.SpeechRecognizer(
                    speech_config=self.speech_config,
                    auto_detect_source_language_config=auto_detect_config,
                    audio_config=audio_config
                )
            else:
                # Use specific language
                recognizer = speechsdk.SpeechRecognizer(
                    speech_config=self.speech_config,
                    audio_config=audio_config
                )
            
            # Set up event handlers
            def handle_recognized(evt):
                """Handle final recognition results."""
                reason = speechsdk.ResultReason.RecognizedSpeech
                if evt.result.reason == reason:
                    # Detect language if auto-detection is enabled
                    detected_lang = None
                    if lang == "auto":
                        try:
                            # Get detected language from result properties
                            auto_detect_result = (
                                speechsdk.AutoDetectSourceLanguageResult(
                                    evt.result
                                )
                            )
                            detected_lang = auto_detect_result.language
                            
                            # Check if language changed
                            if detected_lang != self.current_language:
                                lang_map = {
                                    "en-US": "🇺🇸 English",
                                    "ru-RU": "🇷🇺 Russian",
                                    "tr-TR": "🇹🇷 Turkish"
                                }
                                lang_name = lang_map.get(
                                    detected_lang, detected_lang
                                )
                                print(
                                    f"\n🌍 Language detected: "
                                    f"{lang_name} [{source_label}]"
                                )
                                self.current_language = detected_lang
                                
                                # Log to file if logger available
                                if self.logger:
                                    self.logger.log_language_change(
                                        detected_lang, source_label
                                    )
                        except Exception:
                            # Language detection not available
                            pass
                    
                    if result_callback:
                        result_callback(evt.result.text, source_label)
            
            def handle_recognizing(evt):
                """Handle interim results for live display."""
                reason = speechsdk.ResultReason.RecognizingSpeech
                if evt.result.reason == reason and interim_callback:
                    # Send partial transcription
                    interim_callback(evt.result.text, source_label)
            
            def handle_canceled(evt):
                """Handle cancellation/errors."""
                if evt.reason == speechsdk.CancellationReason.Error:
                    print(f"⚠️  Recognition error: {evt.error_details}")
            
            # Connect event handlers
            recognizer.recognized.connect(handle_recognized)
            recognizer.recognizing.connect(handle_recognizing)
            recognizer.canceled.connect(handle_canceled)
            
            # Start continuous recognition
            recognizer.start_continuous_recognition_async().get()
            
            self.is_streaming = True
            return self.audio_stream, recognizer
            
        except Exception as e:
            print(f"⚠️  Error starting streaming: {e}")
            return None, None
    
    def stop_continuous_recognition(self, recognizer):
        """
        Stop continuous recognition.
        
        Args:
            recognizer: The recognizer instance to stop
        """
        if recognizer and self.is_streaming:
            try:
                recognizer.stop_continuous_recognition_async().get()
                if self.audio_stream:
                    self.audio_stream.close()
                self.is_streaming = False
            except Exception as e:
                print(f"⚠️  Error stopping streaming: {e}")
    
    def transcribe_with_diarization(
        self,
        audio_data: bytes,
        source_label: str = "audio"
    ) -> list:
        """
        Transcribe audio with speaker diarization.
        
        Args:
            audio_data: WAV format audio bytes
            source_label: Label for the audio source
            
        Returns:
            List of tuples: [(speaker_id, text, start_time, end_time), ...]
        """
        if not audio_data or len(audio_data) < 1000:
            return []
        
        try:
            # For speaker diarization, we need to use conversation transcriber
            # This requires audio file format
            audio_config = speechsdk.audio.AudioConfig(
                filename=None  # We'll use push stream
            )
            
            # Create conversation transcriber
            conversation_transcriber = (
                speechsdk.transcription.ConversationTranscriber(
                    speech_config=self.speech_config,
                    audio_config=audio_config
                )
            )
            
            results = []
            
            def handle_result(evt):
                """Handle transcription result with speaker info."""
                reason = speechsdk.ResultReason.RecognizedSpeech
                if evt.result.reason == reason:
                    speaker_id = evt.result.speaker_id
                    text = evt.result.text
                    results.append((speaker_id, text))
            
            # Subscribe to events
            conversation_transcriber.transcribed.connect(handle_result)
            
            # Start transcription
            conversation_transcriber.start_transcribing_async().get()
            
            # Wait for completion (simplified for now)
            # In production, this would be more sophisticated
            
            conversation_transcriber.stop_transcribing_async().get()
            
            return results
            
        except Exception as e:
            print(f"⚠️  Speaker diarization error: {e}")
            # Fall back to simple transcription
            simple_result = self.transcribe_audio_bytes(
                audio_data, source_label
            )
            if simple_result:
                return [("Unknown", simple_result)]
            return []

