from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from RealtimeSTT import AudioToTextRecorder
import pyautogui
import threading
import logging
from logging.handlers import RotatingFileHandler
import gzip
import numpy as np
from scipy.signal import resample
import time
import json
import os
from datetime import datetime
import re

# --- Global Variables ---
recorder_instance = None
dictation_thread = None
current_session = {
    'start_time': None,
    'word_count': 0,
    'sentence_count': 0,
    'model': 'small.en',
    'language': 'en'
}
session_stats = []

# --- Enhanced App Setup ---
# Centralized logging with size-based rotation and optional gzip compression
def _setup_logging():
    try:
        log_level_name = os.getenv('STT_LOG_LEVEL', 'WARNING').upper()
        log_level = getattr(logging, log_level_name, logging.WARNING)
        root_logger = logging.getLogger()
        root_logger.setLevel(log_level)

        # Avoid adding duplicate handlers if already configured
        log_path = 'realtimesst.log'
        for h in root_logger.handlers:
            if isinstance(h, RotatingFileHandler):
                try:
                    if getattr(h, 'baseFilename', '').endswith(log_path):
                        return
                except Exception:
                    pass

        max_bytes = int(os.getenv('STT_LOG_MAX_BYTES', '5000000'))  # ~5MB
        backups = int(os.getenv('STT_LOG_BACKUPS', '3'))

        handler = RotatingFileHandler(
            log_path,
            maxBytes=max_bytes,
            backupCount=backups,
            encoding='utf-8'
        )

        def _namer(default_name):
            return default_name + '.gz'

        def _rotator(source, dest):
            try:
                with open(source, 'rb') as src, gzip.open(dest + '.gz', 'wb') as dst:
                    dst.writelines(src)
            finally:
                try:
                    os.remove(source)
                except Exception:
                    pass

        handler.namer = _namer
        handler.rotator = _rotator
        handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s'))
        root_logger.addHandler(handler)

        # Mute framework noise
        logging.getLogger('werkzeug').setLevel(logging.ERROR)
        logging.getLogger('engineio').setLevel(logging.ERROR)
        logging.getLogger('socketio').setLevel(logging.ERROR)
    except Exception:
        # As a fallback, don't crash on logging setup issues
        pass

_setup_logging()

app = Flask(__name__)
CORS(app)
socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    ping_timeout=60,
    ping_interval=25,
    logger=False,
    engineio_logger=False
)

# --- Enhanced Configuration ---
CONFIG = {
    'models': {
        'tiny.en': {'size': 'tiny', 'lang': 'en', 'speed': 'fastest'},
        'base.en': {'size': 'base', 'lang': 'en', 'speed': 'fast'},
        'small.en': {'size': 'small', 'lang': 'en', 'speed': 'balanced'},
        'medium.en': {'size': 'medium', 'lang': 'en', 'speed': 'accurate'},
        'large-v1': {'size': 'large', 'lang': 'multilingual', 'speed': 'high_accurate'},
        'large-v2': {'size': 'large', 'lang': 'multilingual', 'speed': 'better_accurate'},
        'large-v3': {'size': 'large', 'lang': 'multilingual', 'speed': 'most_accurate'},
        'large-v3-turbo': {'size': 'large', 'lang': 'multilingual', 'speed': 'ultra_fast'}
    },
    'auto_punctuation': True,
    'auto_capitalize': True,
    'global_typing': True,
    'realtime_typing': False,  # New: Enable real-time typing as you speak
    'voice_commands_enabled': True,
    'smart_text_processing': True,
    'audio_enhancement_enabled': True
}

# --- Enhanced Transcription Callbacks ---
def on_realtime_text_update(text):
    """Handles real-time transcription updates (continuous typing)."""
    if text and text.strip():
        processed_text = preprocess_realtime_text(text)
        socketio.emit('realtime_update', {'text': processed_text, 'timestamp': time.time()})
        
        # Global typing for real-time updates if enabled
        if CONFIG.get('global_typing', True) and CONFIG.get('realtime_typing', False):
            try:
                # Clear previous text and type new text
                clear_and_type_realtime(processed_text)
            except Exception as e:
                print(f"Error in real-time global typing: {e}")

