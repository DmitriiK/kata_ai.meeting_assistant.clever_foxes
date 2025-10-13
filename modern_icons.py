"""
Modern Icon Set for Meeting Assistant
Professional SVG icons for EPAM-inspired UI
"""

# SVG Icons as data URIs
ICONS = {
    # Navigation and Controls
    'play': """data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' viewBox='0 0 16 16' fill='none'%3E%3Cpath d='M3 2l10 6-10 6V2z' fill='%23ffffff'/%3E%3C/svg%3E""",
    'pause': """data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' viewBox='0 0 16 16' fill='none'%3E%3Crect x='3' y='2' width='3' height='12' fill='%23ffffff'/%3E%3Crect x='10' y='2' width='3' height='12' fill='%23ffffff'/%3E%3C/svg%3E""",
    'microphone': """data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' viewBox='0 0 16 16' fill='none'%3E%3Crect x='6' y='2' width='4' height='8' rx='2' fill='%23666666'/%3E%3Cpath d='M4 8v1a4 4 0 0 0 8 0V8' stroke='%23666666' stroke-width='1.5' fill='none'/%3E%3Cpath d='M8 12v2' stroke='%23666666' stroke-width='1.5'/%3E%3Cpath d='M6 14h4' stroke='%23666666' stroke-width='1.5'/%3E%3C/svg%3E""",
    'speaker': """data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' viewBox='0 0 16 16' fill='none'%3E%3Cpath d='M8 3v10l-3-2H3V5h2l3-2z' fill='%23666666'/%3E%3Cpath d='M10 5.5a2 2 0 0 1 0 5M12 3.5a4 4 0 0 1 0 9' stroke='%23666666' stroke-width='1.5' fill='none'/%3E%3C/svg%3E""",
    'settings': """data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' viewBox='0 0 16 16' fill='none'%3E%3Ccircle cx='8' cy='8' r='2' fill='%23666666'/%3E%3Cpath d='M6.5 1h3v2.5h-3zM6.5 12.5h3V15h-3zM1 6.5h2.5v3H1zM12.5 6.5H15v3h-2.5z' fill='%23666666'/%3E%3C/svg%3E""",
    'translate': """data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' viewBox='0 0 16 16' fill='none'%3E%3Cpath d='M1 4h6M4 1v3M8 1l3 7h-1l-.5-1.5h-3L6 8H5l3-7zM9.5 5.5h1' stroke='%230066CC' stroke-width='1.5' fill='none'/%3E%3Cpath d='M12 9v6M9 12h6' stroke='%230066CC' stroke-width='1.5'/%3E%3C/svg%3E""",
    'chat': """data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' viewBox='0 0 16 16' fill='none'%3E%3Cpath d='M2 2h12a1 1 0 0 1 1 1v8a1 1 0 0 1-1 1H6l-3 3V3a1 1 0 0 1 1-1z' stroke='%23666666' stroke-width='1.5' fill='%23f8f9fa'/%3E%3Ccircle cx='5' cy='7' r='0.5' fill='%23666666'/%3E%3Ccircle cx='8' cy='7' r='0.5' fill='%23666666'/%3E%3Ccircle cx='11' cy='7' r='0.5' fill='%23666666'/%3E%3C/svg%3E""",
    'insights': """data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' viewBox='0 0 16 16' fill='none'%3E%3Cpath d='M8 1l2 5h5l-4 3 1.5 5L8 11l-4.5 3L5 9l-4-3h5L8 1z' fill='%23FFD700' stroke='%23FFA000' stroke-width='0.5'/%3E%3C/svg%3E""",
    'document': """data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' viewBox='0 0 16 16' fill='none'%3E%3Cpath d='M3 1h7l3 3v11H3V1z' fill='%23ffffff' stroke='%23666666' stroke-width='1.5'/%3E%3Cpath d='M10 1v3h3' stroke='%23666666' stroke-width='1.5' fill='none'/%3E%3Cpath d='M5 7h6M5 9h6M5 11h4' stroke='%23666666' stroke-width='1'/%3E%3C/svg%3E""",
    'calendar': """data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' viewBox='0 0 16 16' fill='none'%3E%3Crect x='2' y='3' width='12' height='11' rx='1' fill='%23ffffff' stroke='%23666666' stroke-width='1.5'/%3E%3Cpath d='M5 1v4M11 1v4M2 6h12' stroke='%23666666' stroke-width='1.5'/%3E%3Ccircle cx='6' cy='9' r='0.5' fill='%230066CC'/%3E%3Ccircle cx='8' cy='9' r='0.5' fill='%23666666'/%3E%3Ccircle cx='10' cy='9' r='0.5' fill='%23666666'/%3E%3C/svg%3E""",
    'live': """data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' viewBox='0 0 16 16' fill='none'%3E%3Ccircle cx='8' cy='8' r='3' fill='%23FF0000'/%3E%3Ccircle cx='8' cy='8' r='5' stroke='%23FF0000' stroke-width='1' fill='none' opacity='0.5'/%3E%3Ccircle cx='8' cy='8' r='7' stroke='%23FF0000' stroke-width='0.5' fill='none' opacity='0.3'/%3E%3C/svg%3E""",
    'check': """data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' viewBox='0 0 16 16' fill='none'%3E%3Cpath d='M13 4L6 11l-3-3' stroke='%234CAF50' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'/%3E%3C/svg%3E""",
    'warning': """data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' viewBox='0 0 16 16' fill='none'%3E%3Cpath d='M8 1l7 13H1L8 1z' fill='%23FFA726' stroke='%23FF8F00' stroke-width='1'/%3E%3Cpath d='M8 6v3' stroke='%23ffffff' stroke-width='1.5' stroke-linecap='round'/%3E%3Ccircle cx='8' cy='11' r='0.5' fill='%23ffffff'/%3E%3C/svg%3E""",
    'timer': """data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' viewBox='0 0 16 16' fill='none'%3E%3Ccircle cx='8' cy='9' r='6' fill='%23ffffff' stroke='%230066CC' stroke-width='1.5'/%3E%3Cpath d='M8 5v4l2 2' stroke='%230066CC' stroke-width='1.5' stroke-linecap='round'/%3E%3Crect x='6' y='1' width='4' height='1.5' rx='0.5' fill='%230066CC'/%3E%3C/svg%3E""",
}

