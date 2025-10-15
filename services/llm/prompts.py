"""
Prompts for LLM-based translation and other text processing tasks.
"""


def get_translation_prompt(text: str, target_language: str) -> str:
    """
    Generate a translation prompt for the LLM.
    
    Args:
        text: Text to translate
        target_language: Target language name (e.g., "English", "Russian", "Turkish")
    
    Returns:
        Formatted prompt for translation
    """
    language_codes = {
        "English": "en-US",
        "Russian": "ru-RU",
        "Turkish": "tr-TR"
    }
    
    prompt = f"""Translate the following text to {target_language}. 
Provide ONLY the translation without any explanations, notes, or additional text.

Text to translate:
{text}

Translation:"""
    
    return prompt


def get_summary_prompt(text: str) -> str:
    """
    Generate a summary prompt for the LLM.
    
    Args:
        text: Text to summarize
    
    Returns:
        Formatted prompt for summarization
    """
    prompt = f"""Summarize the following conversation transcript concisely:

{text}

Summary:"""
    
    return prompt


# ===== PRIVATE CHAT PROMPTS =====

def get_chat_prompt(question_type: str, custom_question: str, transcript_context: str) -> str:
    """
    Generate context-aware prompt for private chat questions.
    
    Args:
        question_type: Type of question (last_said, who_spoke, action_items, etc.)
        custom_question: Custom question text (if question_type is "custom")
        transcript_context: Recent meeting transcript for context
    
    Returns:
        Formatted prompt for chat question
    """
    base_prompt = f"""You are an AI assistant helping with a live meeting. 

RECENT MEETING TRANSCRIPT:
{transcript_context}

"""
    
    if question_type == "last_said":
        prompt = base_prompt + """Based on the transcript above, what was the last thing discussed in the meeting? 
Provide a concise 1-2 sentence answer."""
    
    elif question_type == "who_spoke":
        prompt = base_prompt + """Who last spoke and what did they say? 
Be specific about the speaker label (e.g., MIC, SYSTEM, Speaker 1) and quote their exact words."""
    
    elif question_type == "action_items":
        prompt = base_prompt + """What action items or tasks were mentioned in the recent transcript?
List them clearly and concisely."""
    
    elif question_type == "main_topic":
        prompt = base_prompt + """What is the main topic or theme being discussed?
Provide a brief summary of the conversation focus."""
    
    elif question_type == "concerns":
        prompt = base_prompt + """What concerns, problems, or issues were raised in the discussion?
List them clearly."""
    
    elif question_type == "next_steps":
        prompt = base_prompt + """What are the next steps or future plans mentioned?
List them in order if possible."""
    
    elif question_type == "decisions":
        prompt = base_prompt + """What decisions or conclusions were made during this discussion?
Be specific about what was decided."""
    
    elif question_type == "custom":
        prompt = base_prompt + f"""Answer the following question based on the meeting transcript:

Question: {custom_question}

Provide a clear, concise answer based on the transcript above."""
    
    else:
        # Fallback for unknown question types
        prompt = base_prompt + f"""Answer the following question based on the meeting transcript:

Question: {custom_question}

Provide a clear, concise answer."""
    
    return prompt


# Common questions mapping
COMMON_CHAT_QUESTIONS = {
    "last_said": "What was the last thing discussed?",
    "who_spoke": "Who last spoke and what did they say?",
    "action_items": "What action items were mentioned?",
    "main_topic": "What is the main topic?",
    "concerns": "What concerns were raised?",
    "next_steps": "What are the next steps?",
    "decisions": "What decisions were made?"
}