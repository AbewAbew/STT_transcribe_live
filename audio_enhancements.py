"""
Audio Enhancement Features
Advanced audio processing and microphone management
"""

import numpy as np
import sounddevice as sd
import threading
import time
from scipy import signal
import json
import os

class AudioEnhancer:
    def __init__(self):
        self.noise_profile = None
        self.is_calibrating = False
        self.settings_file = "audio_settings.json"
        self.load_settings()
        
    def load_settings(self):
        """Load audio settings"""
        default_settings = {
            "noise_reduction": True,
            "auto_gain": True,
            "voice_activation_threshold": 0.02,
            "preferred_device": None,
            "sample_rate": 16000
        }
        
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, 'r') as f:
                    self.settings = {**default_settings, **json.load(f)}
            except:
                self.settings = default_settings
        else:
            self.settings = default_settings
    
    def save_settings(self):
        """Save audio settings"""
        try:
            with open(self.settings_file, 'w') as f:
                json.dump(self.settings, f, indent=2)
        except Exception as e:
            print(f"Error saving audio settings: {e}")
    
    def get_audio_devices(self):
        """Get list of available audio input devices"""
        devices = sd.query_devices()
        input_devices = []
        
        for i, device in enumerate(devices):
            if device['max_input_channels'] > 0:
                input_devices.append({
                    'id': i,
                    'name': device['name'],
                    'channels': device['max_input_channels'],
                    'sample_rate': device['default_samplerate']
                })
        
        return input_devices
    
    def calibrate_noise_floor(self, duration=3):
        """Calibrate background noise for noise reduction"""
        print(f"Calibrating noise floor for {duration} seconds...")
        print("Please remain quiet during calibration...")
        
        self.is_calibrating = True
        
        def calibration_callback(indata, frames, time, status):
            if self.is_calibrating:
                if self.noise_profile is None:
                    self.noise_profile = np.abs(np.fft.fft(indata[:, 0]))
                else:
                    current_fft = np.abs(np.fft.fft(indata[:, 0]))
                    self.noise_profile = 0.9 * self.noise_profile + 0.1 * current_fft
        
        with sd.InputStream(callback=calibration_callback, 
                           channels=1, 
                           samplerate=self.settings['sample_rate']):
            time.sleep(duration)
        
        self.is_calibrating = False
        print("Noise calibration complete!")
        
        # Save noise profile
        if self.noise_profile is not None:
            np.save('noise_profile.npy', self.noise_profile)
    
    def load_noise_profile(self):
        """Load saved noise profile"""
        try:
            self.noise_profile = np.load('noise_profile.npy')
            return True
        except:
            return False
    
    def apply_noise_reduction(self, audio_data):
        """Apply spectral subtraction noise reduction"""
        if not self.settings['noise_reduction'] or self.noise_profile is None:
            return audio_data
        
        try:
            # Convert to frequency domain
            audio_fft = np.fft.fft(audio_data)
            audio_magnitude = np.abs(audio_fft)
            audio_phase = np.angle(audio_fft)
            
            # Spectral subtraction
            alpha = 2.0  # Over-subtraction factor
            noise_magnitude = self.noise_profile[:len(audio_magnitude)]
            
            # Ensure noise profile matches audio length
            if len(noise_magnitude) != len(audio_magnitude):
                noise_magnitude = np.resize(noise_magnitude, len(audio_magnitude))
            
            clean_magnitude = audio_magnitude - alpha * noise_magnitude
            clean_magnitude = np.maximum(clean_magnitude, 0.1 * audio_magnitude)
            
            # Reconstruct signal
            clean_fft = clean_magnitude * np.exp(1j * audio_phase)
            clean_audio = np.real(np.fft.ifft(clean_fft))
            
            return clean_audio.astype(audio_data.dtype)
            
        except Exception as e:
            print(f"Noise reduction error: {e}")
            return audio_data
    
    def apply_auto_gain(self, audio_data):
        """Apply automatic gain control"""
        if not self.settings['auto_gain']:
            return audio_data
        
        try:
            # Calculate RMS
            rms = np.sqrt(np.mean(audio_data**2))
            
            if rms > 0:
                # Target RMS level
                target_rms = 0.1
                gain = target_rms / rms
                
                # Limit gain to prevent distortion
                gain = np.clip(gain, 0.1, 10.0)
                
                return (audio_data * gain).astype(audio_data.dtype)
            
            return audio_data
            
        except Exception as e:
            print(f"Auto gain error: {e}")
            return audio_data
    
    def detect_voice_activity(self, audio_data):
        """Simple voice activity detection"""
        try:
            # Calculate energy
            energy = np.sum(audio_data**2) / len(audio_data)
            
            # Check against threshold
            return energy > self.settings['voice_activation_threshold']
            
        except:
            return True  # Default to active if detection fails
    
    def apply_high_pass_filter(self, audio_data, cutoff=80):
        """Apply high-pass filter to remove low-frequency noise"""
        try:
            nyquist = self.settings['sample_rate'] / 2
            normalized_cutoff = cutoff / nyquist
            
            b, a = signal.butter(4, normalized_cutoff, btype='high')
            filtered_audio = signal.filtfilt(b, a, audio_data)
            
            return filtered_audio.astype(audio_data.dtype)
            
        except Exception as e:
            print(f"High-pass filter error: {e}")
            return audio_data
    
    def process_audio_chunk(self, audio_data):
        """Apply all audio enhancements to a chunk of audio"""
        # Apply high-pass filter first
        processed = self.apply_high_pass_filter(audio_data)
        
        # Apply noise reduction
        processed = self.apply_noise_reduction(processed)
        
        # Apply auto gain
        processed = self.apply_auto_gain(processed)
        
        return processed
    
    def get_optimal_device_settings(self, device_id):
        """Get optimal settings for a specific audio device"""
        try:
            device_info = sd.query_devices(device_id)
            
            # Recommend settings based on device capabilities
            recommended = {
                'sample_rate': min(48000, int(device_info['default_samplerate'])),
                'channels': 1,
                'dtype': 'int16',
                'latency': 'low'
            }
            
            return recommended
            
        except Exception as e:
            print(f"Error getting device settings: {e}")
            return None