# Emoji to Icon mapping for consistent modern look
EMOJI_TO_ICON = {
    '🎤': ICONS['microphone'],
    '🔊': ICONS['speaker'], 
    '🌍': ICONS['translate'],
    '💬': ICONS['chat'],
    '🤖': ICONS['insights'],
    '📝': ICONS['document'],
    '📁': ICONS['calendar'],
    '🔴': ICONS['live'],
    '✅': ICONS['check'],
    '⚠️': ICONS['warning'],
    '⏱️': ICONS['timer'],
    '▶': ICONS['play'],
    '⏸': ICONS['pause'],
}

def get_icon_path(icon_name):
    """Get the data URI for an icon"""
    return ICONS.get(icon_name, '')

def replace_emoji_with_icon(text):
    """Replace common emojis with professional SVG icons in text"""
    for emoji, icon_uri in EMOJI_TO_ICON.items():
        if emoji in text:
            # For now, just remove emoji - proper SVG integration would need QSvgWidget
            text = text.replace(emoji, '')
    return text.strip()

# Modern button text without emojis - more professional
MODERN_BUTTON_TEXT = {
    'start_transcription': 'Start Transcription',
    'stop_transcription': 'Stop Transcription', 
    'clear_final': 'Clear Final',
    'speak_to_mic': 'Speak to Mic',
    'stop_speaking': 'Stop Speaking',
    'ask': 'Ask',
    'clear': 'Clear',
    'all_sessions': 'All Sessions',
    'live_session': 'LIVE Session',
}

# Professional section headers without emojis
MODERN_HEADERS = {
    'transcription_tab': 'Transcription',
    'insights_tab': 'AI Insights', 
    'speech_translation': 'Speech to Text Translation',
    'tts_translation': 'Text to Speech Translation',
    'private_chat': 'Private AI Chat',
    'interim_results': 'Interim Results (Live Transcription)',
    'final_results': 'Final Results (Confirmed Transcriptions)', 
    'translation_results': 'Translation Results',
    'key_points': 'Key Points',
    'decisions': 'Decisions',
    'action_items': 'Action Items',
    'follow_up_questions': 'Follow-up Questions',
    'past_sessions': 'Past Sessions',
}

# Chat button text - professional and clean
MODERN_CHAT_BUTTONS = {
    'last_said': 'Last Said',
    'who_spoke': 'Who Spoke',
    'action_items': 'Action Items', 
    'main_topic': 'Main Topic',
    'concerns': 'Concerns',
    'next_steps': 'Next Steps',
    'decisions': 'Decisions',
}