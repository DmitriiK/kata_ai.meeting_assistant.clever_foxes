# Configuration Guide

## Environment Variables

Create a `.env` file in the project root with the following variables:

### Required: Azure Speech Service
```bash
AZURE_SPEECH_SERVICE_KEY=your_key_here
AZURE_SPEECH_SERVICE_REGION=your_region_here  # e.g., "eastus"
```

### Optional: Language Configuration
```bash
# Language for speech recognition
# Options: "auto" (default), "en-US", "ru-RU", "tr-TR", or any Azure-supported language
SPEECH_LANGUAGE=auto

# When using "auto", it will detect between English, Russian, and Turkish
# You can customize candidate languages in config.py
```

**Supported Languages**:
- `auto` - Automatic detection (English/Russian/Turkish by default)
- `en-US` - English (United States)
- `ru-RU` - Russian
- `tr-TR` - Turkish
- `es-ES` - Spanish (Spain)
- `fr-FR` - French
- `de-DE` - German
- `ja-JP` - Japanese
- `zh-CN` - Chinese (Mandarin)
- And [many more](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/language-support)

### Optional: Custom Log File Path
```bash
# Default: transcriptions.log (in project directory)
TRANSCRIPTION_LOG_FILE=/path/to/your/logfile.log
```

## Application Settings

All settings can be customized in `config.py`:

### Audio Settings
```python
class AudioSettings:
    CHUNK_DURATION = 5.0      # Recording chunk size (seconds)
    SAMPLE_RATE = 16000       # Audio sample rate (Hz) - Azure requires 16kHz
    CHUNK_SIZE = 1024         # Audio buffer size
    MIN_AUDIO_LENGTH = 1000   # Min bytes to attempt transcription
```

### Logging
```python
class LogSettings:
    LOG_FILE = "transcriptions.log"  # Main log file (or from env var)
    DISPLAY_FILE = "transcription_display.txt"  # Live display file
    SHOW_INTERIM_RESULTS = True     # Show partial transcriptions
```

### Azure Speech Service
```python
class AzureSpeechService:
    # Language: "auto", "en-US", "ru-RU", "tr-TR", or any supported language code
    SPEECH_LANGUAGE = "auto"
    # For auto-detection, specify candidate languages
    CANDIDATE_LANGUAGES = ["en-US", "ru-RU", "tr-TR"]
    
    ENABLE_DIARIZATION = True   # Enable speaker identification
    MIN_SPEAKERS = 2            # Minimum expected speakers
    MAX_SPEAKERS = 10           # Maximum expected speakers
```

## Output Files

### `transcriptions.log` (or custom path)
**Format**: Plain text with timestamps
```
[2025-10-09 21:43:30] [🎤 MICROPHONE] Hello, this is a test.
[2025-10-09 21:43:35] [🔊 SYSTEM_AUDIO] Audio from system output.
```

**Customization**:
- Set via environment variable: `TRANSCRIPTION_LOG_FILE=/path/to/custom.log`
- Or modify `config.py`: `LOG_FILE = "my_custom.log"`

**Console Output**: 
Rich formatted output is displayed in the console with colors and emojis, while the log file contains plain text for easy parsing and analysis.

## Interim Results

When `SHOW_INTERIM_RESULTS = True`:
- **Interim results**: Show in console as you speak (yellow, single line)
- **Final results**: Logged to file when phrase completes (green, formatted)

**Benefits**:
- See transcription in real-time (no waiting for phrase to end)
- Only final results written to log file (cleaner logs)

To disable: Set `SHOW_INTERIM_RESULTS = False` in `config.py`

## Usage Examples

### Default Configuration
```bash
# Uses transcriptions.log in current directory
python main.py
```

### Custom Log File
```bash
# Set environment variable
export TRANSCRIPTION_LOG_FILE=/Users/me/meeting_logs/session1.log
python main.py
```

Or add to `.env`:
```bash
TRANSCRIPTION_LOG_FILE=/Users/me/meeting_logs/session1.log
```

### Disable Interim Results
Edit `config.py`:
```python
class LogSettings:
    SHOW_INTERIM_RESULTS = False  # Only show final results
```

## Monitoring Transcriptions

### View live log file
```bash
tail -f transcriptions.log
```

### Search for specific speaker
```bash
grep "MICROPHONE" transcriptions.log
grep "SYSTEM_AUDIO" transcriptions.log
```

### Filter by time period
```bash
grep "2025-10-09 21:4" transcriptions.log  # Filter by timestamp
```
