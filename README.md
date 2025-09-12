# 🎤 Modern RealtimeSTT System

A professional-grade Speech-to-Text system with modular architecture, system tray integration, and advanced features. Features real-time transcription, visual indicators, audio notifications, and global hotkey support.

## 📌 Status
- **Modern Architecture**: Fully refactored with modular components
- **System Tray App**: Stable Qt-based tray application with visual indicators
- **Audio Enhancements**: Ready notifications, sound feedback, and state management
- **Production Ready**: Comprehensive error handling and user experience

## ✨ Key Features

### 🖥️ Modern System Tray Integration
- **Qt System Tray** with dynamic microphone icons
- **Visual State Indicators** - Icons change color based on system state:
  - Gray: Idle/stopped
  - Orange: Initializing/loading model  
  - Green: Ready to record
  - Red: Currently recording
  - Blue: Processing speech
- **Audio Notifications** when model is ready and during state changes
- **System Notifications** for important events
- **Right-click Menu** with full feature access

### 🎯 Advanced Speech-to-Text
- **Multiple AI Models** (Tiny → Large-v3) with local processing
- **Real-time Transcription** with immediate text output
- **Global Hotkeys** - Work in any application:
  - `Ctrl+Shift+S` - Start recording
  - `Ctrl+Shift+X` - Stop recording  
  - `Ctrl+Shift+T` - Toggle recording
  - `Ctrl+Shift+N` - Calibrate noise
- **Wake Word Support** (optional) with customizable sensitivity
- **Voice Activity Detection** with advanced tuning

### 🔧 Intelligent Text Processing
- **Real-time Typing** - Type as you speak with smart backspace management
- **Auto-punctuation** and capitalization
- **Voice Commands** (new line, copy, paste, undo, etc.)
- **Custom Vocabulary** with spoken→written mappings
- **Multiple Insert Modes** - Direct typing, clipboard, or text replacement

### ⚙️ Professional Configuration
- **Tabbed Settings Dialog** with organized options:
  - Basic Settings (model, language, typing mode)
  - Wake Word Configuration
  - Real-time Processing Options
  - VAD & Audio Settings
  - Model & Performance Tuning
  - Audio Notifications
- **Persistent Settings** automatically saved
- **Model Hot-swapping** without restart
- **Noise Calibration** for optimal audio input

## 🛠️ Installation

### Prerequisites
- **Windows 10/11**
- **Python 3.8+**  
- **Virtual Environment** (recommended)
- **Microphone** with good quality

