# Simple Audio Transcription App

A simple Python application that captures audio from your microphone, transcribes it using OpenAI's Whisper speech-to-text model, and logs the results to both console and file.

## Features

- 🎤 Real-time microphone audio capture using PyAudio
- 🤖 Speech-to-text transcription using Whisper (runs locally)
- 📝 Logs transcriptions to console with timestamps and emojis
- 📁 Saves all transcriptions to `transcriptions.log` file
- 🔄 Two modes: continuous chunked recording or single recording
- 🚫 No temporary audio files created - everything works in memory

## Quick Start

1. **Install dependencies** (already done with uv):
   ```bash
   uv sync
   ```

2. **Run the application**:
   ```bash
   python main.py
   ```

3. **Choose your mode**:
   - **Continuous mode**: Records in 5-second chunks, transcribes each chunk
   - **Single mode**: Records for 10 seconds, transcribes once

4. **Speak into your microphone** and watch the transcriptions appear!

5. **Stop anytime** by pressing `Ctrl+C`

## How It Works

The application consists of four main components:

- **AudioRecorder** (`audio_recorder.py`): Captures audio from microphone using PyAudio
- **TranscriptionService** (`transcription_service.py`): Uses Whisper to convert audio to text
- **TranscriptionLogger** (`transcription_logger.py`): Handles logging to console and file
- **Main App** (`main.py`): Ties everything together with a simple interface

## Requirements

- Python 3.10+
- Working microphone
- The app will automatically download the Whisper model on first run

## Output

- **Console**: Real-time transcription results with timestamps and status emojis
- **File**: All transcriptions are saved to `transcriptions.log` with timestamps

## Simple Architecture

The design is intentionally simple and straightforward:
- No complex streaming protocols
- No external API dependencies (Whisper runs locally)
- Minimal error handling for clarity
- Easy to understand and modify