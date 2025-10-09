# Streaming Transcription System Setup Guide

## Overview

This meeting assistant uses **Azure Speech Service streaming recognition** for:
- **Real-time transcription**: No delays, transcribes as you speak
- **Multi-language support**: Auto-detects English, Russian, Turkish
- **Dual audio sources**: Captures both microphone and system audio
- **Language detection**: Automatically identifies and switches between languages

## Prerequisites

### 1. Azure Speech Service Setup

1. **Create Azure Speech Service:**
   - Go to [Azure Portal](https://portal.azure.com)
   - Create a new "Speech" resource
   - Note your **API Key** and **Region**

2. **Add to `.env` file:**
   ```env
   AZURE_SPEECH_SERVICE_KEY=your_azure_speech_key_here
   AZURE_SPEECH_SERVICE_REGION=your_region_here  # e.g., "westus"
   ```

### 2. Install Dependencies

Already installed:
```bash
uv add azure-cognitiveservices-speech
```

## Configuration

Edit `config.py` to customize:

### Azure Speech Settings
```python
class AzureSpeechService:
    SPEECH_LANGUAGE = "auto"  # Auto-detect or "en-US", "ru-RU", "tr-TR"
    CANDIDATE_LANGUAGES = ["en-US", "ru-RU", "tr-TR"]
```

## How It Works

### Workflow:
```
1. Continuous Audio Streaming
   ↓
2. Azure Speech Service (cloud, real-time)
   ↓
3. Language Detection (automatic)
   ↓
4. Display with source labels (mic/system audio)
```

### Benefits:

**Real-Time Transcription:**
- Azure has built-in silence detection
- Immediate transcription as you speak
- No chunking delays

**Accuracy:**
- Azure Speech Service handles multiple languages
- Automatically switches between languages
- High-quality transcription

**Source Identification:**
- 🎤 MICROPHONE - Your voice
- 🔊 SYSTEM_AUDIO - Other participants (from meetings)

## Usage

### Basic Usage (Automatic):
```bash
uv run python main.py
```

The app will:
1. Auto-detect your microphone and BlackHole (system audio)
2. Stream audio directly to Azure Speech Service
3. Display interim results as you speak (yellow text)
4. Show final transcriptions (green boxes)
5. Log language changes automatically

### Expected Output:
```
⚡ [INTERIM] [� MICROPHONE] I think we should...
⚡ [INTERIM] [🎤 MICROPHONE] I think we should increase the budget

🌍 Language detected: 🇺🇸 English [🎤 MICROPHONE]

�🎯 TRANSCRIPTION RESULT 
💬 I think we should increase the budget
⏰ 2025-10-09 12:34:56 | 🎤 🎤 MICROPHONE

🎯 TRANSCRIPTION RESULT 
💬 That sounds good, let me check the numbers
⏰ 2025-10-09 12:34:59 | 🎤 🔊 SYSTEM_AUDIO
```

## Testing

### Test Azure Connection:
```python
# test_azure_speech.py
from azure_speech_service import AzureSpeechTranscriber

transcriber = AzureSpeechTranscriber()
print("✅ Azure Speech Service connected!")
```

## Troubleshooting

### "AZURE_SPEECH_SERVICE_KEY not set"
- Check your `.env` file
- Ensure the key is correct
- Restart the app after adding the key

### Wrong language detected
- Set specific language in `.env`: `SPEECH_LANGUAGE=ru-RU`
- Or adjust `CANDIDATE_LANGUAGES` in `config.py`

### Delayed transcription
- Azure has built-in silence detection
- Transcription appears when you pause/finish sentence
- Interim results show real-time progress

### High Azure costs
- Monitor usage in Azure Portal
- Consider using specific language instead of auto-detection
- Azure charges per minute of audio processed

## Cost Estimation

**Azure Speech Service Pricing (as of 2025):**
- Standard: ~$1/hour of audio transcribed
- Streaming recognition charges per minute processed

**Example:**
- 1-hour meeting
- Cost: ~$1.00

## Next Steps

After setup:
1. Test with a YouTube video
2. Try a quick Zoom/Teams call
3. Check transcription accuracy
4. Adjust VAD settings if needed
5. Monitor Azure costs in first week

## Support

For issues:
- Check `transcriptions.log` for errors
- Verify Azure credentials in `.env`
- Test internet connection for Azure API
- Review language settings in `config.py`
