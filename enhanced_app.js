// Enhanced app.js with all new features
let audioContext;
let scriptProcessor;
let mediaStreamSource;
const socket = io("http://127.0.0.1:5000");

let fullSentences = [];
let sentenceIndex = 0;
let wordCount = 0;
let isRecording = false;
let startTime = null;

// UI Element References
const startBtn = document.getElementById('start-button');
const stopBtn = document.getElementById('stop-button');
const textDisplay = document.getElementById('text-display');
const modelSelect = document.getElementById('model-select');
const wordCountDisplay = document.getElementById('word-count');
const wpmDisplay = document.getElementById('wpm');

// Feature toggles
const voiceCommandsToggle = document.getElementById('voice-commands-toggle');
const smartTextToggle = document.getElementById('smart-text-toggle');
const audioEnhancementToggle = document.getElementById('audio-enhancement-toggle');
const autoPunctuationToggle = document.getElementById('auto-punctuation-toggle');
const realtimeTypingToggle = document.getElementById('realtime-typing-toggle');

// Buttons
const calibrateBtn = document.getElementById('calibrate-noise');
const clearTextBtn = document.getElementById('clear-text');
const copyTextBtn = document.getElementById('copy-text');
const saveTextBtn = document.getElementById('save-text');
const exportTextBtn = document.getElementById('export-text');
const addWordBtn = document.getElementById('add-word');
const shutdownBtn = document.getElementById('shutdown-button');

// WebSocket Event Listeners
socket.on('connect', () => {
    console.log('Connected to server.');
    textDisplay.innerHTML = '✅ Enhanced STT Ready - All AI features active! ✅';
});

socket.on('disconnect', () => {
    console.log('Disconnected from server.');
    stopAudioProcessing();
    textDisplay.innerHTML = '❌ Server disconnected. Please restart the Python server. ❌';
});

socket.on('realtime_update', (data) => {
    updateTextDisplay(data.text);
});

socket.on('full_sentence_update', (data) => {
    const processedText = data.text;
    fullSentences.push({ text: processedText, index: sentenceIndex++ });
    updateWordCount(processedText);
    updateTextDisplay(""); // Clear the real-time part
});

// Stop event from server (e.g., voice command)
socket.on('transcription_stopped', () => {
    if (!isRecording) return;
    // Clean up audio resources without re-emitting stop
    isRecording = false;
    if (mediaStreamSource) {
        try { mediaStreamSource.disconnect(); } catch (e) {}
        mediaStreamSource = null;
    }
    if (scriptProcessor) {
        try { scriptProcessor.disconnect(); } catch (e) {}
        scriptProcessor = null;
    }
    if (audioContext) {
        try { audioContext.close(); } catch (e) {}
        audioContext = null;
    }
    if (window.currentStream) {
        try { window.currentStream.getTracks().forEach(track => track.stop()); } catch (e) {}
        window.currentStream = null;
    }
    resetRecordingState();
    textDisplay.innerHTML += '<br/><em style="color: #ff4d4d;">⏹️ Recording stopped by server/voice command.</em>';
});

socket.on('voice_command_executed', (data) => {
    textDisplay.innerHTML += `<br/><em style="color: #0F0;">✓ Voice command: ${data.command}</em><br/>`;
});

socket.on('noise_calibrated', () => {
    textDisplay.innerHTML += '<br/><em style="color: #0F0;">✓ Noise calibration complete!</em><br/>';
});

socket.on('model_loaded', (data) => {
    textDisplay.innerHTML += `<br/><em style="color: #0F0;">✓ Model loaded: ${data.model}</em><br/>`;
});

socket.on('error', (data) => {
    textDisplay.innerHTML += `<br/><em style="color: #ff4d4d;">❌ Error: ${data.message}</em><br/>`;
});

// Button Event Listeners
startBtn.addEventListener('click', () => {
    startAudioProcessing();
});

stopBtn.addEventListener('click', () => {
    stopAudioProcessing();
});

// Feature toggle listeners
document.querySelectorAll('.toggle-switch').forEach(toggle => {
    toggle.addEventListener('click', function() {
        this.classList.toggle('active');
        const feature = this.id.replace('-toggle', '');
        updateFeatureSetting(feature, this.classList.contains('active'));
    });
});

// Other button listeners
calibrateBtn.addEventListener('click', () => {
    socket.emit('calibrate_noise');
    textDisplay.innerHTML += '<br/><em>🔧 Calibrating noise... Stay quiet for 3 seconds...</em><br/>';
});

