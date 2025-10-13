"""
Private AI Chat Service

Handles chat logic, prompt generation, and history management for the
private AI chat feature that allows users to query meeting transcript context.
"""
import os
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
import prompts


class PrivateChatService:
    """Service for managing private AI chat with transcript context."""
    
    def __init__(self, max_context_chars: int = 3000):
        """
        Initialize the chat service.
        
        Args:
            max_context_chars: Maximum characters to include in transcript context
        """
        self.max_context_chars = max_context_chars
        self.chat_history_filename = "private-chat-history.txt"
    
    def get_question_text(self, question_type: str) -> str:
        """
        Get the question text for a common question type.
        
        Args:
            question_type: Type of question (e.g., 'last_said', 'who_spoke')
        
        Returns:
            Question text
        """
        return prompts.COMMON_CHAT_QUESTIONS.get(
            question_type, 
            "What is happening in the meeting?"
        )
    
    def get_transcript_context(self, conversation_history: List[Dict[str, Any]]) -> str:
        """
        Extract recent conversation context for AI analysis.
        
        Args:
            conversation_history: List of conversation entries from meeting assistant
        
        Returns:
            Formatted transcript context string
        """
        if not conversation_history:
            return "No conversation yet. The meeting is just starting or no speech has been detected."
        
        # Combine recent conversation
        context_parts = []
        char_count = 0
        
        # Start from most recent and work backwards
        for entry in reversed(conversation_history):
            text = entry.get('text', '')
            source = entry.get('source', 'UNKNOWN')
            timestamp = entry.get('timestamp', '')
            
            # Format: [timestamp] [source] text
            formatted = f"[{timestamp}] [{source}] {text}"
            
            if char_count + len(formatted) > self.max_context_chars:
                break
            
            context_parts.insert(0, formatted)
            char_count += len(formatted)
        
        if not context_parts:
            return "No recent conversation available."
        
        return "\n".join(context_parts)
    
    def generate_prompt(
        self, 
        question_type: str, 
        custom_question: str, 
        transcript_context: str
    ) -> str:
        """
        Generate a prompt for the chat question.
        
        Args:
            question_type: Type of question
            custom_question: Custom question text (used if question_type is "custom")
            transcript_context: Recent meeting transcript
        
        Returns:
            Formatted prompt string
        """
        return prompts.get_chat_prompt(question_type, custom_question, transcript_context)
    
    def save_to_history(
        self, 
        question: str, 
        answer: str, 
        question_type: str, 
        session_folder: str
    ):
        """
        Save question and answer to chat history file.
        
        Args:
            question: Question text
            answer: Answer text
            question_type: Type of question
            session_folder: Path to session folder
        """
        try:
            # Ensure session folder exists
            session_path = Path(session_folder)
            session_path.mkdir(parents=True, exist_ok=True)
            
            # Chat history file path
            history_file = session_path / self.chat_history_filename
            
            # Format entry
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            entry = f"""
============================================================
[{timestamp}] [{question_type}]
============================================================
Q: {question}

A: {answer}
"""
            
            # Append to file
            with open(history_file, 'a', encoding='utf-8') as f:
                f.write(entry)
            
            print(f"💾 Chat history saved: {question_type}")
            
        except Exception as e:
            print(f"⚠️ Warning: Could not save chat history: {e}")
    
    def load_history(self, session_folder: str) -> str:
        """
        Load chat history from file.
        
        Args:
            session_folder: Path to session folder
        
        Returns:
            Chat history content (empty string if file doesn't exist)
        """
        try:
            session_path = Path(session_folder)
            history_file = session_path / self.chat_history_filename
            
            if history_file.exists():
                with open(history_file, 'r', encoding='utf-8') as f:
                    return f.read()
            else:
                return ""
        
        except Exception as e:
            print(f"⚠️ Warning: Could not load chat history: {e}")
            return ""
    
    def clear_history(self, session_folder: str):
        """
        Clear chat history file for a session.
        
        Args:
            session_folder: Path to session folder
        """
        try:
            session_path = Path(session_folder)
            history_file = session_path / self.chat_history_filename
            
            if history_file.exists():
                history_file.unlink()
                print(f"🗑️ Chat history cleared for session")
        
        except Exception as e:
            print(f"⚠️ Warning: Could not clear chat history: {e}")