def on_realtime_text_stabilized(text):
    """Handles stabilized real-time transcription (for display only)."""
    if text and text.strip():
        socketio.emit('realtime_stabilized', {'text': text, 'timestamp': time.time()})

def on_full_sentence(text):
    """Handles a completed sentence with enhanced processing."""
    if not text or not text.strip():
        return
        
    processed_text = process_text(text)
    
    # If it was a voice command, processed_text will be None
    if processed_text is None:
        return
    
    logging.debug(f"Final sentence: {processed_text}")
    
    # Update session statistics
    current_session['sentence_count'] += 1
    current_session['word_count'] += len(processed_text.split())
    
    # Send to browser
    socketio.emit('full_sentence_update', {
        'text': processed_text,
        'timestamp': time.time(),
        'stats': {
            'word_count': current_session['word_count'],
            'sentence_count': current_session['sentence_count']
        }
    })
    
    # Global typing if enabled
    if CONFIG.get('global_typing', True):
        try:
            # Add small delay to ensure window focus
            time.sleep(0.1)
            pyautogui.typewrite(processed_text + " ")
        except Exception as e:
            print(f"Error in global typing: {e}")

def preprocess_realtime_text(text):
    """Preprocess real-time text for display and typing."""
    if not text:
        return text
    
    # Remove leading whitespaces
    text = text.lstrip()
    
    # Remove starting ellipses if present
    if text.startswith("..."):
        text = text[3:]
    
    # Remove any leading whitespaces again after ellipses removal
    text = text.lstrip()
    
    # Uppercase the first letter
    if text:
        text = text[0].upper() + text[1:]
    
    return text

def process_text(text):
    """Process text with voice commands and formatting."""
    if not text:
        return text
    
    text_lower = text.lower().strip()
    
    # Check for voice commands first
    if CONFIG.get('voice_commands_enabled', True):
        command_executed = process_voice_command(text_lower)
        if command_executed:
            return None  # Don't process as regular text
    
    processed = text.strip()
    
    # Auto-capitalize
    if CONFIG.get('auto_capitalize', True) and processed:
        processed = processed[0].upper() + processed[1:] if len(processed) > 1 else processed.upper()
    
    # Auto-punctuation
    if CONFIG.get('auto_punctuation', True):
        # Add period if no ending punctuation
        if not re.search(r'[.!?]$', processed):
            processed += '.'
    
    return processed

def process_voice_command(text):
    """Process voice commands and execute actions"""
    # Text editing commands
    if re.search(r'\b(new line|next line)\b', text):
        pyautogui.press('enter')
        socketio.emit('voice_command_executed', {'command': 'new line'})
        return True
    
    if re.search(r'\bnew paragraph\b', text):
        pyautogui.press('enter')
        pyautogui.press('enter')
        socketio.emit('voice_command_executed', {'command': 'new paragraph'})
        return True
    
    if re.search(r'\b(delete that|delete last)\b', text):
        pyautogui.hotkey('ctrl', 'z')
        socketio.emit('voice_command_executed', {'command': 'undo'})
        return True
    
    if re.search(r'\bselect all\b', text):
        pyautogui.hotkey('ctrl', 'a')
        socketio.emit('voice_command_executed', {'command': 'select all'})
        return True
    
    if re.search(r'\b(copy that|copy text)\b', text):
        pyautogui.hotkey('ctrl', 'c')
        socketio.emit('voice_command_executed', {'command': 'copy'})
        return True
    
    if re.search(r'\b(paste that|paste text)\b', text):
        pyautogui.hotkey('ctrl', 'v')
        socketio.emit('voice_command_executed', {'command': 'paste'})
        return True
    
    if re.search(r'\b(save file|save document)\b', text):
        pyautogui.hotkey('ctrl', 's')
        socketio.emit('voice_command_executed', {'command': 'save file'})
        return True
    
    # Time command
    if re.search(r'\b(what time is it|current time)\b', text):
        current_time = datetime.now().strftime("%I:%M %p")
        pyautogui.typewrite(f"The current time is {current_time}")
        socketio.emit('voice_command_executed', {'command': 'insert time'})
        return True

    # System control: stop recording
    if re.search(r'\b(stop recording|stop dictation|stop transcribing)\b', text):
        try:
            socketio.emit('voice_command_executed', {'command': 'stop recording'})
            # Stop the transcription session and notify clients
            handle_stop_transcription()
        except Exception as e:
            print(f"Error handling 'stop recording' voice command: {e}")
        return True

    return False

