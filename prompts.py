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
