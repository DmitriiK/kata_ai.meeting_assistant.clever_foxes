# Hybrid Transcription System Setup Guide

## Overview

This meeting assistant uses a **hybrid approach** combining:
- **Local VAD (Voice Activity Detection)**: Detects when speech occurs (fast, free, privacy-preserving)
- **Azure Speech Service**: Cloud transcription with speaker diarization (accurate, identifies speakers)

This approach minimizes cloud costs by only sending audio when speech is detected, while providing high-quality transcription with speaker identification.

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
uv add azure-cognitiveservices-speech webrtcvad
```

## Configuration

Edit `config.py` to customize:

### VAD Settings
```python
class VADSettings:
    AGGRESSIVENESS = 2  # 0-3: higher = more aggressive filtering
    FRAME_DURATION_MS = 30  # 10, 20, or 30
    MIN_SPEECH_DURATION = 0.5  # Minimum speech length in seconds
```

### Azure Speech Settings
```python
class AzureSpeechService:
    ENABLE_DIARIZATION = True  # Speaker identification
    MIN_SPEAKERS = 2  # Expected minimum speakers
    MAX_SPEAKERS = 10  # Expected maximum speakers
```

## How It Works

### Workflow:
```
1. Audio Recording (5s chunks)
   ↓
2. VAD Detection (local, instant)
   ↓ (if speech detected)
3. Azure Speech Service (cloud transcription + diarization)
   ↓
4. Display with speaker labels
```

### Benefits:

**Cost Optimization:**
- VAD filters silence and noise locally
- Only actual speech sent to Azure
- Reduces Azure costs by 50-80%

**Accuracy:**
- Azure Speech Service > Local Whisper
- Real-time processing
- No missed speech at chunk boundaries

**Speaker Identification:**
- Distinguishes different speakers: "Speaker 1", "Speaker 2", etc.
- Helps identify who said what in meetings

## Usage

### Basic Usage (Automatic):
```bash
uv run python main.py
```

The app will:
1. Auto-detect your microphone and BlackHole (system audio)
2. Use VAD to detect speech
3. Send speech to Azure for transcription
4. Display results with speaker labels

### Expected Output:
```
🎯 TRANSCRIPTION RESULT 
💬 [Speaker 1] I think we should increase the budget
⏰ 2025-10-09 12:34:56 | 🎤 MICROPHONE

🎯 TRANSCRIPTION RESULT 
💬 [Speaker 2] That sounds good, let me check the numbers
⏰ 2025-10-09 12:34:59 | 🔊 SYSTEM_AUDIO
```

## Testing

### Test Azure Connection:
```python
# test_azure_speech.py
from azure_speech_service import AzureSpeechTranscriber

transcriber = AzureSpeechTranscriber()
print("✅ Azure Speech Service connected!")
```

### Test VAD:
```python
# test_vad.py
from vad_detector import VADDetector

vad = VADDetector()
# Record some audio and test
# vad.detect_speech_in_chunk(audio_bytes)
```

## Troubleshooting

### "AZURE_SPEECH_SERVICE_KEY not set"
- Check your `.env` file
- Ensure the key is correct
- Restart the app after adding the key

### No speaker diarization
- Ensure `ENABLE_DIARIZATION = True` in config
- Speaker diarization requires Azure Speech Service (not available in free tier with all features)
- Check Azure Speech Service pricing for diarization support

### High Azure costs
- Increase `VADSettings.AGGRESSIVENESS` to filter more non-speech
- Increase `MIN_SPEECH_DURATION` to ignore very short sounds
- Monitor usage in Azure Portal

### VAD too sensitive/not sensitive enough
- Adjust `AGGRESSIVENESS`:
  - 0: Most sensitive (captures more, may include noise)
  - 3: Least sensitive (only clear speech)

## Fallback Mode

If Azure credentials are not set, the app automatically falls back to local Whisper transcription (no speaker diarization, but still works offline).

## Cost Estimation

**Azure Speech Service Pricing (as of 2025):**
- Standard: ~$1/hour of audio
- With VAD filtering: ~$0.30-$0.50/hour (typical meeting)

**Example:**
- 1-hour meeting with 40% actual speech
- Cost: ~$0.40

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
- Review VAD settings in `config.py`
