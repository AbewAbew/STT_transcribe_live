"""
Global Speech-to-Text System with System Tray Integration
Allows STT usage in any text box with global hotkeys
"""

import sys
import threading
import time
import pyautogui
import pystray
from PIL import Image, ImageDraw
import keyboard
from RealtimeSTT import AudioToTextRecorder
import re
import tkinter as tk
from tkinter import messagebox, ttk
import json
import os
import signal
from voice_commands import VoiceCommandProcessor
from text_processor import TextProcessor
from audio_enhancements import AudioEnhancer

# Define ANSI color codes for better console output (from RealtimeSTT_server)
class bcolors:
    HEADER = '\033[95m'   # Magenta
    OKBLUE = '\033[94m'   # Blue
    OKCYAN = '\033[96m'   # Cyan
    OKGREEN = '\033[92m'  # Green
    WARNING = '\033[93m'  # Yellow
    FAIL = '\033[91m'     # Red
    ENDC = '\033[0m'      # Reset to default
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

class GlobalSTTManager:
    def __init__(self, enable_tray: bool = True, enable_hotkeys: bool = True):
        self.recorder = None
        self.is_recording = False
        self.current_model = "small.en"
        # Defaults for text processing
        self.auto_punctuation = True
        self.auto_capitalize = True
        self.settings_file = "stt_settings.json"
        self.load_settings()
        
        # Initialize enhancement modules
        self.voice_commands = VoiceCommandProcessor()
        self.text_processor = TextProcessor()
        self.audio_enhancer = AudioEnhancer()
        
        # Global hotkeys
        self.start_hotkey = "ctrl+shift+s"
        self.stop_hotkey = "ctrl+shift+x"
        self.toggle_hotkey = "ctrl+shift+t"
        self.calibrate_hotkey = "ctrl+shift+n"
        
        # Enhanced options
        self.voice_commands_enabled = True
        self.audio_enhancement_enabled = True
        self.smart_text_processing = True
        self.insert_mode = "type"
        self.realtime_typing = False
        self.debug_mode = True  # Enable debug output
        # Real-time editing parameters (to keep edits local and non-destructive)
        # Tuning for realtime edits (defaults = current behavior)
        self.realtime_edit_window = 48   # reserved for future use
        self.max_backspaces_per_update = 20 # generous cap; live region only
        # Recorder/segmentation defaults (tunable)
        self.realtime_processing_pause = 0.02
        self.post_speech_silence_duration = 0.7
        self.min_length_of_recording = 0.3
        self.min_gap_between_recordings = 0.0
        # Finalization suppression window (to drop stale realtime after finalize)
        self.finalize_suppress_window = 0.5
        self.last_finalized_text = ""
        
        # Wake word settings defaults
        self.wake_words_enabled = False
        self.wake_words = "jarvis"  # Default wake word
        self.wake_words_sensitivity = 0.6
        self.wakeword_backend = "pvporcupine"  # Default backend
        self.custom_wakeword_model_path = None  # Path to custom trained model
        
        # Advanced VAD settings (from RealtimeSTT_server)
        self.silero_sensitivity = 0.05
        self.silero_use_onnx = False
        self.webrtc_sensitivity = 3
        self.early_transcription_on_silence = 0.2
        
        # Enhanced model parameters
        self.beam_size = 5
        self.beam_size_realtime = 3
        self.initial_prompt = "End incomplete sentences with ellipses. Examples: Complete: The sky is blue. Incomplete: When the sky..."
        self.batch_size = 16
        
        # Advanced pause detection (intelligent speech detection)
        self.end_of_sentence_detection_pause = 0.45
        self.unknown_sentence_detection_pause = 0.7
        self.mid_sentence_detection_pause = 2.0
        
        # Real-time typing state
        self.last_typed_text = ""
        self.is_realtime_mode = False
        self.typing_lock = threading.Lock()  # Prevent concurrent typing
        self.suppress_realtime_until = 0.0  # throttle window after finalize
        
        if enable_hotkeys:
            self.setup_hotkeys()
        self.icon = None
        self.enable_tray = enable_tray
        # Optional callback for showing native tray notifications (e.g., Qt)
        # Signature: tray_notify(title: str, message: str) -> None
        self.tray_notify = None
        if enable_tray:
            self.create_system_tray()
        
    def detect_supported_features(self):
        """Detect which advanced RealtimeSTT features are supported in the current version"""
        supported_features = {
            'silero_sensitivity': False,
            'silero_use_onnx': False,
            'webrtc_sensitivity': False,
            'beam_size': False,
            'beam_size_realtime': False,
            'initial_prompt': False,
            'early_transcription_on_silence': False,
            'end_of_sentence_detection_pause': False,
            'unknown_sentence_detection_pause': False,
            'mid_sentence_detection_pause': False
        }
        
        # Test each parameter by checking AudioToTextRecorder init signature
        try:
            import inspect
            from RealtimeSTT import AudioToTextRecorder
            
            # Get the init signature
            init_signature = inspect.signature(AudioToTextRecorder.__init__)
            params = list(init_signature.parameters.keys())
            
            for feature in supported_features.keys():
                if feature in params:
                    supported_features[feature] = True
                    if self.debug_mode:
                        print(f"{bcolors.OKGREEN}[DEBUG] Supported: {feature}{bcolors.ENDC}")
                elif self.debug_mode:
                    print(f"{bcolors.WARNING}[DEBUG] Not supported: {feature}{bcolors.ENDC}")
                    
        except Exception as e:
            if self.debug_mode:
                print(f"{bcolors.FAIL}[DEBUG] Could not detect features: {e}{bcolors.ENDC}")
        
        return supported_features

    def load_settings(self):
        """Load settings from JSON file"""
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, 'r') as f:
                    settings = json.load(f)
                    self.current_model = settings.get('model', 'small.en')
                    self.auto_punctuation = settings.get('auto_punctuation', True)
                    self.auto_capitalize = settings.get('auto_capitalize', True)
                    self.insert_mode = settings.get('insert_mode', 'type')
                    self.realtime_typing = settings.get('realtime_typing', False)
                    self.wake_words_enabled = settings.get('wake_words_enabled', False)
                    self.wake_words = settings.get('wake_words', 'jarvis')
                    self.wake_words_sensitivity = settings.get('wake_words_sensitivity', 0.6)
                    self.custom_wakeword_model_path = settings.get('custom_wakeword_model_path', None)
                    # Optional tunables with defaults matching current behavior
                    self.max_backspaces_per_update = int(settings.get('max_backspaces_per_update', self.max_backspaces_per_update))
                    self.realtime_processing_pause = float(settings.get('realtime_processing_pause', self.realtime_processing_pause))
                    self.post_speech_silence_duration = float(settings.get('post_speech_silence_duration', self.post_speech_silence_duration))
                    self.min_length_of_recording = float(settings.get('min_length_of_recording', self.min_length_of_recording))
                    self.min_gap_between_recordings = float(settings.get('min_gap_between_recordings', self.min_gap_between_recordings))
                    self.finalize_suppress_window = float(settings.get('finalize_suppress_window', self.finalize_suppress_window))
                    # Advanced VAD settings
                    self.silero_sensitivity = float(settings.get('silero_sensitivity', self.silero_sensitivity))
                    self.silero_use_onnx = bool(settings.get('silero_use_onnx', self.silero_use_onnx))
                    self.webrtc_sensitivity = int(settings.get('webrtc_sensitivity', self.webrtc_sensitivity))
                    self.early_transcription_on_silence = float(settings.get('early_transcription_on_silence', self.early_transcription_on_silence))
                    # Enhanced model parameters
                    self.beam_size = int(settings.get('beam_size', self.beam_size))
                    self.beam_size_realtime = int(settings.get('beam_size_realtime', self.beam_size_realtime))
                    self.initial_prompt = settings.get('initial_prompt', self.initial_prompt)
                    self.batch_size = int(settings.get('batch_size', self.batch_size))
                    # Advanced pause detection
                    self.end_of_sentence_detection_pause = float(settings.get('end_of_sentence_detection_pause', self.end_of_sentence_detection_pause))
                    self.unknown_sentence_detection_pause = float(settings.get('unknown_sentence_detection_pause', self.unknown_sentence_detection_pause))
                    self.mid_sentence_detection_pause = float(settings.get('mid_sentence_detection_pause', self.mid_sentence_detection_pause))
            except Exception as e:
                print(f"Error loading settings: {e}")
    
    def save_settings(self):
        """Save settings to JSON file"""
        settings = {
            'model': self.current_model,
            'auto_punctuation': self.auto_punctuation,
            'auto_capitalize': self.auto_capitalize,
            'insert_mode': self.insert_mode,
            'realtime_typing': self.realtime_typing,
            'wake_words_enabled': self.wake_words_enabled,
            'wake_words': self.wake_words,
            'wake_words_sensitivity': self.wake_words_sensitivity,
            'custom_wakeword_model_path': self.custom_wakeword_model_path,
            # Tunables persisted with defaults that match current behavior
            'max_backspaces_per_update': self.max_backspaces_per_update,
            'realtime_processing_pause': self.realtime_processing_pause,
            'post_speech_silence_duration': self.post_speech_silence_duration,
            'min_length_of_recording': self.min_length_of_recording,
            'min_gap_between_recordings': self.min_gap_between_recordings,
            'finalize_suppress_window': self.finalize_suppress_window,
            # Advanced VAD settings
            'silero_sensitivity': self.silero_sensitivity,
            'silero_use_onnx': self.silero_use_onnx,
            'webrtc_sensitivity': self.webrtc_sensitivity,
            'early_transcription_on_silence': self.early_transcription_on_silence,
            # Enhanced model parameters
            'beam_size': self.beam_size,
            'beam_size_realtime': self.beam_size_realtime,
            'initial_prompt': self.initial_prompt,
            'batch_size': self.batch_size,
            # Advanced pause detection
            'end_of_sentence_detection_pause': self.end_of_sentence_detection_pause,
            'unknown_sentence_detection_pause': self.unknown_sentence_detection_pause,
            'mid_sentence_detection_pause': self.mid_sentence_detection_pause
        }
        try:
            with open(self.settings_file, 'w') as f:
                json.dump(settings, f, indent=2)
        except Exception as e:
            print(f"Error saving settings: {e}")
    
    def setup_hotkeys(self):
        """Setup global hotkeys"""
        keyboard.add_hotkey(self.start_hotkey, self.start_recording)
        keyboard.add_hotkey(self.stop_hotkey, self.stop_recording)
        keyboard.add_hotkey(self.toggle_hotkey, self.toggle_recording)
        keyboard.add_hotkey(self.calibrate_hotkey, self.calibrate_noise)
    
    def create_system_tray_icon(self):
        """Create system tray icon"""
        # Create a simple microphone icon
        image = Image.new('RGB', (64, 64), color='black')
        draw = ImageDraw.Draw(image)
        
        # Draw microphone shape
        draw.ellipse([20, 15, 44, 35], fill='white')
        draw.rectangle([30, 35, 34, 45], fill='white')
        draw.rectangle([25, 45, 39, 50], fill='white')
        
        return image
    
    def create_system_tray(self):
        """Create system tray application"""
        icon_image = self.create_system_tray_icon()
        
        # Create model selection submenu
        model_menu = pystray.Menu(
            pystray.MenuItem("tiny.en (Fastest)", lambda: self.change_model("tiny.en")),
            pystray.MenuItem("base.en (Fast)", lambda: self.change_model("base.en")),
            pystray.MenuItem("small.en (Balanced)", lambda: self.change_model("small.en")),
            pystray.MenuItem("medium.en (Accurate)", lambda: self.change_model("medium.en")),
            pystray.MenuItem("large-v1 (High Accuracy)", lambda: self.change_model("large-v1")),
            pystray.MenuItem("large-v2 (Better Accuracy)", lambda: self.change_model("large-v2")),
            pystray.MenuItem("large-v3 (Most Accurate)", lambda: self.change_model("large-v3")),
            pystray.MenuItem("large-v3-turbo (Ultra Fast)", lambda: self.change_model("large-v3-turbo"))
        )
        
        menu = pystray.Menu(
            pystray.MenuItem("Start Recording", self.start_recording),
            pystray.MenuItem("Stop Recording", self.stop_recording),
            pystray.MenuItem(f"Model: {self.current_model}", model_menu),
            pystray.MenuItem("Settings", self.show_settings),
            pystray.MenuItem("Web Interface", self.open_web_interface),
            pystray.MenuItem("Status", self.show_status),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Exit", self.quit_application)
        )
        
        self.icon = pystray.Icon("GlobalSTT", icon_image, "Advanced Global STT", menu)

    def _show_notification(self, title: str, message: str):
        """Show a system notification via available tray integration."""
        # Prefer an injected tray notification handler (e.g., Qt)
        try:
            if callable(getattr(self, 'tray_notify', None)):
                self.tray_notify(title, message)
                return
        except Exception:
            pass

        # Fallback to pystray notifications if available
        try:
            if self.enable_tray and getattr(self, 'icon', None):
                # pystray accepts (message, optional title)
                self.icon.notify(message, title=title)
                return
        except Exception:
            pass

        # As a last resort, print to stdout (useful when a console is visible)
        try:
            print(f"[NOTICE] {title}: {message}")
        except Exception:
            pass
    
    def calibrate_noise(self):
        """Calibrate background noise for better recognition"""
        if self.is_recording:
            print("Stop recording before calibrating noise")
            return
        
        print("Starting noise calibration...")
        threading.Thread(target=self.audio_enhancer.calibrate_noise_floor, daemon=True).start()
    
    def start_recording(self):
        """Start speech recognition"""
        if self.is_recording:
            return
            
        try:
            self.is_recording = True
            if self.debug_mode:
                print(f"[DEBUG] Starting recording - realtime_typing: {self.realtime_typing}, wake_words: {self.wake_words_enabled}")
            
            if self.wake_words_enabled:
                print(f"{bcolors.OKCYAN}🎤 Listening for wake word: '{self.wake_words}'...{bcolors.ENDC}")
            else:
                print(f"{bcolors.OKGREEN}🎤 Starting global recording with model: {self.current_model}{bcolors.ENDC}")
            
            # Try to connect to web interface first
            if self._try_web_interface():
                print("Connected to web interface - using shared model")
                self._show_notification(
                    "Model Ready",
                    "Connected to web interface — ready to record"
                )
                return
            
            # Fallback to standalone mode
            print("Web interface not available - starting standalone mode")
            if not self.recorder:
                if self.debug_mode:
                    print(f"[DEBUG] Creating recorder with real-time typing: {self.realtime_typing}")
                
                # Detect supported features
                supported = self.detect_supported_features()
                
                # Start with basic supported parameters
                recorder_config = {
                    'model': self.current_model,
                    'language': "en",
                    'device': "cuda",
                    'use_microphone': True,
                    'spinner': False,
                    'enable_realtime_transcription': True,
                    'realtime_model_type': 'tiny.en',
                    'realtime_processing_pause': float(self.realtime_processing_pause),
                    'post_speech_silence_duration': float(self.post_speech_silence_duration),
                    'min_length_of_recording': float(self.min_length_of_recording),
                    'min_gap_between_recordings': float(self.min_gap_between_recordings)
                }
                
                # Add advanced parameters if supported
                if supported.get('silero_sensitivity'):
                    recorder_config['silero_sensitivity'] = float(self.silero_sensitivity)
                if supported.get('silero_use_onnx'):
                    recorder_config['silero_use_onnx'] = bool(self.silero_use_onnx)
                if supported.get('webrtc_sensitivity'):
                    recorder_config['webrtc_sensitivity'] = int(self.webrtc_sensitivity)
                if supported.get('beam_size'):
                    recorder_config['beam_size'] = int(self.beam_size)
                if supported.get('beam_size_realtime'):
                    recorder_config['beam_size_realtime'] = int(self.beam_size_realtime)
                if supported.get('initial_prompt'):
                    recorder_config['initial_prompt'] = self.initial_prompt
                if supported.get('early_transcription_on_silence'):
                    recorder_config['early_transcription_on_silence'] = float(self.early_transcription_on_silence)
                
                # Advanced pause detection parameters (likely from server version)
                if supported.get('end_of_sentence_detection_pause'):
                    recorder_config['end_of_sentence_detection_pause'] = float(self.end_of_sentence_detection_pause)
                if supported.get('unknown_sentence_detection_pause'):
                    recorder_config['unknown_sentence_detection_pause'] = float(self.unknown_sentence_detection_pause)
                if supported.get('mid_sentence_detection_pause'):
                    recorder_config['mid_sentence_detection_pause'] = float(self.mid_sentence_detection_pause)
                
                if self.debug_mode:
                    supported_count = sum(supported.values())
                    total_count = len(supported)
                    print(f"{bcolors.OKCYAN}[DEBUG] Using {supported_count}/{total_count} advanced features{bcolors.ENDC}")
                    if supported_count > 0:
                        print(f"{bcolors.OKGREEN}[DEBUG] Active advanced features: {[k for k, v in supported.items() if v]}{bcolors.ENDC}")
                    else:
                        print(f"{bcolors.WARNING}[DEBUG] No advanced features supported - using basic RealtimeSTT version{bcolors.ENDC}")
                
                # Add real-time callback only if real-time typing is enabled
                if self.realtime_typing:
                    recorder_config['on_realtime_transcription_update'] = self.on_realtime_update
                    if self.debug_mode:
                        print("[DEBUG] Real-time callback added")
                
                recorder_config['on_realtime_transcription_stabilized'] = self.on_realtime_stabilized
                
                # Add wake word configuration if enabled
                if self.wake_words_enabled:
                    if self.custom_wakeword_model_path:
                        # Custom model - use OpenWakeWord with workaround
                        recorder_config['wakeword_backend'] = 'oww'
                        recorder_config['wake_words'] = 'hey jarvis'  # Required workaround
                        recorder_config['openwakeword_model_paths'] = self.custom_wakeword_model_path
                        recorder_config['wake_words_sensitivity'] = self.wake_words_sensitivity
                        if self.debug_mode:
                            print(f"[DEBUG] Custom wake word model (OWW): {self.custom_wakeword_model_path}")
                            print(f"[DEBUG] Using 'hey jarvis' as wake_words workaround")
                    else:
                        # Built-in wake words
                        recorder_config['wakeword_backend'] = 'pvporcupine'
                        recorder_config['wake_words'] = self.wake_words
                        recorder_config['wake_words_sensitivity'] = self.wake_words_sensitivity
                        if self.debug_mode:
                            print(f"[DEBUG] Built-in wake word: {self.wake_words}")
                    
                    recorder_config['on_wakeword_detected'] = self.on_wakeword_detected
                    recorder_config['on_wakeword_timeout'] = self.on_wakeword_timeout
                
                self.recorder = AudioToTextRecorder(**recorder_config)
                if self.debug_mode:
                    print("[DEBUG] Recorder created successfully")
                # Notify that the local model is ready
                if self.wake_words_enabled:
                    wake_name = "jimbo" if self.custom_wakeword_model_path else self.wake_words
                    self._show_notification(
                        "Model Ready",
                        f"{self.current_model} loaded — say '{wake_name}' to start"
                    )
                else:
                    self._show_notification(
                        "Model Ready",
                        f"{self.current_model} loaded — ready to record"
                    )
            
            # Start recording in a separate thread
            threading.Thread(target=self._recording_loop, daemon=True).start()
            
        except Exception as e:
            print(f"Error starting recording: {e}")
            self.is_recording = False
    
    def _try_web_interface(self):
        """Try to connect to web interface"""
        try:
            import requests
            response = requests.get('http://127.0.0.1:5000/api/health', timeout=2)
            if response.status_code == 200:
                # Only use the web interface if it is actively recording/processing
                try:
                    data = response.json()
                    if bool(data.get('recorder_active')):
                        threading.Thread(target=self._web_interface_mode, daemon=True).start()
                        return True
                except Exception:
                    # If parsing fails, treat as not available for shared mode
                    pass
        except:
            pass
        return False
    
    def on_realtime_update(self, text):
        """Handle real-time transcription updates."""
        if self.debug_mode:
            print(f"[DEBUG] Real-time update called: recording={self.is_recording}, realtime_typing={self.realtime_typing}, text='{text}'")
        
        if not (self.is_recording and self.realtime_typing and text and text.strip()):
            return

        # Throttle immediately after a finalize event to avoid stale updates
        try:
            if time.time() < float(self.suppress_realtime_until):
                if self.debug_mode:
                    print("[DEBUG] Realtime update suppressed by throttle window after finalize")
                return
        except Exception:
            pass

        processed_text = self.preprocess_realtime_text(text)

        # If this update is effectively the same as the last finalized sentence (or a prefix of it), ignore it
        try:
            if self.last_finalized_text:
                def _norm(s: str) -> str:
                    s = (s or "").strip().lower()
                    s = re.sub(r"[.!?\s]+$", "", s)  # trim trailing punct/space
                    s = re.sub(r"\s+", " ", s)
                    return s
                new_n = _norm(processed_text)
                fin_n = _norm(self.last_finalized_text)
                if new_n and fin_n and fin_n.startswith(new_n):
                    if self.debug_mode:
                        print(f"[DEBUG] Realtime update ignored (subset of finalized): '{processed_text}' ~ '{self.last_finalized_text}'")
                    return
        except Exception as e:
            if self.debug_mode:
                print(f"[DEBUG] Realtime compare error: {e}")

        if self.debug_mode:
            print(f"[DEBUG] Processed text: '{processed_text}', Last typed: '{self.last_typed_text}'")
        self.type_realtime_text(processed_text)
    
    def on_realtime_stabilized(self, text):
        """Mirror the web interface: do nothing on stabilized updates for typing.
        Finalization only happens on full sentence events."""
        if self.debug_mode:
            try:
                t = (text or "").strip()
                if t:
                    print("[DEBUG] Stabilized received (no-op for typing)")
            except Exception:
                pass
        return
    
    def on_wakeword_detected(self):
        """Handle wake word detection."""
        wake_word_name = "jimbo" if self.custom_wakeword_model_path else self.wake_words
        if self.debug_mode:
            print(f"[DEBUG] Wake word '{wake_word_name}' detected!")
        print(f"🎤 Wake word '{wake_word_name}' detected - listening...")
    
    def on_wakeword_timeout(self):
        """Handle wake word timeout."""
        if self.debug_mode:
            print("[DEBUG] Wake word timeout - back to listening for wake word")
        print("⏰ No speech detected after wake word - back to listening...")
    
    def preprocess_realtime_text(self, text):
        """Preprocess real-time text for typing.
        Keep transformations minimal to reduce disruptive diffs.
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
        
        # Uppercase the first letter to mirror web UI behavior
        if text:
            text = text[0].upper() + text[1:]
        
        return text
    
    def type_realtime_text(self, text):
        """Type real-time text by fully replacing the current live region.
        This mirrors the web UI which redraws the entire realtime span each update."""
        if not text:
            return

        with self.typing_lock:
            try:
                old = self.last_typed_text or ""
                new = text

                if new == old:
                    return

                if new.startswith(old):
                    # Fast path: just type the new suffix
                    suffix = new[len(old):]
                    if suffix:
                        if self.debug_mode:
                            print(f"[DEBUG] Realtime extend: typing suffix '{suffix}'")
                        pyautogui.typewrite(suffix)
                else:
                    # Clear entire previous live region, then type new (mirror web clear_and_type_realtime)
                    old_len = len(old)
                    if old_len > 0:
                        if self.debug_mode:
                            print(f"[DEBUG] Realtime replace: clearing live region of {old_len} chars")
                        # Match interface behavior: backspace one char at a time
                        # (kept bounded by max_backspaces_per_update for safety)
                        to_clear = min(old_len, int(self.max_backspaces_per_update))
                        for _ in range(to_clear):
                            pyautogui.press('backspace')
                        # If more than cap, clear remaining in capped batches
                        if old_len > to_clear:
                            remaining = old_len - to_clear
                            while remaining > 0:
                                batch = min(remaining, int(self.max_backspaces_per_update))
                                for _ in range(batch):
                                    pyautogui.press('backspace')
                                remaining -= batch
                    if new:
                        pyautogui.typewrite(new)

                self.last_typed_text = new
            except Exception as e:
                if self.debug_mode:
                    print(f"[DEBUG] Error in type_realtime_text: {e}")
                self.last_typed_text = ""
    
    def reset_realtime_state(self):
        """Reset real-time typing state."""
        with self.typing_lock:
            if self.debug_mode:
                print(f"[DEBUG] Resetting real-time state. Last typed was: '{self.last_typed_text}'")
            self.last_typed_text = ""
            self.is_realtime_mode = False
            self.last_finalized_text = ""
    
    def _web_interface_mode(self):
        """Use web interface for transcription"""
        try:
            import socketio
            
            sio = socketio.Client()
            
            @sio.event
            def realtime_update(data):
                if not (self.is_recording and self.realtime_typing):
                    return
                text = data.get('text', '')
                if not text or not text.strip():
                    return
                # Drop updates during suppression window
                try:
                    if time.time() < float(self.suppress_realtime_until):
                        if self.debug_mode:
                            print("[DEBUG] (Web) Realtime update suppressed by throttle window after finalize")
                        return
                except Exception:
                    pass
                processed = self.preprocess_realtime_text(text) or ""
                # Ignore if redundant with last finalized
                try:
                    if self.last_finalized_text:
                        def _norm(s: str) -> str:
                            s = (s or "").strip().lower()
                            s = re.sub(r"[.!?\s]+$", "", s)
                            s = re.sub(r"\s+", " ", s)
                            return s
                        if _norm(self.last_finalized_text).startswith(_norm(processed)):
                            if self.debug_mode:
                                print(f"[DEBUG] (Web) Realtime update ignored (subset of finalized): '{processed}'")
                            return
                except Exception:
                    pass
                self.type_realtime_text(processed)
            
            @sio.event
            def full_sentence_update(data):
                if not self.is_recording:
                    return
                text = data.get('text', '')
                if not text or not text.strip():
                    return
                processed_text = self.process_text(text)
                if not processed_text:
                    return
                if self.realtime_typing:
                    # Skip duplicate finalizations
                    if processed_text == self.last_finalized_text:
                        if self.debug_mode:
                            print("[DEBUG] (Web) Duplicate final sentence; skipping")
                        return
                    # Finalize realtime: prefer extending when possible to avoid backspacing
                    final_text = processed_text + " "
                    if self.debug_mode:
                        print(f"[DEBUG] (Web) Final sentence: {processed_text}")
                    with self.typing_lock:
                        old_live = self.last_typed_text or ""
                        if final_text.startswith(old_live):
                            suffix = final_text[len(old_live):]
                            if suffix:
                                pyautogui.typewrite(suffix)
                        else:
                            if old_live:
                                # Mirror web behavior: backspace one char at a time
                                to_clear = min(len(old_live), int(self.max_backspaces_per_update))
                                for _ in range(to_clear):
                                    pyautogui.press('backspace')
                                if len(old_live) > to_clear:
                                    remaining = len(old_live) - to_clear
                                    while remaining > 0:
                                        batch = min(remaining, int(self.max_backspaces_per_update))
                                        for _ in range(batch):
                                            pyautogui.press('backspace')
                                        remaining -= batch
                            pyautogui.typewrite(final_text)
                        self.last_typed_text = ""
                        self.last_finalized_text = processed_text
                        self.suppress_realtime_until = time.time() + float(self.finalize_suppress_window)
                else:
                    # Non-realtime: append full sentence directly
                    self.insert_text(processed_text)
            
            sio.connect('http://127.0.0.1:5000')
            
            while self.is_recording:
                time.sleep(0.1)
                
            sio.disconnect()
            
        except Exception as e:
            print(f"Web interface mode error: {e}")
            # Fallback to standalone mode
            self._recording_loop()
    
    def _recording_loop(self):
        """Main recording loop"""
        try:
            while self.is_recording and self.recorder:
                text = self.recorder.text()
                if text and text.strip():
                    # Only process final sentences if not using real-time typing
                    if not self.realtime_typing:
                        processed_text = self.process_text(text)
                        if processed_text:  # Only insert if not a voice command
                            self.insert_text(processed_text)
                    else:
                        # In real-time mode, finalize here like the web app does on full_sentence_update
                        processed_text = self.process_text(text)
                        if not processed_text:
                            continue
                        if processed_text == self.last_finalized_text:
                            if self.debug_mode:
                                print("[DEBUG] Duplicate final sentence (polling); skipping")
                            continue
                        final_text = processed_text + " "
                        if self.debug_mode:
                            print(f"[DEBUG] Final sentence (polling): {processed_text}")
                        with self.typing_lock:
                            old_live = self.last_typed_text or ""
                            if final_text.startswith(old_live):
                                suffix = final_text[len(old_live):]
                                if suffix:
                                    pyautogui.typewrite(suffix)
                            else:
                                if old_live:
                                    # Mirror web behavior: backspace one char at a time
                                    to_clear = min(len(old_live), int(self.max_backspaces_per_update))
                                    for _ in range(to_clear):
                                        pyautogui.press('backspace')
                                    if len(old_live) > to_clear:
                                        remaining = len(old_live) - to_clear
                                        while remaining > 0:
                                            batch = min(remaining, int(self.max_backspaces_per_update))
                                            for _ in range(batch):
                                                pyautogui.press('backspace')
                                            remaining -= batch
                                pyautogui.typewrite(final_text)
                            self.last_typed_text = ""
                            self.last_finalized_text = processed_text
                            self.suppress_realtime_until = time.time() + float(self.finalize_suppress_window)
        except Exception as e:
            print(f"Recording loop error: {e}")
        finally:
            self.is_recording = False
    
    def stop_recording(self):
        """Stop speech recognition"""
        self.is_recording = False
        self.reset_realtime_state()
        if self.debug_mode:
            print("[DEBUG] Recording stopped, real-time state reset")
        print("Recording stopped")
    
    def toggle_recording(self):
        """Toggle recording on/off"""
        if self.is_recording:
            self.stop_recording()
        else:
            self.start_recording()
    
    def process_text(self, text):
        """Process transcribed text with advanced formatting"""
        if not text or not text.strip():
            return text
        
        # Check for voice commands first
        if self.voice_commands_enabled:
            command_result = self.voice_commands.process_command(text)
            if command_result:
                if isinstance(command_result, str):
                    if command_result == "STOP_RECORDING":
                        self.stop_recording()
                        return None
                    elif command_result.startswith("SWITCH_MODEL:"):
                        model_name = command_result.split(":")[1]
                        self.change_model(model_name)
                        return None
                return None
        
        # Apply smart text processing
        if self.smart_text_processing:
            processed_text = self.text_processor.process_text(text)
        else:
            processed_text = text.capitalize() if text else text
            if processed_text and not processed_text.endswith(('.', '!', '?')):
                processed_text += '.'
        
        return processed_text
    
    def insert_text(self, text):
        """Insert text based on selected mode"""
        if self.insert_mode == "type":
            pyautogui.typewrite(text + " ")
        elif self.insert_mode == "clipboard":
            pyautogui.hotkey('ctrl', 'c')  # Copy current selection
            time.sleep(0.1)
            # Add to clipboard and paste
            import pyperclip
            pyperclip.copy(text)
            pyautogui.hotkey('ctrl', 'v')
        elif self.insert_mode == "replace":
            pyautogui.hotkey('ctrl', 'a')  # Select all
            time.sleep(0.1)
            pyautogui.typewrite(text)
    
    def show_settings(self):
        """Show settings window"""
        # Create a fresh Tk window for settings to ensure it opens reliably
        settings_window = tk.Tk()
        settings_window.title("Global STT Settings")
        settings_window.geometry("500x1000")
        settings_window.resizable(False, False)
        settings_window.configure(bg='#f0f0f0')

        # Ensure focus/topmost briefly so first click registers
        settings_window.lift()
        settings_window.attributes('-topmost', True)
        settings_window.after(200, lambda: settings_window.attributes('-topmost', False))
        settings_window.focus_force()
        
        # Model selection
        tk.Label(settings_window, text="Model:", font=("Arial", 10, "bold")).pack(pady=5)
        model_var = tk.StringVar(value=self.current_model)
        model_combo = ttk.Combobox(settings_window, textvariable=model_var, values=[
            "tiny.en", "base.en", "small.en", "medium.en", "large-v1", "large-v2", "large-v3", "large-v3-turbo"
        ], state="readonly")
        model_combo.pack(pady=5)
        
        # Text processing options
        tk.Label(settings_window, text="Text Processing:", font=("Arial", 10, "bold")).pack(pady=(15,5))
        
        auto_punct_var = tk.BooleanVar(value=self.auto_punctuation)
        tk.Checkbutton(settings_window, text="Auto Punctuation", variable=auto_punct_var).pack()
        
        auto_cap_var = tk.BooleanVar(value=self.auto_capitalize)
        tk.Checkbutton(settings_window, text="Auto Capitalize", variable=auto_cap_var).pack()
        
        realtime_var = tk.BooleanVar(value=self.realtime_typing)
        tk.Checkbutton(settings_window, text="Real-time Typing (type as you speak)", variable=realtime_var).pack()

        # Realtime tuning
        tk.Label(settings_window, text="Realtime Tuning:", font=("Arial", 10, "bold")).pack(pady=(15,5))

        # Helper to add labeled horizontal scales
        def add_scale(parent, label, from_, to, resolution, init_val, fmt="{:.2f}", is_int=False):
            frame = tk.Frame(parent)
            frame.pack(fill='x', padx=6, pady=2)
            tk.Label(frame, text=label, font=("Arial", 9)).pack(anchor='w')
            var = tk.IntVar(value=int(init_val)) if is_int else tk.DoubleVar(value=float(init_val))
            val_label = tk.Label(frame, text=(str(int(init_val)) if is_int else fmt.format(float(init_val))), font=("Arial", 8))
            val_label.pack(anchor='e')
            def on_change(v):
                try:
                    val_label.config(text=(str(int(float(v))) if is_int else fmt.format(float(v))))
                except Exception:
                    pass
            scale = tk.Scale(frame, from_=from_, to=to, resolution=resolution, orient=tk.HORIZONTAL, showvalue=False, length=360, command=on_change, variable=var)
            scale.pack(fill='x')
            return var

        rp_pause_var = add_scale(settings_window, "Realtime Processing Pause (s)", 0.005, 0.1, 0.005, self.realtime_processing_pause)
        pssd_var = add_scale(settings_window, "Post-speech Silence (s)", 0.2, 2.0, 0.05, self.post_speech_silence_duration)
        min_len_var = add_scale(settings_window, "Min Utterance Length (s)", 0.1, 1.0, 0.05, self.min_length_of_recording)
        min_gap_var = add_scale(settings_window, "Min Gap Between Recordings (s)", 0.0, 0.5, 0.01, self.min_gap_between_recordings)
        suppress_var = add_scale(settings_window, "Finalize Suppression Window (s)", 0.0, 1.0, 0.05, self.finalize_suppress_window)
        max_bksp_var = add_scale(settings_window, "Max Backspaces Per Update", 32, 1024, 32, self.max_backspaces_per_update, fmt="{}", is_int=True)
        
        # Advanced VAD Settings
        tk.Label(settings_window, text="Advanced VAD Settings:", font=("Arial", 10, "bold")).pack(pady=(15,5))
        
        silero_sens_var = add_scale(settings_window, "Silero VAD Sensitivity", 0.01, 1.0, 0.01, self.silero_sensitivity)
        webrtc_sens_var = add_scale(settings_window, "WebRTC VAD Sensitivity", 0, 3, 1, self.webrtc_sensitivity, fmt="{}", is_int=True)
        early_trans_var = add_scale(settings_window, "Early Transcription on Silence (s)", 0.0, 1.0, 0.05, self.early_transcription_on_silence)
        
        silero_onnx_var = tk.BooleanVar(value=self.silero_use_onnx)
        tk.Checkbutton(settings_window, text="Use Silero ONNX (faster)", variable=silero_onnx_var).pack()
        
        # Enhanced Model Parameters
        tk.Label(settings_window, text="Model Parameters:", font=("Arial", 10, "bold")).pack(pady=(15,5))
        
        beam_size_var = add_scale(settings_window, "Main Model Beam Size", 1, 10, 1, self.beam_size, fmt="{}", is_int=True)
        beam_realtime_var = add_scale(settings_window, "Realtime Model Beam Size", 1, 5, 1, self.beam_size_realtime, fmt="{}", is_int=True)
        batch_size_var = add_scale(settings_window, "Batch Size", 1, 32, 1, self.batch_size, fmt="{}", is_int=True)
        
        # Advanced Pause Detection
        tk.Label(settings_window, text="Intelligent Pause Detection:", font=("Arial", 10, "bold")).pack(pady=(15,5))
        
        end_pause_var = add_scale(settings_window, "End of Sentence Pause (s)", 0.1, 2.0, 0.05, self.end_of_sentence_detection_pause)
        unknown_pause_var = add_scale(settings_window, "Unknown Sentence Pause (s)", 0.1, 3.0, 0.1, self.unknown_sentence_detection_pause)
        mid_pause_var = add_scale(settings_window, "Mid Sentence Pause (s)", 0.5, 5.0, 0.1, self.mid_sentence_detection_pause)
        
        # Wake word settings
        tk.Label(settings_window, text="Wake Words:", font=("Arial", 10, "bold")).pack(pady=(15,5))
        
        wake_enabled_var = tk.BooleanVar(value=self.wake_words_enabled)
        tk.Checkbutton(settings_window, text="Enable Wake Words", variable=wake_enabled_var).pack()
        
        tk.Label(settings_window, text="Wake Word:", font=("Arial", 9)).pack(pady=(5,0))
        wake_word_var = tk.StringVar(value=self.wake_words if not self.custom_wakeword_model_path else "custom")
        wake_word_combo = ttk.Combobox(settings_window, textvariable=wake_word_var, values=[
            "custom", "jarvis", "computer", "hey google", "hey siri", "ok google", "alexa", 
            "porcupine", "bumblebee", "terminator", "picovoice", "americano", 
            "blueberry", "grapefruits", "grasshopper"
        ], state="readonly", width=15)
        wake_word_combo.pack(pady=2)
        
        # Sensitivity
        tk.Label(settings_window, text="Sensitivity (0.0-1.0):", font=("Arial", 9)).pack(pady=(5,0))
        sensitivity_var = tk.StringVar(value=str(self.wake_words_sensitivity if self.wake_words_sensitivity is not None else 0.6))
        sensitivity_entry = tk.Entry(settings_window, textvariable=sensitivity_var, width=10)
        sensitivity_entry.pack(pady=2)

        tk.Label(settings_window, text="Custom Model Path:", font=("Arial", 9)).pack(pady=(5,0))
        custom_model_var = tk.StringVar(value=self.custom_wakeword_model_path or "")
        custom_model_entry = tk.Entry(settings_window, textvariable=custom_model_var, width=40)
        custom_model_entry.pack(pady=2)
        
        def browse_model():
            try:
                from tkinter import filedialog
                settings_window.attributes('-topmost', False)  # Allow file dialog to appear
                filename = filedialog.askopenfilename(
                    parent=settings_window,
                    title="Select Custom Wake Word Model",
                    filetypes=[("Model files", "*.ppn *.onnx *.pth"), ("All files", "*.*")]
                )
                if filename:
                    custom_model_var.set(filename)
                    wake_word_var.set("custom")
                    settings_window.update_idletasks()
                settings_window.lift()  # Bring settings window back to front
            except Exception as e:
                print(f"Browse error: {e}")
        
        browse_btn = tk.Button(settings_window, text="Browse...", command=browse_model, font=("Arial", 8))
        browse_btn.pack(pady=2)
        
        # Helper to enable/disable wake-related controls
        def update_wake_controls():
            enabled = wake_enabled_var.get()
            if enabled:
                wake_word_combo.configure(state='readonly')
                sensitivity_entry.configure(state='normal')
                if wake_word_var.get() == 'custom':
                    custom_model_entry.configure(state='normal')
                    browse_btn.configure(state='normal')
                else:
                    custom_model_entry.configure(state='disabled')
                    browse_btn.configure(state='disabled')
            else:
                wake_word_combo.configure(state='disabled')
                sensitivity_entry.configure(state='disabled')
                custom_model_entry.configure(state='disabled')
                browse_btn.configure(state='disabled')

        def on_wake_word_change(*args):
            try:
                update_wake_controls()
                settings_window.update_idletasks()
            except Exception as e:
                print(f"Wake word change error: {e}")
        wake_word_var.trace('w', on_wake_word_change)

        def on_wake_enabled_change(*args):
            try:
                if wake_enabled_var.get():
                    # Ensure a sensible default when enabling
                    try:
                        val = float(sensitivity_var.get())
                    except Exception:
                        val = -1
                    if not (0.0 <= val <= 1.0):
                        sensitivity_var.set("0.6")
                update_wake_controls()
                settings_window.update_idletasks()
            except Exception as e:
                print(f"Wake enable change error: {e}")
        wake_enabled_var.trace('w', on_wake_enabled_change)

        # Set initial state for wake controls
        update_wake_controls()
        
        # Insert mode
        tk.Label(settings_window, text="Insert Mode:", font=("Arial", 10, "bold")).pack(pady=(15,5))
        insert_var = tk.StringVar(value=self.insert_mode)
        for mode, desc in [("type", "Type directly"), ("clipboard", "Use clipboard"), ("replace", "Replace all text")]:
            tk.Radiobutton(settings_window, text=desc, variable=insert_var, value=mode).pack()
        
        # Hotkeys info
        tk.Label(settings_window, text="Hotkeys:", font=("Arial", 10, "bold")).pack(pady=(15,5))
        tk.Label(settings_window, text=f"Start: {self.start_hotkey.upper()}", font=("Arial", 8)).pack()
        tk.Label(settings_window, text=f"Stop: {self.stop_hotkey.upper()}", font=("Arial", 8)).pack()
        tk.Label(settings_window, text=f"Toggle: {self.toggle_hotkey.upper()}", font=("Arial", 8)).pack()
        
        def save_and_close():
            try:
                # Disable buttons to prevent double-clicks
                save_btn.config(state='disabled')
                cancel_btn.config(state='disabled')
                settings_window.update_idletasks()
                
                old_realtime_setting = self.realtime_typing
                
                self.current_model = model_var.get()
                self.auto_punctuation = auto_punct_var.get()
                self.auto_capitalize = auto_cap_var.get()
                self.insert_mode = insert_var.get()
                self.realtime_typing = realtime_var.get()
                self.wake_words_enabled = wake_enabled_var.get()
                
                if wake_word_var.get() == "custom":
                    self.custom_wakeword_model_path = custom_model_var.get().strip() or None
                    self.wake_words = "custom"
                else:
                    self.wake_words = wake_word_var.get()
                    self.custom_wakeword_model_path = None
                
                try:
                    self.wake_words_sensitivity = float(sensitivity_var.get())
                    if not 0.0 <= self.wake_words_sensitivity <= 1.0:
                        self.wake_words_sensitivity = 0.6
                except ValueError:
                    self.wake_words_sensitivity = 0.6
                
                # Realtime tuning values
                try:
                    self.realtime_processing_pause = float(rp_pause_var.get())
                except Exception:
                    pass
                try:
                    self.post_speech_silence_duration = float(pssd_var.get())
                except Exception:
                    pass
                try:
                    self.min_length_of_recording = float(min_len_var.get())
                except Exception:
                    pass
                try:
                    self.min_gap_between_recordings = float(min_gap_var.get())
                except Exception:
                    pass
                try:
                    self.finalize_suppress_window = float(suppress_var.get())
                except Exception:
                    pass
                try:
                    self.max_backspaces_per_update = int(max_bksp_var.get())
                except Exception:
                    pass
                
                # Advanced VAD settings
                try:
                    self.silero_sensitivity = float(silero_sens_var.get())
                except Exception:
                    pass
                try:
                    self.webrtc_sensitivity = int(webrtc_sens_var.get())
                except Exception:
                    pass
                try:
                    self.early_transcription_on_silence = float(early_trans_var.get())
                except Exception:
                    pass
                self.silero_use_onnx = silero_onnx_var.get()
                
                # Enhanced model parameters
                try:
                    self.beam_size = int(beam_size_var.get())
                except Exception:
                    pass
                try:
                    self.beam_size_realtime = int(beam_realtime_var.get())
                except Exception:
                    pass
                try:
                    self.batch_size = int(batch_size_var.get())
                except Exception:
                    pass
                
                # Advanced pause detection
                try:
                    self.end_of_sentence_detection_pause = float(end_pause_var.get())
                except Exception:
                    pass
                try:
                    self.unknown_sentence_detection_pause = float(unknown_pause_var.get())
                except Exception:
                    pass
                try:
                    self.mid_sentence_detection_pause = float(mid_pause_var.get())
                except Exception:
                    pass

                self.save_settings()

                # Apply potentially heavy runtime changes in the background
                def apply_runtime_changes():
                    try:
                        if self.recorder and (old_realtime_setting != self.realtime_typing):
                            print("Real-time setting changed, recreating recorder...")
                            self.recorder.shutdown()
                            self.recorder = None
                        elif self.recorder:
                            # Recreate to apply model or other changes
                            self.recorder.shutdown()
                            self.recorder = None
                        # Update tray menu with new labels/status
                        self.update_menu()
                    except Exception as e:
                        print(f"Apply changes error: {e}")

                threading.Thread(target=apply_runtime_changes, daemon=True).start()

                # Close immediately for responsiveness
                settings_window.destroy()
            except Exception as e:
                print(f"Save error: {e}")
                settings_window.destroy()
        
        # Button frame
        button_frame = tk.Frame(settings_window)
        button_frame.pack(pady=20)
        
        save_btn = tk.Button(button_frame, text="Save & Close", command=save_and_close, 
                 bg="#4CAF50", fg="white", font=("Arial", 10, "bold"), width=12, height=2)
        save_btn.pack(side=tk.LEFT, padx=10)
        
        cancel_btn = tk.Button(button_frame, text="Cancel", command=lambda: settings_window.destroy(), 
                 bg="#f44336", fg="white", font=("Arial", 10, "bold"), width=12, height=2)
        cancel_btn.pack(side=tk.LEFT, padx=10)
        
        # Handle window close button
        settings_window.protocol("WM_DELETE_WINDOW", lambda: settings_window.destroy())

        # Run a local event loop for this window
        settings_window.mainloop()
    
    def open_web_interface(self):
        """Open web interface in browser"""
        try:
            import webbrowser
            import subprocess
            import os
            
            # Check if web server is running
            try:
                import requests
                requests.get('http://127.0.0.1:5000/api/health', timeout=2)
                print("Web server is already running")
            except:
                print("Starting web server...")
                # Start the web server
                subprocess.Popen([sys.executable, "app.py"], cwd=os.path.dirname(__file__))
                time.sleep(3)  # Wait for server to start
            
            # Open the enhanced interface
            interface_path = os.path.join(os.path.dirname(__file__), "enhanced_interface.html")
            webbrowser.open(f"file://{interface_path}")
            
        except Exception as e:
            print(f"Error opening web interface: {e}")
    
    def change_model(self, model_name):
        """Change the current model"""
        if self.is_recording:
            print("Stop recording before changing model")
            return
            
        self.current_model = model_name
        self.save_settings()
        
        # Shutdown current recorder to free memory
        if self.recorder:
            self.recorder.shutdown()
            self.recorder = None
        
        print(f"{bcolors.OKGREEN}Model changed to: {bcolors.OKBLUE}{model_name}{bcolors.ENDC}")
        
        # Update the menu to show current model
        if getattr(self, 'icon', None):
            self.update_menu()
    
    def update_menu(self):
        """Update the system tray menu"""
        if not getattr(self, 'icon', None):
            return
        # Recreate the menu with updated model name
        model_menu = pystray.Menu(
            pystray.MenuItem("tiny.en (Fastest)", lambda: self.change_model("tiny.en")),
            pystray.MenuItem("base.en (Fast)", lambda: self.change_model("base.en")),
            pystray.MenuItem("small.en (Balanced)", lambda: self.change_model("small.en")),
            pystray.MenuItem("medium.en (Accurate)", lambda: self.change_model("medium.en")),
            pystray.MenuItem("large-v1 (High Accuracy)", lambda: self.change_model("large-v1")),
            pystray.MenuItem("large-v2 (Better Accuracy)", lambda: self.change_model("large-v2")),
            pystray.MenuItem("large-v3 (Most Accurate)", lambda: self.change_model("large-v3")),
            pystray.MenuItem("large-v3-turbo (Ultra Fast)", lambda: self.change_model("large-v3-turbo"))
        )
        
        wake_status = f"Wake: {self.wake_words}" if self.wake_words_enabled else "Wake: Disabled"
        
        menu = pystray.Menu(
            pystray.MenuItem("Start Recording", self.start_recording),
            pystray.MenuItem("Stop Recording", self.stop_recording),
            pystray.MenuItem(f"Model: {self.current_model}", model_menu),
            pystray.MenuItem(wake_status, self.show_settings),
            pystray.MenuItem("Settings", self.show_settings),
            pystray.MenuItem("Web Interface", self.open_web_interface),
            pystray.MenuItem("Status", self.show_status),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Exit", self.quit_application)
        )
        
        self.icon.menu = menu
    
    def show_status(self):
        """Show current status"""
        try:
            import requests
            response = requests.get('http://127.0.0.1:5000/api/health', timeout=2)
            web_status = "🟢 Running" if response.status_code == 200 else "🔴 Stopped"
        except:
            web_status = "🔴 Stopped"
        
        global_status = "🟢 Running" if self.is_recording else "🔴 Stopped"
        
        import tkinter as tk
        from tkinter import messagebox
        
        root = tk.Tk()
        root.withdraw()  # Hide the main window
        
        messagebox.showinfo("STT System Status", 
                           f"Web Interface: {web_status}\n"
                           f"Global STT: {global_status}\n\n"
                           f"Model: {self.current_model}\n"
                           f"Both can run simultaneously!")
        
        root.destroy()
    
    def quit_application(self):
        """Quit the application"""
        try:
            self.is_recording = False
            if self.recorder:
                self.recorder.shutdown()
            # Force stop the icon with a timeout
            import threading
            def force_stop():
                time.sleep(1)
                os._exit(0)
            threading.Thread(target=force_stop, daemon=True).start()
            self.icon.stop()
        except:
            pass
        os._exit(0)
    
    def run(self):
        """Run the system tray application"""
        print(f"{bcolors.BOLD}{bcolors.OKGREEN}Global STT Manager started!{bcolors.ENDC}")
        print(f"{bcolors.OKCYAN}Hotkeys: {bcolors.OKBLUE}Start={self.start_hotkey}, Stop={self.stop_hotkey}, Toggle={self.toggle_hotkey}{bcolors.ENDC}")
        print(f"{bcolors.WARNING}Check system tray for controls.{bcolors.ENDC}")
        self.icon.run()

if __name__ == "__main__":
    manager = None
    
    def signal_handler(sig, frame):
        print("\nShutting down...")
        if manager:
            try:
                manager.quit_application()
            except:
                pass
        os._exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        manager = GlobalSTTManager()
        manager.run()
    except Exception as e:
        print(f"Error: {e}")
        if manager:
            try:
                manager.quit_application()
            except:
                pass
