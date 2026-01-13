#!/usr/bin/env python3
"""
Lens System Tray Application for Windows
Provides a system tray icon to manage the Lens backend server.
"""

import os
import sys
import subprocess
import time
from pathlib import Path

try:
    import pystray
    from PIL import Image
except ImportError as e:
    print(f"Error: Missing required package: {e}")
    print("Please install dependencies: pip install pystray Pillow")
    sys.exit(1)


class LensTrayApp:
    def __init__(self):
        # Get script directory (installation root for packaged builds)
        self.script_dir = Path(__file__).parent.absolute()
        self.install_root = self.script_dir
        
        # Paths
        self.backend_dir = self.install_root / "backend"
        self.venv_python = self.install_root / "venv" / "Scripts" / "python.exe"
        self.log_file = self.install_root / "logs" / "backend.log"
        self.pid_file = self.install_root / ".pids"
        self.icon_path = self.script_dir / "lens_icon_32.png"
        
        # Configuration
        self.port = 34001
        self.host = "0.0.0.0"
        self.backend_process = None
        self.is_running = False
        
        # Load configuration
        self._load_config()
        
        # Ensure logs directory exists
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Load icon
        self.icon_image = self._load_icon()
        
        # Check if backend is already running
        self.is_running = self._check_backend_running()
        if self.is_running:
            # Try to find the process from PID file
            self._load_pid_from_file()
        
        # Create menu
        self.menu = pystray.Menu(
            pystray.MenuItem("Start", self.start_backend, enabled=lambda item: not self.is_running),
            pystray.MenuItem("Stop", self.stop_backend, enabled=lambda item: self.is_running),
            pystray.MenuItem("Restart", self.restart_backend),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("View Logs", self.view_logs),
            pystray.MenuItem("Open in Browser", self.open_browser),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Exit", self.exit_app),
        )
        
        # Create tray icon
        self.icon = pystray.Icon(
            "Lens",
            self.icon_image,
            "Lens Backend Server",
            self.menu
        )
    
    def _load_config(self):
        """Load port and host from backend/.env if it exists."""
        env_file = self.backend_dir / ".env"
        if env_file.exists():
            try:
                with open(env_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            if '=' in line:
                                key, value = line.split('=', 1)
                                key = key.strip()
                                value = value.strip().strip('"').strip("'")
                                if key == "PORT":
                                    try:
                                        self.port = int(value)
                                    except ValueError:
                                        pass
                                elif key == "HOST":
                                    self.host = value
            except Exception as e:
                self._log_error(f"Error reading .env file: {e}")
    
    def _load_icon(self):
        """Load the tray icon image."""
        if self.icon_path.exists():
            try:
                return Image.open(self.icon_path)
            except Exception as e:
                self._log_error(f"Error loading icon: {e}")
        
        # Fallback: create a simple icon programmatically
        img = Image.new('RGB', (32, 32), color='#4F46E5')
        return img
    
    def _log_error(self, message):
        """Log error message to log file."""
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(f"[TRAY] {time.strftime('%Y-%m-%d %H:%M:%S')} ERROR: {message}\n")
        except Exception:
            pass  # Don't fail if logging fails
    
    def _log_info(self, message):
        """Log info message to log file."""
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(f"[TRAY] {time.strftime('%Y-%m-%d %H:%M:%S')} INFO: {message}\n")
        except Exception:
            pass
    
    def _load_pid_from_file(self):
        """Try to load backend PID from PID file."""
        if self.pid_file.exists():
            try:
                with open(self.pid_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        parts = line.strip().split()
                        if len(parts) >= 2 and parts[0] == "backend":
                            try:
                                pid = int(parts[1])
                                # Check if process is still running (Windows)
                                if sys.platform == "win32":
                                    result = subprocess.run(
                                        ["tasklist", "/FI", f"PID eq {pid}", "/FO", "CSV"],
                                        capture_output=True,
                                        timeout=2
                                    )
                                    if pid in result.stdout.decode('utf-8', errors='ignore'):
                                        # Process exists, but we can't get a handle to it
                                        # Just note that it's running
                                        pass
                            except (ValueError, subprocess.TimeoutExpired):
                                pass
            except Exception:
                pass
    
    def _check_backend_running(self):
        """Check if backend is currently running."""
        # Check if process is still alive
        if self.backend_process and self.backend_process.poll() is None:
            return True
        
        # Check if port is listening
        try:
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.5)
            host = "127.0.0.1" if self.host == "0.0.0.0" else self.host
            result = sock.connect_ex((host, self.port))
            sock.close()
            if result == 0:
                return True
        except Exception:
            pass
        
        return False
    
    def start_backend(self, icon=None, item=None):
        """Start the backend server."""
        if self.is_running:
            return
        
        self._log_info("Starting backend server...")
        
        # Check if backend directory exists
        if not self.backend_dir.exists():
            self._log_error(f"Backend directory not found: {self.backend_dir}")
            self.icon.notify("Error", f"Backend directory not found: {self.backend_dir}")
            return
        
        # Check if Python executable exists
        if not self.venv_python.exists():
            self._log_error(f"Python executable not found: {self.venv_python}")
            self.icon.notify("Error", f"Python executable not found. Please run setup first.")
            return
        
        # Change to backend directory
        os.chdir(str(self.backend_dir))
        
        # Prepare environment
        env = os.environ.copy()
        env["SERVE_FRONTEND"] = "true"
        
        # Prepare command
        cmd = [
            str(self.venv_python),
            "-u",  # Unbuffered output
            "-m", "uvicorn",
            "app.main:app",
            "--host", self.host,
            "--port", str(self.port)
        ]
        
        try:
            # Start backend process
            with open(self.log_file, 'a', encoding='utf-8') as log:
                log.write(f"\n{'='*60}\n")
                log.write(f"Backend Started: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                log.write(f"{'='*60}\n")
                self.backend_process = subprocess.Popen(
                    cmd,
                    env=env,
                    stdout=log,
                    stderr=subprocess.STDOUT,
                    cwd=str(self.backend_dir),
                    creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
                )
            
            # Save PID
            try:
                with open(self.pid_file, 'w', encoding='utf-8') as f:
                    f.write(f"backend {self.backend_process.pid}\n")
            except Exception as e:
                self._log_error(f"Error writing PID file: {e}")
            
            self.is_running = True
            self._log_info(f"Backend started (PID: {self.backend_process.pid})")
            
            # Update icon menu
            self.icon.update_menu()
            
            # Wait for server to be ready, then show notification and open browser
            def wait_and_open():
                time.sleep(4)  # Give server time to start
                if self._check_backend_running():
                    url = f"http://127.0.0.1:{self.port}"
                    self.icon.notify("Lens Started", f"Server running on {url}")
                    self.open_browser()
            
            # Run in background thread to avoid blocking
            import threading
            threading.Thread(target=wait_and_open, daemon=True).start()
            
        except Exception as e:
            self._log_error(f"Error starting backend: {e}")
            self.icon.notify("Error", f"Failed to start backend: {str(e)}")
    
    def stop_backend(self, icon=None, item=None):
        """Stop the backend server."""
        if not self.is_running:
            return
        
        self._log_info("Stopping backend server...")
        
        try:
            # Kill the process
            if self.backend_process and self.backend_process.poll() is None:
                self.backend_process.terminate()
                # Wait up to 5 seconds for graceful shutdown
                try:
                    self.backend_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.backend_process.kill()
                    self.backend_process.wait()
            
            # Also try to kill by PID file
            if self.pid_file.exists():
                try:
                    with open(self.pid_file, 'r', encoding='utf-8') as f:
                        for line in f:
                            parts = line.strip().split()
                            if len(parts) >= 2 and parts[0] == "backend":
                                try:
                                    pid = int(parts[1])
                                    if sys.platform == "win32":
                                        subprocess.run(["taskkill", "/PID", str(pid), "/F"], 
                                                     capture_output=True, timeout=5)
                                    else:
                                        os.kill(pid, 15)
                                except (ValueError, ProcessLookupError, subprocess.TimeoutExpired):
                                    pass
                except Exception:
                    pass
                
                # Remove PID file
                try:
                    self.pid_file.unlink()
                except Exception:
                    pass
            
            self.backend_process = None
            self.is_running = False
            self._log_info("Backend stopped")
            
            # Update icon menu
            self.icon.update_menu()
            
            # Show notification
            self.icon.notify("Lens Stopped", "Backend server has been stopped")
            
        except Exception as e:
            self._log_error(f"Error stopping backend: {e}")
            self.icon.notify("Error", f"Failed to stop backend: {str(e)}")
    
    def restart_backend(self, icon=None, item=None):
        """Restart the backend server."""
        self._log_info("Restarting backend server...")
        self.stop_backend()
        time.sleep(1)
        self.start_backend()
    
    def view_logs(self, icon=None, item=None):
        """Open log file in default text editor."""
        try:
            if sys.platform == "win32":
                os.startfile(str(self.log_file))
            else:
                subprocess.run(["xdg-open", str(self.log_file)])
        except Exception as e:
            self._log_error(f"Error opening logs: {e}")
            self.icon.notify("Error", f"Failed to open logs: {str(e)}")
    
    def open_browser(self, icon=None, item=None):
        """Open application in default browser."""
        try:
            url = f"http://127.0.0.1:{self.port}"
            if sys.platform == "win32":
                os.startfile(url)
            else:
                subprocess.run(["xdg-open", url])
        except Exception as e:
            self._log_error(f"Error opening browser: {e}")
            self.icon.notify("Error", f"Failed to open browser: {str(e)}")
    
    def exit_app(self, icon=None, item=None):
        """Exit the tray application."""
        self._log_info("Exiting tray application...")
        if self.is_running:
            self.stop_backend()
            time.sleep(1)
        self.icon.stop()
    
    
    def run(self):
        """Run the tray application."""
        self._log_info("Starting Lens tray application...")
        self.icon.run()


def main():
    """Main entry point."""
    try:
        app = LensTrayApp()
        app.run()
    except KeyboardInterrupt:
        pass
    except Exception as e:
        # Try to log error before exiting
        try:
            with open("tray_error.log", 'w') as f:
                f.write(f"Tray application error: {e}\n")
                import traceback
                f.write(traceback.format_exc())
        except Exception:
            pass
        sys.exit(1)


if __name__ == "__main__":
    main()
