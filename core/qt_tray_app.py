"""
Qt Tray Application
Modern Qt-based system tray using refactored components
"""

import sys
import webbrowser
import subprocess
import os
from typing import Optional

from PySide6.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QMessageBox
from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor, QAction
from PySide6.QtCore import Qt

from .refactored_global_stt import RefactoredGlobalSTTManager
from .qt_settings_dialog import QtSettingsDialog
from .config import get_config, AVAILABLE_MODELS
from .visual_indicators import get_visual_indicator_manager
from .model_ready_events import ModelState


def create_default_icon() -> QIcon:
    """Create default microphone icon for system tray"""
    pixmap = QPixmap(32, 32)
    pixmap.fill(QColor(255, 0, 0, 0))  # Transparent background
    
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    
    # Draw microphone body (rounded rectangle)
    painter.setBrush(QColor(80, 80, 80))
    painter.setPen(QColor(60, 60, 60))
    painter.drawRoundedRect(12, 6, 8, 14, 3, 3)
    
    # Draw microphone base/stand
    painter.drawRect(14, 20, 4, 4)
    painter.drawRect(10, 24, 12, 2)
    
    # Draw sound waves
    painter.setPen(QColor(100, 150, 255, 180))
    painter.drawArc(4, 8, 6, 6, 0, 180 * 16)
    painter.drawArc(2, 6, 10, 10, 0, 180 * 16)
    
    painter.end()
    
    return QIcon(pixmap)


