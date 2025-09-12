"""
Transparent Overlay Window for STT Controls
Small, always-on-top window with start/stop recording buttons
"""

from typing import Optional, Callable
from PySide6.QtWidgets import (QWidget, QPushButton, QHBoxLayout, QVBoxLayout, 
                               QLabel, QGraphicsDropShadowEffect)
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, Signal
from PySide6.QtGui import QFont, QPalette, QColor, QPainter, QBrush, QPixmap


class STTOverlayWindow(QWidget):
    """
    Small, transparent, always-on-top overlay window for STT controls.
    Features:
    - Minimal design with start/stop buttons
    - Semi-transparent background
    - Always stays on top
    - Can be dragged around
    - Visual feedback for recording state
    """
    
    # Signals
    start_requested = Signal()
    stop_requested = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Window properties
        self.is_recording = False
        self.drag_position = None
        
        # Callbacks
        self.start_callback: Optional[Callable] = None
        self.stop_callback: Optional[Callable] = None
        
        self._setup_window()
        self._setup_ui()
        self._setup_animations()
        
    def _setup_window(self):
        """Configure window properties"""
        # Window flags for overlay behavior
        self.setWindowFlags(
            Qt.WindowStaysOnTopHint |           # Always on top
            Qt.FramelessWindowHint |            # No frame
            Qt.WindowSystemMenuHint |           # Allow system menu
            Qt.Tool                             # Tool window (doesn't show in taskbar)
        )
        
        # Set window attributes
        self.setAttribute(Qt.WA_TranslucentBackground)  # Transparent background
        self.setAttribute(Qt.WA_ShowWithoutActivating)  # Don't steal focus
        
        # Size and position
        self.setFixedSize(190, 80)
        self._center_on_screen()
        
        # Make window semi-transparent
        self.setWindowOpacity(0.9)
        
    def _center_on_screen(self):
        """Position window in top-right corner of screen"""
        from PySide6.QtWidgets import QApplication
        screen = QApplication.primaryScreen().geometry()
        self.move(screen.width() - self.width() - 20, 20)
    
    def _setup_ui(self):
        """Setup the user interface"""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 8, 10, 8)
        main_layout.setSpacing(5)
        
        # Status label
        self.status_label = QLabel("STT Ready")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-size: 11px;
                font-weight: bold;
                background: transparent;
                padding: 2px;
            }
        """)
        main_layout.addWidget(self.status_label)
        
        # Button layout
        button_layout = QHBoxLayout()
        button_layout.setSpacing(8)
        
        # Start/Stop button (toggles based on state)
        self.toggle_button = QPushButton("Start")
        self.toggle_button.setFixedSize(170, 30)  # Make it wider since no close button
        self.toggle_button.clicked.connect(self._toggle_recording)
        button_layout.addWidget(self.toggle_button)
        
        main_layout.addLayout(button_layout)
        
        # Apply styles
        self._apply_styles()
        
        # Add drop shadow effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 100))
        shadow.setOffset(2, 2)
        self.setGraphicsEffect(shadow)
    
    def _apply_styles(self):
        """Apply window and button styles"""
        # Main window style
        self.setStyleSheet("""
            STTOverlayWindow {
                background: rgba(30, 30, 35, 200);
                border-radius: 12px;
                border: 1px solid rgba(255, 255, 255, 30);
            }
        """)
        
        # Toggle button styles
        self._update_button_style()
    
    def _update_button_style(self):
        """Update button style based on recording state"""
        if self.is_recording:
            # Red stop button
            self.toggle_button.setStyleSheet("""
                QPushButton {
                    background: rgba(220, 50, 50, 180);
                    color: white;
                    border: none;
                    border-radius: 12px;
                    font-size: 12px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background: rgba(240, 70, 70, 200);
                }
                QPushButton:pressed {
                    background: rgba(200, 30, 30, 220);
                }
            """)
        else:
            # Green start button
            self.toggle_button.setStyleSheet("""
                QPushButton {
                    background: rgba(50, 180, 50, 180);
                    color: white;
                    border: none;
                    border-radius: 12px;
                    font-size: 12px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background: rgba(70, 200, 70, 200);
                }
                QPushButton:pressed {
                    background: rgba(30, 160, 30, 220);
                }
            """)
    
    def _setup_animations(self):
        """Setup animations for visual feedback"""
        self.blink_timer = QTimer()
        self.blink_timer.timeout.connect(self._blink_recording)
        
    def _toggle_recording(self):
        """Toggle between start and stop recording"""
        if self.is_recording:
            self._stop_recording()
        else:
            self._start_recording()
    
    def _start_recording(self):
        """Start recording"""
        # Immediately update UI state for responsiveness
        self.set_recording_state(True)
        
        if self.start_callback:
            self.start_callback()
        self.start_requested.emit()
        
    def _stop_recording(self):
        """Stop recording"""
        # Immediately update UI state for responsiveness
        self.set_recording_state(False)
        
        if self.stop_callback:
            self.stop_callback()
        self.stop_requested.emit()
    
    def set_recording_state(self, is_recording: bool):
        """Update UI to reflect recording state"""
        self.is_recording = is_recording
        
        if is_recording:
            self.toggle_button.setText("Stop")
            self.status_label.setText("Recording...")
            self.status_label.setStyleSheet("""
                QLabel {
                    color: #ff4444;
                    font-size: 11px;
                    font-weight: bold;
                    background: transparent;
                    padding: 2px;
                }
            """)
            # Start blinking animation
            self.blink_timer.start(1000)  # Blink every second
        else:
            self.toggle_button.setText("Start")
            self.status_label.setText("STT Ready")
            self.status_label.setStyleSheet("""
                QLabel {
                    color: #ffffff;
                    font-size: 11px;
                    font-weight: bold;
                    background: transparent;
                    padding: 2px;
                }
            """)
            # Stop blinking
            self.blink_timer.stop()
            self.setWindowOpacity(0.9)  # Reset opacity
        
        self._update_button_style()
    
    def _blink_recording(self):
        """Blink effect while recording"""
        current_opacity = self.windowOpacity()
        new_opacity = 0.6 if current_opacity > 0.8 else 0.9
        self.setWindowOpacity(new_opacity)
    
    def set_callbacks(self, start_callback: Callable, stop_callback: Callable):
        """Set the callback functions for start/stop actions"""
        self.start_callback = start_callback
        self.stop_callback = stop_callback
    
    # Mouse events for dragging
    def mousePressEvent(self, event):
        """Handle mouse press for dragging"""
        if event.button() == Qt.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
    
    def mouseMoveEvent(self, event):
        """Handle mouse move for dragging"""
        if event.buttons() == Qt.LeftButton and self.drag_position is not None:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release"""
        self.drag_position = None
    
    def paintEvent(self, event):
        """Custom paint event for rounded corners"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw rounded rectangle background
        painter.setBrush(QBrush(QColor(30, 30, 35, 200)))
        painter.setPen(QColor(255, 255, 255, 30))
        painter.drawRoundedRect(self.rect(), 12, 12)
        
        super().paintEvent(event)
    
    def show_temporarily(self, duration_ms: int = 5000):
        """Show window temporarily then hide it"""
        self.show()
        QTimer.singleShot(duration_ms, self.hide)
    
    def toggle_visibility(self):
        """Toggle window visibility"""
        if self.isVisible():
            self.hide()
        else:
            self.show()
            self.raise_()  # Bring to front
            self.activateWindow()
    
    def closeEvent(self, event):
        """Override close event to prevent window from closing via X button"""
        # Ignore the close event - window can only be closed via system tray
        event.ignore()
        # Optionally hide the window instead of closing it
        # self.hide()
    
    def force_close(self):
        """Force close the window (called from system tray exit)"""
        # Temporarily disable the close event override
        self.closeEvent = lambda event: event.accept()
        self.close()