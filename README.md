# AI-Powered Meeting Assistant

An intelligent meeting assistant that combines real-time transcription with AI-powered insights to enhance meeting productivity and capture important information automatically.

## Features

### 🎤 Real-Time Transcription
- Real-time microphone and system audio capture using PyAudio
- Speech-to-text transcription using Azure Speech Service
- Support for multiple languages with auto-detection
- Streaming transcription with minimal delay

### 🤖 AI-Powered Meeting Intelligence
- **Smart Follow-up Questions**: Automatically suggests relevant questions to clarify or expand on topics
- **Key Points Extraction**: Identifies and highlights important information from conversations
- **Action Items Tracking**: Captures tasks, commitments, and assignments mentioned during meetings
- **Decision Recording**: Automatically identifies and logs decisions made during discussions
- **Meeting Summaries**: Generates comprehensive summaries with key outcomes and insights

### 📊 Advanced Meeting Management
- Session-based meeting tracking with timestamps
- Comprehensive meeting statistics and analytics
- Export summaries in JSON and Markdown formats
- Persistent storage of meeting history and insights
- Real-time meeting status and progress tracking

## Prerequisites

1. **Azure Services Setup**:
   - Azure Speech Service subscription (for real-time transcription)
   - Azure OpenAI Service subscription (for AI insights and analysis)

2. **Environment Configuration**:
   Create a `.env` file with your Azure credentials:
   ```env
   AZURE_SPEECH_SERVICE_KEY=your_speech_service_key
   AZURE_SPEECH_SERVICE_REGION=your_speech_region
   AZURE_OPENAI_ENDPOINT=your_openai_endpoint
   AZURE_OPENAI_API_KEY=your_openai_api_key
   ```

## Quick Start

1. **Install dependencies**:
   ```bash
   uv sync
   ```

2. **Configure your environment**:
   - Set up your `.env` file with Azure credentials (see Prerequisites)
   - Ensure your microphone is working
   - (Optional) Set up virtual audio device for system audio capture

3. **Run the AI Meeting Assistant**:
   ```bash
   python main.py
   ```

4. **Start your meeting**:
   - The application will automatically start a new meeting session
   - Speak into your microphone and watch real-time transcription
   - AI insights will appear automatically as the conversation progresses

5. **End the meeting**:
   - Press `Ctrl+C` to stop and generate a comprehensive meeting summary
   - Summary files will be saved in both JSON and Markdown formats

## How It Works

The AI Meeting Assistant consists of several intelligent components working together:

### Core Components

- **StreamingTranscriptionApp** (`main.py`): Main application orchestrating all services
- **AzureSpeechTranscriber** (`azure_speech_service.py`): Real-time speech-to-text using Azure Speech Service
- **MeetingAssistantService** (`meeting_assistant_service.py`): AI-powered analysis and insight generation
- **MeetingSummaryManager** (`summary_manager.py`): Session management and persistent storage
- **TranscriptionLogger** (`transcription_logger.py`): Enhanced logging with visual formatting
- **AudioRecorder** (`audio_recorder.py`): Multi-device audio capture management

### AI Analysis Pipeline

1. **Real-time Transcription**: Audio is continuously streamed to Azure Speech Service
2. **Context Building**: Recent conversation context is maintained for AI analysis
3. **Intelligent Analysis**: Azure OpenAI analyzes transcribed text to generate:
   - Relevant follow-up questions
   - Key points and important topics
   - Action items and assignments
   - Decisions and conclusions
4. **Session Management**: All insights are tracked and organized throughout the meeting
5. **Summary Generation**: Comprehensive meeting summaries are created automatically

### Smart Features

- **Contextual Understanding**: AI considers conversation flow and context
- **Real-time Insights**: Analysis happens as the conversation progresses
- **Duplicate Prevention**: Smart filtering to avoid repetitive suggestions
- **Session Persistence**: All meeting data is saved for future reference

## System Requirements

- Python 3.10+
- Working microphone (required)
- Azure Speech Service subscription (required)
- Azure OpenAI Service subscription (required)
- Virtual audio device (optional, for system audio capture)
- Stable internet connection (for Azure services)

## Output & Results

### Real-time Console Output
- **Live Transcription**: Real-time speech-to-text with source identification
- **AI Insights**: Contextual suggestions and analysis displayed as they're generated
- **Session Status**: Ongoing statistics and meeting progress indicators
- **Visual Formatting**: Color-coded output with emojis for easy reading

### Generated Files
- **Transcription Log**: `transcriptions.log` - All spoken text with timestamps
- **Meeting Summaries**: JSON format with comprehensive session data
- **Markdown Reports**: Human-readable meeting reports with organized sections
- **Session Data**: Persistent storage in `meeting_summaries/` directory

### Meeting Summary Contents
- Session information (duration, participants, timestamps)
- Complete conversation transcript
- AI-generated follow-up questions
- Extracted key points and topics
- Identified action items and assignments
- Recorded decisions and agreements
- Session statistics and analytics

## Configuration Options

### Audio Settings (`config.py`)
- `CHUNK_DURATION`: Audio processing chunk size
- `SAMPLE_RATE`: Audio sampling rate (16kHz recommended)
- `MIN_AUDIO_LENGTH`: Minimum audio length for processing

### AI Analysis Settings
- `min_text_length`: Minimum text length to trigger AI analysis
- `max_history_items`: Number of recent conversations to keep in context
- Language detection and multi-language support

### Output Settings
- `LOG_FILE`: Custom transcription log file path
- `SHOW_INTERIM_RESULTS`: Toggle partial transcription display
- Summary export formats and locations

## Architecture

The system uses a modern, cloud-integrated architecture:

- **Streaming Audio Processing**: Direct Azure Speech Service integration
- **AI-Powered Analysis**: Azure OpenAI for intelligent meeting insights
- **Session Management**: Persistent meeting tracking and organization
- **Real-time Processing**: Minimal latency for immediate feedback
- **Scalable Design**: Easily extensible for additional AI features

## Demo & Testing

### Try the Demo First

Before running a live meeting, try the interactive demo to see AI capabilities:

```bash
python demo.py
```

The demo simulates a realistic meeting conversation and demonstrates:
- Real-time AI analysis and insights
- Follow-up question generation
- Key points extraction
- Action items identification
- Decision tracking
- Meeting summary generation

### Run Tests

Verify functionality with the test suite:

```bash
python tests/test_llm_communicator.py
```

The tests cover:
- Azure OpenAI integration
- Meeting assistant service functionality
- Summary manager operations
- Session lifecycle management
- AI analysis pipeline

## Troubleshooting

### Common Issues

1. **Azure Connection Errors**: Verify your API keys and endpoints in `.env`
2. **Audio Device Not Found**: Check microphone permissions and device availability
3. **AI Analysis Not Working**: Ensure Azure OpenAI service is properly configured
4. **No System Audio**: Set up a virtual audio device for system sound capture

### Performance Tips

- Ensure stable internet connection for optimal Azure service performance
- Use a quality microphone for better transcription accuracy
- Close unnecessary applications to reduce audio interference
- Monitor token usage to manage Azure OpenAI costs