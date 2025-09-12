"""
Shared Configuration and Constants for RealtimeSTT System
Centralized settings management for both Tkinter and Qt interfaces
"""

import os
import json
from dataclasses import dataclass, asdict
from typing import Dict, Optional, Any
from pathlib import Path

# Model configurations with descriptions
AVAILABLE_MODELS = {
    "tiny.en": {"size": "tiny", "lang": "en", "speed": "fastest", "description": "Fastest"},
    "base.en": {"size": "base", "lang": "en", "speed": "fast", "description": "Fast"},
    "small.en": {"size": "small", "lang": "en", "speed": "balanced", "description": "Balanced"},
    "medium.en": {"size": "medium", "lang": "en", "speed": "accurate", "description": "Accurate"},
    "large-v1": {"size": "large", "lang": "multilingual", "speed": "high_accurate", "description": "High Accuracy"},
    "large-v2": {"size": "large", "lang": "multilingual", "speed": "better_accurate", "description": "Better Accuracy"},
    "large-v3": {"size": "large", "lang": "multilingual", "speed": "most_accurate", "description": "Most Accurate"},
    "large-v3-turbo": {"size": "large", "lang": "multilingual", "speed": "ultra_fast", "description": "Ultra Fast"}
}

# Available wake words
AVAILABLE_WAKE_WORDS = [
    "custom", "jarvis", "computer", "hey google", "hey siri", "ok google", "alexa",
    "porcupine", "bumblebee", "terminator", "picovoice", "americano",
    "blueberry", "grapefruits", "grasshopper"
]

# Default hotkeys
DEFAULT_HOTKEYS = {
    "start": "ctrl+shift+s",
    "stop": "ctrl+shift+x",
    "toggle": "ctrl+shift+t",
    "calibrate": "ctrl+shift+n"
}

# UI constants
UI_COLORS = {
    "success": "#4CAF50",
    "error": "#f44336",
    "warning": "#ff9800",
    "info": "#2196F3",
    "background": "#f0f0f0"
}

@dataclass
class BasicSettings:
    """Basic STT settings"""
    model: str = "small.en"
    auto_punctuation: bool = True
    auto_capitalize: bool = True
    insert_mode: str = "type"  # "type", "clipboard", "replace"
    realtime_typing: bool = False

@dataclass
class WakeWordSettings:
    """Wake word configuration"""
    enabled: bool = False
    wake_words: str = "jarvis"
    sensitivity: float = 0.6
    custom_model_path: Optional[str] = None
    timeout: float = 12.0
    conversation_window: float = 4.0

@dataclass
class RealtimeSettings:
    """Real-time processing tuning"""
    processing_pause: float = 0.02
    post_speech_silence_duration: float = 0.7
    min_length_of_recording: float = 0.3
    min_gap_between_recordings: float = 0.0
    finalize_suppress_window: float = 0.5
    max_backspaces_per_update: int = 512

@dataclass
class VADSettings:
    """Voice Activity Detection settings"""
    silero_sensitivity: float = 0.05
    silero_use_onnx: bool = False
    webrtc_sensitivity: int = 3
    early_transcription_on_silence: float = 0.2

@dataclass
class ModelSettings:
    """Model parameters"""
    beam_size: int = 5
    beam_size_realtime: int = 3
    batch_size: int = 16
    initial_prompt: str = "End incomplete sentences with ellipses. Examples: Complete: The sky is blue. Incomplete: When the sky..."

@dataclass
class PauseDetectionSettings:
    """Intelligent pause detection"""
    end_of_sentence_pause: float = 0.45
    unknown_sentence_pause: float = 0.7
    mid_sentence_pause: float = 2.0

@dataclass
class AudioNotificationSettings:
    """Audio notification settings"""
    enabled: bool = True
    volume: float = 0.7
    sounds_dir: Optional[str] = None
    play_ready_sound: bool = True
    play_start_sound: bool = True
    play_stop_sound: bool = True
    play_command_sound: bool = True
    play_error_sound: bool = True

@dataclass
class STTConfig:
    """Complete STT configuration"""
    basic: BasicSettings = None
    wake_word: WakeWordSettings = None
    realtime: RealtimeSettings = None
    vad: VADSettings = None
    model: ModelSettings = None
    pause_detection: PauseDetectionSettings = None
    audio_notifications: AudioNotificationSettings = None
    
    def __post_init__(self):
        if self.basic is None:
            self.basic = BasicSettings()
        if self.wake_word is None:
            self.wake_word = WakeWordSettings()
        if self.realtime is None:
            self.realtime = RealtimeSettings()
        if self.vad is None:
            self.vad = VADSettings()
        if self.model is None:
            self.model = ModelSettings()
        if self.pause_detection is None:
            self.pause_detection = PauseDetectionSettings()
        if self.audio_notifications is None:
            self.audio_notifications = AudioNotificationSettings()

