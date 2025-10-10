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
        self.last_result = None  # Track last result to avoid duplicates
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
        Start continuous conversation transcription with speaker diarization.
        Uses Conversation Transcriber API for multi-speaker identification.
        
        Args:
            source_label: Label for the audio source
            result_callback: Function to call with final results
                           Signature: callback(text, source_label, speaker_id)
            interim_callback: Function to call with partial results
                            Signature: callback(text, source_label, speaker_id)
        
        Returns:
            tuple: (audio_stream, transcriber) - use these to push audio
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
            
            # Configure speech config for conversation transcription
            lang = AzureSpeechService.SPEECH_LANGUAGE
            
            # Set language for transcription with multi-language support
            if lang == "auto":
                # Enable continuous language identification for multi-language
                # This allows the transcriber to switch between languages
                auto_detect_config = (
                    speechsdk.languageconfig.AutoDetectSourceLanguageConfig(
                        languages=AzureSpeechService.CANDIDATE_LANGUAGES
                    )
                )
                print(f"🌍 Multi-language mode enabled: "
                      f"{', '.join(AzureSpeechService.CANDIDATE_LANGUAGES)}")
            else:
                auto_detect_config = None
                self.speech_config.speech_recognition_language = lang
            
            # Enable speaker diarization properties
            # Note: Conversation Transcriber automatically enables diarization
            # Configure speaker ranges using string properties
            if AzureSpeechService.MIN_SPEAKERS:
                self.speech_config.set_property_by_name(
                    "DiarizeGuests",
                    "true"
                )
            if AzureSpeechService.MAX_SPEAKERS:
                # Set expected speaker count for better accuracy
                self.speech_config.set_property_by_name(
                    "MaxSpeakers",
                    str(AzureSpeechService.MAX_SPEAKERS)
                )
            
            # Configure for faster interim results
            # Reduce initial silence timeout for quicker response
            self.speech_config.set_property(
                speechsdk.PropertyId.Speech_SegmentationSilenceTimeoutMs,
                "500"  # 500ms silence = faster segmentation
            )
            # Enable faster interim result updates
            self.speech_config.set_property(
                speechsdk.PropertyId.SpeechServiceResponse_PostProcessingOption,
                "TrueText"
            )
            
            # Create conversation transcriber with language detection
            if lang == "auto" and auto_detect_config:
                transcriber = speechsdk.transcription.ConversationTranscriber(
                    speech_config=self.speech_config,
                    audio_config=audio_config,
                    auto_detect_source_language_config=auto_detect_config
                )
            else:
                transcriber = speechsdk.transcription.ConversationTranscriber(
                    speech_config=self.speech_config,
                    audio_config=audio_config
                )
            
            # Set up event handlers
            def handle_transcribed(evt):
                """Handle final transcription results with speaker ID."""
                reason = speechsdk.ResultReason.RecognizedSpeech
                if evt.result.reason == reason:
                    speaker_id = evt.result.speaker_id
                    text = evt.result.text
                    
                    # Deduplicate: check if this is the same as last result
                    result_key = f"{speaker_id}:{text}"
                    if result_key == self.last_result:
                        return  # Skip duplicate
                    self.last_result = result_key
                    
                    # Format speaker ID for display
                    if speaker_id and speaker_id.startswith("Guest-"):
                        # Extract number from "Guest-1", "Guest-2", etc.
                        speaker_num = speaker_id.replace("Guest-", "")
                        speaker_display = f"Speaker {speaker_num}"
                    elif speaker_id:
                        speaker_display = speaker_id
                    else:
                        speaker_display = "Unknown"
                    
                    if result_callback and text:
                        # Pass speaker info to callback
                        result_callback(text, source_label, speaker_display)
            
            def handle_transcribing(evt):
                """Handle interim results for live display."""
                reason = speechsdk.ResultReason.RecognizingSpeech
                if evt.result.reason == reason and interim_callback:
                    speaker_id = evt.result.speaker_id
                    text = evt.result.text
                    
                    # Format speaker ID
                    if speaker_id and speaker_id.startswith("Guest-"):
                        speaker_num = speaker_id.replace("Guest-", "")
                        speaker_display = f"Speaker {speaker_num}"
                    elif speaker_id:
                        speaker_display = speaker_id
                    else:
                        speaker_display = "..."
                    
                    if text:
                        interim_callback(text, source_label, speaker_display)
            
            def handle_canceled(evt):
                """Handle cancellation/errors."""
                if evt.reason == speechsdk.CancellationReason.Error:
                    print(f"⚠️  Transcription error: {evt.error_details}")
            
            # Connect event handlers
            transcriber.transcribed.connect(handle_transcribed)
            transcriber.transcribing.connect(handle_transcribing)
            transcriber.canceled.connect(handle_canceled)
            
            # Start conversation transcription
            transcriber.start_transcribing_async().get()
            
            self.is_streaming = True
            print(f"👥 Speaker diarization enabled for {source_label}")
            return self.audio_stream, transcriber
            
        except Exception as e:
            print(f"⚠️  Error starting conversation transcription: {e}")
            import traceback
            traceback.print_exc()
            return None, None
    
    def stop_continuous_recognition(self, transcriber):
        """
        Stop continuous conversation transcription.
        
        Args:
            transcriber: The conversation transcriber instance to stop
        """
        if transcriber and self.is_streaming:
            try:
                transcriber.stop_transcribing_async().get()
                if self.audio_stream:
                    self.audio_stream.close()
                self.is_streaming = False
            except Exception as e:
                print(f"⚠️  Error stopping transcription: {e}")
    
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

