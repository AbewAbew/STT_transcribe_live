#!/usr/bin/env python3
"""
Test script for the STT Overlay Window
Quick test to verify overlay window functionality
"""

import sys
from pathlib import Path

# Add core module to path
sys.path.insert(0, str(Path(__file__).parent / "core"))

from PySide6.QtWidgets import QApplication
from core.overlay_window import STTOverlayWindow


def test_start():
    print("Test: Start recording called")


def test_stop():
    print("Test: Stop recording called")


def main():
    app = QApplication(sys.argv)
    
    # Create overlay window
    overlay = STTOverlayWindow()
    
    # Set test callbacks
    overlay.set_callbacks(test_start, test_stop)
    
    # Show window
    overlay.show()
    
    print("Overlay window displayed!")
    print("Click Start/Stop buttons to test functionality")
    print("Close the window or press Ctrl+C to exit")
    
    try:
        return app.exec()
    except KeyboardInterrupt:
        print("\nTest finished.")
        return 0


if __name__ == "__main__":
    sys.exit(main())