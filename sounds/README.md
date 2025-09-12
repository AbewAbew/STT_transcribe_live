# 🔊 Audio Notifications

This folder contains sound files for STT system notifications.

## 📁 Sound Files:

- **`ready.wav`** - Played when model is loaded and ready to transcribe
- **`start.wav`** - Played when recording starts  
- **`stop.wav`** - Played when recording stops
- **`command.wav`** - Played when voice command is executed
- **`error.wav`** - Played when an error occurs
- **`notification.wav`** - Generic notification sound

## 🎵 Supported Formats:

- **Primary**: WAV files (recommended)
- **Fallback**: System sounds if WAV files not found

## 📥 Adding Custom Sounds:

1. Place your `.wav` files in this directory
2. Use the exact filenames listed above
3. Recommended: 16kHz sample rate, mono, short duration (0.5-2 seconds)

## ⚙️ Configuration:

Audio notifications can be enabled/disabled and volume controlled through the settings interface.

**Note**: If no custom sound files are found, the system will use built-in system sounds as fallback.