"""
Refactored Global STT Manager
Clean, modular implementation using the new architecture
"""

import threading
import time
import logging
import keyboard
from typing import Optional, Callable

from .config import get_config, DEFAULT_HOTKEYS
from .unified_text_processor import get_text_processor
from .realtime_typing_manager import get_typing_manager
from .audio_notifications import get_notification_manager
from .model_ready_events import get_model_event_manager, ModelState


class RefactoredGlobalSTTManager:
    """
    Simplified, modular Global STT Manager.
    All complex logic moved to dedicated components.
    """
    
    def __init__(self, enable_hotkeys: bool = True):
        # Core components
        self.config = get_config()
        self.text_processor = get_text_processor(self._handle_voice_command)
        self.typing_manager = get_typing_manager()
        self.notification_manager = get_notification_manager()
        # Configure notification manager with settings
        self.notification_manager.set_enabled(self.config.config.audio_notifications.enabled)
        self.notification_manager.set_volume(self.config.config.audio_notifications.volume)
        self.model_event_manager = get_model_event_manager()
        
        # Setup model ready callback
        self.model_event_manager.add_state_callback(
            ModelState.READY, 
            self._on_model_ready
        )
        
        # State
        self.recorder = None
        self.is_recording = False
        self.recording_thread = None
        
        # Audio enhancer (optional)
        self.audio_enhancer = None
        self._try_load_audio_enhancer()
        
        # Hotkeys
        if enable_hotkeys:
            self._setup_hotkeys()
        
        # Logging
        self._setup_logging()
        
        # Notification callback (set by Qt tray)
        self.notification_callback: Optional[Callable[[str, str], None]] = None
    
    def _try_load_audio_enhancer(self):
        """Try to load audio enhancer if available"""
        try:
            from audio_enhancements import AudioEnhancer
            self.audio_enhancer = AudioEnhancer()
            if self.audio_enhancer.noise_profile is None:
                self.audio_enhancer.load_noise_profile()
        except ImportError:
            print("Audio enhancer not available")
    
    def _setup_logging(self):
        """Setup logging if not already configured"""
        try:
            # Let the config module handle logging setup
            pass
        except Exception as e:
            print(f"Logging setup error: {e}")
    
    def _setup_hotkeys(self):
        """Setup global hotkeys"""
        try:
            keyboard.add_hotkey(DEFAULT_HOTKEYS["start"], self.start_recording)
            keyboard.add_hotkey(DEFAULT_HOTKEYS["stop"], self.stop_recording)
            keyboard.add_hotkey(DEFAULT_HOTKEYS["toggle"], self.toggle_recording)
            keyboard.add_hotkey(DEFAULT_HOTKEYS["calibrate"], self.calibrate_noise)
        except Exception as e:
            print(f"Hotkey setup error: {e}")
    
    def _handle_voice_command(self, command: str):
        """Handle voice command results"""
        if command == "STOP_RECORDING":
            self.stop_recording()
        elif command.startswith("SWITCH_MODEL:"):
            model_name = command.split(":", 1)[1]
            self.change_model(model_name)
        elif command == "COMMAND_EXECUTED":
            # Play command sound and notify
            if self.config.config.audio_notifications.play_command_sound:
                self.notification_manager.play_command()
            if self.notification_callback:
                self.notification_callback("Command", "Voice command executed")
    
    def _show_notification(self, title: str, message: str):
        """Show notification via callback or fallback"""
        if self.notification_callback:
            self.notification_callback(title, message)
        else:
            print(f"[{title}] {message}")
    
    def _on_model_ready(self):
        """Callback when model becomes ready"""
        # Play ready sound
        if self.config.config.audio_notifications.play_ready_sound:
            self.notification_manager.play_ready()
        
        # Show notification with timing info
        duration = self.model_event_manager.get_initialization_duration()
        if duration:
            message = f"Ready to transcribe ({duration:.1f}s load time)"
        else:
            message = "Ready to transcribe"
        
        self._show_notification("Model Ready", message)
    
    def start_recording(self):
        """Start speech recognition"""
        if self.is_recording:
            return
        
        try:
            self.is_recording = True
            self.typing_manager.reset_state()
            
            # Play start sound
            if self.config.config.audio_notifications.play_start_sound:
                self.notification_manager.play_start()
            
            config = self.config.config
            if config.wake_word.enabled:
                self._show_notification(
                    "STT Ready", 
                    f"Listening for wake word: '{config.wake_word.wake_words}'"
                )
            else:
                self._show_notification(
                    "STT Started", 
                    f"Recording with model: {config.basic.model}"
                )
            
            # Start recording in background thread
            self.recording_thread = threading.Thread(
                target=self._recording_loop, 
                daemon=True
            )
            self.recording_thread.start()
            
        except Exception as e:
            print(f"Error starting recording: {e}")
            # Play error sound
            if self.config.config.audio_notifications.play_error_sound:
                self.notification_manager.play_error()
            self.is_recording = False
    
    def stop_recording(self):
        """Stop speech recognition"""
        self.is_recording = False
        self.typing_manager.reset_state()
        
        # Play stop sound
        if self.config.config.audio_notifications.play_stop_sound:
            self.notification_manager.play_stop()
        
        if self.recorder:
            try:
                self.recorder.shutdown()
                # Mark model as shutdown
                self.model_event_manager.mark_shutdown()
            except Exception as e:
                print(f"Error stopping recorder: {e}")
                # Play error sound for recording stop error
                if self.config.config.audio_notifications.play_error_sound:
                    self.notification_manager.play_error()
            finally:
                self.recorder = None
        
        self._show_notification("STT Stopped", "Recording stopped")
    
    def toggle_recording(self):
        """Toggle recording state"""
        if self.is_recording:
            self.stop_recording()
        else:
            self.start_recording()
    
    def calibrate_noise(self):
        """Calibrate background noise"""
        if self.is_recording:
            print("Stop recording before calibrating noise")
            return
        
        if self.audio_enhancer:
            self._show_notification("Calibrating", "Please remain quiet...")
            threading.Thread(
                target=self.audio_enhancer.calibrate_noise_floor, 
                daemon=True
            ).start()
        else:
            print("Audio enhancer not available")
    
    def change_model(self, model_name: str):
        """Change the current model"""
        if self.is_recording:
            print("Stop recording before changing model")
            return
        
        # Update config
        self.config.config.basic.model = model_name
        self.config.save_settings()
        
        # Shutdown current recorder
        if self.recorder:
            try:
                self.recorder.shutdown()
                self.recorder = None
            except Exception as e:
                print(f"Error changing model: {e}")
        
        self._show_notification("Model Changed", f"Switched to: {model_name}")
    
    def _create_recorder(self):
        """Create recorder with current configuration"""
        # Mark model initialization as starting
        self.model_event_manager.start_initialization()
        
        try:
            from RealtimeSTT import AudioToTextRecorder
            
            # Get complete recorder config with all supported features
            recorder_config = self.config.get_complete_recorder_config()
            
            # Add real-time callbacks if enabled
            if self.config.config.basic.realtime_typing:
                recorder_config['on_realtime_transcription_update'] = self._on_realtime_update
            
            recorder_config['on_realtime_transcription_stabilized'] = self._on_realtime_stabilized
            
            # Add wake word configuration if enabled
            if self.config.config.wake_word.enabled:
                self._configure_wake_words(recorder_config)
            
            # Create recorder (this is the slow part)
            print("Loading AI model... (this may take a moment)")
            self.recorder = AudioToTextRecorder(**recorder_config)
            
            # Warm up (optional)
            try:
                import numpy as np
                dummy_audio = np.zeros(16000, dtype=np.int16)
                self.recorder.feed_audio(dummy_audio.tobytes())
            except Exception:
                pass  # Warm-up is optional
            
            # Mark model as ready (triggers ready callback and sound)
            self.model_event_manager.mark_ready()
            
            return True
            
        except Exception as e:
            print(f"Error creating recorder: {e}")
            # Mark model as having error
            self.model_event_manager.mark_error(e)
            return False
    
    def _configure_wake_words(self, recorder_config: dict):
        """Configure wake word settings in recorder config"""
        wake_config = self.config.config.wake_word
        
        if wake_config.custom_model_path:
            # Custom wake word model
            recorder_config['wakeword_backend'] = 'oww'
            recorder_config['wake_words'] = 'hey jarvis'  # Workaround
            recorder_config['openwakeword_model_paths'] = wake_config.custom_model_path
            
            # Inference framework based on file extension
            import os
            ext = os.path.splitext(wake_config.custom_model_path.lower())[1]
            if ext == '.onnx':
                recorder_config['openwakeword_inference_framework'] = 'onnx'
            elif ext == '.tflite':
                recorder_config['openwakeword_inference_framework'] = 'tflite'
        else:
            # Built-in wake words
            recorder_config['wakeword_backend'] = 'pvporcupine'
            recorder_config['wake_words'] = wake_config.wake_words
        
        recorder_config['wake_words_sensitivity'] = wake_config.sensitivity
        recorder_config['wake_word_timeout'] = wake_config.timeout
        recorder_config['wake_word_activation_delay'] = wake_config.conversation_window
        
        # Wake word callbacks
        recorder_config['on_wakeword_detected'] = self._on_wakeword_detected
        recorder_config['on_wakeword_timeout'] = self._on_wakeword_timeout
        recorder_config['on_recording_stop'] = self._on_recording_stop
    
    def _recording_loop(self):
        """Main recording loop"""
        try:
            if not self._create_recorder():
                self.is_recording = False
                return
            
            # Model ready notification is handled by the event system
            # Wait for model to be ready before proceeding
            if not self.model_event_manager.wait_for_ready(timeout=60):
                print("Model failed to initialize within 60 seconds")
                self.is_recording = False
                return
            
            while self.is_recording and self.recorder:
                try:
                    text = self.recorder.text()
                    if text and text.strip():
                        self._process_final_text(text)
                except Exception as e:
                    print(f"Recording loop error: {e}")
                    if self.config.config.audio_notifications.play_error_sound:
                        self.notification_manager.play_error()
                    break
        
        except Exception as e:
            print(f"Recording thread error: {e}")
            if self.config.config.audio_notifications.play_error_sound:
                self.notification_manager.play_error()
        finally:
            self.is_recording = False
            if self.recorder:
                try:
                    self.recorder.shutdown()
                except:
                    pass
                self.recorder = None
    
    def _on_realtime_update(self, text: str):
        """Handle real-time transcription updates"""
        if not self.is_recording:
            return
        
        processed_text = self.text_processor.preprocess_realtime_text(text)
        self.typing_manager.process_realtime_update(processed_text)
    
    def _on_realtime_stabilized(self, text: str):
        """Handle stabilized real-time updates (no-op for now)"""
        pass
    
    def _on_wakeword_detected(self):
        """Handle wake word detection"""
        wake_name = (
            "custom model" 
            if self.config.config.wake_word.custom_model_path 
            else self.config.config.wake_word.wake_words
        )
        print(f"Wake word '{wake_name}' detected - listening...")
    
    def _on_wakeword_timeout(self):
        """Handle wake word timeout"""
        print("No speech detected - back to listening for wake word...")
    
    def _on_recording_stop(self):
        """Handle recording stop (for conversation window)"""
        try:
            wake_config = self.config.config.wake_word
            if wake_config.enabled and wake_config.conversation_window > 0 and self.recorder:
                # Keep listening briefly without wake word
                self.recorder.listen()
        except Exception as e:
            print(f"Recording stop handler error: {e}")
    
    def _process_final_text(self, text: str):
        """Process final transcribed text"""
        processed_text = self.text_processor.process_final_text(text)
        
        if processed_text:  # None means it was a voice command
            if self.config.config.basic.realtime_typing:
                # Finalize in real-time mode
                self.typing_manager.finalize_text(processed_text)
            else:
                # Direct typing mode
                self.typing_manager.insert_text(processed_text)
    
    def apply_config_changes(self):
        """Apply configuration changes (called after settings save)"""
        try:
            # Recreate recorder if recording to apply new settings
            if self.is_recording and self.recorder:
                self.recorder.shutdown()
                self.recorder = None
                # Recorder will be recreated in recording loop
        except Exception as e:
            print(f"Error applying config changes: {e}")
    
    def get_status(self) -> dict:
        """Get current system status"""
        model_status = self.model_event_manager.get_status_info()
        
        return {
            'is_recording': self.is_recording,
            'current_model': self.config.config.basic.model,
            'realtime_typing': self.config.config.basic.realtime_typing,
            'wake_words_enabled': self.config.config.wake_word.enabled,
            'wake_word': self.config.config.wake_word.wake_words,
            'recorder_active': self.recorder is not None,
            'model_state': model_status['state'],
            'model_ready': model_status['is_ready'],
            'model_initializing': model_status['is_initializing'],
            'model_load_time': model_status['initialization_duration']
        }