clearTextBtn.addEventListener('click', () => {
    clearText();
});

copyTextBtn.addEventListener('click', () => {
    copyToClipboard();
});

saveTextBtn.addEventListener('click', () => {
    saveText();
});

exportTextBtn.addEventListener('click', () => {
    exportText();
});

addWordBtn.addEventListener('click', () => {
    const spoken = prompt('Enter how you speak the word:');
    const written = prompt('Enter how it should be written:');
    if (spoken && written) {
        socket.emit('add_custom_word', { spoken, written });
        textDisplay.innerHTML += `<br/><em style="color: #0F0;">✓ Added: "${spoken}" → "${written}"</em><br/>`;
    }
});

// Close/shutdown the web interface server
shutdownBtn.addEventListener('click', async () => {
    try {
        if (isRecording) {
            // Ensure recording pipeline is fully stopped locally and on server
            try { stopAudioProcessing(); } catch (e) {}
        }
        showNotification('Shutting down web interface...');
        await fetch('http://127.0.0.1:5000/api/shutdown', { method: 'POST' });
        // Inform user and disable controls
        startBtn.disabled = true;
        stopBtn.disabled = true;
        shutdownBtn.disabled = true;
        textDisplay.innerHTML += '<br/><em style="color:#ff4d4d;">🛑 Web interface is shutting down. You can close this tab.</em>';
    } catch (err) {
        console.error('Failed to shutdown server:', err);
        showNotification('Failed to shutdown server', 'error');
    }
});

// Core Functions
function startAudioProcessing() {
    if (isRecording) return;
    
    startBtn.disabled = true;
    stopBtn.disabled = false;
    isRecording = true;
    startTime = Date.now();
    
    // Reset counters
    fullSentences = [];
    sentenceIndex = 0;
    wordCount = 0;
    updateWordCount('');
    
    textDisplay.innerHTML = "<strong>🎙️ Recording with AI Enhancement Active!</strong><br/>Voice commands enabled - speak naturally!";

    const selectedModel = modelSelect.value;
    
    socket.emit('start_transcription', { 
        model: selectedModel,
        language: 'en'
    });

    navigator.mediaDevices.getUserMedia({ 
        audio: {
            echoCancellation: true,
            noiseSuppression: true,
            autoGainControl: true,
            sampleRate: 48000
        }, 
        video: false 
    })
    .then(stream => {
        const sampleRate = 48000;
        audioContext = new (window.AudioContext || window.webkitAudioContext)({ sampleRate: sampleRate });
        mediaStreamSource = audioContext.createMediaStreamSource(stream);
        scriptProcessor = audioContext.createScriptProcessor(4096, 1, 1);

        scriptProcessor.onaudioprocess = (event) => {
            if (!isRecording) return;
            
            const inputData = event.inputBuffer.getChannelData(0);
            const int16Data = new Int16Array(inputData.length);
            
            for (let i = 0; i < inputData.length; i++) {
                int16Data[i] = Math.max(-32768, Math.min(32767, inputData[i] * 32768));
            }
            
            if (socket.connected) {
                socket.emit('audio_chunk', int16Data.buffer);
            }
        };

        mediaStreamSource.connect(scriptProcessor);
        scriptProcessor.connect(audioContext.destination);
        
        window.currentStream = stream;
    })
    .catch(error => {
        console.error('Error getting microphone:', error);
        textDisplay.innerHTML = `❌ Microphone Error: ${error.message}<br/>Please check your microphone permissions and try again. ❌`;
        resetRecordingState();
    });
}

function stopAudioProcessing() {
    if (!isRecording) return;
    
    isRecording = false;
    
    // Clean up audio resources
    if (mediaStreamSource) {
        mediaStreamSource.disconnect();
        mediaStreamSource = null;
    }
    if (scriptProcessor) {
        scriptProcessor.disconnect();
        scriptProcessor = null;
    }
    if (audioContext) {
        audioContext.close();
        audioContext = null;
    }
    
    // Stop all media tracks
    if (window.currentStream) {
        window.currentStream.getTracks().forEach(track => track.stop());
        window.currentStream = null;
    }
    
    // Notify server
    socket.emit('stop_transcription');
    
    resetRecordingState();
    
    // Show session summary
    const duration = startTime ? Math.round((Date.now() - startTime) / 1000) : 0;
    textDisplay.innerHTML += `<br/><br/><strong>📊 Session Summary:</strong><br/>Duration: ${duration}s | Words: ${wordCount} | Sentences: ${fullSentences.length}`;
}