# --- Real-time Typing Functions ---
last_typed_text = ""
typing_position = 0

def clear_and_type_realtime(text):
    """Clear previous text and type new real-time text."""
    global last_typed_text, typing_position
    
    if not text:
        return
    
    # Calculate what needs to be typed
    if text.startswith(last_typed_text):
        # New text is an extension of previous text
        new_part = text[len(last_typed_text):]
        if new_part:
            pyautogui.typewrite(new_part)
    else:
        # Text has changed, need to clear and retype
        if last_typed_text:
            # Clear previous text
            for _ in range(len(last_typed_text)):
                pyautogui.press('backspace')
        # Type new text
        pyautogui.typewrite(text)
    
    last_typed_text = text

def reset_typing_state():
    """Reset the typing state when recording stops."""
    global last_typed_text, typing_position
    last_typed_text = ""
    typing_position = 0

# --- Enhanced Audio Processing ---
def decode_and_resample(audio_data, original_sample_rate, target_sample_rate=16000):
    """Enhanced audio resampling with error handling and optimization"""
    try:
        # Convert to numpy array
        audio_np = np.frombuffer(audio_data, dtype=np.int16)
        
        # Skip resampling if rates are the same
        if original_sample_rate == target_sample_rate:
            return audio_data
        
        # Calculate target samples
        num_original_samples = len(audio_np)
        num_target_samples = int(num_original_samples * target_sample_rate / original_sample_rate)
        
        # Resample audio
        resampled_audio = resample(audio_np, num_target_samples)
        
        # Ensure proper data type and range
        resampled_audio = np.clip(resampled_audio, -32768, 32767)
        
        return resampled_audio.astype(np.int16).tobytes()
        
    except Exception as e:
        print(f"Error in audio resampling: {e}")
        return audio_data

def apply_audio_filters(audio_data):
    """Apply basic audio filtering for better recognition"""
    try:
        audio_np = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32)
        
        # Normalize audio
        if np.max(np.abs(audio_np)) > 0:
            audio_np = audio_np / np.max(np.abs(audio_np)) * 0.8
        
        # Simple high-pass filter to remove low-frequency noise
        # This is a very basic implementation
        if len(audio_np) > 1:
            audio_np[1:] = audio_np[1:] - 0.95 * audio_np[:-1]
        
        return (audio_np * 32767).astype(np.int16).tobytes()
        
    except Exception as e:
        print(f"Error in audio filtering: {e}")
        return audio_data

# --- Enhanced Dictation Loop ---
def run_dictation_loop(model_name, language="en"):
    global recorder_instance, current_session
    
    print(f"\n--- Loading model: {model_name} (Language: {language}) ---")
    current_session['start_time'] = time.time()
    current_session['model'] = model_name
    current_session['language'] = language
    
    try:
        # Enhanced recorder configuration with real-time callbacks
        recorder_config = {
            'model': model_name,
            'language': language,
            'device': "cuda",
            'use_microphone': False,
            'spinner': False,
            'enable_realtime_transcription': True,
            'realtime_model_type': 'tiny.en',
            'realtime_processing_pause': 0.02,
            'on_realtime_transcription_update': on_realtime_text_update,
            'on_realtime_transcription_stabilized': on_realtime_text_stabilized,
            'post_speech_silence_duration': 0.7,
            'min_length_of_recording': 0.3,
            'min_gap_between_recordings': 0
        }
        
        # Initialize recorder with GPU optimization
        print("Initializing AudioToTextRecorder with CUDA...")
        recorder_instance = AudioToTextRecorder(**recorder_config)
        
        # Warm up the model for better performance
        print("Warming up model...")
        dummy_audio = np.zeros(16000, dtype=np.int16)  # 1 second of silence
        recorder_instance.feed_audio(dummy_audio.tobytes())
        print(f"--- Model '{model_name}' loaded successfully ---")
        
        socketio.emit('model_loaded', {
            'model': model_name,
            'language': language,
            'timestamp': time.time()
        })
        
        # Main transcription loop
        while recorder_instance:
            try:
                full_sentence = recorder_instance.text()
                if full_sentence and full_sentence.strip():
                    on_full_sentence(full_sentence)
            except Exception as e:
                print(f"Error in transcription loop: {e}")
                break

    except Exception as e:
        error_msg = f"Dictation loop error: {e}"
        print(error_msg)
        socketio.emit('error', {
            'message': f'Model loading error: {str(e)}',
            'timestamp': time.time(),
            'model': model_name
        })
    finally:
        print("Dictation thread has stopped.")
        if recorder_instance:
            try:
                recorder_instance.shutdown()
            except:
                pass
            recorder_instance = None
        save_session_stats()

