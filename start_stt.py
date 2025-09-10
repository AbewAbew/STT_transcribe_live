"""
Enhanced STT System Launcher
Provides easy startup options for different STT modes
"""

import os
import sys
import subprocess
import webbrowser
import time
from pathlib import Path
import json

class STTLauncher:
    def __init__(self):
        self.project_dir = Path(__file__).parent
        self.config_file = self.project_dir / "launcher_config.json"
        self.load_config()
        
    def load_config(self):
        """Load launcher configuration"""
        default_config = {
            "auto_open_browser": True,
            "preferred_model": "small.en",
            "start_global_stt": False,
            "check_dependencies": True
        }
        
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    self.config = {**default_config, **json.load(f)}
            except:
                self.config = default_config
        else:
            self.config = default_config
            self.save_config()
    
    def save_config(self):
        """Save launcher configuration"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save config: {e}")
    
    def check_dependencies(self):
        """Check if required dependencies are installed"""
        print("🔍 Checking dependencies...")
        
        required_packages = [
            'RealtimeSTT', 'flask', 'flask_socketio', 'numpy', 
            'scipy', 'pyautogui', 'keyboard', 'pystray'
        ]
        
        missing_packages = []
        
        for package in required_packages:
            try:
                __import__(package.replace('-', '_'))
                print(f"  ✅ {package}")
            except ImportError:
                print(f"  ❌ {package}")
                missing_packages.append(package)
        
        if missing_packages:
            print(f"\n⚠️  Missing packages: {', '.join(missing_packages)}")
            print("Run: pip install -r requirements.txt")
            return False
        
        print("✅ All dependencies satisfied!")
        return True
    
    def check_cuda(self):
        """Check CUDA availability"""
        try:
            import torch
            if torch.cuda.is_available():
                gpu_name = torch.cuda.get_device_name(0)
                print(f"🚀 CUDA GPU detected: {gpu_name}")
                return True
            else:
                print("⚠️  CUDA not available, using CPU (slower)")
                return False
        except ImportError:
            print("⚠️  PyTorch not installed, cannot check CUDA")
            return False
    
    def start_web_server(self):
        """Start the web server"""
        print("🌐 Starting web server...")
        try:
            # Start server in a separate process
            self.server_process = subprocess.Popen(
                [sys.executable, "app.py"],
                cwd=self.project_dir
            )
            
            # Wait a moment for server to start
            time.sleep(3)
            
            if self.config["auto_open_browser"]:
                interface_path = self.project_dir / "enhanced_interface.html"
                webbrowser.open(f"file://{interface_path.absolute()}")
                print("🌐 Enhanced web interface opened in browser")
            
            return True
            
        except Exception as e:
            print(f"❌ Error starting web server: {e}")
            return False
    
    def quick_start(self):
        """Quick start with all checks"""
        print("\n🚀 Starting Advanced STT System...")
        
        if self.config["check_dependencies"] and not self.check_dependencies():
            print("❌ Missing dependencies. Install them first.")
            return
        
        self.check_cuda()
        
        if not self.start_web_server():
            return
        
        print("\n✅ System started successfully!")
        print("📝 Web Interface: Open enhanced_interface.html in your browser")
        print("⌨️  Hotkeys: Ctrl+Shift+S (start), Ctrl+Shift+X (stop)")
        print("\nPress Ctrl+C to stop the server")
        
        try:
            # Keep the launcher running
            self.server_process.wait()
        except KeyboardInterrupt:
            print("\n🛑 Shutting down...")
            self.cleanup_and_exit()
    
    def show_menu(self):
        """Show interactive menu"""
        while True:
            print("\n" + "="*50)
            print("🎤 Advanced RealtimeSTT System")
            print("="*50)
            print("1. 🚀 Quick Start (Web Interface)")
            print("2. 🌟 Start Global STT (Qt)")
            print("3. 📥 Download/Update Models")
            print("4. ❓ Help")
            print("0. 🚪 Exit")
            print("="*50)
            
            choice = input("Select option: ").strip()
            
            if choice == "1":
                self.quick_start()
            elif choice == "2":
                self.start_global_stt_qt()
            elif choice == "3":
                self.download_models()
            elif choice == "4":
                self.show_help()
            elif choice == "0":
                self.cleanup_and_exit()
            else:
                print("❌ Invalid option")
    
    def start_global_stt_qt(self):
        """Start global STT using Qt tray (recommended)"""
        print("🌟 Starting global STT (Qt tray)...")
        try:
            subprocess.Popen(
                [sys.executable, "global_stt_qt.py"],
                cwd=self.project_dir
            )
            print("✅ Global STT (Qt) started (check system tray)")
            input("Press Enter to return to menu...")
        except Exception as e:
            print(f"❌ Error starting global STT (Qt): {e}")
            print("Tip: pip install -r requirements.txt to install PySide6")
    
    def download_models(self):
        """Download required models"""
        print("📥 Downloading AI models...")
        try:
            subprocess.run([sys.executable, "download_models.py"], 
                         cwd=self.project_dir, check=True)
            print("✅ Models ready!")
        except subprocess.CalledProcessError as e:
            print(f"❌ Error downloading models: {e}")
        except FileNotFoundError:
            print("❌ download_models.py not found")
        input("Press Enter to continue...")
    
    def show_help(self):
        """Show help information"""
        print("\n❓ Help & Usage Guide")
        print("="*40)
        print("\n🌐 Web Interface:")
        print("  • Open enhanced_interface.html in your browser")
        print("  • Select AI model and language")
        print("  • Click 'Start Recording' to begin")
        print("  • Speak clearly into your microphone")
        print("  • Text appears in real-time")
        print("\n🌍 Global STT (System Tray):")
        print("  • Works in any application")
        print("  • Hotkeys: Ctrl+Shift+S (start), Ctrl+Shift+X (stop)")
        print("  • Right-click system tray icon for settings")
        print("\n🎯 Tips for Best Results:")
        print("  • Use a good quality microphone")
        print("  • Speak clearly and at normal pace")
        print("  • Minimize background noise")
        print("  • Use 'small.en' model for best speed/accuracy balance")
        input("\nPress Enter to continue...")
    
    def cleanup_and_exit(self):
        """Clean up and exit"""
        print("🧹 Cleaning up...")
        
        if hasattr(self, 'server_process'):
            try:
                self.server_process.terminate()
                self.server_process.wait(timeout=5)
            except:
                try:
                    self.server_process.kill()
                except:
                    pass
        
        print("👋 Goodbye!")
        sys.exit(0)

def main():
    """Main entry point"""
    try:
        launcher = STTLauncher()
        
        # Check for command line arguments
        if len(sys.argv) > 1:
            if sys.argv[1] == "--quick":
                launcher.quick_start()
            elif sys.argv[1] == "--global":
                launcher.start_global_stt_qt()
            elif sys.argv[1] == "--download":
                launcher.download_models()
            else:
                print("Usage: python start_stt.py [--quick|--global|--download]")
        else:
            launcher.show_menu()
            
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
