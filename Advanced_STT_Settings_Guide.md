# Advanced STT Settings Guide

This guide explains all the advanced settings available in your enhanced Global STT system and when to adjust them for optimal performance.

## 🎯 Overview

Your Global STT system now includes enterprise-level features from RealtimeSTT_server, allowing you to fine-tune speech recognition for your specific environment and needs.

## 📊 Advanced VAD Settings

Voice Activity Detection (VAD) determines when you're speaking vs. when there's silence/noise.

### Silero VAD Sensitivity (0.01 - 1.0)
**Default: 0.05**

- **What it does**: Controls how sensitive the Silero VAD model is to detecting speech
- **Lower values (0.01-0.03)**: Less sensitive, ignores more background noise
- **Higher values (0.06-1.0)**: More sensitive, picks up quieter speech but may trigger on noise

**When to adjust**:
- **Noisy environment**: Lower to 0.02-0.03
- **Quiet environment**: Raise to 0.06-0.08
- **Soft speaker**: Raise to 0.07-0.10
- **Background music/TV**: Lower to 0.01-0.02

### WebRTC VAD Sensitivity (0 - 3)
**Default: 3**

- **What it does**: Alternative VAD method, integer scale where higher = less sensitive
- **0**: Most sensitive (picks up everything)
- **1**: Moderately sensitive
- **2**: Less sensitive
- **3**: Least sensitive (default, good for most cases)

**When to adjust**:
- **Very noisy environment**: Keep at 3 or try Silero instead
- **Clean environment with soft speech**: Try 1-2
- **If Silero VAD isn't working well**: Switch to WebRTC and experiment

### Early Transcription on Silence (0.0 - 1.0s)
**Default: 0.2**

- **What it does**: Starts transcribing after this many seconds of silence during speech
- **0.0**: Disabled, only transcribe after you fully stop speaking
- **0.1-0.3**: Quick response, good for interactive use
- **0.4-1.0**: More deliberate, waits longer before transcribing

**When to adjust**:
- **Fast typing**: Lower to 0.1s for quicker response
- **Careful speech**: Raise to 0.4-0.5s to avoid premature transcription
- **Presentations**: Raise to 0.3-0.4s for natural pauses

### Use Silero ONNX (faster)
**Default: Unchecked**

- **What it does**: Uses optimized ONNX version of Silero for faster processing
- **Checked**: Faster but uses more CPU
- **Unchecked**: Slower but more compatible

**When to enable**:
- **Powerful CPU**: Enable for better performance
- **Real-time typing**: Enable for reduced latency
- **Older hardware**: Keep disabled to avoid overload

## 🤖 Model Parameters

Controls how the AI models process your speech.

### Main Model Beam Size (1 - 10)
**Default: 5**

- **What it does**: How many possibilities the main model considers
- **Lower (1-3)**: Faster but less accurate
- **Higher (6-10)**: More accurate but slower

**When to adjust**:
- **Gaming/fast typing**: Lower to 2-3 for speed
- **Professional writing**: Raise to 7-8 for accuracy
- **Technical terms**: Raise to 8-10 for better recognition
- **Slow computer**: Lower to 2-4

### Realtime Model Beam Size (1 - 5)
**Default: 3**

- **What it does**: Beam size for real-time typing (when enabled)
- **Lower (1-2)**: Faster real-time updates
- **Higher (4-5)**: More accurate real-time text

**When to adjust**:
- **Real-time typing enabled**: Keep at 2-3 for responsiveness
- **Accuracy over speed**: Raise to 4-5
- **Performance issues**: Lower to 1-2

### Batch Size (1 - 32)
**Default: 16**

- **What it does**: How much audio to process at once
- **Lower (1-8)**: Lower latency, more responsive
- **Higher (24-32)**: More efficient but higher latency

**When to adjust**:
- **Real-time use**: Lower to 4-8
- **Batch processing**: Raise to 24-32
- **Memory issues**: Lower to 2-4
- **Powerful GPU**: Raise to 24-32

## 🧠 Intelligent Pause Detection

Controls how the system interprets different types of pauses in your speech.

### End of Sentence Pause (0.1 - 2.0s)
**Default: 0.45**

- **What it does**: How long a pause indicates you finished a sentence
- **Shorter (0.1-0.3s)**: Quick sentence detection
- **Longer (0.6-2.0s)**: More deliberate, waits for clear end

**When to adjust**:
- **Fast speaker**: Lower to 0.2-0.3s
- **Thoughtful speaker**: Raise to 0.6-0.8s
- **Dictation**: Lower to 0.3s for quick sentences
- **Presentations**: Raise to 0.5-0.7s

### Unknown Sentence Pause (0.1 - 3.0s)
**Default: 0.7**

- **What it does**: Pause length that suggests incomplete/trailing sentences
- **Shorter**: Catches "um..." and incomplete thoughts faster
- **Longer**: Gives more time to complete thoughts

