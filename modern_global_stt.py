#!/usr/bin/env python3
"""
Modern Global STT Application
Replaces both global_stt.py and global_stt_qt.py with clean, modular architecture

Usage:
    python modern_global_stt.py              # Run with Qt tray (recommended)
    python modern_global_stt.py --headless   # Run headless (no GUI)
    python modern_global_stt.py --help       # Show help
"""

import sys
import argparse
import signal
import os
from pathlib import Path

# Add core module to path
sys.path.insert(0, str(Path(__file__).parent / "core"))

def setup_signal_handlers():
    """Setup signal handlers for clean shutdown"""
    def signal_handler(sig, frame):
        print("\n🛑 Shutting down gracefully...")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    try:
        signal.signal(signal.SIGTERM, signal_handler)
    except AttributeError:
        # SIGTERM not available on Windows
        pass


def run_qt_tray():
    """Run the Qt tray application"""
    try:
        from core.qt_tray_app import ModernQtTrayApp
        app = ModernQtTrayApp()
        return app.run()
    except ImportError as e:
        print(f"❌ Error: Qt dependencies not available: {e}")
        print("Please install PySide6: pip install PySide6")
        return 1
    except Exception as e:
        print(f"❌ Error running Qt tray: {e}")
        import traceback
        traceback.print_exc()
        return 1


def run_headless():
    """Run headless mode (no GUI)"""
    try:
        from core.refactored_global_stt import RefactoredGlobalSTTManager
        
        print("Starting Headless Global STT...")
        print("Use Ctrl+Shift+S to start, Ctrl+Shift+X to stop, Ctrl+Shift+T to toggle")
        print("Press Ctrl+C to quit")
        
        manager = RefactoredGlobalSTTManager(enable_hotkeys=True)
        
        # Keep running
        try:
            while True:
                import time
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nStopping...")
            manager.stop_recording()
            return 0
            
    except Exception as e:
        print(f"Error in headless mode: {e}")
        return 1


def show_system_info():
    """Show system information and configuration"""
    print("System Information:")
    print(f"   Python: {sys.version}")
    
    try:
        from core.config import get_config
        config = get_config()
        print(f"   Current Model: {config.config.basic.model}")
        print(f"   Real-time Typing: {config.config.basic.realtime_typing}")
        print(f"   Wake Words: {config.config.wake_word.enabled}")
        if config.config.wake_word.enabled:
            print(f"   Wake Word: {config.config.wake_word.wake_words}")
    except Exception as e:
        print(f"   Config Error: {e}")
    
    # Check dependencies
    print("\nDependencies:")
    deps = [
        ("RealtimeSTT", "Core STT functionality"),
        ("PySide6", "Qt GUI (optional)"),
        ("keyboard", "Global hotkeys"),
        ("pyautogui", "Text insertion"),
        ("numpy", "Audio processing"),
        ("scipy", "Audio filters")
    ]
    
    for dep, desc in deps:
        try:
            __import__(dep)
            print(f"   [OK] {dep}: Available ({desc})")
        except ImportError:
            print(f"   [MISSING] {dep}: Missing ({desc})")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Modern Global STT - Advanced Speech-to-Text System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                    # Run with Qt system tray (recommended)
  %(prog)s --headless         # Run without GUI (hotkeys only)
  %(prog)s --info             # Show system information
  
Hotkeys (when running):
  Ctrl+Shift+S    Start recording
  Ctrl+Shift+X    Stop recording  
  Ctrl+Shift+T    Toggle recording
  Ctrl+Shift+N    Calibrate noise
        """
    )
    
    parser.add_argument(
        "--headless", 
        action="store_true",
        help="Run without GUI (hotkeys only)"
    )
    
    parser.add_argument(
        "--info",
        action="store_true", 
        help="Show system information and exit"
    )
    
    parser.add_argument(
        "--config-file",
        default="stt_settings.json",
        help="Configuration file path (default: stt_settings.json)"
    )
    
    args = parser.parse_args()
    
    # Setup signal handlers
    setup_signal_handlers()
    
    # Show info and exit
    if args.info:
        show_system_info()
        return 0
    
    # Set config file if specified
    if args.config_file != "stt_settings.json":
        os.environ['STT_CONFIG_FILE'] = args.config_file
    
    print("Modern Global STT v2.0")
    print("=" * 40)
    
    # Run in appropriate mode
    if args.headless:
        return run_headless()
    else:
        return run_qt_tray()


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)