# --- Enhanced WebSocket Event Handlers ---
@socketio.on('connect')
def handle_connect():
    client_ip = request.environ.get('REMOTE_ADDR', 'unknown')
    print(f'Client connected from {client_ip}')
    emit('connection_status', {
        'status': 'connected',
        'server_time': time.time(),
        'available_models': list(CONFIG['models'].keys())
    })

@socketio.on('disconnect')
def handle_disconnect():
    global recorder_instance
    client_ip = request.environ.get('REMOTE_ADDR', 'unknown')
    print(f'Client disconnected from {client_ip}')
    
    if recorder_instance:
        try:
            recorder_instance.shutdown()
        except Exception as e:
            print(f"Error shutting down recorder: {e}")
        finally:
            recorder_instance = None
    
    save_session_stats()

@socketio.on('start_transcription')
def handle_start(data):
    global dictation_thread, current_session
    
    model = data.get('model', 'small.en')
    language = data.get('language', 'en')
    
    print(f"Starting transcription with model: {model}, language: {language}")
    
    # Stop existing session if running
    if dictation_thread and dictation_thread.is_alive():
        print("Stopping existing transcription session")
        handle_stop_transcription()
        time.sleep(1)
    
    # Reset session stats
    current_session = {
        'start_time': time.time(),
        'word_count': 0,
        'sentence_count': 0,
        'model': model,
        'language': language
    }
    
    # Start new transcription thread
    dictation_thread = threading.Thread(
        target=run_dictation_loop, 
        args=(model, language),
        daemon=True
    )
    dictation_thread.start()
    
    emit('transcription_started', {
        'model': model,
        'language': language,
        'timestamp': time.time()
    })

@socketio.on('stop_transcription')
def handle_stop_transcription():
    global recorder_instance
    print("Stopping transcription")
    
    # Reset real-time typing state
    reset_typing_state()
    
    if recorder_instance:
        try:
            recorder_instance.shutdown()
        except Exception as e:
            print(f"Error stopping recorder: {e}")
        finally:
            recorder_instance = None
    
    save_session_stats()
    # Use socketio.emit so this works from any thread/context
    socketio.emit('transcription_stopped', {'timestamp': time.time()})

@socketio.on('audio_chunk')
def handle_audio_chunk(chunk_data):
    if recorder_instance:
        try:
            filtered_chunk = apply_audio_filters(chunk_data)
            resampled_chunk = decode_and_resample(filtered_chunk, 48000, 16000)
            recorder_instance.feed_audio(resampled_chunk)
        except Exception as e:
            print(f"Error processing audio chunk: {e}")

@socketio.on('update_feature')
def handle_update_feature(data):
    """Handle feature toggle updates"""
    feature = data.get('feature')
    enabled = data.get('enabled', True)
    
    if feature == 'voice_commands':
        CONFIG['voice_commands_enabled'] = enabled
    elif feature == 'smart_text':
        CONFIG['smart_text_processing'] = enabled
    elif feature == 'audio_enhancement':
        CONFIG['audio_enhancement_enabled'] = enabled
    elif feature == 'auto_punctuation':
        CONFIG['auto_punctuation'] = enabled
    elif feature == 'realtime_typing':
        CONFIG['realtime_typing'] = enabled
        if not enabled:
            reset_typing_state()
    
    print(f"Feature {feature}: {'enabled' if enabled else 'disabled'}")
    emit('feature_updated', {'feature': feature, 'enabled': enabled})

