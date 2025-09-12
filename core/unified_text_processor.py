"""
Unified Text Processing System
Consolidates all text processing logic from app.py, global_stt.py, and text_processor.py
"""

import re
from typing import Optional, Callable, Any
from datetime import datetime
from .config import get_config


class UnifiedTextProcessor:
    """
    Unified text processor that handles:
    1. Voice command processing  
    2. Text formatting and enhancement
    3. Real-time text preprocessing
    4. Final sentence processing
    """
    
    def __init__(self, voice_command_callback: Optional[Callable] = None):
        self.config = get_config()
        self.voice_command_callback = voice_command_callback
        
        # Load processors
        self._load_voice_processor()
        self._load_text_processor()
        
    def _load_voice_processor(self):
        """Load voice command processor"""
        try:
            from voice_commands import VoiceCommandProcessor
            self.voice_processor = VoiceCommandProcessor()
        except ImportError:
            print("Warning: VoiceCommandProcessor not available")
            self.voice_processor = None
    
    def _load_text_processor(self):
        """Load advanced text processor"""
        try:
            from text_processor import TextProcessor
            self.text_processor = TextProcessor()
        except ImportError:
            print("Warning: TextProcessor not available")
            self.text_processor = None
    
    def preprocess_realtime_text(self, text: str) -> str:
        """
        Preprocess real-time text for display and typing.
        Consolidated from app.py:175 and global_stt.py:629
        """
        if not text:
            return text
        
        # Remove leading whitespaces
        text = text.lstrip()
        
        # Remove starting ellipses if present
        if text.startswith("..."):
            text = text[3:]
        
        # Remove any leading whitespaces again after ellipses removal
        text = text.lstrip()
        
        # Uppercase the first letter
        if text:
            text = text[0].upper() + text[1:]
        
        return text
    
    def process_voice_commands(self, text: str) -> Optional[str]:
        """
        Process voice commands and return command result or None.
        Consolidated from app.py:223 and global_stt.py voice command logic
        """
        if not text or not text.strip():
            return None
            
        # Check if voice commands are enabled
        if not self.config.config.basic:  # Fallback check
            return None
            
        text_lower = text.lower().strip()
        
        # Use dedicated voice processor if available
        if self.voice_processor:
            try:
                result = self.voice_processor.process_command(text)
                if result:
                    if isinstance(result, str):
                        return result  # Return command result
                    return "COMMAND_EXECUTED"  # Generic command executed
            except Exception as e:
                print(f"Voice command error: {e}")
        
        # Fallback to inline commands for critical ones
        return self._process_inline_commands(text_lower)
    
    def _process_inline_commands(self, text_lower: str) -> Optional[str]:
        """Process critical inline voice commands"""
        try:
            import pyautogui
            import time
            
            # Text editing commands
            if re.search(r'\b(new line|next line)\b', text_lower):
                pyautogui.press('enter')
                return "COMMAND_EXECUTED"
            
            if re.search(r'\bnew paragraph\b', text_lower):
                pyautogui.press('enter')
                pyautogui.press('enter')
                return "COMMAND_EXECUTED"
            
            if re.search(r'\b(delete that|delete last)\b', text_lower):
                pyautogui.hotkey('ctrl', 'z')
                return "COMMAND_EXECUTED"
            
            if re.search(r'\bselect all\b', text_lower):
                pyautogui.hotkey('ctrl', 'a')
                return "COMMAND_EXECUTED"
            
            if re.search(r'\b(copy that|copy text)\b', text_lower):
                pyautogui.hotkey('ctrl', 'c')
                return "COMMAND_EXECUTED"
            
            if re.search(r'\b(paste that|paste text)\b', text_lower):
                pyautogui.hotkey('ctrl', 'v')
                return "COMMAND_EXECUTED"
            
            if re.search(r'\b(save file|save document)\b', text_lower):
                pyautogui.hotkey('ctrl', 's')
                return "COMMAND_EXECUTED"
            
            # Time command
            if re.search(r'\b(what time is it|current time)\b', text_lower):
                current_time = datetime.now().strftime("%I:%M %p")
                pyautogui.typewrite(f"The current time is {current_time}")
                return "COMMAND_EXECUTED"

            # System control: stop recording
            if re.search(r'\b(stop recording|stop dictation|stop transcribing)\b', text_lower):
                return "STOP_RECORDING"
            
            # Model switching
            model_match = re.search(r'\bswitch to (.*?) model\b', text_lower)
            if model_match:
                model_name = model_match.group(1).strip()
                return f"SWITCH_MODEL:{model_name}"
                
        except Exception as e:
            print(f"Inline command error: {e}")
        
        return None
    
    def process_final_text(self, text: str) -> Optional[str]:
        """
        Process final transcribed text with formatting and enhancements.
        Consolidated from app.py:196 and global_stt.py:873
        """
        if not text or not text.strip():
            return text
        
        # First check for voice commands
        command_result = self.process_voice_commands(text)
        if command_result:
            # Voice command was executed, don't process as regular text
            if self.voice_command_callback:
                self.voice_command_callback(command_result)
            return None
        
        # Use advanced text processor if available
        if self.text_processor:
            try:
                processed_text = self.text_processor.process_text(text)
                return processed_text
            except Exception as e:
                print(f"Advanced text processing error: {e}")
                # Fall back to basic processing
        
        # Basic text processing fallback
        return self._basic_text_processing(text)
    
    def _basic_text_processing(self, text: str) -> str:
        """Basic text processing fallback"""
        processed = text.strip()
        
        # Auto-capitalize
        config = self.config.config.basic
        if config.auto_capitalize and processed:
            processed = processed[0].upper() + processed[1:] if len(processed) > 1 else processed.upper()
        
        # Auto-punctuation
        if config.auto_punctuation:
            # Add period if no ending punctuation
            if not re.search(r'[.!?]$', processed):
                processed += '.'
        
        return processed
    
    def get_text_statistics(self, text: str) -> dict:
        """Get text statistics using advanced processor if available"""
        if self.text_processor:
            try:
                return self.text_processor.get_text_statistics(text)
            except Exception:
                pass
        
        # Basic statistics fallback
        if not text:
            return {}
        
        words = text.split()
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        return {
            'character_count': len(text),
            'word_count': len(words),
            'sentence_count': len(sentences),
            'average_words_per_sentence': len(words) / len(sentences) if sentences else 0,
            'reading_time_minutes': len(words) / 200
        }
    
    def add_custom_vocabulary(self, spoken_form: str, written_form: str):
        """Add custom vocabulary using advanced processor if available"""
        if self.text_processor:
            try:
                self.text_processor.add_custom_word(spoken_form, written_form)
            except Exception as e:
                print(f"Error adding custom vocabulary: {e}")


# Singleton instance for global use
_text_processor = None

def get_text_processor(voice_command_callback: Optional[Callable] = None) -> UnifiedTextProcessor:
    """Get global text processor instance"""
    global _text_processor
    if _text_processor is None:
        _text_processor = UnifiedTextProcessor(voice_command_callback)
    return _text_processor

def reset_text_processor() -> None:
    """Reset text processor (useful for testing)"""
    global _text_processor
    _text_processor = None