**When to adjust**:
- **Clean speaker**: Lower to 0.4-0.5s
- **Lots of "um/ah"**: Raise to 1.0-1.5s
- **Technical explanations**: Raise to 0.8-1.0s

### Mid Sentence Pause (0.5 - 5.0s)
**Default: 2.0**

- **What it does**: How long a pause can be while still being the same sentence
- **Shorter**: Breaks sentences more aggressively  
- **Longer**: Keeps longer thoughts together

**When to adjust**:
- **Continuous speaking**: Raise to 3.0-4.0s
- **Short phrases**: Lower to 1.0-1.5s
- **List dictation**: Lower to 0.8-1.2s

## ⚡ Realtime Tuning

Fine-tune the real-time transcription behavior.

### Realtime Processing Pause (0.005 - 0.1s)
**Default: 0.02**

- **What it does**: Delay between processing audio chunks
- **Lower (0.005-0.01s)**: More responsive, higher CPU usage
- **Higher (0.03-0.1s)**: Less responsive, lower CPU usage

### Post-speech Silence (0.2 - 2.0s)
**Default: 0.7**

- **What it does**: How long to wait after you stop speaking before finalizing
- **Lower**: Quick finalization, good for short commands
- **Higher**: More time to continue thoughts

### Min Utterance Length (0.1 - 1.0s)
**Default: 0.3**

- **What it does**: Minimum speech length to process
- **Lower**: Catches short words/sounds
- **Higher**: Ignores brief noises

### Min Gap Between Recordings (0.0 - 0.5s)
**Default: 0.0**

- **What it does**: Minimum silence between separate recordings
- **0.0**: No gap required
- **Higher**: Prevents overlapping recordings

## 🎯 Recommended Settings by Use Case

### 🎮 Gaming/Fast Commands
```
Silero VAD Sensitivity: 0.03
Main Model Beam Size: 2
Realtime Model Beam Size: 2
End of Sentence Pause: 0.2s
Batch Size: 4
```

### 📝 Professional Writing
```
Silero VAD Sensitivity: 0.05
Main Model Beam Size: 8
Realtime Model Beam Size: 3
End of Sentence Pause: 0.5s
Batch Size: 16
```

### 🏢 Noisy Office Environment
```
Silero VAD Sensitivity: 0.02
WebRTC VAD Sensitivity: 3
Use Silero ONNX: ✓
Early Transcription: 0.3s
```

### 🎤 Presentations/Public Speaking
```
Silero VAD Sensitivity: 0.06
End of Sentence Pause: 0.6s
Mid Sentence Pause: 3.0s
Post-speech Silence: 1.0s
```

### 💻 Technical Documentation
```
Main Model Beam Size: 9
Realtime Model Beam Size: 4
End of Sentence Pause: 0.4s
Unknown Sentence Pause: 1.0s
```

### 🏠 Quiet Home Environment
```
Silero VAD Sensitivity: 0.07
WebRTC VAD Sensitivity: 1
Early Transcription: 0.15s
Min Utterance Length: 0.2s
```

## 🔧 Troubleshooting

### Problem: Not picking up quiet speech
**Solution**: 
- Increase Silero VAD Sensitivity to 0.06-0.08
- Lower WebRTC VAD Sensitivity to 1-2
- Decrease Min Utterance Length to 0.2s

### Problem: Triggering on background noise
**Solution**:
- Decrease Silero VAD Sensitivity to 0.02-0.03
- Keep WebRTC VAD Sensitivity at 3
- Increase Min Utterance Length to 0.4s

### Problem: Slow/laggy transcription
**Solution**:
- Lower Main Model Beam Size to 3-4
- Lower Realtime Model Beam Size to 2
- Decrease Batch Size to 8
- Enable Silero ONNX

### Problem: Cutting off sentences too early
**Solution**:
- Increase End of Sentence Pause to 0.6-0.8s
- Increase Post-speech Silence to 1.0s
- Increase Mid Sentence Pause to 3.0s

### Problem: Taking too long to finalize text
**Solution**:
- Decrease End of Sentence Pause to 0.3s
- Decrease Post-speech Silence to 0.5s
- Decrease Early Transcription to 0.1s

## 💡 Pro Tips

1. **Start with defaults** and adjust one setting at a time
2. **Test in your actual environment** - settings that work at home may not work in the office
3. **Lower beam sizes for speed** when doing real-time work
4. **Higher beam sizes for accuracy** when doing final drafts
5. **Save different profiles** by backing up your `stt_settings.json` file for different scenarios
6. **Use real-time typing sparingly** - it's more resource-intensive than batch processing
7. **Enable debug mode** to see what features are working and monitor performance

## 📁 Settings File Location

Your settings are saved in: `stt_settings.json`

You can back up this file to save your configurations or share settings between installations.

---

*This guide covers the advanced features integrated from RealtimeSTT_server. Your system automatically detects which features are supported by your RealtimeSTT version.*