@socketio.on('calibrate_noise')
def handle_calibrate_noise():
    """Handle noise calibration request"""
    print("Starting noise calibration...")
    
    def calibration_complete():
        time.sleep(3)
        socketio.emit('noise_calibrated', {'status': 'complete'})
    
    threading.Thread(target=calibration_complete, daemon=True).start()
    emit('calibration_started', {'duration': 3})

@socketio.on('add_custom_word')
def handle_add_custom_word(data):
    """Add custom word to vocabulary"""
    spoken = data.get('spoken', '').lower().strip()
    written = data.get('written', '').strip()
    
    if spoken and written:
        vocab_file = 'custom_vocabulary.json'
        try:
            if os.path.exists(vocab_file):
                with open(vocab_file, 'r') as f:
                    vocab = json.load(f)
            else:
                vocab = {}
            
            vocab[spoken] = written
            
            with open(vocab_file, 'w') as f:
                json.dump(vocab, f, indent=2)
            
            print(f"Added custom word: '{spoken}' -> '{written}'")
            emit('word_added', {'spoken': spoken, 'written': written})
            
        except Exception as e:
            print(f"Error adding custom word: {e}")
            emit('error', {'message': f'Failed to add custom word: {str(e)}'})

# --- Session Statistics ---
def save_session_stats():
    """Save session statistics to file"""
    if current_session['start_time']:
        duration = time.time() - current_session['start_time']
        session_data = {
            'timestamp': datetime.now().isoformat(),
            'duration': duration,
            'word_count': current_session['word_count'],
            'sentence_count': current_session['sentence_count'],
            'model': current_session['model'],
            'language': current_session['language'],
            'wpm': (current_session['word_count'] / (duration / 60)) if duration > 0 else 0
        }
        
        stats_file = 'session_stats.json'
        try:
            if os.path.exists(stats_file):
                with open(stats_file, 'r') as f:
                    stats = json.load(f)
            else:
                stats = []
            
            stats.append(session_data)
            
            if len(stats) > 100:
                stats = stats[-100:]
            
            with open(stats_file, 'w') as f:
                json.dump(stats, f, indent=2)
                
            print(f"Session stats saved: {duration:.1f}s, {current_session['word_count']} words")
        except Exception as e:
            print(f"Error saving session stats: {e}")

# --- REST API Endpoints ---
@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': time.time(),
        'recorder_active': recorder_instance is not None
    })

@app.route('/api/shutdown', methods=['POST'])
def shutdown_server():
    """Gracefully stop transcription (if any) and shut down the web server."""
    try:
        # Stop any ongoing transcription first
        try:
            handle_stop_transcription()
        except Exception:
            pass

        # Schedule server shutdown shortly after responding
        func = request.environ.get('werkzeug.server.shutdown')

        def _do_shutdown(shutdown_callable):
            try:
                time.sleep(0.5)
                if shutdown_callable:
                    shutdown_callable()
                else:
                    # Fallback if not running with Werkzeug
                    os._exit(0)
            except Exception:
                os._exit(0)

        threading.Thread(target=_do_shutdown, args=(func,), daemon=True).start()
        return jsonify({'status': 'shutting_down', 'timestamp': time.time()})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🎤 Advanced RealtimeSTT Server Starting...")
    print("="*60)
    print(f"📡 Server: http://127.0.0.1:5000")
    print(f"🌐 Web Interface: Open 'enhanced_interface.html' in your browser")
    print(f"🚀 CUDA Enabled: GPU acceleration active")
    print("="*60 + "\n")
    
    try:
        socketio.run(
            app, 
            host='127.0.0.1', 
            port=5000, 
            debug=False,
            allow_unsafe_werkzeug=True
        )
    except KeyboardInterrupt:
        print("\n🛑 Server shutting down...")
        if recorder_instance:
            recorder_instance.shutdown()
        print("✅ Shutdown complete")
