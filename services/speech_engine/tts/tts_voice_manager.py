"""
TTS Voice Manager
Manages TTS voices from configuration file.
Parses tts_voices.yml and provides API to get voices by language code.
"""
import yaml
from pathlib import Path
from typing import Dict, Optional, List
from dataclasses import dataclass


@dataclass
class Voice:
    """Represents a TTS voice."""
    name: str
    sex: str
    language: str
    language_code: str


class TTSVoiceManager:
    """Manages TTS voices from YAML configuration."""
    
    def __init__(self, config_path: str = None):
        """
        Initialize voice manager.
        
        Args:
            config_path: Path to voices configuration file
        """
        if config_path is None:
            # Default to tts_voices.yml in the same directory as this file
            config_path = Path(__file__).parent / "tts_voices.yml"
        self.config_path = Path(config_path)
        self.voices: Dict[str, Dict[str, Voice]] = {}
        self._load_voices()
        
    def _load_voices(self):
        """Load voices from YAML configuration."""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                
            languages = config.get('languages', {})
            
            for lang_code, lang_data in languages.items():
                language_name = lang_data.get('language', lang_code)
                voices_data = lang_data.get('voices', {})
                
                self.voices[lang_code] = {}
                
                for voice_name, voice_info in voices_data.items():
                    self.voices[lang_code][voice_name] = Voice(
                        name=voice_name,
                        sex=voice_info.get('sex', 'unknown'),
                        language=language_name,
                        language_code=lang_code
                    )
                    
            print(f"✅ Loaded {len(self.voices)} language configurations")
            
        except Exception as e:
            print(f"⚠️ Error loading TTS voices: {e}")
            self.voices = {}
            
    def get_voice(self, language_code: str, sex: Optional[str] = None) -> Optional[Voice]:
        """
        Get voice for language and optional sex preference.
        
        Args:
            language_code: BCP-47 language code (e.g., "en-US")
            sex: Preferred voice sex ("male" or "female")
            
        Returns:
            Voice object or None if not found
        """
        if language_code not in self.voices:
            return None
            
        voices = self.voices[language_code]
        
        if not voices:
            return None
            
        # If sex preference specified, try to find matching voice
        if sex:
            for voice in voices.values():
                if voice.sex.lower() == sex.lower():
                    return voice
                    
        # Return first available voice
        return next(iter(voices.values()))
        
    def get_default_voice(self, language_code: str) -> Optional[Voice]:
        """
        Get default voice for language (first available).
        
        Args:
            language_code: BCP-47 language code
            
        Returns:
            Voice object or None
        """
        return self.get_voice(language_code)
        
    def get_available_languages(self) -> Dict[str, str]:
        """
        Get available languages.
        
        Returns:
            Dict mapping language codes to language names
        """
        result = {}
        for lang_code, voices in self.voices.items():
            if voices:
                # Get language name from first voice
                first_voice = next(iter(voices.values()))
                result[lang_code] = first_voice.language
        return result
        
    def list_voices(self, language_code: str) -> List[Voice]:
        """
        List all voices for a language.
        
        Args:
            language_code: BCP-47 language code
            
        Returns:
            List of Voice objects
        """
        if language_code not in self.voices:
            return []
        return list(self.voices[language_code].values())
    
    def get_language_code(self, language_name: str) -> Optional[str]:
        """
        Get language code from friendly language name.
        
        Args:
            language_name: Friendly name like "English", "Russian", "Turkish"
            
        Returns:
            Language code like "en-US" or None if not found
        """
        # Mapping of friendly names to language codes
        name_mapping = {
            "english": "en-US",
            "russian": "ru-RU",
            "turkish": "tr-TR"
        }
        
        language_lower = language_name.lower()
        return name_mapping.get(language_lower)


# Test module
if __name__ == "__main__":
    manager = TTSVoiceManager()
    
    print("\n📋 Available Languages:")
    for code, name in manager.get_available_languages().items():
        print(f"  {code}: {name}")
    
    print("\n🎤 English Voices:")
    for voice in manager.list_voices("en-US"):
        print(f"  {voice.name} ({voice.sex})")
    
    print("\n🔍 Get specific voice:")
    voice = manager.get_voice("ru-RU", sex="female")
    if voice:
        print(f"  Found: {voice.name} - {voice.language}")