class ConfigManager:
    """Centralized configuration management"""
    
    def __init__(self, config_file: str = "stt_settings.json"):
        self.config_file = Path(config_file)
        self.config = STTConfig()
        self.load_settings()
    
    def load_settings(self) -> None:
        """Load settings from JSON file"""
        if not self.config_file.exists():
            self.save_settings()  # Create default config
            return
        
        try:
            with open(self.config_file, 'r') as f:
                data = json.load(f)
            
            # Load each section
            if 'basic' in data:
                self.config.basic = BasicSettings(**data['basic'])
            if 'wake_word' in data:
                self.config.wake_word = WakeWordSettings(**data['wake_word'])
            if 'realtime' in data:
                self.config.realtime = RealtimeSettings(**data['realtime'])
            if 'vad' in data:
                self.config.vad = VADSettings(**data['vad'])
            if 'model' in data:
                self.config.model = ModelSettings(**data['model'])
            if 'pause_detection' in data:
                self.config.pause_detection = PauseDetectionSettings(**data['pause_detection'])
            if 'audio_notifications' in data:
                self.config.audio_notifications = AudioNotificationSettings(**data['audio_notifications'])
                
        except Exception as e:
            print(f"Error loading settings: {e}")
            # Keep default settings on error
    
    def save_settings(self) -> None:
        """Save settings to JSON file"""
        try:
            data = {
                'basic': asdict(self.config.basic),
                'wake_word': asdict(self.config.wake_word),
                'realtime': asdict(self.config.realtime),
                'vad': asdict(self.config.vad),
                'model': asdict(self.config.model),
                'pause_detection': asdict(self.config.pause_detection),
                'audio_notifications': asdict(self.config.audio_notifications)
            }
            
            with open(self.config_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            print(f"Error saving settings: {e}")
    
    def get_recorder_config(self) -> Dict[str, Any]:
        """Get configuration dictionary for AudioToTextRecorder"""
        config = {
            'model': self.config.basic.model,
            'language': "en",
            'device': "cuda",
            'use_microphone': True,
            'spinner': False,
            'enable_realtime_transcription': True,
            'realtime_model_type': 'tiny.en',
            'realtime_processing_pause': self.config.realtime.processing_pause,
            'post_speech_silence_duration': self.config.realtime.post_speech_silence_duration,
            'min_length_of_recording': self.config.realtime.min_length_of_recording,
            'min_gap_between_recordings': self.config.realtime.min_gap_between_recordings,
        }
        
        return config
    
    def get_supported_features(self) -> Dict[str, bool]:
        """Check which RealtimeSTT features are supported"""
        try:
            import inspect
            from RealtimeSTT import AudioToTextRecorder
            
            init_signature = inspect.signature(AudioToTextRecorder.__init__)
            params = list(init_signature.parameters.keys())
            
            features = {
                'silero_sensitivity': 'silero_sensitivity' in params,
                'silero_use_onnx': 'silero_use_onnx' in params,
                'webrtc_sensitivity': 'webrtc_sensitivity' in params,
                'beam_size': 'beam_size' in params,
                'beam_size_realtime': 'beam_size_realtime' in params,
                'initial_prompt': 'initial_prompt' in params,
                'early_transcription_on_silence': 'early_transcription_on_silence' in params,
                'end_of_sentence_detection_pause': 'end_of_sentence_detection_pause' in params,
                'unknown_sentence_detection_pause': 'unknown_sentence_detection_pause' in params,
                'mid_sentence_detection_pause': 'mid_sentence_detection_pause' in params
            }
            
            return features
        except Exception:
            return {key: False for key in [
                'silero_sensitivity', 'silero_use_onnx', 'webrtc_sensitivity',
                'beam_size', 'beam_size_realtime', 'initial_prompt',
                'early_transcription_on_silence', 'end_of_sentence_detection_pause',
                'unknown_sentence_detection_pause', 'mid_sentence_detection_pause'
            ]}
    
    def add_supported_features_to_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Add supported advanced features to recorder config"""
        supported = self.get_supported_features()
        
        if supported.get('silero_sensitivity'):
            config['silero_sensitivity'] = self.config.vad.silero_sensitivity
        if supported.get('silero_use_onnx'):
            config['silero_use_onnx'] = self.config.vad.silero_use_onnx
        if supported.get('webrtc_sensitivity'):
            config['webrtc_sensitivity'] = self.config.vad.webrtc_sensitivity
        if supported.get('beam_size'):
            config['beam_size'] = self.config.model.beam_size
        if supported.get('beam_size_realtime'):
            config['beam_size_realtime'] = self.config.model.beam_size_realtime
        if supported.get('initial_prompt'):
            config['initial_prompt'] = self.config.model.initial_prompt
        if supported.get('early_transcription_on_silence'):
            config['early_transcription_on_silence'] = self.config.vad.early_transcription_on_silence
        if supported.get('end_of_sentence_detection_pause'):
            config['end_of_sentence_detection_pause'] = self.config.pause_detection.end_of_sentence_pause
        if supported.get('unknown_sentence_detection_pause'):
            config['unknown_sentence_detection_pause'] = self.config.pause_detection.unknown_sentence_pause
        if supported.get('mid_sentence_detection_pause'):
            config['mid_sentence_detection_pause'] = self.config.pause_detection.mid_sentence_pause
            
        return config
    
    def get_complete_recorder_config(self) -> Dict[str, Any]:
        """Get complete recorder configuration with all supported features"""
        config = self.get_recorder_config()
        return self.add_supported_features_to_config(config)

# Global config instance
_config_manager = None

def get_config() -> ConfigManager:
    """Get global config manager instance"""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager

def reset_config() -> None:
    """Reset config manager (useful for testing)"""
    global _config_manager
    _config_manager = None