### Quick Setup

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd RealtimeSTT_Project
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   pip install PySide6  # For system tray functionality
   ```

4. **Run the system**:
   ```bash
   venv\Scripts\python.exe modern_global_stt.py
   ```

### Alternative Launch Methods

#### Batch File (Windows)
```bash
start_stt.bat  # Uses virtual environment automatically
```

#### Hidden Mode (Background)
```vbs
start_stt_hidden.vbs  # Runs without console window
```

#### Headless Mode (No GUI)
```bash
venv\Scripts\python.exe modern_global_stt.py --headless
```

## 🎯 Usage

### System Tray Mode (Recommended)
1. Run `venv\Scripts\python.exe modern_global_stt.py`
2. Look for the microphone icon in your system tray
3. You'll see a notification: "STT System Ready"
4. Use global hotkeys in any application
5. Right-click tray icon for settings and controls

### Command Line Options
```bash
python modern_global_stt.py              # Qt tray mode (default)
python modern_global_stt.py --headless   # No GUI, hotkeys only
python modern_global_stt.py --info       # Show system information
python modern_global_stt.py --help       # Show all options
```

### System Tray Menu
- **Start/Stop Recording** - Quick recording controls
- **Model Selection** - Switch between AI models
- **Settings** - Open comprehensive settings dialog
- **Status** - View system and connection status
- **Calibrate Noise** - Optimize audio input
- **Web Interface** - Launch web-based interface

## 🤖 AI Models

| Model | Speed | Accuracy | RAM | Best For |
|-------|-------|----------|-----|----------|
| **tiny.en** | ⚡⚡⚡⚡⚡ | ⭐⭐⭐ | ~1GB | Quick notes, testing |
| **base.en** | ⚡⚡⚡⚡ | ⭐⭐⭐⭐ | ~1GB | General use |
| **small.en** | ⚡⚡⚡ | ⭐⭐⭐⭐ | ~2GB | **Recommended balance** |
| **medium.en** | ⚡⚡ | ⭐⭐⭐⭐⭐ | ~5GB | High accuracy |
| **large-v3** | ⚡ | ⭐⭐⭐⭐⭐ | ~10GB | Maximum accuracy |

## 🏗️ Modern Architecture

### Core Components
```
core/
├── config.py                    # Centralized configuration system
├── refactored_global_stt.py     # Main STT manager (86% smaller)
├── qt_tray_app.py              # Qt system tray application
├── qt_settings_dialog.py       # Modern tabbed settings UI
├── unified_text_processor.py   # Consolidated text processing
├── realtime_typing_manager.py  # Smart typing with backspace management
├── audio_notifications.py      # Multi-backend audio system
├── model_ready_events.py       # Thread-safe model state management
└── visual_indicators.py        # Dynamic tray icons and states
```

### Entry Points
- `modern_global_stt.py` - Main launcher (replaces old files)
- `start_stt.bat` - Windows batch launcher
- `start_stt_hidden.vbs` - Background launcher

### Key Improvements
- **85+ Configuration Parameters** centralized into structured dataclasses
- **800+ Lines of Code Duplication** eliminated
- **50% Reduction** in main codebase size while adding features
- **Thread-safe Operations** with proper synchronization
- **Error Handling** with graceful fallbacks and user feedback

## ⚙️ Configuration Options

### Basic Settings
- **Model Selection** - Choose AI model for transcription
- **Language** - Input language selection
- **Realtime Typing** - Type as you speak
- **Post-processing** - Auto-punctuation and capitalization

### Wake Word Settings
- **Enable/Disable** wake word detection
- **Custom Wake Words** - Configure activation phrases
- **Sensitivity** - Adjust detection threshold
- **Custom Model Path** - Use specialized wake word models

### Audio & VAD Settings
- **Audio Enhancement** - Noise reduction and filtering
- **VAD Sensitivity** - Voice activity detection tuning
- **Silence Detection** - Pause handling configuration
- **Device Selection** - Choose audio input device

### Model & Performance
- **Beam Size** - Search algorithm width (accuracy vs speed)
- **Batch Size** - Processing chunk size
- **Temperature** - Output randomness control
- **Model Caching** - Faster startup options

### Audio Notifications
- **Enable/Disable** system sounds
- **Volume Control** - Notification audio level
- **Sound Types** - Different sounds for different events

## 🔧 Troubleshooting

### System Tray Issues
**Tray icon not appearing:**
- Ensure you're using the virtual environment Python: `venv\Scripts\python.exe`
- Check PySide6 installation: `pip show PySide6`
- Restart Windows to refresh system tray
- Run with debug output for detailed information

**PySide6 import errors:**
```bash
pip install PySide6
# or
pip install --upgrade PySide6
```

### Audio Issues
**Microphone not working:**
- Check Windows microphone permissions
- Test microphone in Windows Sound settings
- Run "Calibrate Noise" from tray menu
- Ensure microphone is set as default device

**No audio notifications:**
- Check audio notification settings in Settings dialog
- Verify system volume is not muted
- Test with different audio backends (sounddevice, pygame, system sounds)

### Performance Issues
**Slow transcription:**
- Use smaller models (tiny.en, base.en)
- Check available RAM and CPU usage  
- Close other resource-intensive applications
- Consider GPU acceleration if available

**High memory usage:**
- Switch to smaller models
- Restart application periodically for long sessions
- Check for memory leaks in Task Manager

### Model Issues
**Model loading errors:**
- Check internet connection for initial downloads
- Verify sufficient disk space (models are 100MB-3GB)
- Try re-downloading models
- Check file permissions in model directory

## 📊 System Information

Use `--info` flag to view detailed system information:
```bash
venv\Scripts\python.exe modern_global_stt.py --info
```

Shows:
- Python version and executable path
- Virtual environment status
- Installed package versions
- System specifications
- Available AI models
- Audio device information

## 🔒 Privacy & Security

- **100% Local Processing** - No cloud services or data transmission
- **No Data Collection** - All transcription stays on your machine
- **Open Source Architecture** - Full code transparency
- **Secure Configuration** - Settings stored locally only
- **No Network Requirements** - Works completely offline after setup

## 🚀 Performance Tips

### Optimal Setup
1. **Use Virtual Environment** - Ensures clean dependency management
2. **Quality Microphone** - USB or XLR mics provide best results
3. **Quiet Environment** - Minimize background noise
4. **Appropriate Model** - Balance speed vs accuracy for your use case
5. **Adequate RAM** - 8GB+ recommended for larger models

### System Requirements
- **Minimum**: 4GB RAM, any CPU, built-in microphone
- **Recommended**: 8GB+ RAM, dedicated microphone, SSD storage
- **Optimal**: 16GB+ RAM, professional microphone, fast CPU

## 🆕 Recent Enhancements

### Version 2.0 Features
- ✅ **Complete Architecture Refactor** with modular components
- ✅ **Modern Qt System Tray** with dynamic visual indicators  
- ✅ **Audio Notification System** with multi-backend support
- ✅ **Thread-safe Model State Management** with event synchronization
- ✅ **Unified Configuration System** with 85+ organized parameters
- ✅ **Smart Real-time Typing** with backspace management
- ✅ **Comprehensive Settings Dialog** with tabbed interface
- ✅ **Professional Error Handling** with user-friendly feedback

### Legacy File Migration
The following files have been replaced by the modern architecture:
- `global_stt.py` → `core/refactored_global_stt.py`
- `global_stt_qt.py` → `modern_global_stt.py` + `core/qt_tray_app.py`
- Various scattered utilities → Organized `core/` modules

## 🤝 Contributing

This project follows modern software development practices:
- **Modular Architecture** for maintainability
- **Type Hints** for better code quality
- **Error Handling** for reliability
- **Documentation** for usability

Suggestions and improvements are welcome!

## 📄 License

This project is for personal and educational use. Please respect the licenses of underlying libraries (RealtimeSTT, PySide6, etc.).

---

**🎯 Modern Speech-to-Text Made Simple**

*Experience seamless voice-to-text with professional-grade features and intuitive design.*