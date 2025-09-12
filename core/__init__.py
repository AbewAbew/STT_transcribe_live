"""
Core module for Modern Global STT
Refactored, modular components for the RealtimeSTT system
"""

from .config import get_config, reset_config
from .unified_text_processor import get_text_processor, reset_text_processor  
from .realtime_typing_manager import get_typing_manager, reset_typing_manager
from .audio_notifications import get_notification_manager, reset_notification_manager
from .model_ready_events import get_model_event_manager, reset_model_event_manager, ModelState
from .visual_indicators import get_visual_indicator_manager, reset_visual_indicator_manager, IndicatorState
from .refactored_global_stt import RefactoredGlobalSTTManager

# Try to import Qt components (optional)
try:
    from .qt_settings_dialog import QtSettingsDialog
    from .qt_tray_app import ModernQtTrayApp
    QT_AVAILABLE = True
except ImportError:
    QT_AVAILABLE = False

__version__ = "2.0.0"
__all__ = [
    "get_config",
    "reset_config", 
    "get_text_processor",
    "reset_text_processor",
    "get_typing_manager", 
    "reset_typing_manager",
    "get_notification_manager",
    "reset_notification_manager",
    "get_model_event_manager",
    "reset_model_event_manager",
    "ModelState",
    "get_visual_indicator_manager",
    "reset_visual_indicator_manager", 
    "IndicatorState",
    "RefactoredGlobalSTTManager",
    "QT_AVAILABLE"
]

if QT_AVAILABLE:
    __all__.extend(["QtSettingsDialog", "ModernQtTrayApp"])