class ModernQtTrayApp:
    """
    Modern Qt system tray application using refactored components.
    Much cleaner than the original implementation.
    """
    
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)  # Keep running when dialogs close
        
        # Initialize components
        self.config = get_config()
        self.manager = RefactoredGlobalSTTManager(enable_hotkeys=True)
        
        # Setup system tray
        self._setup_tray()
        
        # Setup visual indicators
        self.visual_indicators = get_visual_indicator_manager(self.tray_icon)
        self._setup_visual_callbacks()
        
        # Connect manager notifications to tray
        self.manager.notification_callback = self._show_tray_notification
    
    def _setup_tray(self):
        """Setup system tray icon and menu"""
        # Check system tray availability
        if not QSystemTrayIcon.isSystemTrayAvailable():
            print("❌ System tray is not available!")
            return
        
        self.tray_icon = QSystemTrayIcon(create_default_icon(), self.app)
        self.tray_icon.setToolTip("Advanced Global STT")
        
        # Create and set menu
        self.menu = QMenu()
        self._build_menu()
        self.tray_icon.setContextMenu(self.menu)
        
        # Show tray icon
        self.tray_icon.show()
        
        # Show notification to help locate the icon
        self.tray_icon.showMessage(
            "STT System Ready", 
            "Advanced Global STT is now running in the system tray", 
            QSystemTrayIcon.Information, 
            3000
        )
    
    def _setup_visual_callbacks(self):
        """Setup visual indicator callbacks"""
        # Connect to model state changes
        self.manager.model_event_manager.add_state_callback(
            ModelState.INITIALIZING, 
            lambda: self.visual_indicators.set_initializing("Loading AI model...")
        )
        self.manager.model_event_manager.add_state_callback(
            ModelState.READY,
            lambda: self.visual_indicators.set_ready()
        )
        self.manager.model_event_manager.add_state_callback(
            ModelState.ERROR,
            lambda: self.visual_indicators.set_error("Model failed to load")
        )
        
        # Override manager notifications to sync with visual indicators
        original_notification = self.manager.notification_callback
        
        def enhanced_notification(title: str, message: str):
            # Call original notification
            if original_notification:
                original_notification(title, message)
            
            # Update visual indicators based on notification
            if "Started" in title or "Recording" in title:
                self.visual_indicators.set_recording()
            elif "Stopped" in title:
                self.visual_indicators.set_ready()
            elif "Command" in title:
                self.visual_indicators.show_command_executed()
            elif "Error" in title:
                self.visual_indicators.set_error()
        
        self.manager.notification_callback = enhanced_notification
    
    def _build_menu(self):
        """Build the context menu"""
        self.menu.clear()
        
        # Recording controls
        start_action = QAction("Start Recording", self.menu)
        start_action.triggered.connect(self.manager.start_recording)
        self.menu.addAction(start_action)
        
        stop_action = QAction("Stop Recording", self.menu)
        stop_action.triggered.connect(self.manager.stop_recording)
        self.menu.addAction(stop_action)
        
        self.menu.addSeparator()
        
        # Model selection submenu
        current_model = self.config.config.basic.model
        model_menu = QMenu(f"Model: {current_model}", self.menu)
        
        for model_id, model_info in AVAILABLE_MODELS.items():
            action = QAction(f"{model_id} ({model_info['description']})", model_menu)
            action.triggered.connect(lambda checked=False, m=model_id: self._change_model(m))
            if model_id == current_model:
                action.setCheckable(True)
                action.setChecked(True)
            model_menu.addAction(action)
        
        self.menu.addMenu(model_menu)
        
        # Status indicators
        wake_config = self.config.config.wake_word
        if wake_config.enabled:
            wake_text = f"Wake: {wake_config.wake_words}"
        else:
            wake_text = "Wake: Disabled"
        
        wake_action = QAction(wake_text, self.menu)
        wake_action.triggered.connect(self._open_settings)
        self.menu.addAction(wake_action)
        
        # Real-time typing indicator
        realtime_text = "Real-time: On" if self.config.config.basic.realtime_typing else "Real-time: Off"
        realtime_action = QAction(realtime_text, self.menu)
        realtime_action.triggered.connect(self._open_settings)
        self.menu.addAction(realtime_action)
        
        self.menu.addSeparator()
        
        # Settings and tools
        settings_action = QAction("Settings", self.menu)
        settings_action.triggered.connect(self._open_settings)
        self.menu.addAction(settings_action)
        
        calibrate_action = QAction("Calibrate Noise", self.menu)
        calibrate_action.triggered.connect(self.manager.calibrate_noise)
        self.menu.addAction(calibrate_action)
        
        status_action = QAction("Status", self.menu)
        status_action.triggered.connect(self._show_status)
        self.menu.addAction(status_action)
        
        web_action = QAction("Web Interface", self.menu)
        web_action.triggered.connect(self._open_web_interface)
        self.menu.addAction(web_action)
        
        self.menu.addSeparator()
        
        # Exit
        exit_action = QAction("Exit", self.menu)
        exit_action.triggered.connect(self._quit_application)
        self.menu.addAction(exit_action)
    
    def _change_model(self, model_name: str):
        """Change the current model"""
        if self.manager.is_recording:
            QMessageBox.information(
                None, 
                "Change Model", 
                "Please stop recording before changing the model."
            )
            return
        
        self.manager.change_model(model_name)
        self._refresh_menu()
    
    def _refresh_menu(self):
        """Refresh the menu to reflect current state"""
        self._build_menu()
    
    def _open_settings(self):
        """Open settings dialog"""
        try:
            dialog = QtSettingsDialog(
                manager=self.manager,
                refresh_callback=self._refresh_menu
            )
            dialog.exec()
        except Exception as e:
            QMessageBox.critical(None, "Settings Error", f"Error opening settings: {e}")
    
    def _show_status(self):
        """Show system status"""
        try:
            # Check web interface status
            web_status = self._check_web_interface_status()
            
            # Get manager status
            status = self.manager.get_status()
            
            recording_status = "Running" if status['is_recording'] else "Stopped"
            
            status_text = (
                f"Global STT: {recording_status}\n"
                f"Web Interface: {web_status}\n\n"
                f"Current Model: {status['current_model']}\n"
                f"Real-time Typing: {'Enabled' if status['realtime_typing'] else 'Disabled'}\n"
                f"Wake Words: {'Enabled' if status['wake_words_enabled'] else 'Disabled'}"
            )
            
            if status['wake_words_enabled']:
                status_text += f"\nWake Word: {status['wake_word']}"
            
            QMessageBox.information(None, "STT System Status", status_text)
            
        except Exception as e:
            QMessageBox.critical(None, "Status Error", f"Error getting status: {e}")
    
    def _check_web_interface_status(self) -> str:
        """Check if web interface is running"""
        try:
            import requests
            response = requests.get('http://127.0.0.1:5000/api/health', timeout=2)
            return "Running" if response.status_code == 200 else "Stopped"
        except Exception:
            return "Stopped"
    
    def _open_web_interface(self):
        """Open web interface in browser"""
        try:
            # Check if web server is running
            if "Stopped" in self._check_web_interface_status():
                # Start web server
                self._show_tray_notification("Starting Web Server", "Launching web interface...")
                script_dir = os.path.dirname(os.path.dirname(__file__))  # Go up from core/
                app_path = os.path.join(script_dir, "app.py")
                subprocess.Popen([sys.executable, app_path], cwd=script_dir)
                import time
                time.sleep(3)  # Wait for server to start
            
            # Open interface
            interface_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)), 
                "enhanced_interface.html"
            )
            webbrowser.open(f"file://{interface_path}")
            
        except Exception as e:
            QMessageBox.critical(None, "Web Interface Error", f"Error opening web interface: {e}")
    
    def _show_tray_notification(self, title: str, message: str):
        """Show system tray notification"""
        try:
            self.tray_icon.showMessage(
                title, 
                message, 
                QSystemTrayIcon.Information, 
                4000  # 4 seconds
            )
        except Exception as e:
            print(f"Notification error: {e}")
    
    def _quit_application(self):
        """Quit the application cleanly"""
        try:
            # Stop recording
            if self.manager.is_recording:
                self.manager.stop_recording()
            
            # Hide tray icon
            self.tray_icon.hide()
            
            # Quit application
            self.app.quit()
            
        except Exception as e:
            print(f"Quit error: {e}")
        finally:
            sys.exit(0)
    
    def run(self):
        """Run the application"""
        print("Modern Global STT started!")
        print("Hotkeys: Start=Ctrl+Shift+S, Stop=Ctrl+Shift+X, Toggle=Ctrl+Shift+T")
        print("Check system tray for controls")
        
        return self.app.exec()


def main():
    """Main entry point"""
    try:
        app = ModernQtTrayApp()
        return app.run()
    except Exception as e:
        print(f"Application error: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())