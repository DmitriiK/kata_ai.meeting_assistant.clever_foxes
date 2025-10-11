# Real-Time Insights File Saving Feature

## Overview
The AI Meeting Assistant now saves real-time insights to individual text files in the session folder, in addition to displaying them in the console and saving them to the comprehensive JSON/Markdown summaries.

## New Files Created
When running a meeting session, the following additional files are now created in the session folder:

- `follow-up-questions.txt` - AI-generated follow-up questions and prompts
- `key-points.txt` - Summarized key points and important topics
- `decisions.txt` - Recorded decisions and conclusions
- `action-items.txt` - Identified action items and tasks

## File Format
Each file uses a timestamp-based format for easy tracking:

```
=== 2025-10-11 00:28:13 ===
1. What are the next steps for the project?
2. Who will be responsible for implementation?
3. When is the deadline for completion?

=== 2025-10-11 00:28:15 ===
1. How can we improve user experience?
```

## Benefits
1. **Real-time access** - View insights as they are generated during the meeting
2. **Organized storage** - Separate files for different types of insights
3. **Easy review** - Simple text format for quick scanning
4. **Historical tracking** - Timestamps show when insights were generated
5. **Complementary** - Works alongside existing JSON and Markdown summaries

## Implementation Details
- Files are created only when insights are generated
- Content is appended with timestamps for chronological tracking
- Files are saved in the session-specific folder (e.g., `sessions/session_20251011_002813/`)
- No changes to existing console output or summary functionality
- Gracefully handles errors without affecting main functionality

## Usage
The feature is automatically enabled and requires no additional configuration. Simply run your meeting assistant as usual:

```bash
python main.py
```

During the meeting, as AI insights are generated and displayed in the console, they will also be automatically saved to the individual text files in the current session folder.

## Example Session Folder Structure
```
sessions/session_20251011_002813/
├── action-items.txt
├── decisions.txt
├── follow-up-questions.txt
├── key-points.txt
├── meeting_summary_20251011_002813.json
└── meeting_summary_20251011_002813.md
```