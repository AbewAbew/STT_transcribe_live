# 🎤 Advanced RealtimeSTT System

A professional-grade Speech-to-Text system with web interface and global integration for Windows. Transform your voice into text anywhere on your system with GPU acceleration and multiple AI models.

## ✨ Features

### 🌐 Web Interface
- **Modern UI** with real-time transcription display
- **Multiple AI Models** (Tiny to Large-v3) with speed/accuracy trade-offs
- **Live Statistics** showing word count, sentences, and WPM
- **Text Processing** with auto-punctuation and capitalization
- **Export Options** - Copy, save, or download transcriptions
- **Keyboard Shortcuts** for quick control

### 🌍 Global STT Integration
- **System Tray Application** for system-wide speech-to-text
- **Global Hotkeys** - Use STT in any application
- **Configurable Settings** with persistent preferences
- **Multiple Insert Modes** - Type directly, clipboard, or replace text

### 🚀 Performance & Quality
- **NVIDIA GPU Acceleration** with CUDA support
- **Advanced Audio Processing** with noise reduction
- **Real-time Transcription** with live preview
- **Session Statistics** and usage analytics
- **Model Caching** for faster startup

## 🛠️ Installation

### Prerequisites
- **Windows 10/11**
- **Python 3.8+**
- **NVIDIA GPU** with CUDA support (recommended)
- **Microphone** with good quality

### Quick Setup

1. **Clone or download** this repository
2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Download AI models**:
   ```bash
   python download_models.py
   ```
4. **Start the system**:
   ```bash
   python start_stt.py
   ```

### Alternative: Use Batch File
Double-click `start_stt.bat` for automatic setup and launch.

## 🎯 Usage

### Web Interface Mode
1. Run `python start_stt.py` or `start_stt.bat`
2. Open `interface.html` in your browser (auto-opens)
3. Select your preferred AI model
4. Click "Start Recording" and speak
5. Watch real-time transcription appear
6. Use text controls to copy, save, or export

### Global STT Mode
1. Run `python global_stt.py` or select from launcher menu
2. Check system tray for the microphone icon
3. Use hotkeys anywhere in Windows:
   - **Ctrl+Shift+S** - Start recording
   - **Ctrl+Shift+X** - Stop recording
   - **Ctrl+Shift+T** - Toggle recording
4. Right-click tray icon for settings

### Keyboard Shortcuts (Web Interface)
- **Ctrl+Shift+S** - Start recording
- **Ctrl+Shift+X** - Stop recording
- **Ctrl+Shift+C** - Copy transcription

## 🤖 AI Models

| Model | Speed | Accuracy | Language | Best For |
|-------|-------|----------|----------|----------|
| **tiny.en** | ⚡⚡⚡⚡⚡ | ⭐⭐⭐ | English | Quick notes, testing |
| **base.en** | ⚡⚡⚡⚡ | ⭐⭐⭐⭐ | English | General use |
| **small.en** | ⚡⚡⚡ | ⭐⭐⭐⭐ | English | **Recommended balance** |
| **medium.en** | ⚡⚡ | ⭐⭐⭐⭐⭐ | English | High accuracy needs |
| **large-v3** | ⚡ | ⭐⭐⭐⭐⭐ | Multilingual | Maximum accuracy |

## ⚙️ Configuration

### Web Interface Settings
- **Model Selection** - Choose AI model for transcription
- **Language** - Select input language
- **Auto-Punctuation** - Automatically add periods
- **Auto-Capitalize** - Capitalize first letter of sentences
- **Global Typing** - Type transcription into active window

### Global STT Settings
- **Insert Mode** - How text is inserted (type/clipboard/replace)
- **Text Processing** - Punctuation and capitalization options
- **Hotkey Customization** - Change global keyboard shortcuts

## 📊 Statistics & Analytics

The system tracks:
- **Session Duration** - How long you've been using STT
- **Word Count** - Total words transcribed
- **Sentences** - Number of complete sentences
- **WPM** - Words per minute speaking rate
- **Model Usage** - Which models you use most

