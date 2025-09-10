import sys
import os
import threading
import time
import json

from PySide6.QtWidgets import (
    QApplication, QSystemTrayIcon, QMenu, QMessageBox,
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QCheckBox, QComboBox,
    QLineEdit, QPushButton, QRadioButton, QButtonGroup, QFileDialog,
    QFormLayout, QDoubleSpinBox, QSpinBox, QWidget
)
from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor, QAction
from PySide6.QtCore import Qt

from global_stt import GlobalSTTManager  # type: ignore


def build_mic_icon() -> QIcon:
    pix = QPixmap(64, 64)
    pix.fill(QColor('black'))
    p = QPainter(pix)
    p.setPen(Qt.NoPen)
    p.setBrush(QColor('white'))
    p.drawEllipse(20, 15, 24, 20)
    p.drawRect(30, 35, 4, 10)
    p.drawRect(25, 45, 14, 5)
    p.end()
    return QIcon(pix)


class SettingsDialog(QDialog):
    def __init__(self, manager: 'GlobalSTTManager', refresh_menu_cb, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Global STT Settings")
        # Wider dialog to accommodate two-column layout
        self.resize(1000, 720)
        self.manager = manager
        self.refresh_menu_cb = refresh_menu_cb

        layout = QVBoxLayout(self)
        # Two-column layout to reduce vertical height
        columns = QHBoxLayout()
        layout.addLayout(columns)
        left = QVBoxLayout()
        right = QVBoxLayout()
        columns.addLayout(left)
        columns.addLayout(right)
        columns.setStretch(0, 1)
        columns.setStretch(1, 1)

        # Model
        form = QFormLayout()
        self.model_combo = QComboBox()
        self.model_combo.addItems(["tiny.en", "base.en", "small.en", "medium.en", "large-v1", "large-v2", "large-v3", "large-v3-turbo"])
        idx = self.model_combo.findText(self.manager.current_model)
        self.model_combo.setCurrentIndex(max(idx, 0))
        form.addRow(QLabel("Model:"), self.model_combo)

        # Text processing (left column)
        left.addLayout(form)
        left.addWidget(QLabel("Text Processing:"))
        self.auto_punct_cb = QCheckBox("Auto Punctuation")
        self.auto_punct_cb.setChecked(bool(getattr(self.manager, 'auto_punctuation', True)))
        self.auto_cap_cb = QCheckBox("Auto Capitalize")
        self.auto_cap_cb.setChecked(bool(getattr(self.manager, 'auto_capitalize', True)))
        self.realtime_cb = QCheckBox("Real-time Typing (type as you speak)")
        self.realtime_cb.setChecked(bool(getattr(self.manager, 'realtime_typing', False)))
        left.addWidget(self.auto_punct_cb)
        left.addWidget(self.auto_cap_cb)
        left.addWidget(self.realtime_cb)

        # Wake words (right column)
        right.addWidget(QLabel("Wake Words:"))
        self.wake_enable_cb = QCheckBox("Enable Wake Words")
        self.wake_enable_cb.setChecked(bool(getattr(self.manager, 'wake_words_enabled', False)))
        right.addWidget(self.wake_enable_cb)

        form2 = QFormLayout()
        self.wake_word_combo = QComboBox()
        self.wake_word_combo.addItems([
            "custom", "jarvis", "computer", "hey google", "hey siri", "ok google", "alexa",
            "porcupine", "bumblebee", "terminator", "picovoice", "americano",
            "blueberry", "grapefruits", "grasshopper"
        ])
        if getattr(self.manager, 'custom_wakeword_model_path', None):
            self.wake_word_combo.setCurrentText("custom")
        else:
            self.wake_word_combo.setCurrentText(getattr(self.manager, 'wake_words', 'jarvis'))
        form2.addRow(QLabel("Wake Word:"), self.wake_word_combo)

        self.sens_spin = QDoubleSpinBox()
        self.sens_spin.setRange(0.0, 1.0)
        self.sens_spin.setSingleStep(0.05)
        self.sens_spin.setValue(float(getattr(self.manager, 'wake_words_sensitivity', 0.6) or 0.6))
        form2.addRow(QLabel("Sensitivity:"), self.sens_spin)

        self.custom_model_edit = QLineEdit(getattr(self.manager, 'custom_wakeword_model_path', '') or '')
        browse_btn = QPushButton("Browse…")
        h = QHBoxLayout()
        h.addWidget(self.custom_model_edit)
        h.addWidget(browse_btn)
        container = QWidget()
        container.setLayout(h)
        form2.addRow(QLabel("Custom Model Path:"), container)
        right.addLayout(form2)

        def browse_model():
            path, _ = QFileDialog.getOpenFileName(self, "Select Custom Wake Word Model", os.getcwd(),
                                                 "Model files (*.ppn *.onnx *.pth);;All files (*.*)")
            if path:
                self.custom_model_edit.setText(path)
                self.wake_word_combo.setCurrentText("custom")
        browse_btn.clicked.connect(browse_model)

        # Wake word behavior (right column)
        right.addWidget(QLabel("Wake Word Behavior:"))
        form3 = QFormLayout()
        self.wake_timeout_spin = QDoubleSpinBox()
        self.wake_timeout_spin.setRange(2.0, 60.0)
        self.wake_timeout_spin.setSingleStep(0.5)
        self.wake_timeout_spin.setDecimals(1)
        self.wake_timeout_spin.setValue(float(getattr(self.manager, 'wake_word_timeout', 12.0)))
        form3.addRow(QLabel("Wake Word Timeout (s)"), self.wake_timeout_spin)

        self.conv_window_spin = QDoubleSpinBox()
        self.conv_window_spin.setRange(0.0, 15.0)
        self.conv_window_spin.setSingleStep(0.5)
        self.conv_window_spin.setDecimals(1)
        self.conv_window_spin.setValue(float(getattr(self.manager, 'conversation_window', 4.0)))
        form3.addRow(QLabel("Conversation Window After Speech (s)"), self.conv_window_spin)
        right.addLayout(form3)

        # Insert mode (left column)
        left.addWidget(QLabel("Insert Mode:"))
        self.rb_type = QRadioButton("Type directly")
        self.rb_clip = QRadioButton("Use clipboard")
        self.rb_replace = QRadioButton("Replace all text")
        self.insert_group = QButtonGroup(self)
        for i, rb in enumerate([self.rb_type, self.rb_clip, self.rb_replace]):
            self.insert_group.addButton(rb, i)
            left.addWidget(rb)
        current_mode = getattr(self.manager, 'insert_mode', 'type')
        {"type": self.rb_type, "clipboard": self.rb_clip, "replace": self.rb_replace}.get(current_mode, self.rb_type).setChecked(True)

        # Enable/disable wake controls
        def update_wake_controls():
            enabled = self.wake_enable_cb.isChecked()
            self.wake_word_combo.setEnabled(enabled)
            self.sens_spin.setEnabled(enabled)
            custom = self.wake_word_combo.currentText() == 'custom'
            self.custom_model_edit.setEnabled(enabled and custom)
        self.wake_enable_cb.toggled.connect(update_wake_controls)
        self.wake_word_combo.currentTextChanged.connect(update_wake_controls)
        update_wake_controls()

        # Advanced VAD Settings (right column)
        right.addWidget(QLabel("Advanced VAD Settings:"))
        vad_form = QFormLayout()
        
        self.silero_sens_spin = QDoubleSpinBox()
        self.silero_sens_spin.setRange(0.01, 1.0)
        self.silero_sens_spin.setSingleStep(0.01)
        self.silero_sens_spin.setDecimals(3)
        self.silero_sens_spin.setValue(float(getattr(self.manager, 'silero_sensitivity', 0.05)))
        vad_form.addRow(QLabel("Silero VAD Sensitivity"), self.silero_sens_spin)
        
        self.webrtc_sens_spin = QSpinBox()
        self.webrtc_sens_spin.setRange(0, 3)
        self.webrtc_sens_spin.setValue(int(getattr(self.manager, 'webrtc_sensitivity', 3)))
        vad_form.addRow(QLabel("WebRTC VAD Sensitivity"), self.webrtc_sens_spin)
        
        self.early_trans_spin = QDoubleSpinBox()
        self.early_trans_spin.setRange(0.0, 1.0)
        self.early_trans_spin.setSingleStep(0.05)
        self.early_trans_spin.setDecimals(2)
        self.early_trans_spin.setValue(float(getattr(self.manager, 'early_transcription_on_silence', 0.2)))
        vad_form.addRow(QLabel("Early Transcription on Silence (s)"), self.early_trans_spin)
        
        self.silero_onnx_cb = QCheckBox("Use Silero ONNX (faster)")
        self.silero_onnx_cb.setChecked(bool(getattr(self.manager, 'silero_use_onnx', False)))
        vad_form.addRow(self.silero_onnx_cb)
        
        right.addLayout(vad_form)
        
        # Enhanced Model Parameters (right column)
        right.addWidget(QLabel("Model Parameters:"))
        model_form = QFormLayout()
        
        self.beam_size_spin = QSpinBox()
        self.beam_size_spin.setRange(1, 10)
        self.beam_size_spin.setValue(int(getattr(self.manager, 'beam_size', 5)))
        model_form.addRow(QLabel("Main Model Beam Size"), self.beam_size_spin)
        
        self.beam_realtime_spin = QSpinBox()
        self.beam_realtime_spin.setRange(1, 5)
        self.beam_realtime_spin.setValue(int(getattr(self.manager, 'beam_size_realtime', 3)))
        model_form.addRow(QLabel("Realtime Model Beam Size"), self.beam_realtime_spin)
        
        self.batch_size_spin = QSpinBox()
        self.batch_size_spin.setRange(1, 32)
        self.batch_size_spin.setValue(int(getattr(self.manager, 'batch_size', 16)))
        model_form.addRow(QLabel("Batch Size"), self.batch_size_spin)
        
        right.addLayout(model_form)
        
        # Advanced Pause Detection (right column)
        right.addWidget(QLabel("Intelligent Pause Detection:"))
        pause_form = QFormLayout()
        
        self.end_pause_spin = QDoubleSpinBox()
        self.end_pause_spin.setRange(0.1, 2.0)
        self.end_pause_spin.setSingleStep(0.05)
        self.end_pause_spin.setDecimals(2)
        self.end_pause_spin.setValue(float(getattr(self.manager, 'end_of_sentence_detection_pause', 0.45)))
        pause_form.addRow(QLabel("End of Sentence Pause (s)"), self.end_pause_spin)
        
        self.unknown_pause_spin = QDoubleSpinBox()
        self.unknown_pause_spin.setRange(0.1, 3.0)
        self.unknown_pause_spin.setSingleStep(0.1)
        self.unknown_pause_spin.setDecimals(1)
        self.unknown_pause_spin.setValue(float(getattr(self.manager, 'unknown_sentence_detection_pause', 0.7)))
        pause_form.addRow(QLabel("Unknown Sentence Pause (s)"), self.unknown_pause_spin)
        
        self.mid_pause_spin = QDoubleSpinBox()
        self.mid_pause_spin.setRange(0.5, 5.0)
        self.mid_pause_spin.setSingleStep(0.1)
        self.mid_pause_spin.setDecimals(1)
        self.mid_pause_spin.setValue(float(getattr(self.manager, 'mid_sentence_detection_pause', 2.0)))
        pause_form.addRow(QLabel("Mid Sentence Pause (s)"), self.mid_pause_spin)
        
        right.addLayout(pause_form)

        # Realtime tuning (left column)
        left.addWidget(QLabel("Realtime Tuning:"))
        tune_form = QFormLayout()

        self.rp_pause_spin = QDoubleSpinBox()
        self.rp_pause_spin.setRange(0.005, 0.1)
        self.rp_pause_spin.setSingleStep(0.005)
        self.rp_pause_spin.setDecimals(3)
        self.rp_pause_spin.setValue(float(getattr(self.manager, 'realtime_processing_pause', 0.02)))
        tune_form.addRow(QLabel("Realtime Processing Pause (s)"), self.rp_pause_spin)

        self.pssd_spin = QDoubleSpinBox()
        self.pssd_spin.setRange(0.2, 2.0)
        self.pssd_spin.setSingleStep(0.05)
        self.pssd_spin.setDecimals(2)
        self.pssd_spin.setValue(float(getattr(self.manager, 'post_speech_silence_duration', 0.7)))
        tune_form.addRow(QLabel("Post-speech Silence (s)"), self.pssd_spin)

        self.min_len_spin = QDoubleSpinBox()
        self.min_len_spin.setRange(0.1, 1.0)
        self.min_len_spin.setSingleStep(0.05)
        self.min_len_spin.setDecimals(2)
        self.min_len_spin.setValue(float(getattr(self.manager, 'min_length_of_recording', 0.3)))
        tune_form.addRow(QLabel("Min Utterance Length (s)"), self.min_len_spin)

        self.min_gap_spin = QDoubleSpinBox()
        self.min_gap_spin.setRange(0.0, 0.5)
        self.min_gap_spin.setSingleStep(0.01)
        self.min_gap_spin.setDecimals(2)
        self.min_gap_spin.setValue(float(getattr(self.manager, 'min_gap_between_recordings', 0.0)))
        tune_form.addRow(QLabel("Min Gap Between Recordings (s)"), self.min_gap_spin)

        self.suppress_spin = QDoubleSpinBox()
        self.suppress_spin.setRange(0.0, 1.0)
        self.suppress_spin.setSingleStep(0.05)
        self.suppress_spin.setDecimals(2)
        self.suppress_spin.setValue(float(getattr(self.manager, 'finalize_suppress_window', 0.5)))
        tune_form.addRow(QLabel("Finalize Suppression Window (s)"), self.suppress_spin)

        self.max_backspaces_spin = QSpinBox()
        self.max_backspaces_spin.setRange(32, 1024)
        self.max_backspaces_spin.setSingleStep(32)
        self.max_backspaces_spin.setValue(int(getattr(self.manager, 'max_backspaces_per_update', 512)))
        tune_form.addRow(QLabel("Max Backspaces Per Update"), self.max_backspaces_spin)

        left.addLayout(tune_form)

        # Buttons
        btns = QHBoxLayout()
        save_btn = QPushButton("Save & Close")
        cancel_btn = QPushButton("Cancel")
        btns.addWidget(save_btn)
        btns.addWidget(cancel_btn)
        layout.addLayout(btns)

        cancel_btn.clicked.connect(self.reject)

        def on_save():
            # Capture old states for runtime updates
            old_realtime = bool(getattr(self.manager, 'realtime_typing', False))
            old_model = self.manager.current_model
            old_rp_pause = float(getattr(self.manager, 'realtime_processing_pause', 0.02))
            old_pssd = float(getattr(self.manager, 'post_speech_silence_duration', 0.7))
            old_min_len = float(getattr(self.manager, 'min_length_of_recording', 0.3))
            old_min_gap = float(getattr(self.manager, 'min_gap_between_recordings', 0.0))

            # Apply new settings
            self.manager.current_model = self.model_combo.currentText()
            self.manager.auto_punctuation = self.auto_punct_cb.isChecked()
            self.manager.auto_capitalize = self.auto_cap_cb.isChecked()
            self.manager.realtime_typing = self.realtime_cb.isChecked()
            self.manager.insert_mode = (
                'type' if self.rb_type.isChecked() else 'clipboard' if self.rb_clip.isChecked() else 'replace'
            )
            self.manager.wake_words_enabled = self.wake_enable_cb.isChecked()
            if self.wake_word_combo.currentText() == 'custom':
                self.manager.custom_wakeword_model_path = self.custom_model_edit.text().strip() or None
                self.manager.wake_words = 'custom'
            else:
                self.manager.wake_words = self.wake_word_combo.currentText()
                self.manager.custom_wakeword_model_path = None
            self.manager.wake_words_sensitivity = float(self.sens_spin.value())
            # Wake word behavior
            self.manager.wake_word_timeout = float(self.wake_timeout_spin.value())
            self.manager.conversation_window = float(self.conv_window_spin.value())

            # Realtime tuning values
            self.manager.realtime_processing_pause = float(self.rp_pause_spin.value())
            self.manager.post_speech_silence_duration = float(self.pssd_spin.value())
            self.manager.min_length_of_recording = float(self.min_len_spin.value())
            self.manager.min_gap_between_recordings = float(self.min_gap_spin.value())
            self.manager.finalize_suppress_window = float(self.suppress_spin.value())
            self.manager.max_backspaces_per_update = int(self.max_backspaces_spin.value())
            
            # Advanced VAD settings
            self.manager.silero_sensitivity = float(self.silero_sens_spin.value())
            self.manager.webrtc_sensitivity = int(self.webrtc_sens_spin.value())
            self.manager.early_transcription_on_silence = float(self.early_trans_spin.value())
            self.manager.silero_use_onnx = bool(self.silero_onnx_cb.isChecked())
            
            # Enhanced model parameters
            self.manager.beam_size = int(self.beam_size_spin.value())
            self.manager.beam_size_realtime = int(self.beam_realtime_spin.value())
            self.manager.batch_size = int(self.batch_size_spin.value())
            
            # Advanced pause detection
            self.manager.end_of_sentence_detection_pause = float(self.end_pause_spin.value())
            self.manager.unknown_sentence_detection_pause = float(self.unknown_pause_spin.value())
            self.manager.mid_sentence_detection_pause = float(self.mid_pause_spin.value())

            self.manager.save_settings()

            # Heavy work (recorder shutdown) in background thread
            def apply_runtime_changes():
                try:
                    need_recreate = (
                        (old_realtime != self.manager.realtime_typing) or
                        (old_model != self.manager.current_model) or
                        (old_rp_pause != float(self.manager.realtime_processing_pause)) or
                        (old_pssd != float(self.manager.post_speech_silence_duration)) or
                        (old_min_len != float(self.manager.min_length_of_recording)) or
                        (old_min_gap != float(self.manager.min_gap_between_recordings)) or
                        # Re-init on wakeword changes as backend/model need reload
                        (bool(getattr(self.manager, 'wake_words_enabled', False)) != bool(self.wake_enable_cb.isChecked())) or
                        (str(getattr(self.manager, 'wake_words', '')) != (self.wake_word_combo.currentText() if self.wake_word_combo.currentText() != 'custom' else 'custom')) or
                        (str(getattr(self.manager, 'custom_wakeword_model_path', '') or '') != str(self.custom_model_edit.text().strip() or '')) or
                        (float(getattr(self.manager, 'wake_words_sensitivity', 0.6) or 0.6) != float(self.sens_spin.value())) or
                        (float(getattr(self.manager, 'wake_word_timeout', 12.0)) != float(self.wake_timeout_spin.value())) or
                        (float(getattr(self.manager, 'conversation_window', 4.0)) != float(self.conv_window_spin.value()))
                    )
                    if need_recreate and self.manager.recorder:
                        self.manager.recorder.shutdown()
                        self.manager.recorder = None
                except Exception as e:
                    print(f"Apply changes error (Qt): {e}")

            threading.Thread(target=apply_runtime_changes, daemon=True).start()

            # Refresh menu immediately on the GUI thread
            try:
                self.refresh_menu_cb()
            except Exception:
                pass
            self.accept()

        save_btn.clicked.connect(on_save)


class QtTrayApp:
    def __init__(self):
        self.app = QApplication(sys.argv)
        # Keep app running when the last window (e.g., settings dialog) closes
        self.app.setQuitOnLastWindowClosed(False)
        self.manager = GlobalSTTManager(enable_tray=False, enable_hotkeys=True)
        self.tray = QSystemTrayIcon(build_mic_icon(), self.app)
        self.tray.setToolTip("Advanced Global STT")
        self.menu = QMenu()
        self._build_menu()
        self.tray.setContextMenu(self.menu)
        self.tray.show()
        # Bridge notifications from manager to Qt tray balloons
        self.manager.tray_notify = lambda title, msg: self.tray.showMessage(
            title, msg, QSystemTrayIcon.Information, 4000
        )

    def _build_menu(self):
        self.menu.clear()
        # Start/Stop
        start_action = QAction("Start Recording", self.menu)
        start_action.triggered.connect(self.manager.start_recording)
        stop_action = QAction("Stop Recording", self.menu)
        stop_action.triggered.connect(self.manager.stop_recording)
        self.menu.addAction(start_action)
        self.menu.addAction(stop_action)

        # Model submenu
        model_menu = QMenu(f"Model: {self.manager.current_model}", self.menu)
        for name in ["tiny.en", "base.en", "small.en", "medium.en", "large-v1", "large-v2", "large-v3", "large-v3-turbo"]:
            act = QAction(name, model_menu)
            act.triggered.connect(lambda checked=False, m=name: self._change_model(m))
            model_menu.addAction(act)
        self.menu.addMenu(model_menu)

        # Wake status and Settings
        wake_status = f"Wake: {self.manager.wake_words}" if self.manager.wake_words_enabled else "Wake: Disabled"
        wake_action = QAction(wake_status, self.menu)
        wake_action.triggered.connect(self.open_settings)
        self.menu.addAction(wake_action)

        settings_action = QAction("Settings", self.menu)
        settings_action.triggered.connect(self.open_settings)
        self.menu.addAction(settings_action)

        web_action = QAction("Web Interface", self.menu)
        web_action.triggered.connect(self.manager.open_web_interface)
        self.menu.addAction(web_action)

        status_action = QAction("Status", self.menu)
        status_action.triggered.connect(self.show_status)
        self.menu.addAction(status_action)

        self.menu.addSeparator()
        exit_action = QAction("Exit", self.menu)
        exit_action.triggered.connect(self.quit)
        self.menu.addAction(exit_action)

    def _change_model(self, name: str):
        if self.manager.is_recording:
            QMessageBox.information(None, "Change Model", "Stop recording before changing model.")
            return
        self.manager.change_model(name)
        self._build_menu()

    def _refresh_menu(self):
        self._build_menu()

    def open_settings(self):
        dlg = SettingsDialog(self.manager, refresh_menu_cb=self._refresh_menu)
        dlg.exec()

    def show_status(self):
        try:
            import requests
            response = requests.get('http://127.0.0.1:5000/api/health', timeout=2)
            web_status = "🟢 Running" if response.status_code == 200 else "🔴 Stopped"
        except Exception:
            web_status = "🔴 Stopped"
        global_status = "🟢 Running" if self.manager.is_recording else "🔴 Stopped"
        QMessageBox.information(None, "STT System Status",
                                f"Web Interface: {web_status}\n"
                                f"Global STT: {global_status}\n\n"
                                f"Model: {self.manager.current_model}\n"
                                f"Both can run simultaneously!")

    def quit(self):
        try:
            self.manager.is_recording = False
            if self.manager.recorder:
                self.manager.recorder.shutdown()
        except Exception:
            pass
        self.tray.hide()
        self.app.quit()

    def run(self):
        sys.exit(self.app.exec())


if __name__ == '__main__':
    app = QtTrayApp()
    app.run()