function resetRecordingState() {
    startBtn.disabled = false;
    stopBtn.disabled = true;
    isRecording = false;
}

function updateTextDisplay(realtimeText) {
    let html = fullSentences.map(sentence => {
        const colorClass = sentence.index % 2 === 0 ? 'yellow' : 'cyan';
        return `<span class="${colorClass}">${sentence.text}</span>`;
    }).join(' ');

    if (realtimeText && realtimeText.trim()) {
        html += ' <span style="color: #fff; opacity: 0.8;">' + realtimeText + '</span>';
    }

    textDisplay.innerHTML = html;
    
    // Auto-scroll to bottom
    const container = document.getElementById('text-display-container');
    container.scrollTop = container.scrollHeight;
}

function updateWordCount(text) {
    if (text && text.trim()) {
        const words = text.trim().split(/\s+/).length;
        wordCount += words;
        wordCountDisplay.textContent = wordCount;
        
        // Update WPM
        if (startTime) {
            const minutes = (Date.now() - startTime) / 60000;
            const wpm = Math.round(wordCount / minutes);
            if (wpmDisplay) {
                wpmDisplay.textContent = isFinite(wpm) ? wpm : 0;
            }
        }
    }
}

function updateFeatureSetting(feature, enabled) {
    // Map UI ids (kebab-case) to server feature keys (snake_case)
    const map = {
        'voice-commands': 'voice_commands',
        'smart-text': 'smart_text',
        'audio-enhancement': 'audio_enhancement',
        'auto-punctuation': 'auto_punctuation',
        'realtime-typing': 'realtime_typing',
    };
    const serverFeature = map[feature] || feature;
    socket.emit('update_feature', { feature: serverFeature, enabled });
    console.log(`Feature ${feature}: ${enabled ? 'enabled' : 'disabled'}`);
    
    // Special handling for realtime typing
    if (serverFeature === 'realtime_typing') {
        if (enabled) {
            showNotification('Real-time typing enabled - text will appear as you speak!');
        } else {
            showNotification('Real-time typing disabled - text will appear after sentences.');
        }
    }
}

function clearText() {
    fullSentences = [];
    sentenceIndex = 0;
    wordCount = 0;
    updateWordCount('');
    textDisplay.innerHTML = '📝 Text cleared. Ready for new transcription.';
}

function copyToClipboard() {
    const text = fullSentences.map(s => s.text).join(' ');
    if (text) {
        navigator.clipboard.writeText(text).then(() => {
            showNotification('Text copied to clipboard!');
        }).catch(err => {
            console.error('Failed to copy text:', err);
            showNotification('Failed to copy text', 'error');
        });
    } else {
        showNotification('No text to copy', 'warning');
    }
}

function saveText() {
    const text = fullSentences.map(s => s.text).join(' ');
    if (text) {
        localStorage.setItem('stt_transcription_' + Date.now(), text);
        showNotification('Text saved locally!');
    } else {
        showNotification('No text to save', 'warning');
    }
}

function exportText() {
    const text = fullSentences.map(s => s.text).join(' ');
    if (text) {
        const blob = new Blob([text], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `transcription_${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}.txt`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        showNotification('Text exported as file!');
    } else {
        showNotification('No text to export', 'warning');
    }
}

function showNotification(message, type = 'success') {
    const notification = document.createElement('div');
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        left: 50%;
        transform: translateX(-50%);
        background: ${type === 'error' ? '#f44336' : type === 'warning' ? '#ff9800' : '#4caf50'};
        color: white;
        padding: 12px 24px;
        border-radius: 8px;
        z-index: 10000;
        font-weight: bold;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    `;
    notification.textContent = message;
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.remove();
    }, 3000);
}

// Keyboard Shortcuts
document.addEventListener('keydown', (e) => {
    if (e.ctrlKey && e.shiftKey && e.key === 'S') {
        e.preventDefault();
        if (!isRecording) startAudioProcessing();
    }
    if (e.ctrlKey && e.shiftKey && e.key === 'X') {
        e.preventDefault();
        if (isRecording) stopAudioProcessing();
    }
    if (e.ctrlKey && e.shiftKey && e.key === 'C') {
        e.preventDefault();
        copyToClipboard();
    }
});

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    console.log('Enhanced STT interface loaded');
});
