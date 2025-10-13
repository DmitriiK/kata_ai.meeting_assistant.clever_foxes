#!/usr/bin/env python3
"""
Script to replace emoji characters with ASCII text in Python files
to avoid encoding issues on Windows with cp1252
"""

import os
import re
import glob

# Mapping of emoji to text replacements
EMOJI_REPLACEMENTS = {
    '✅': '[OK]',
    '⚠️': '[WARNING]',
    '🔊': '[AUDIO]',
    '🎤': '[MIC]',
    '🎧': '[HEADPHONES]',
    '💬': '[CHAT]',
    '📝': '[NOTE]',
    '🔴': '[RED]',
    '🟢': '[GREEN]',
    '🎵': '[MUSIC]',
    '🛑': '[STOP]',
    '❌': '[ERROR]',
    '⏹️': '[STOP]',
    '🎶': '[MUSIC]',
    '📊': '[CHART]',
    '🔍': '[SEARCH]',
    '📂': '[FOLDER]',
    '📄': '[FILE]',
    '⭐': '[STAR]',
    '🚀': '[ROCKET]',
    '💡': '[IDEA]',
    '🔥': '[FIRE]',
    '🏆': '[TROPHY]',
    '🎯': '[TARGET]',
    '📈': '[GRAPH]',
    '🔧': '[TOOL]',
    '⚡': '[LIGHTNING]',
    '🌟': '[STAR]',
    '🔔': '[BELL]',
    '📱': '[PHONE]',
    '💻': '[COMPUTER]',
    '🖥️': '[DESKTOP]',
    '⌚': '[WATCH]',
    '📡': '[SATELLITE]',
    '🌐': '[GLOBE]',
    '🔐': '[LOCK]',
    '🗝️': '[KEY]',
    '🎪': '[CIRCUS]',
    '🎨': '[ART]'
}

def fix_emojis_in_file(filepath):
    """Fix emoji characters in a single file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Replace each emoji
        for emoji, replacement in EMOJI_REPLACEMENTS.items():
            content = content.replace(emoji, replacement)
        
        # If content changed, write it back
        if content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Fixed emojis in: {filepath}")
            return True
        
    except Exception as e:
        print(f"Error processing {filepath}: {e}")
        return False
    
    return False

def main():
    """Main function to fix emojis in all Python files"""
    python_files = glob.glob('*.py')
    
    fixed_count = 0
    for filepath in python_files:
        if fix_emojis_in_file(filepath):
            fixed_count += 1
    
    print(f"\nProcessed {len(python_files)} files, fixed {fixed_count} files")

if __name__ == "__main__":
    main()