#!/bin/bash
# Watch transcriptions log file in real-time
# Usage: ./watch_transcriptions.sh

echo "📝 Monitoring transcriptions.log in real-time..."
echo "Press Ctrl+C to stop"
echo ""
echo "Current file size: $(wc -l transcriptions.log | awk '{print $1}') lines"
echo ""
echo "==================== LATEST ENTRIES ===================="
tail -5 transcriptions.log
echo "========================================================"
echo ""
echo "Watching for new entries..."
tail -f transcriptions.log
