"""
Visual Status Indicators
Provides visual feedback for STT system state
"""

from typing import Optional, Dict, Any, Callable
from enum import Enum
import time
import threading

try:
    from PySide6.QtCore import QTimer, QObject, pyqtSignal
    from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor, QPen
    from PySide6.QtWidgets import QSystemTrayIcon
    QT_AVAILABLE = True
except ImportError:
    QT_AVAILABLE = False
    # Create stub classes for when Qt is not available
    class QTimer: pass
    class QObject: pass
    class pyqtSignal: pass 
    class QIcon: pass
    class QPixmap: pass
    class QPainter: 
        Antialiasing = None
    class QColor: pass
    class QPen: pass
    class QSystemTrayIcon: pass


class IndicatorState(Enum):
    """Visual indicator states"""
    IDLE = "idle"
    INITIALIZING = "initializing"
    READY = "ready"
    RECORDING = "recording"
    PROCESSING = "processing"
    ERROR = "error"


class IndicatorColors:
    """Color constants for different states"""
    IDLE = QColor(128, 128, 128) if QT_AVAILABLE else None        # Gray
    INITIALIZING = QColor(255, 165, 0) if QT_AVAILABLE else None  # Orange
    READY = QColor(0, 255, 0) if QT_AVAILABLE else None          # Green
    RECORDING = QColor(255, 0, 0) if QT_AVAILABLE else None      # Red
    PROCESSING = QColor(0, 100, 255) if QT_AVAILABLE else None   # Blue
    ERROR = QColor(255, 100, 100) if QT_AVAILABLE else None      # Light Red


class IconGenerator:
    """Generates icons for different states"""
    
    @staticmethod
    def create_microphone_icon(color: 'QColor', size: int = 32, animated: bool = False) -> 'QIcon':
        """Create simple microphone icon with specified color"""
        if not QT_AVAILABLE:
            return None
            
        pixmap = QPixmap(size, size)
        pixmap.fill(QColor(255, 0, 0, 0))  # Transparent background
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw microphone body (rounded rectangle)
        painter.setBrush(color)
        painter.setPen(color)
        painter.drawRoundedRect(12, 6, 8, 14, 3, 3)
        
        # Draw microphone base/stand
        painter.drawRect(14, 20, 4, 4)
        painter.drawRect(10, 24, 12, 2)
        
        # Add visual state indicator if animated
        if animated:
            # Add sound waves
            painter.setPen(QColor(color.red(), color.green(), color.blue(), 120))
            painter.drawArc(4, 8, 6, 6, 0, 180 * 16)
            painter.drawArc(2, 6, 10, 10, 0, 180 * 16)
        
        painter.end()
        return QIcon(pixmap)
    
    @staticmethod
    def create_state_icon(state: IndicatorState, size: int = 64) -> 'QIcon':
        """Create icon for specific state"""
        if not QT_AVAILABLE:
            return None
            
        color_map = {
            IndicatorState.IDLE: IndicatorColors.IDLE,
            IndicatorState.INITIALIZING: IndicatorColors.INITIALIZING,
            IndicatorState.READY: IndicatorColors.READY,
            IndicatorState.RECORDING: IndicatorColors.RECORDING,
            IndicatorState.PROCESSING: IndicatorColors.PROCESSING,
            IndicatorState.ERROR: IndicatorColors.ERROR
        }
        
        color = color_map.get(state, IndicatorColors.IDLE)
        animated = state in [IndicatorState.INITIALIZING, IndicatorState.RECORDING, IndicatorState.PROCESSING]
        
        return IconGenerator.create_microphone_icon(color, size, animated)


class TrayIconManager(QObject):
    """Manages system tray icon animations and states"""
    
    def __init__(self, tray_icon: 'QSystemTrayIcon'):
        super().__init__()
        if not QT_AVAILABLE:
            return
            
        self.tray_icon = tray_icon
        self.current_state = IndicatorState.IDLE
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self._animate_icon)
        self.animation_frame = 0
        
        # Icon cache
        self.icon_cache: Dict[str, QIcon] = {}
        
        # Preload common icons
        self._preload_icons()
        
        # Set initial icon
        self.set_state(IndicatorState.IDLE)
    
    def _preload_icons(self):
        """Preload commonly used icons"""
        for state in IndicatorState:
            key = f"{state.value}_normal"
            self.icon_cache[key] = IconGenerator.create_state_icon(state)
            
            # Create animated versions for states that need them
            if state in [IndicatorState.INITIALIZING, IndicatorState.RECORDING, IndicatorState.PROCESSING]:
                for frame in range(3):  # 3 animation frames
                    key = f"{state.value}_frame_{frame}"
                    # Create slightly different icons for animation frames
                    self.icon_cache[key] = IconGenerator.create_state_icon(state)
    
    def set_state(self, state: IndicatorState, tooltip: Optional[str] = None):
        """Set tray icon state with optional tooltip"""
        if not QT_AVAILABLE:
            return
            
        self.current_state = state
        
        # Update tooltip
        if tooltip:
            self.tray_icon.setToolTip(tooltip)
        else:
            # Default tooltips
            tooltip_map = {
                IndicatorState.IDLE: "Global STT - Idle",
                IndicatorState.INITIALIZING: "Global STT - Loading Model...",
                IndicatorState.READY: "Global STT - Ready",
                IndicatorState.RECORDING: "Global STT - Recording",
                IndicatorState.PROCESSING: "Global STT - Processing",
                IndicatorState.ERROR: "Global STT - Error"
            }
            self.tray_icon.setToolTip(tooltip_map.get(state, "Global STT"))
        
        # Set icon
        icon_key = f"{state.value}_normal"
        if icon_key in self.icon_cache:
            self.tray_icon.setIcon(self.icon_cache[icon_key])
        
        # Start/stop animation
        if state in [IndicatorState.INITIALIZING, IndicatorState.RECORDING, IndicatorState.PROCESSING]:
            self.animation_timer.start(500)  # 500ms interval
        else:
            self.animation_timer.stop()
            self.animation_frame = 0
    
    def _animate_icon(self):
        """Animate icon for active states"""
        if not QT_AVAILABLE:
            return
            
        if self.current_state in [IndicatorState.INITIALIZING, IndicatorState.RECORDING, IndicatorState.PROCESSING]:
            # Cycle through animation frames
            self.animation_frame = (self.animation_frame + 1) % 3
            
            # Simple animation: alternate between normal and slightly different icons
            if self.animation_frame == 0:
                icon_key = f"{self.current_state.value}_normal"
            else:
                # Create pulsing effect by varying opacity
                icon_key = f"{self.current_state.value}_normal"
            
            if icon_key in self.icon_cache:
                self.tray_icon.setIcon(self.icon_cache[icon_key])
    
    def show_temporary_state(self, state: IndicatorState, duration_ms: int = 2000, tooltip: Optional[str] = None):
        """Show temporary state and return to previous state"""
        if not QT_AVAILABLE:
            return
            
        previous_state = self.current_state
        self.set_state(state, tooltip)
        
        # Schedule return to previous state
        QTimer.singleShot(duration_ms, lambda: self.set_state(previous_state))