Access statistics via:
- Web interface statistics panel
- Launcher menu → View Statistics
- `session_stats.json` file

## 🔧 Troubleshooting

### Common Issues

**Microphone not working:**
- Check Windows microphone permissions
- Ensure microphone is set as default device
- Test microphone in Windows Sound settings

**CUDA/GPU issues:**
- Verify NVIDIA drivers are installed
- Check CUDA toolkit installation
- Models will fall back to CPU if GPU unavailable

**Model loading errors:**
- Run `python download_models.py` to re-download
- Check internet connection
- Ensure sufficient disk space (models are 100MB-3GB each)

**Performance issues:**
- Use smaller models (tiny.en, base.en) for faster processing
- Close other GPU-intensive applications
- Ensure adequate RAM (8GB+ recommended)

### Getting Help

1. Check the **Help** section in the launcher menu
2. Review error messages in the console
3. Check `realtimesst.log` for detailed logs
4. Ensure all requirements are installed: `pip install -r requirements.txt`

## 📁 File Structure

```
RealtimeSTT_Project/
├── 🌐 interface.html          # Modern web interface
├── 📱 app.js                  # Enhanced frontend logic
├── 🖥️ app.py                  # Flask server with API
├── 🌍 global_stt.py           # System tray application
├── 🚀 start_stt.py            # Enhanced launcher
├── 📦 requirements.txt        # Python dependencies
├── 📥 download_models.py      # Model downloader
├── 🧪 test_stt.py            # System tester
├── 📝 dictate.py             # Simple dictation script
├── 🪟 start_stt.bat          # Windows batch launcher
└── 📊 session_stats.json     # Usage statistics
```

## 🎨 Customization

### Themes & Appearance
The web interface uses a Matrix-inspired theme with:
- **Dark background** with animated binary rain
- **Green accent colors** for cyberpunk aesthetic
- **Responsive design** for different screen sizes
- **Modern glassmorphism** effects

### Adding Custom Models
1. Add model name to `CONFIG['models']` in `app.py`
2. Update model selection in `interface.html`
3. Download model using `download_models.py`

### Custom Hotkeys
Modify hotkey combinations in `global_stt.py`:
```python
self.start_hotkey = "ctrl+shift+s"  # Change as needed
self.stop_hotkey = "ctrl+shift+x"   # Change as needed
```

## 🔒 Privacy & Security

- **Local Processing** - All transcription happens on your machine
- **No Cloud Services** - Your voice data never leaves your computer
- **No Data Collection** - Only local usage statistics are stored
- **Open Source** - Full transparency in code and functionality

## 🚀 Performance Tips

### For Best Results:
1. **Use a quality microphone** - USB or XLR mics work best
2. **Minimize background noise** - Use in quiet environments
3. **Speak clearly** - Normal pace, clear pronunciation
4. **Choose appropriate model** - Balance speed vs accuracy needs
5. **GPU acceleration** - Ensure CUDA is properly configured

### System Requirements:
- **Minimum**: 4GB RAM, any CPU, integrated audio
- **Recommended**: 8GB+ RAM, NVIDIA GPU, dedicated microphone
- **Optimal**: 16GB+ RAM, RTX 3060+, professional microphone

## 📈 Future Enhancements

Planned features:
- **Voice Commands** - Control system with voice
- **Custom Vocabularies** - Add specialized terms
- **Multiple Languages** - Simultaneous multi-language support
- **Cloud Sync** - Optional cloud backup of transcriptions
- **Plugin System** - Extend functionality with plugins

## 🤝 Contributing

This is a personal project, but suggestions and improvements are welcome!

## 📄 License

This project is for personal use. Please respect the licenses of underlying libraries (RealtimeSTT, Flask, etc.).

---

**Made with ❤️ for seamless speech-to-text integration**

*Transform your voice into text, anywhere, anytime.*