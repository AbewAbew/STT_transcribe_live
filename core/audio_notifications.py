"""
Audio Notification System
Provides audio feedback for various STT events
"""

import os
import threading
from pathlib import Path
from typing import Optional, Dict, Any
import time


class AudioNotificationManager:
    """
    Manages audio notifications for STT events.
    Supports both system sounds and custom WAV files.
    """
    
    def __init__(self, sounds_dir: Optional[str] = None, enabled: bool = True):
        self.enabled = enabled
        self.sounds_dir = Path(sounds_dir) if sounds_dir else Path(__file__).parent.parent / "sounds"
        self.audio_backend = None
        self.volume = 0.7
        
        # Sound file mappings
        self.sound_files = {
            'ready': 'ready.wav',
            'start': 'start.wav', 
            'stop': 'stop.wav',
            'command': 'command.wav',
            'error': 'error.wav',
            'notification': 'notification.wav'
        }
        
        # Initialize audio backend
        self._init_audio_backend()
    
    def _init_audio_backend(self):
        """Initialize the best available audio backend"""
        backends = [
            ('sounddevice', self._init_sounddevice),
            ('pygame', self._init_pygame),
            ('playsound', self._init_playsound),
            ('system', self._init_system_sounds)
        ]
        
        for backend_name, init_func in backends:
            try:
                if init_func():
                    self.audio_backend = backend_name
                    print(f"Audio notifications using: {backend_name}")
                    return
            except Exception as e:
                continue
        
        print("Warning: No audio backend available - notifications disabled")
        self.enabled = False
    
    def _init_sounddevice(self) -> bool:
        """Try to initialize sounddevice + soundfile backend"""
        try:
            import sounddevice as sd
            import soundfile as sf
            # Test if we can load and play
            return True
        except ImportError:
            return False
    
    def _init_pygame(self) -> bool:
        """Try to initialize pygame backend"""
        try:
            import pygame
            pygame.mixer.init()
            return True
        except ImportError:
            return False
    
    def _init_playsound(self) -> bool:
        """Try to initialize playsound backend"""
        try:
            import playsound
            return True
        except ImportError:
            return False
    
    def _init_system_sounds(self) -> bool:
        """System sounds always available"""
        return True
    
    def set_enabled(self, enabled: bool):
        """Enable or disable audio notifications"""
        self.enabled = enabled
    
    def set_volume(self, volume: float):
        """Set volume (0.0 to 1.0)"""
        self.volume = max(0.0, min(1.0, volume))
    
    def _get_sound_path(self, sound_type: str) -> Optional[Path]:
        """Get the full path to a sound file"""
        if sound_type not in self.sound_files:
            return None
        
        sound_path = self.sounds_dir / self.sound_files[sound_type]
        return sound_path if sound_path.exists() else None
    
    def _play_with_sounddevice(self, sound_path: Path):
        """Play sound using sounddevice"""
        try:
            import sounddevice as sd
            import soundfile as sf
            
            data, sample_rate = sf.read(str(sound_path))
            # Apply volume
            data = data * self.volume
            sd.play(data, sample_rate)
            
        except Exception as e:
            print(f"Sounddevice playback error: {e}")
    
    def _play_with_pygame(self, sound_path: Path):
        """Play sound using pygame"""
        try:
            import pygame
            
            sound = pygame.mixer.Sound(str(sound_path))
            sound.set_volume(self.volume)
            sound.play()
            
        except Exception as e:
            print(f"Pygame playback error: {e}")
    
    def _play_with_playsound(self, sound_path: Path):
        """Play sound using playsound"""
        try:
            from playsound import playsound
            playsound(str(sound_path), block=False)
            
        except Exception as e:
            print(f"Playsound playback error: {e}")
    
    def _play_system_sound(self, sound_type: str):
        """Play system sound as fallback"""
        try:
            import os
            if os.name == 'nt':  # Windows
                import winsound
                if sound_type == 'error':
                    winsound.MessageBeep(winsound.MB_ICONHAND)
                elif sound_type == 'ready':
                    winsound.MessageBeep(winsound.MB_ICONASTERISK)
                elif sound_type in ['start', 'stop']:
                    winsound.MessageBeep(winsound.MB_OK)
                else:
                    winsound.MessageBeep(winsound.MB_ICONASTERISK)
            else:  # Linux/Mac
                os.system('printf "\\a"')  # Terminal bell
                
        except Exception as e:
            print(f"System sound error: {e}")
    
    def play_sound(self, sound_type: str, blocking: bool = False):
        """
        Play a notification sound.
        
        Args:
            sound_type: Type of sound (ready, start, stop, command, error, notification)
            blocking: Whether to wait for sound to finish
        """
        if not self.enabled:
            return
        
        def _play():
            try:
                # Try to play custom sound file first
                sound_path = self._get_sound_path(sound_type)
                
                if sound_path and self.audio_backend in ['sounddevice', 'pygame', 'playsound']:
                    if self.audio_backend == 'sounddevice':
                        self._play_with_sounddevice(sound_path)
                    elif self.audio_backend == 'pygame':
                        self._play_with_pygame(sound_path)
                    elif self.audio_backend == 'playsound':
                        self._play_with_playsound(sound_path)
                else:
                    # Fallback to system sounds
                    self._play_system_sound(sound_type)
                    
            except Exception as e:
                print(f"Audio notification error: {e}")
        
        if blocking:
            _play()
        else:
            # Play in background thread
            threading.Thread(target=_play, daemon=True).start()
    
    def play_ready(self, blocking: bool = False):
        """Play 'model ready' sound"""
        self.play_sound('ready', blocking)
    
    def play_start(self, blocking: bool = False):
        """Play 'recording started' sound"""
        self.play_sound('start', blocking)
    
    def play_stop(self, blocking: bool = False):
        """Play 'recording stopped' sound"""
        self.play_sound('stop', blocking)
    
    def play_command(self, blocking: bool = False):
        """Play 'command executed' sound"""
        self.play_sound('command', blocking)
    
    def play_error(self, blocking: bool = False):
        """Play 'error' sound"""
        self.play_sound('error', blocking)
    
    def play_notification(self, blocking: bool = False):
        """Play generic notification sound"""
        self.play_sound('notification', blocking)
    
    def test_sounds(self):
        """Test all available sounds"""
        print("Testing audio notifications...")
        sounds = ['ready', 'start', 'stop', 'command', 'error', 'notification']
        
        for sound in sounds:
            print(f"Playing: {sound}")
            self.play_sound(sound, blocking=True)
            time.sleep(0.5)
        
        print("Audio test complete!")
    
    def create_default_sounds_dir(self):
        """Create the sounds directory if it doesn't exist"""
        self.sounds_dir.mkdir(exist_ok=True)
        return self.sounds_dir
    
    def get_missing_sounds(self) -> list:
        """Get list of missing sound files"""
        missing = []
        for sound_type, filename in self.sound_files.items():
            sound_path = self.sounds_dir / filename
            if not sound_path.exists():
                missing.append(filename)
        return missing


# Global instance
_notification_manager = None

def get_notification_manager(**kwargs) -> AudioNotificationManager:
    """Get global notification manager instance"""
    global _notification_manager
    if _notification_manager is None:
        _notification_manager = AudioNotificationManager(**kwargs)
    return _notification_manager

def reset_notification_manager():
    """Reset notification manager (for testing)"""
    global _notification_manager
    _notification_manager = None