class VisualIndicatorManager:
    """
    Main manager for visual indicators.
    Coordinates tray icon, status display, and other visual feedback.
    """
    
    def __init__(self, tray_icon: Optional['QSystemTrayIcon'] = None):
        self.tray_icon_manager = None
        self.callbacks: Dict[str, list] = {'state_change': []}
        
        if QT_AVAILABLE and tray_icon:
            self.tray_icon_manager = TrayIconManager(tray_icon)
    
    def add_callback(self, event: str, callback: Callable):
        """Add callback for visual events"""
        if event not in self.callbacks:
            self.callbacks[event] = []
        self.callbacks[event].append(callback)
    
    def _trigger_callbacks(self, event: str, *args, **kwargs):
        """Trigger callbacks for event"""
        for callback in self.callbacks.get(event, []):
            try:
                callback(*args, **kwargs)
            except Exception as e:
                print(f"Visual indicator callback error: {e}")
    
    def set_idle(self):
        """Set system to idle state"""
        if self.tray_icon_manager:
            self.tray_icon_manager.set_state(IndicatorState.IDLE)
        self._trigger_callbacks('state_change', IndicatorState.IDLE)
    
    def set_initializing(self, tooltip: Optional[str] = None):
        """Set system to initializing state"""
        if self.tray_icon_manager:
            self.tray_icon_manager.set_state(IndicatorState.INITIALIZING, tooltip)
        self._trigger_callbacks('state_change', IndicatorState.INITIALIZING)
    
    def set_ready(self, tooltip: Optional[str] = None):
        """Set system to ready state"""
        if self.tray_icon_manager:
            self.tray_icon_manager.set_state(IndicatorState.READY, tooltip)
        self._trigger_callbacks('state_change', IndicatorState.READY)
    
    def set_recording(self, tooltip: Optional[str] = None):
        """Set system to recording state"""
        if self.tray_icon_manager:
            self.tray_icon_manager.set_state(IndicatorState.RECORDING, tooltip)
        self._trigger_callbacks('state_change', IndicatorState.RECORDING)
    
    def set_processing(self, tooltip: Optional[str] = None):
        """Set system to processing state"""
        if self.tray_icon_manager:
            self.tray_icon_manager.set_state(IndicatorState.PROCESSING, tooltip)
        self._trigger_callbacks('state_change', IndicatorState.PROCESSING)
    
    def set_error(self, tooltip: Optional[str] = None):
        """Set system to error state"""
        if self.tray_icon_manager:
            self.tray_icon_manager.set_state(IndicatorState.ERROR, tooltip)
        self._trigger_callbacks('state_change', IndicatorState.ERROR)
    
    def show_temporary_message(self, state: IndicatorState, duration_ms: int = 2000, tooltip: Optional[str] = None):
        """Show temporary visual state"""
        if self.tray_icon_manager:
            self.tray_icon_manager.show_temporary_state(state, duration_ms, tooltip)
    
    def show_command_executed(self):
        """Show brief indication that command was executed"""
        self.show_temporary_message(IndicatorState.PROCESSING, 1000, "Command Executed")
    
    def show_model_loading(self, model_name: str):
        """Show model loading state"""
        self.set_initializing(f"Loading {model_name}...")
    
    def show_model_ready(self, load_time: Optional[float] = None):
        """Show model ready state"""
        tooltip = "Model Ready"
        if load_time:
            tooltip += f" ({load_time:.1f}s)"
        self.set_ready(tooltip)
    
    def update_recording_status(self, is_recording: bool, details: Optional[str] = None):
        """Update recording status display"""
        if is_recording:
            tooltip = "Recording"
            if details:
                tooltip += f" - {details}"
            self.set_recording(tooltip)
        else:
            self.set_ready()


# Global instance
_visual_indicator_manager = None

def get_visual_indicator_manager(tray_icon: Optional['QSystemTrayIcon'] = None) -> VisualIndicatorManager:
    """Get global visual indicator manager"""
    global _visual_indicator_manager
    if _visual_indicator_manager is None:
        _visual_indicator_manager = VisualIndicatorManager(tray_icon)
    return _visual_indicator_manager

def reset_visual_indicator_manager():
    """Reset visual indicator manager"""
    global _visual_indicator_manager
    _visual_indicator_manager = None