import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import webbrowser
import threading
import os
import sys
from pathlib import Path

class SimpleTeachingContentLauncher:
    def __init__(self):
        # Configuration - make project path dynamic
        self.project_path = str(Path(__file__).parent.absolute())
        self.server_url = "http://127.0.0.1:5000"
        
        # Detect virtual environment and Python executable
        self.python_executable = self.detect_python_executable()
        
        # Server state
        self.server_process = None
        self.server_running = False
        
        # Create main window
        self.root = tk.Tk()
        self.root.title("Teaching Content Database - Simple Launcher")
        self.root.geometry("450x300")
        self.root.resizable(False, False)
        
        # Configure style
        try:
            style = ttk.Style()
            style.theme_use('clam')
        except:
            pass
        
        self.setup_ui()
        
        # Check actual server status on startup
        self.detect_server_status()
        
    def detect_python_executable(self):
        """Detect the correct Python executable to use"""
        # Check for virtual environment
        venv_paths = [
            Path(self.project_path) / 'venv' / 'Scripts' / 'python.exe',  # Windows
            Path(self.project_path) / 'venv' / 'bin' / 'python',  # Unix/Linux/Mac
            Path(self.project_path) / '.venv' / 'Scripts' / 'python.exe',  # Windows alt
            Path(self.project_path) / '.venv' / 'bin' / 'python',  # Unix/Linux/Mac alt
        ]
        
        for venv_python in venv_paths:
            if venv_python.exists():
                print(f"Found virtual environment Python: {venv_python}")
                return str(venv_python)
        
        # Fallback to system Python
        print("No virtual environment found, using system Python")
        return sys.executable
        
    def setup_ui(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky="nsew")
        
        # Title
        title_label = ttk.Label(main_frame, text="Teaching Content Database", 
                               font=('Arial', 14, 'bold'))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 15))
        
        # Project info
        info_frame = ttk.Frame(main_frame)
        info_frame.grid(row=1, column=0, columnspan=2, pady=(0, 15), sticky="ew")
        
        ttk.Label(info_frame, text=f"Project: {Path(self.project_path).name}", 
                 font=('Arial', 9), foreground='gray').pack(anchor=tk.W)
        ttk.Label(info_frame, text=f"Python: {Path(self.python_executable).name}", 
                 font=('Arial', 9), foreground='gray').pack(anchor=tk.W)
        
        # Status indicator
        self.status_frame = ttk.Frame(main_frame)
        self.status_frame.grid(row=2, column=0, columnspan=2, pady=(0, 15))
        
        self.status_indicator = tk.Canvas(self.status_frame, width=20, height=20)
        self.status_indicator.pack(side=tk.LEFT, padx=(0, 10))
        
        self.status_label = ttk.Label(self.status_frame, text="Server Stopped", 
                                     font=('Arial', 10))
        self.status_label.pack(side=tk.LEFT)
        
        # Control buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=3, column=0, columnspan=2, pady=(0, 15))
        
        self.start_button = ttk.Button(button_frame, text="Start Server", 
                                      command=self.start_server)
        self.start_button.pack(side=tk.LEFT, padx=(0, 5))
        
        self.stop_button = ttk.Button(button_frame, text="Stop Server", 
                                     command=self.stop_server, state='disabled')
        self.stop_button.pack(side=tk.LEFT, padx=(0, 5))
        
        self.check_button = ttk.Button(button_frame, text="Check Setup", 
                                      command=self.check_setup)
        self.check_button.pack(side=tk.LEFT)
        
        # URL section
        url_frame = ttk.Frame(main_frame)
        url_frame.grid(row=4, column=0, columnspan=2, pady=(0, 15), sticky="ew")
        
        ttk.Label(url_frame, text="Server URL:", font=('Arial', 9)).pack(anchor=tk.W)
        
        url_entry_frame = ttk.Frame(url_frame)
        url_entry_frame.pack(fill=tk.X, pady=(5, 10))
        
        self.url_entry = ttk.Entry(url_entry_frame, state='readonly', font=('Arial', 9))
        self.url_entry.insert(0, self.server_url)
        self.url_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        ttk.Button(url_entry_frame, text="Copy", width=6, 
                  command=self.copy_url).pack(side=tk.RIGHT)
        
        ttk.Button(url_frame, text="Open in Browser", 
                  command=self.open_browser).pack(fill=tk.X)
        
        # Status message
        self.message_label = ttk.Label(main_frame, text="Ready to start server", 
                                      font=('Arial', 8), foreground='gray')
        self.message_label.grid(row=5, column=0, columnspan=2, pady=(10, 0))
        
        # Update status indicator
        self.update_status_indicator()
        
        # Configure grid weights
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        
    def detect_server_status(self):
        """Detect if server is already running on startup"""
        print("Detecting existing server status...")
        threading.Thread(target=self._detect_server_status_thread, daemon=True).start()
        
    def _detect_server_status_thread(self):
        """Check server status in background thread"""
        try:
            # Method 1: Try HTTP health check
            import requests
            try:
                response = requests.get(f"{self.server_url}/api/health", timeout=3)
                if response.status_code == 200:
                    print("Found running server via HTTP check")
                    self.root.after(0, self._server_detected_callback)
                    return
            except requests.RequestException:
                print("No server responding to HTTP requests")
            
            # Method 2: Check for Flask processes (if psutil available)
            try:
                import psutil
                flask_processes = []
                for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                    try:
                        if proc.info['cmdline']:
                            cmdline = ' '.join(proc.info['cmdline'])
                            if 'start_server.py' in cmdline and 'python' in cmdline.lower():
                                flask_processes.append(proc)
                                print(f"Found Flask process: PID {proc.info['pid']}")
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        # Process might have ended or access denied
                        continue
                
                if flask_processes:
                    # Found existing Flask processes but no HTTP response
                    # Server might be starting up or in error state
                    print("Found Flask processes but no HTTP response")
                    self.root.after(0, lambda: self._server_uncertain_callback(flask_processes))
                    return
                    
            except ImportError:
                print("psutil not available for process detection")
            except Exception as e:
                print(f"Error checking processes: {e}")
            
            # Method 3: Check if port 5000 is in use
            import socket
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(2)
                result = sock.connect_ex(('127.0.0.1', 5000))
                sock.close()
                
                if result == 0:
                    print("Port 5000 is in use but not responding to HTTP")
                    self.root.after(0, self._server_uncertain_callback)
                    return
                else:
                    print("Port 5000 is available")
                    
            except Exception as e:
                print(f"Error checking port: {e}")
            
            # No server detected
            print("No existing server detected")
            self.root.after(0, self._no_server_detected_callback)
            
        except Exception as e:
            print(f"Error in server detection: {e}")
            self.root.after(0, self._no_server_detected_callback)
            
    def _server_detected_callback(self):
        """Called when an existing server is detected"""
        self.server_running = True
        self.start_button.config(text="Start Server", state='disabled')
        self.stop_button.config(state='normal')
        self.status_label.config(text="Server Running (Detected)")
        self.message_label.config(text=f"Found existing server at {self.server_url}")
        self.update_status_indicator()
        print("Updated UI: Server detected as running")
        
    def _server_uncertain_callback(self, processes=None):
        """Called when server status is uncertain"""
        self.server_running = False  # Keep as stopped for safety
        self.start_button.config(text="Start Server", state='normal')
        self.stop_button.config(state='disabled')
        self.status_label.config(text="Server Status Unknown")
        if processes:
            self.message_label.config(text="Found Flask processes but no HTTP response")
        else:
            self.message_label.config(text="Port 5000 in use but not responding")
        self.update_status_indicator()
        
    def _no_server_detected_callback(self):
        """Called when no server is detected"""
        self.server_running = False
        self.start_button.config(text="Start Server", state='normal')
        self.stop_button.config(state='disabled')
        self.status_label.config(text="Server Stopped")
        self.message_label.config(text="Ready to start server")
        self.update_status_indicator()
        
    def check_setup(self):
        """Check if the project setup is correct"""
        try:
            checks = []
            
            # Check if project directory exists
            if os.path.exists(self.project_path):
                checks.append("✅ Project directory found")
            else:
                checks.append("❌ Project directory not found")
            
            # Check if start_server.py exists
            server_script = os.path.join(self.project_path, "start_server.py")
            if os.path.exists(server_script):
                checks.append("✅ start_server.py found")
            else:
                checks.append("❌ start_server.py not found")
            
            # Check Python executable
            if os.path.exists(self.python_executable):
                checks.append(f"✅ Python executable found: {Path(self.python_executable).name}")
            else:
                checks.append(f"❌ Python executable not found: {self.python_executable}")
            
            # Check virtual environment
            venv_dir = Path(self.project_path) / 'venv'
            if venv_dir.exists():
                checks.append("✅ Virtual environment found")
            else:
                checks.append("⚠️ Virtual environment not found (will use system Python)")
            
            # Check if Flask is installed
            try:
                result = subprocess.run([self.python_executable, '-c', 'import flask; print("Flask version:", flask.__version__)'], 
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    checks.append(f"✅ Flask installed: {result.stdout.strip()}")
                else:
                    checks.append("❌ Flask not installed")
            except Exception as e:
                checks.append(f"❌ Error checking Flask: {str(e)}")
            
            # Show results
            messagebox.showinfo("Setup Check", "\n".join(checks))
            
        except Exception as e:
            messagebox.showerror("Setup Check Error", f"Error during setup check:\n{str(e)}")
        
    def update_status_indicator(self):
        """Update the status indicator circle"""
        self.status_indicator.delete("all")
        color = "#28a745" if self.server_running else "#dc3545"
        self.status_indicator.create_oval(2, 2, 18, 18, fill=color, outline=color)
        
    def start_server(self):
        """Start the Flask server"""
        if not os.path.exists(self.project_path):
            messagebox.showerror("Error", f"Project path not found:\n{self.project_path}")
            return
            
        server_script = os.path.join(self.project_path, "start_server.py")
        if not os.path.exists(server_script):
            messagebox.showerror("Error", "start_server.py not found in project directory")
            return
            
        if not os.path.exists(self.python_executable):
            messagebox.showerror("Error", f"Python executable not found:\n{self.python_executable}")
            return
            
        try:
            # Update UI
            self.start_button.config(text="Starting...", state='disabled')
            self.status_label.config(text="Starting server...")
            self.message_label.config(text="Launching server process...")
            
            # Start server in separate thread
            threading.Thread(target=self._start_server_thread, daemon=True).start()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start server:\n{str(e)}")
            self.start_button.config(text="Start Server", state='normal')
            
    def _start_server_thread(self):
        """Run server in background thread"""
        try:
            print(f"Starting server with Python: {self.python_executable}")
            print(f"Working directory: {self.project_path}")
            
            # Start server process
            self.server_process = subprocess.Popen(
                [self.python_executable, "start_server.py"],
                cwd=self.project_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
            
            # Monitor server output
            server_started = False
            startup_timeout = 30  # 30 seconds timeout
            import time
            start_time = time.time()
            
            if self.server_process.stdout:
                for line in iter(self.server_process.stdout.readline, ''):
                    print(f"Server output: {line.strip()}")
                    
                    if "Running on http://127.0.0.1:5000" in line or "* Running on all addresses" in line:
                        server_started = True
                        self.root.after(0, self._server_started_callback)
                        break
                    elif self.server_process.poll() is not None:
                        # Process ended unexpectedly
                        break
                    elif time.time() - start_time > startup_timeout:
                        # Timeout
                        self.root.after(0, lambda: self._server_error_callback("Server startup timeout"))
                        break
                        
            if not server_started and self.server_process.poll() is not None:
                # Get error output
                if self.server_process.stderr:
                    error_output = self.server_process.stderr.read()
                else:
                    error_output = "Unknown error"
                self.root.after(0, lambda: self._server_failed_callback(error_output))
                
        except Exception as e:
            print(f"Exception in server thread: {e}")
            self.root.after(0, lambda: self._server_error_callback(str(e)))
            
    def _server_started_callback(self):
        """Called when server successfully starts"""
        self.server_running = True
        self.start_button.config(text="Start Server", state='disabled')
        self.stop_button.config(state='normal')
        self.status_label.config(text="Server Running")
        self.message_label.config(text=f"Server available at {self.server_url}")
        self.update_status_indicator()
        
    def _server_failed_callback(self, error_output=""):
        """Called when server fails to start"""
        self.start_button.config(text="Start Server", state='normal')
        self.status_label.config(text="Server Failed")
        self.message_label.config(text="Server failed to start. Check setup or dependencies.")
        
        if error_output:
            messagebox.showerror("Server Error", f"Server failed to start:\n\n{error_output[:500]}")
        
        self.server_process = None
        
    def _server_error_callback(self, error_msg):
        """Called when there's an error starting server"""
        self.start_button.config(text="Start Server", state='normal')
        self.status_label.config(text="Server Error")
        self.message_label.config(text="Error starting server")
        messagebox.showerror("Server Error", f"Failed to start server:\n{error_msg}")
        self.server_process = None
        
    def stop_server(self):
        """Stop the Flask server"""
        if not self.server_running or not self.server_process:
            return
            
        try:
            # Update UI to show stopping process
            self.stop_button.config(text="Stopping...", state='disabled')
            self.status_label.config(text="Stopping server...")
            self.message_label.config(text="Terminating server process...")
            
            # Start stop process in separate thread to prevent UI blocking
            threading.Thread(target=self._stop_server_thread, daemon=True).start()
            
        except Exception as e:
            messagebox.showerror("Error", f"Error stopping server:\n{str(e)}")
            self._server_stopped_callback()
            
    def _stop_server_thread(self):
        """Stop server in background thread"""
        try:
            if not self.server_process:
                print("No server process to stop")
                self.root.after(0, self._server_stopped_callback)
                return
                
            print(f"Stopping server process: {self.server_process.pid}")
            
            # For Flask development server, we need to handle child processes
            import signal
            import psutil
            
            if self.server_process and hasattr(self.server_process, 'pid') and self.server_process.pid:
                try:
                    # Get the main process
                    parent = psutil.Process(self.server_process.pid)
                    
                    # Get all child processes (Flask debug mode creates children)
                    children = parent.children(recursive=True)
                    
                    # Terminate children first
                    for child in children:
                        try:
                            print(f"Terminating child process: {child.pid}")
                            child.terminate()
                        except psutil.NoSuchProcess:
                            pass
                    
                    # Terminate parent process
                    print(f"Terminating parent process: {parent.pid}")
                    parent.terminate()
                    
                    # Wait for processes to terminate
                    gone, still_alive = psutil.wait_procs(children + [parent], timeout=3)
                    
                    # Force kill any remaining processes
                    for proc in still_alive:
                        try:
                            print(f"Force killing process: {proc.pid}")
                            proc.kill()
                        except psutil.NoSuchProcess:
                            pass
                            
                except psutil.NoSuchProcess:
                    print("Process already terminated")
                except Exception as e:
                    print(f"Error with psutil approach: {e}")
                    # Fallback to standard approach
                    self._fallback_stop_server()
            else:
                print("No valid process PID")
                
            # Clean up
            self.server_process = None
            self.root.after(0, self._server_stopped_callback)
            
        except ImportError:
            print("psutil not available, using fallback method")
            self._fallback_stop_server()
        except Exception as e:
            print(f"Error in stop server thread: {e}")
            self._fallback_stop_server()
            
    def _fallback_stop_server(self):
        """Fallback method to stop server without psutil"""
        try:
            if self.server_process:
                # Try graceful termination first
                self.server_process.terminate()
                
                try:
                    # Wait for termination
                    self.server_process.wait(timeout=5)
                    print("Server terminated gracefully")
                except subprocess.TimeoutExpired:
                    # Force kill if graceful shutdown fails
                    print("Graceful termination failed, force killing")
                    self.server_process.kill()
                    self.server_process.wait()
                    
                self.server_process = None
                
            self.root.after(0, self._server_stopped_callback)
            
        except Exception as e:
            print(f"Error in fallback stop: {e}")
            self.root.after(0, self._server_stopped_callback)
            
    def _server_stopped_callback(self):
        """Called when server has been stopped"""
        self.server_running = False
        self.start_button.config(text="Start Server", state='normal')
        self.stop_button.config(text="Stop Server", state='disabled')
        self.status_label.config(text="Server Stopped")
        self.message_label.config(text="Server stopped successfully")
        self.update_status_indicator()
        print("Server stopped successfully")
            
    def copy_url(self):
        """Copy URL to clipboard"""
        self.root.clipboard_clear()
        self.root.clipboard_append(self.server_url)
        self.message_label.config(text="URL copied to clipboard")
        
    def open_browser(self):
        """Open server URL in default browser"""
        try:
            webbrowser.open(self.server_url)
            self.message_label.config(text="Opened in browser")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open browser:\n{str(e)}")
            
    def on_closing(self):
        """Handle window closing"""
        if self.server_running:
            result = messagebox.askyesno("Confirm Exit", 
                                       "Server is still running. Stop server and exit?")
            if result:
                self.stop_server()
                self.root.destroy()
        else:
            self.root.destroy()
            
    def run(self):
        """Start the application"""
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()

if __name__ == "__main__":
    try:
        app = SimpleTeachingContentLauncher()
        app.run()
    except Exception as e:
        # Show error in a message box instead of crashing silently
        import tkinter as tk
        from tkinter import messagebox
        root = tk.Tk()
        root.withdraw()  # Hide main window
        messagebox.showerror("Launch Error", 
                           f"Failed to start launcher:\n\n{str(e)}\n\n"
                           f"Python path: {__file__}\n"
                           f"Working directory: {os.getcwd()}")
        root.destroy() 