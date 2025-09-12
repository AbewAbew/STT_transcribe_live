"""
Unified Qt Settings Dialog
Consolidated settings UI using the new configuration system
"""

import os
import threading
from typing import Callable, Optional

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QCheckBox, QComboBox,
    QLineEdit, QPushButton, QRadioButton, QButtonGroup, QFileDialog,
    QFormLayout, QDoubleSpinBox, QSpinBox, QWidget, QTabWidget, QScrollArea
)
from PySide6.QtCore import Qt

from .config import get_config, AVAILABLE_MODELS, AVAILABLE_WAKE_WORDS


class QtSettingsDialog(QDialog):
    """Modern Qt settings dialog with tabbed interface"""
    
    def __init__(self, manager, refresh_callback: Optional[Callable] = None, parent=None):
        super().__init__(parent)
        self.manager = manager
        self.refresh_callback = refresh_callback
        self.config = get_config()
        
        self.setWindowTitle("Global STT Settings")
        self.setMinimumSize(800, 600)
        self.setModal(True)
        
        self._setup_ui()
        self._load_current_settings()
        self._setup_connections()
    
    def _setup_ui(self):
        """Setup the user interface with tabs"""
        layout = QVBoxLayout(self)
        
        # Create tab widget
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        
        # Create tabs
        self._create_basic_tab()
        self._create_realtime_tab()
        self._create_wake_word_tab()
        self._create_advanced_tab()
        
        # Buttons
        button_layout = QHBoxLayout()
        self.save_btn = QPushButton("Save & Close")
        self.cancel_btn = QPushButton("Cancel")
        self.reset_btn = QPushButton("Reset to Defaults")
        
        button_layout.addWidget(self.reset_btn)
        button_layout.addStretch()
        button_layout.addWidget(self.save_btn)
        button_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(button_layout)
    
    def _create_basic_tab(self):
        """Create basic settings tab"""
        widget = QWidget()
        layout = QFormLayout(widget)
        
        # Model selection
        self.model_combo = QComboBox()
        models = list(AVAILABLE_MODELS.keys())
        self.model_combo.addItems(models)
        for i, (model, info) in enumerate(AVAILABLE_MODELS.items()):
            self.model_combo.setItemText(i, f"{model} ({info['description']})")
        layout.addRow(QLabel("Model:"), self.model_combo)
        
        # Text processing options
        layout.addRow(QLabel(""), QLabel(""))  # Spacer
        layout.addRow(QLabel("Text Processing Options:"), QLabel(""))
        
        self.auto_punct_cb = QCheckBox("Auto Punctuation")
        self.auto_cap_cb = QCheckBox("Auto Capitalize")
        layout.addRow(self.auto_punct_cb)
        layout.addRow(self.auto_cap_cb)
        
        # Insert mode
        layout.addRow(QLabel(""), QLabel(""))  # Spacer
        layout.addRow(QLabel("Insert Mode:"), QLabel(""))
        
        self.insert_group = QButtonGroup(self)
        self.rb_type = QRadioButton("Type directly")
        self.rb_clipboard = QRadioButton("Use clipboard")
        self.rb_replace = QRadioButton("Replace all text")
        
        self.insert_group.addButton(self.rb_type, 0)
        self.insert_group.addButton(self.rb_clipboard, 1)
        self.insert_group.addButton(self.rb_replace, 2)
        
        layout.addRow(self.rb_type)
        layout.addRow(self.rb_clipboard)
        layout.addRow(self.rb_replace)
        
        self.tabs.addTab(widget, "Basic")
    
    def _create_realtime_tab(self):
        """Create real-time settings tab"""
        widget = QWidget()
        layout = QFormLayout(widget)
        
        # Real-time typing
        self.realtime_cb = QCheckBox("Enable Real-time Typing (type as you speak)")
        layout.addRow(self.realtime_cb)
        
        layout.addRow(QLabel(""), QLabel(""))  # Spacer
        layout.addRow(QLabel("Real-time Tuning Parameters:"), QLabel(""))
        
        # Processing pause
        self.processing_pause_spin = QDoubleSpinBox()
        self.processing_pause_spin.setRange(0.005, 0.1)
        self.processing_pause_spin.setSingleStep(0.005)
        self.processing_pause_spin.setDecimals(3)
        layout.addRow(QLabel("Processing Pause (s):"), self.processing_pause_spin)
        
        # Post-speech silence
        self.silence_duration_spin = QDoubleSpinBox()
        self.silence_duration_spin.setRange(0.2, 2.0)
        self.silence_duration_spin.setSingleStep(0.05)
        self.silence_duration_spin.setDecimals(2)
        layout.addRow(QLabel("Post-speech Silence (s):"), self.silence_duration_spin)
        
        # Min recording length
        self.min_length_spin = QDoubleSpinBox()
        self.min_length_spin.setRange(0.1, 1.0)
        self.min_length_spin.setSingleStep(0.05)
        self.min_length_spin.setDecimals(2)
        layout.addRow(QLabel("Min Recording Length (s):"), self.min_length_spin)
        
        # Min gap between recordings
        self.min_gap_spin = QDoubleSpinBox()
        self.min_gap_spin.setRange(0.0, 0.5)
        self.min_gap_spin.setSingleStep(0.01)
        self.min_gap_spin.setDecimals(2)
        layout.addRow(QLabel("Min Gap Between Recordings (s):"), self.min_gap_spin)
        
        # Suppression window
        self.suppress_window_spin = QDoubleSpinBox()
        self.suppress_window_spin.setRange(0.0, 1.0)
        self.suppress_window_spin.setSingleStep(0.05)
        self.suppress_window_spin.setDecimals(2)
        layout.addRow(QLabel("Finalization Suppression (s):"), self.suppress_window_spin)
        
        # Max backspaces
        self.max_backspaces_spin = QSpinBox()
        self.max_backspaces_spin.setRange(32, 1024)
        self.max_backspaces_spin.setSingleStep(32)
        layout.addRow(QLabel("Max Backspaces Per Update:"), self.max_backspaces_spin)
        
        self.tabs.addTab(widget, "Real-time")
    
    def _create_wake_word_tab(self):
        """Create wake word settings tab"""
        widget = QWidget()
        layout = QFormLayout(widget)
        
        # Enable wake words
        self.wake_enabled_cb = QCheckBox("Enable Wake Words")
        layout.addRow(self.wake_enabled_cb)
        
        # Wake word selection
        self.wake_word_combo = QComboBox()
        self.wake_word_combo.addItems(AVAILABLE_WAKE_WORDS)
        layout.addRow(QLabel("Wake Word:"), self.wake_word_combo)
        
        # Sensitivity
        self.wake_sensitivity_spin = QDoubleSpinBox()
        self.wake_sensitivity_spin.setRange(0.0, 1.0)
        self.wake_sensitivity_spin.setSingleStep(0.05)
        self.wake_sensitivity_spin.setDecimals(2)
        layout.addRow(QLabel("Sensitivity:"), self.wake_sensitivity_spin)
        
        # Custom model path
        custom_layout = QHBoxLayout()
        self.custom_model_edit = QLineEdit()
        self.browse_btn = QPushButton("Browse...")
        custom_layout.addWidget(self.custom_model_edit)
        custom_layout.addWidget(self.browse_btn)
        custom_widget = QWidget()
        custom_widget.setLayout(custom_layout)
        layout.addRow(QLabel("Custom Model Path:"), custom_widget)
        
        layout.addRow(QLabel(""), QLabel(""))  # Spacer
        layout.addRow(QLabel("Wake Word Behavior:"), QLabel(""))
        
        # Wake word timeout
        self.wake_timeout_spin = QDoubleSpinBox()
        self.wake_timeout_spin.setRange(2.0, 60.0)
        self.wake_timeout_spin.setSingleStep(0.5)
        self.wake_timeout_spin.setDecimals(1)
        layout.addRow(QLabel("Wake Word Timeout (s):"), self.wake_timeout_spin)
        
        # Conversation window
        self.conversation_window_spin = QDoubleSpinBox()
        self.conversation_window_spin.setRange(0.0, 15.0)
        self.conversation_window_spin.setSingleStep(0.5)
        self.conversation_window_spin.setDecimals(1)
        layout.addRow(QLabel("Conversation Window (s):"), self.conversation_window_spin)
        
        self.tabs.addTab(widget, "Wake Words")
    
    def _create_advanced_tab(self):
        """Create advanced settings tab"""
        # Create scrollable area for advanced settings
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        
        widget = QWidget()
        layout = QFormLayout(widget)
        
        # VAD Settings
        layout.addRow(QLabel("Voice Activity Detection:"), QLabel(""))
        
        self.silero_sensitivity_spin = QDoubleSpinBox()
        self.silero_sensitivity_spin.setRange(0.01, 1.0)
        self.silero_sensitivity_spin.setSingleStep(0.01)
        self.silero_sensitivity_spin.setDecimals(3)
        layout.addRow(QLabel("Silero VAD Sensitivity:"), self.silero_sensitivity_spin)
        
        self.silero_onnx_cb = QCheckBox("Use Silero ONNX (faster)")
        layout.addRow(self.silero_onnx_cb)
        
        self.webrtc_sensitivity_spin = QSpinBox()
        self.webrtc_sensitivity_spin.setRange(0, 3)
        layout.addRow(QLabel("WebRTC VAD Sensitivity:"), self.webrtc_sensitivity_spin)
        
        self.early_transcription_spin = QDoubleSpinBox()
        self.early_transcription_spin.setRange(0.0, 1.0)
        self.early_transcription_spin.setSingleStep(0.05)
        self.early_transcription_spin.setDecimals(2)
        layout.addRow(QLabel("Early Transcription on Silence (s):"), self.early_transcription_spin)
        
        # Model Parameters
        layout.addRow(QLabel(""), QLabel(""))  # Spacer
        layout.addRow(QLabel("Model Parameters:"), QLabel(""))
        
        self.beam_size_spin = QSpinBox()
        self.beam_size_spin.setRange(1, 10)
        layout.addRow(QLabel("Beam Size:"), self.beam_size_spin)
        
        self.beam_realtime_spin = QSpinBox()
        self.beam_realtime_spin.setRange(1, 5)
        layout.addRow(QLabel("Real-time Beam Size:"), self.beam_realtime_spin)
        
        self.batch_size_spin = QSpinBox()
        self.batch_size_spin.setRange(1, 32)
        layout.addRow(QLabel("Batch Size:"), self.batch_size_spin)
        
        # Pause Detection
        layout.addRow(QLabel(""), QLabel(""))  # Spacer
        layout.addRow(QLabel("Intelligent Pause Detection:"), QLabel(""))
        
        self.end_sentence_pause_spin = QDoubleSpinBox()
        self.end_sentence_pause_spin.setRange(0.1, 2.0)
        self.end_sentence_pause_spin.setSingleStep(0.05)
        self.end_sentence_pause_spin.setDecimals(2)
        layout.addRow(QLabel("End of Sentence Pause (s):"), self.end_sentence_pause_spin)
        
        self.unknown_sentence_pause_spin = QDoubleSpinBox()
        self.unknown_sentence_pause_spin.setRange(0.1, 3.0)
        self.unknown_sentence_pause_spin.setSingleStep(0.1)
        self.unknown_sentence_pause_spin.setDecimals(1)
        layout.addRow(QLabel("Unknown Sentence Pause (s):"), self.unknown_sentence_pause_spin)
        
        self.mid_sentence_pause_spin = QDoubleSpinBox()
        self.mid_sentence_pause_spin.setRange(0.5, 5.0)
        self.mid_sentence_pause_spin.setSingleStep(0.1)
        self.mid_sentence_pause_spin.setDecimals(1)
        layout.addRow(QLabel("Mid Sentence Pause (s):"), self.mid_sentence_pause_spin)
        
        scroll_area.setWidget(widget)
        self.tabs.addTab(scroll_area, "Advanced")
    
    def _setup_connections(self):
        """Setup signal connections"""
        # Browse button for custom wake word model
        self.browse_btn.clicked.connect(self._browse_model)
        
        # Wake word controls
        self.wake_enabled_cb.toggled.connect(self._update_wake_controls)
        self.wake_word_combo.currentTextChanged.connect(self._update_wake_controls)
        
        # Buttons
        self.save_btn.clicked.connect(self._save_and_close)
        self.cancel_btn.clicked.connect(self.reject)
        self.reset_btn.clicked.connect(self._reset_to_defaults)
        
        # Initial state
        self._update_wake_controls()
    
    def _browse_model(self):
        """Browse for custom wake word model"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Custom Wake Word Model",
            os.getcwd(),
            "Model files (*.ppn *.onnx *.pth *.tflite);;All files (*.*)"
        )
        if file_path:
            self.custom_model_edit.setText(file_path)
            self.wake_word_combo.setCurrentText("custom")
    
    def _update_wake_controls(self):
        """Update wake word control states"""
        enabled = self.wake_enabled_cb.isChecked()
        is_custom = self.wake_word_combo.currentText() == "custom"
        
        self.wake_word_combo.setEnabled(enabled)
        self.wake_sensitivity_spin.setEnabled(enabled)
        self.wake_timeout_spin.setEnabled(enabled)
        self.conversation_window_spin.setEnabled(enabled)
        
        self.custom_model_edit.setEnabled(enabled and is_custom)
        self.browse_btn.setEnabled(enabled and is_custom)
    
    def _load_current_settings(self):
        """Load current settings into UI"""
        config = self.config.config
        
        # Basic settings
        model_index = self.model_combo.findText(config.basic.model)
        if model_index >= 0:
            self.model_combo.setCurrentIndex(model_index)
        
        self.auto_punct_cb.setChecked(config.basic.auto_punctuation)
        self.auto_cap_cb.setChecked(config.basic.auto_capitalize)
        self.realtime_cb.setChecked(config.basic.realtime_typing)
        
        # Insert mode
        mode_map = {"type": 0, "clipboard": 1, "replace": 2}
        self.insert_group.button(mode_map.get(config.basic.insert_mode, 0)).setChecked(True)
        
        # Real-time settings
        self.processing_pause_spin.setValue(config.realtime.processing_pause)
        self.silence_duration_spin.setValue(config.realtime.post_speech_silence_duration)
        self.min_length_spin.setValue(config.realtime.min_length_of_recording)
        self.min_gap_spin.setValue(config.realtime.min_gap_between_recordings)
        self.suppress_window_spin.setValue(config.realtime.finalize_suppress_window)
        self.max_backspaces_spin.setValue(config.realtime.max_backspaces_per_update)
        
        # Wake word settings
        self.wake_enabled_cb.setChecked(config.wake_word.enabled)
        if config.wake_word.custom_model_path:
            self.wake_word_combo.setCurrentText("custom")
            self.custom_model_edit.setText(config.wake_word.custom_model_path)
        else:
            self.wake_word_combo.setCurrentText(config.wake_word.wake_words)
        
        self.wake_sensitivity_spin.setValue(config.wake_word.sensitivity)
        self.wake_timeout_spin.setValue(config.wake_word.timeout)
        self.conversation_window_spin.setValue(config.wake_word.conversation_window)
        
        # Advanced settings
        self.silero_sensitivity_spin.setValue(config.vad.silero_sensitivity)
        self.silero_onnx_cb.setChecked(config.vad.silero_use_onnx)
        self.webrtc_sensitivity_spin.setValue(config.vad.webrtc_sensitivity)
        self.early_transcription_spin.setValue(config.vad.early_transcription_on_silence)
        
        self.beam_size_spin.setValue(config.model.beam_size)
        self.beam_realtime_spin.setValue(config.model.beam_size_realtime)
        self.batch_size_spin.setValue(config.model.batch_size)
        
        self.end_sentence_pause_spin.setValue(config.pause_detection.end_of_sentence_pause)
        self.unknown_sentence_pause_spin.setValue(config.pause_detection.unknown_sentence_pause)
        self.mid_sentence_pause_spin.setValue(config.pause_detection.mid_sentence_pause)
    
    def _save_settings_to_config(self):
        """Save UI settings to config object"""
        config = self.config.config
        
        # Basic settings
        config.basic.model = self.model_combo.currentText().split(' ')[0]  # Remove description
        config.basic.auto_punctuation = self.auto_punct_cb.isChecked()
        config.basic.auto_capitalize = self.auto_cap_cb.isChecked()
        config.basic.realtime_typing = self.realtime_cb.isChecked()
        
        # Insert mode
        mode_map = {0: "type", 1: "clipboard", 2: "replace"}
        config.basic.insert_mode = mode_map[self.insert_group.checkedId()]
        
        # Real-time settings
        config.realtime.processing_pause = self.processing_pause_spin.value()
        config.realtime.post_speech_silence_duration = self.silence_duration_spin.value()
        config.realtime.min_length_of_recording = self.min_length_spin.value()
        config.realtime.min_gap_between_recordings = self.min_gap_spin.value()
        config.realtime.finalize_suppress_window = self.suppress_window_spin.value()
        config.realtime.max_backspaces_per_update = self.max_backspaces_spin.value()
        
        # Wake word settings
        config.wake_word.enabled = self.wake_enabled_cb.isChecked()
        if self.wake_word_combo.currentText() == "custom":
            config.wake_word.custom_model_path = self.custom_model_edit.text().strip() or None
            config.wake_word.wake_words = "custom"
        else:
            config.wake_word.wake_words = self.wake_word_combo.currentText()
            config.wake_word.custom_model_path = None
        
        config.wake_word.sensitivity = self.wake_sensitivity_spin.value()
        config.wake_word.timeout = self.wake_timeout_spin.value()
        config.wake_word.conversation_window = self.conversation_window_spin.value()
        
        # Advanced settings
        config.vad.silero_sensitivity = self.silero_sensitivity_spin.value()
        config.vad.silero_use_onnx = self.silero_onnx_cb.isChecked()
        config.vad.webrtc_sensitivity = self.webrtc_sensitivity_spin.value()
        config.vad.early_transcription_on_silence = self.early_transcription_spin.value()
        
        config.model.beam_size = self.beam_size_spin.value()
        config.model.beam_size_realtime = self.beam_realtime_spin.value()
        config.model.batch_size = self.batch_size_spin.value()
        
        config.pause_detection.end_of_sentence_pause = self.end_sentence_pause_spin.value()
        config.pause_detection.unknown_sentence_pause = self.unknown_sentence_pause_spin.value()
        config.pause_detection.mid_sentence_pause = self.mid_sentence_pause_spin.value()
    
    def _save_and_close(self):
        """Save settings and close dialog"""
        self._save_settings_to_config()
        self.config.save_settings()
        
        # Apply settings to manager in background
        def apply_changes():
            try:
                if hasattr(self.manager, 'apply_config_changes'):
                    self.manager.apply_config_changes()
            except Exception as e:
                print(f"Error applying config changes: {e}")
        
        threading.Thread(target=apply_changes, daemon=True).start()
        
        # Refresh menu if callback provided
        if self.refresh_callback:
            try:
                self.refresh_callback()
            except Exception as e:
                print(f"Error refreshing menu: {e}")
        
        self.accept()
    
    def _reset_to_defaults(self):
        """Reset all settings to defaults"""
        from .config import STTConfig
        default_config = STTConfig()
        
        # Temporarily replace config with defaults
        self.config.config = default_config
        self._load_current_settings()