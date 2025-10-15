from openai import AzureOpenAI
import config as cfg
from typing import List, Dict, Optional
from datetime import datetime

# Initialize the AzureOpenAI client
client = AzureOpenAI(
    api_version=cfg.AzureOpenAI.OPENAI_API_VERSION,
    azure_endpoint=cfg.AzureOpenAI.AZURE_OPENAI_ENDPOINT,  # type: ignore
    api_key=cfg.AzureOpenAI.AZURE_OPENAI_API_KEY,
)


def list_models():
    """Get list of available models from Azure OpenAI."""
    try:
        models = client.models.list()
        model_names = [model.id for model in models.data]
        return model_names
    except Exception as e:
        print(f"Error listing models: {e}")
        # Return a default model if API call fails (for testing purposes)
        return [cfg.AzureOpenAI.MODEL_NAME]


def chat(message: str, max_tokens: int = 300, temperature: float = 0.7) -> str:
    """Send a message to the LLM and get a response (legacy function for backward compatibility)."""
    try:
        response = client.chat.completions.create(
            model=cfg.AzureOpenAI.MODEL_NAME,
            messages=[
                {"role": "system", "content": "You are a helpful AI meeting assistant. Provide concise, actionable responses that help improve meeting productivity and understanding."},
                {"role": "user", "content": message}
            ],
            max_tokens=max_tokens,
            temperature=temperature
        )
        
        content = response.choices[0].message.content
        return content.strip() if content else "No response"
    except Exception as e:
        print(f"Error in chat: {e}")
        return f"Error: {str(e)}"


class ChatMemoryManager:
    """Manages conversation memory for chat sessions."""
    
    def __init__(self, max_memory_turns: int = 10, max_memory_age_hours: int = 24):
        """
        Initialize the chat memory manager.
        
        Args:
            max_memory_turns: Maximum number of conversation turns to keep in memory
            max_memory_age_hours: Maximum age of memory in hours before cleanup
        """
        self.max_memory_turns = max_memory_turns
        self.max_memory_age_hours = max_memory_age_hours
        self.conversation_memory: List[Dict[str, any]] = []
        self.session_start_time = datetime.now()
    
    def add_message(self, role: str, content: str, metadata: Optional[Dict] = None):
        """
        Add a message to conversation memory.
        
        Args:
            role: Message role ('user', 'assistant', 'system')
            content: Message content
            metadata: Optional metadata (timestamp, question_type, etc.)
        """
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now(),
            "metadata": metadata or {}
        }
        self.conversation_memory.append(message)
        
        # Cleanup old messages if needed
        self._cleanup_memory()
    
    def get_memory_context(self, include_system: bool = True) -> List[Dict[str, str]]:
        """
        Get conversation memory formatted for API calls.
        
        Args:
            include_system: Whether to include system messages
            
        Returns:
            List of messages formatted for OpenAI API
        """
        # Get recent messages within memory limit
        recent_messages = self.conversation_memory[-self.max_memory_turns:]
        
        # Format for API
        api_messages = []
        for msg in recent_messages:
            if not include_system and msg["role"] == "system":
                continue
            api_messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })
        
        return api_messages
    
    def _cleanup_memory(self):
        """Clean up old messages based on age and count limits."""
        now = datetime.now()
        
        # Remove messages older than max age
        self.conversation_memory = [
            msg for msg in self.conversation_memory
            if (now - msg["timestamp"]).total_seconds() < (self.max_memory_age_hours * 3600)
        ]
        
        # Keep only recent messages within turn limit
        if len(self.conversation_memory) > self.max_memory_turns:
            self.conversation_memory = self.conversation_memory[-self.max_memory_turns:]
    
    def clear_memory(self):
        """Clear all conversation memory."""
        self.conversation_memory.clear()
        self.session_start_time = datetime.now()
    
    def get_memory_stats(self) -> Dict[str, any]:
        """Get statistics about current memory usage."""
        return {
            "total_messages": len(self.conversation_memory),
            "session_duration_minutes": (datetime.now() - self.session_start_time).total_seconds() / 60,
            "memory_age_hours": self.max_memory_age_hours,
            "max_turns": self.max_memory_turns
        }


def chat_with_memory(
    user_message: str, 
    memory_manager: ChatMemoryManager,
    system_context: Optional[str] = None,
    max_tokens: int = 400, 
    temperature: float = 0.7,
    question_type: Optional[str] = None
) -> str:
    """
    Send a message to the LLM with conversation memory and get a response.
    
    Args:
        user_message: User's message
        memory_manager: ChatMemoryManager instance
        system_context: Optional system context to prepend
        max_tokens: Maximum tokens for response
        temperature: Response temperature
        question_type: Type of question for metadata
    
    Returns:
        LLM response string
    """
    try:
        # Build messages list
        messages = []
        
        # Add system context if provided
        if system_context:
            messages.append({"role": "system", "content": system_context})
        
        # Add conversation memory
        memory_messages = memory_manager.get_memory_context(include_system=False)
        messages.extend(memory_messages)
        
        # Add current user message
        messages.append({"role": "user", "content": user_message})
        
        # Make API call
        response = client.chat.completions.create(
            model=cfg.AzureOpenAI.MODEL_NAME,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature
        )
        
        content = response.choices[0].message.content
        response_text = content.strip() if content else "No response"
        
        # Add to memory
        memory_manager.add_message("user", user_message, {"question_type": question_type})
        memory_manager.add_message("assistant", response_text, {"question_type": question_type})
        
        return response_text
        
    except Exception as e:
        error_msg = f"Error in chat_with_memory: {e}"
        print(error_msg)
        return f"Error: {str(e)}"

