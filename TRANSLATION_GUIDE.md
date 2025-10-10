# Translation Feature Guide

## Overview
The Meeting Transcription Assistant now includes real-time LLM-powered translation using Azure OpenAI.

## Features

### 1. Translation Checkbox
- **Location**: Below the main control buttons
- **Default**: Unchecked (translation disabled)
- **Action**: Check to enable translation

### 2. Language Selector
- **Languages**: English, Russian, Turkish
- **Enabled**: Only when translation checkbox is checked
- **Function**: Select target language for translation

### 3. Translation Window
- **Appearance**: Blue background (below Final Results)
- **Visibility**: Hidden by default, shows when translation is enabled
- **Content**: Translated versions of final transcriptions

## How It Works

1. **Transcription** → Original speech is transcribed with speaker diarization
2. **Queue** → Final transcriptions are added to translation queue
3. **Background Thread** → Separate worker thread processes translations
4. **LLM Translation** → Azure OpenAI translates text using custom prompts
5. **Display** → Translations appear in dedicated window with timestamps

## Technical Details

### Architecture
- **Non-blocking**: Translation runs in separate thread
- **Queue-based**: Uses Python `Queue` for thread-safe communication
- **LLM-powered**: Uses `llm_service.py` with Azure OpenAI
- **Prompt-driven**: Translation prompts in `prompts.py`

### Files Modified
- `gui_app.py` - Added translation UI and worker thread
- `prompts.py` - Translation prompt templates (NEW)

### Translation Workflow
```
Transcription Result
       ↓
  [Translation Queue]
       ↓
[Background Worker Thread]
       ↓
   Azure OpenAI LLM
       ↓
[Translation Window Display]
```

## Important Notes

✅ **Translations are NOT logged** - Only original transcriptions go to `transcriptions.log`

✅ **Real-time processing** - Translations appear shortly after transcription completes

✅ **Non-blocking** - Translation doesn't affect transcription performance

⚠️ **LLM Latency** - Translation may take 1-3 seconds depending on text length

⚠️ **API Costs** - Each translation uses Azure OpenAI tokens

## Usage Example

1. Start the application: `python gui_app.py`
2. Click "▶ Start Transcription"
3. Check "Enable Translation"
4. Select target language (e.g., "English" if speaking Russian)
5. Speak - see original in green window, translation in blue window

## Prompts

Translation prompts are defined in `prompts.py`:
- Clear instruction: "Translate to [Language]"
- Minimal output: Only translation, no explanations
- Customizable: Easy to modify prompt style

## Future Enhancements

Potential additions:
- Multiple target languages simultaneously
- Translation quality toggle (speed vs accuracy)
- Custom prompt templates
- Translation history export
- Summary generation
