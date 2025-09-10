"""
Setup script for Advanced RealtimeSTT System
Handles installation and initial configuration
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8+ is required")
        print(f"Current version: {version.major}.{version.minor}.{version.micro}")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} detected")
    return True

def check_system():
    """Check system compatibility"""
    system = platform.system()
    if system != "Windows":
        print(f"⚠️  This system is optimized for Windows. Current: {system}")
        print("Some features may not work as expected.")
    else:
        print("✅ Windows system detected")
    return True

def install_dependencies():
    """Install required Python packages"""
    print("📦 Installing dependencies...")
    
    try:
        # Upgrade pip first
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
        
        # Try minimal requirements first
        print("Installing essential packages...")
        essential_packages = [
            "RealtimeSTT>=0.3.104",
            "flask>=2.3.0",
            "flask-cors>=4.0.0", 
            "flask-socketio>=5.3.0",
            "numpy>=1.24.0",
            "scipy>=1.10.0",
            "pyautogui>=0.9.54",
            "keyboard>=0.13.5",
            "pystray>=0.19.4",
            "Pillow>=10.0.0",
            "pyperclip>=1.8.2"
        ]
        
        for package in essential_packages:
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", package])
                print(f"  ✅ {package.split('>=')[0]}")
            except subprocess.CalledProcessError:
                print(f"  ⚠️  Failed to install {package.split('>=')[0]}")
        
        # Try to install PyTorch separately
        print("Installing PyTorch for GPU support...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "torch", "torchaudio", "--index-url", "https://download.pytorch.org/whl/cu118"])
            print("  ✅ PyTorch with CUDA support")
        except subprocess.CalledProcessError:
            print("  ⚠️  Installing CPU-only PyTorch...")
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", "torch", "torchaudio"])
                print("  ✅ PyTorch (CPU only)")
            except subprocess.CalledProcessError:
                print("  ❌ Failed to install PyTorch")
        
        print("✅ Essential dependencies installed")
        return True
        
    except Exception as e:
        print(f"❌ Error installing dependencies: {e}")
        print("\nTry manual installation:")
        print("pip install RealtimeSTT flask flask-cors flask-socketio numpy scipy pyautogui")
        return False

def check_cuda():
    """Check CUDA availability"""
    try:
        import torch
        if torch.cuda.is_available():
            gpu_name = torch.cuda.get_device_name(0)
            print(f"🚀 CUDA GPU detected: {gpu_name}")
            return True
        else:
            print("⚠️  CUDA not available - will use CPU (slower)")
            return False
    except ImportError:
        print("⚠️  PyTorch not installed - cannot check CUDA")
        return False

def download_initial_models():
    """Download essential models"""
    print("📥 Downloading essential AI models...")
    
    try:
        # Download just the recommended model initially
        from RealtimeSTT import AudioToTextRecorder
        
        print("Downloading 'tiny.en' model (fastest for testing)...")
        recorder = AudioToTextRecorder(model="tiny.en", device="cpu")  # Use CPU for initial setup
        recorder.shutdown()
        
        print("✅ Essential model downloaded")
        print("💡 You can download more models later using the launcher menu")
        return True
        
    except Exception as e:
        print(f"⚠️  Could not download models automatically: {e}")
        print("💡 Models will be downloaded automatically when first used")
        return True  # Don't fail setup for this

def create_shortcuts():
    """Create desktop shortcuts (Windows only)"""
    if platform.system() != "Windows":
        return
    
    print("💡 Desktop shortcut creation skipped (optional feature)")
    print("   You can manually create shortcuts to start_stt.bat if needed")

def setup_complete():
    """Show completion message"""
    print("\n" + "="*60)
    print("🎉 Setup Complete!")
    print("="*60)
    print("🚀 Quick Start:")
    print("  • Run: python start_stt.py")
    print("  • Or double-click: start_stt.bat")
    print("  • Or use desktop shortcut (if created)")
    print("\n🌐 Web Interface:")
    print("  • Will open automatically in your browser")
    print("  • Select model and click 'Start Recording'")
    print("\n🌍 Global STT:")
    print("  • Available from launcher menu")
    print("  • Hotkeys: Ctrl+Shift+S (start), Ctrl+Shift+X (stop)")
    print("\n📚 Documentation:")
    print("  • See README.md for detailed usage guide")
    print("  • Use launcher menu for help and settings")
    print("="*60)

def main():
    """Main setup process"""
    print("🎤 Advanced RealtimeSTT System Setup")
    print("="*50)
    
    # System checks
    if not check_python_version():
        return False
    
    check_system()
    
    # Install dependencies
    deps_success = install_dependencies()
    
    # Check CUDA
    cuda_available = check_cuda()
    
    # Download models (optional)
    download_initial_models()
    
    # Create shortcuts (optional)
    create_shortcuts()
    
    # Show completion
    if deps_success:
        setup_complete()
        return True
    else:
        print("\n⚠️  Setup completed with some issues")
        print("💡 You can still try running the system manually")
        return False

if __name__ == "__main__":
    try:
        success = main()
        if success:
            input("\nPress Enter to exit...")
        else:
            input("\nSetup encountered issues. Press Enter to exit...")
    except KeyboardInterrupt:
        print("\n\n❌ Setup cancelled by user")
    except Exception as e:
        print(f"\n❌ Unexpected error during setup: {e}")
        input("Press Enter to exit...")