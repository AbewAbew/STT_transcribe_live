"""
Real-time Typing Manager
Consolidates all real-time typing logic from global_stt.py and app.py
"""

import threading
import time
import re
from typing import Optional, Callable
from .config import get_config


class RealtimeTypingManager:
    """
    Manages real-time typing functionality:
    1. Real-time text updates (typing as you speak)
    2. Finalization of text with proper spacing
    3. State management and threading safety
    4. Backspace optimization
    """
    
    def __init__(self):
        self.config = get_config()
        
        # Typing state
        self.last_typed_text = ""
        self.last_finalized_text = ""
        self.typing_lock = threading.Lock()
        
        # Suppression window after finalization
        self.suppress_realtime_until = 0.0
        
        # Debug mode
        self.debug_mode = False
        
    def set_debug_mode(self, enabled: bool):
        """Enable/disable debug logging"""
        self.debug_mode = enabled
    
    def _debug_print(self, message: str):
        """Print debug message if debug mode is enabled"""
        if self.debug_mode:
            print(f"[TYPING_DEBUG] {message}")
    
    def process_realtime_update(self, text: str) -> bool:
        """
        Process real-time transcription update.
        Returns True if text was typed, False if ignored.
        """
        if not text or not text.strip():
            return False
        
        # Check if real-time typing is enabled
        if not self.config.config.basic.realtime_typing:
            return False
        
        # Check suppression window
        if time.time() < self.suppress_realtime_until:
            self._debug_print("Realtime update suppressed by throttle window")
            return False
        
        # Check if this is redundant with last finalized text
        if self._is_redundant_with_finalized(text):
            self._debug_print(f"Realtime update ignored (subset of finalized): '{text}'")
            return False
        
        self._debug_print(f"Processing realtime update: '{text}'")
        self._type_realtime_text(text)
        return True
    
    def _is_redundant_with_finalized(self, text: str) -> bool:
        """Check if real-time text is redundant with last finalized text"""
        if not self.last_finalized_text:
            return False
        
        try:
            def normalize(s: str) -> str:
                s = (s or "").strip().lower()
                s = re.sub(r"[.!?\s]+$", "", s)  # Remove trailing punct/space
                s = re.sub(r"\s+", " ", s)
                return s
            
            new_normalized = normalize(text)
            finalized_normalized = normalize(self.last_finalized_text)
            
            return bool(new_normalized and finalized_normalized and 
                       finalized_normalized.startswith(new_normalized))
        except Exception as e:
            self._debug_print(f"Error comparing with finalized text: {e}")
            return False
    
    def _type_realtime_text(self, text: str):
        """Type real-time text with optimized backspace handling"""
        if not text:
            return
        
        with self.typing_lock:
            try:
                import pyautogui
                
                old_text = self.last_typed_text or ""
                new_text = text
                
                if new_text == old_text:
                    return
                
                if new_text.startswith(old_text):
                    # Efficient case: just type the new suffix
                    suffix = new_text[len(old_text):]
                    if suffix:
                        self._debug_print(f"Typing suffix: '{suffix}'")
                        pyautogui.typewrite(suffix)
                else:
                    # Need to replace: clear old text and type new
                    self._replace_typed_text(old_text, new_text)
                
                self.last_typed_text = new_text
                
            except Exception as e:
                self._debug_print(f"Error in realtime typing: {e}")
                self.last_typed_text = ""
    
    def _replace_typed_text(self, old_text: str, new_text: str):
        """Replace old typed text with new text using optimized backspacing"""
        import pyautogui
        
        old_len = len(old_text)
        if old_len > 0:
            self._debug_print(f"Clearing {old_len} characters of live text")
            
            # Use batched backspacing with safety limit
            max_backspaces = self.config.config.realtime.max_backspaces_per_update
            remaining = old_len
            
            while remaining > 0:
                batch_size = min(remaining, max_backspaces)
                for _ in range(batch_size):
                    pyautogui.press('backspace')
                remaining -= batch_size
                
                # Small delay between batches to prevent overwhelming
                if remaining > 0:
                    time.sleep(0.001)
        
        # Type the new text
        if new_text:
            pyautogui.typewrite(new_text)
    
    def finalize_text(self, final_text: str) -> bool:
        """
        Finalize real-time text into final sentence.
        Returns True if text was typed, False if ignored.
        """
        if not final_text or not final_text.strip():
            return False
        
        # Skip duplicate finalizations
        if final_text == self.last_finalized_text:
            self._debug_print("Duplicate finalization ignored")
            return False
        
        self._debug_print(f"Finalizing text: '{final_text}'")
        
        if self.config.config.basic.realtime_typing:
            return self._finalize_realtime_text(final_text)
        else:
            return self._type_final_text_direct(final_text)
    
    def _finalize_realtime_text(self, final_text: str) -> bool:
        """Finalize text in real-time typing mode"""
        import pyautogui
        
        with self.typing_lock:
            try:
                final_with_space = final_text + " "
                old_live_text = self.last_typed_text or ""
                
                if final_with_space.startswith(old_live_text):
                    # Efficient case: extend existing text
                    suffix = final_with_space[len(old_live_text):]
                    if suffix:
                        self._debug_print(f"Finalizing with suffix: '{suffix}'")
                        pyautogui.typewrite(suffix)
                else:
                    # Replace entire live region
                    self._debug_print("Finalizing with full replacement")
                    self._replace_typed_text(old_live_text, final_with_space)
                
                # Reset state and set suppression window
                self.last_typed_text = ""
                self.last_finalized_text = final_text
                self.suppress_realtime_until = (
                    time.time() + self.config.config.realtime.finalize_suppress_window
                )
                
                return True
                
            except Exception as e:
                self._debug_print(f"Error in finalization: {e}")
                return False
    
    def _type_final_text_direct(self, final_text: str) -> bool:
        """Type final text directly (non-realtime mode)"""
        try:
            import pyautogui
            pyautogui.typewrite(final_text + " ")
            self.last_finalized_text = final_text
            return True
        except Exception as e:
            self._debug_print(f"Error in direct typing: {e}")
            return False
    
    def insert_text(self, text: str, mode: Optional[str] = None):
        """
        Insert text using specified mode.
        Consolidated from global_stt.py:902
        """
        if not text:
            return
        
        insert_mode = mode or self.config.config.basic.insert_mode
        
        try:
            import pyautogui
            import time
            
            if insert_mode == "type":
                pyautogui.typewrite(text + " ")
            elif insert_mode == "clipboard":
                # Copy current selection, add to clipboard, and paste
                pyautogui.hotkey('ctrl', 'c')
                time.sleep(0.1)
                import pyperclip
                pyperclip.copy(text)
                pyautogui.hotkey('ctrl', 'v')
            elif insert_mode == "replace":
                # Select all and replace
                pyautogui.hotkey('ctrl', 'a')
                time.sleep(0.1)
                pyautogui.typewrite(text)
                
        except Exception as e:
            self._debug_print(f"Error inserting text: {e}")
    
    def reset_state(self):
        """Reset all typing state"""
        with self.typing_lock:
            self._debug_print("Resetting typing state")
            self.last_typed_text = ""
            self.last_finalized_text = ""
            self.suppress_realtime_until = 0.0
    
    def get_state(self) -> dict:
        """Get current typing state for debugging"""
        return {
            'last_typed_text': self.last_typed_text,
            'last_finalized_text': self.last_finalized_text,
            'suppress_until': self.suppress_realtime_until,
            'realtime_enabled': self.config.config.basic.realtime_typing
        }


# Singleton instance for global use
_typing_manager = None

def get_typing_manager() -> RealtimeTypingManager:
    """Get global typing manager instance"""
    global _typing_manager
    if _typing_manager is None:
        _typing_manager = RealtimeTypingManager()
    return _typing_manager

def reset_typing_manager() -> None:
    """Reset typing manager (useful for testing)"""
    global _typing_manager
    _typing_manager = None