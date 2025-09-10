"""
Voice Commands System
Adds voice control capabilities to the STT system
"""

import re
import subprocess
import webbrowser
import os
import pyautogui
import time
from datetime import datetime

class VoiceCommandProcessor:
    def __init__(self):
        self.commands = {
            # Text editing commands
            r"new line|next line": self.new_line,
            r"new paragraph": self.new_paragraph,
            r"delete that|delete last": self.delete_last,
            r"delete all": self.delete_all,
            r"select all": self.select_all,
            r"copy that|copy text": self.copy_text,
            r"paste that|paste text": self.paste_text,
            r"undo that|undo": self.undo,
            r"save file|save document": self.save_file,
            
            # Navigation commands
            r"go to start|beginning": self.go_to_start,
            r"go to end": self.go_to_end,
            r"scroll up": self.scroll_up,
            r"scroll down": self.scroll_down,
            
            # Application commands
            r"open (\w+)": self.open_application,
            r"search for (.+)": self.web_search,
            r"close window|close app": self.close_window,
            r"minimize window": self.minimize_window,
            r"maximize window": self.maximize_window,
            
            # System commands
            r"what time is it|current time": self.get_time,
            r"open file explorer|open explorer": self.open_explorer,
            r"take screenshot": self.take_screenshot,
            
            # STT control commands
            r"stop recording|stop listening": self.stop_recording,
            r"switch to (.*?) model": self.switch_model,
        }
    
    def process_command(self, text):
        """Process voice command and return True if command was executed"""
        text_lower = text.lower().strip()
        
        for pattern, action in self.commands.items():
            match = re.search(pattern, text_lower)
            if match:
                try:
                    if match.groups():
                        action(match.group(1))
                    else:
                        action()
                    return True
                except Exception as e:
                    print(f"Command error: {e}")
                    return False
        
        return False
    
    # Text editing commands
    def new_line(self):
        pyautogui.press('enter')
    
    def new_paragraph(self):
        pyautogui.press('enter')
        pyautogui.press('enter')
    
    def delete_last(self):
        pyautogui.hotkey('ctrl', 'z')
    
    def select_all(self):
        pyautogui.hotkey('ctrl', 'a')
    
    def copy_text(self):
        pyautogui.hotkey('ctrl', 'c')
    
    def paste_text(self):
        pyautogui.hotkey('ctrl', 'v')
    
    def undo(self):
        pyautogui.hotkey('ctrl', 'z')
    
    def save_file(self):
        pyautogui.hotkey('ctrl', 's')
    
    def delete_all(self):
        pyautogui.hotkey('ctrl', 'a')
        pyautogui.press('delete')
    
    # Navigation commands
    def go_to_start(self):
        pyautogui.hotkey('ctrl', 'home')
    
    def go_to_end(self):
        pyautogui.hotkey('ctrl', 'end')
    
    def scroll_up(self):
        pyautogui.scroll(3)
    
    def scroll_down(self):
        pyautogui.scroll(-3)
    
    # Application commands
    def open_application(self, app_name):
        app_name = app_name.lower().strip()
        
        # Use Windows Start menu approach
        try:
            if app_name in ['chrome', 'browser']:
                pyautogui.hotkey('win', 'r')
                time.sleep(0.5)
                pyautogui.typewrite('chrome')
                pyautogui.press('enter')
            elif app_name == 'word':
                pyautogui.hotkey('win', 'r')
                time.sleep(0.5)
                pyautogui.typewrite('winword')
                pyautogui.press('enter')
            elif app_name == 'excel':
                pyautogui.hotkey('win', 'r')
                time.sleep(0.5)
                pyautogui.typewrite('excel')
                pyautogui.press('enter')
            elif app_name in ['notepad', 'calculator']:
                subprocess.Popen(f"{app_name}.exe" if app_name == 'notepad' else 'calc.exe', shell=True)
            else:
                # Try Windows Run dialog
                pyautogui.hotkey('win', 'r')
                time.sleep(0.5)
                pyautogui.typewrite(app_name)
                pyautogui.press('enter')
            print(f"Opening {app_name}...")
        except Exception as e:
            print(f"Failed to open {app_name}: {e}")
    
    def web_search(self, query):
        search_url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
        webbrowser.open(search_url)
    
    def close_window(self):
        pyautogui.hotkey('alt', 'f4')
    
    def minimize_window(self):
        pyautogui.hotkey('win', 'down')
    
    def maximize_window(self):
        pyautogui.hotkey('win', 'up')
    
    # System commands
    def get_time(self):
        current_time = datetime.now().strftime("%I:%M %p")
        pyautogui.typewrite(f"The current time is {current_time}")
    
    def open_explorer(self):
        pyautogui.hotkey('win', 'e')
    
    def take_screenshot(self):
        pyautogui.hotkey('win', 'shift', 's')
    
    # STT control commands
    def stop_recording(self):
        # This will be handled by the main STT system
        return "STOP_RECORDING"
    
    def switch_model(self, model_name):
        # This will be handled by the main STT system
        return f"SWITCH_MODEL:{model_name}"