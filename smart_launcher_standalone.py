import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import webbrowser
import threading
import os
import time
import sys

# Try to import optional dependencies
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

class SmartTeachingContentLauncher:
    def __init__(self):
        # Configuration
        self.project_path = r"C:\Users\Dell\teaching-content-db"
        self.server_url = "http://127.0.0.1:5000"
        self.health_url = f"{self.server_url}/api/health"
        
        # Server state
        self.server_process = None
        self.server_running = False
        self.server_managed = False  # True if we started it, False if external
        
        # Create main window
        self.root = tk.Tk()
        self.root.title("Teaching Content Database - Smart Launcher")
        self.root.geometry("450x320")
        self.root.resizable(False, False)
        
        # Configure style
        style = ttk.Style()
        style.theme_use('clam')
        
        self.setup_ui()
        
        # Check dependencies and server status
        self.root.after(100, self.initial_setup)
        
    def setup_ui(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky="nsew")
        
        # Title
        title_label = ttk.Label(main_frame, text="Teaching Content Database", 
                               font=('Arial', 14, 'bold'))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # Dependency status
        self.dependency_frame = ttk.LabelFrame(main_frame, text="System Status", padding="10")
        self.dependency_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        
        self.dependency_label = ttk.Label(self.dependency_frame, text="Checking dependencies...", 
                                         font=('Arial', 9), foreground='blue')
        self.dependency_label.pack(anchor=tk.W)
        
        # Status section
        status_frame = ttk.LabelFrame(main_frame, text="Server Status", padding="10")
        status_frame.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(0, 15))
        
        # Status indicator
        self.indicator_frame = ttk.Frame(status_frame)
        self.indicator_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.status_indicator = tk.Canvas(self.indicator_frame, width=20, height=20)
        self.status_indicator.pack(side=tk.LEFT, padx=(0, 10))
        
        self.status_label = ttk.Label(self.indicator_frame, text="Checking server...", 
                                     font=('Arial', 10, 'bold'))
        self.status_label.pack(side=tk.LEFT)
        
        # Server type label
        self.server_type_label = ttk.Label(status_frame, text="", 
                                          font=('Arial', 9), foreground='gray')
        self.server_type_label.pack(anchor=tk.W)
        
        # Control section
        control_frame = ttk.LabelFrame(main_frame, text="Server Control", padding="10")
        control_frame.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(0, 15))
        
        # Control buttons frame
        button_frame = ttk.Frame(control_frame)
        button_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.start_button = ttk.Button(button_frame, text="Start Server", 
                                      command=self.start_server)
        self.start_button.pack(side=tk.LEFT, padx=(0, 5))
        
        self.stop_button = ttk.Button(button_frame, text="Stop Server", 
                                     command=self.stop_server, state='disabled')
        self.stop_button.pack(side=tk.LEFT, padx=(0, 5))
        
        self.restart_button = ttk.Button(button_frame, text="Restart", 
                                        command=self.restart_server, state='disabled')
        self.restart_button.pack(side=tk.LEFT)
        
        # URL section
        url_frame = ttk.LabelFrame(main_frame, text="Server Access", padding="10")
        url_frame.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(0, 15))
        
        # URL entry
        url_entry_frame = ttk.Frame(url_frame)
        url_entry_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(url_entry_frame, text="URL:", font=('Arial', 9)).pack(side=tk.LEFT, padx=(0, 5))
        
        self.url_entry = ttk.Entry(url_entry_frame, state='readonly', font=('Arial', 9))
        self.url_entry.insert(0, self.server_url)
        self.url_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        self.copy_button = ttk.Button(url_entry_frame, text="Copy", width=6, 
                                     command=self.copy_url, state='disabled')
        self.copy_button.pack(side=tk.RIGHT)
        
        self.browser_button = ttk.Button(url_frame, text="Open in Browser", 
                                        command=self.open_browser, state='disabled')
        self.browser_button.pack(fill=tk.X)
        
        # Status message
        self.message_label = ttk.Label(main_frame, text="Initializing...", 
                                      font=('Arial', 8), foreground='gray')
        self.message_label.grid(row=5, column=0, columnspan=2)
        
        # Update status indicator
        self.update_status_indicator()
        
    def initial_setup(self):
        """Check dependencies and then server status"""
        self.check_dependencies()
        if HAS_REQUESTS:
            threading.Thread(target=self._check_server_status, daemon=True).start()
        else:
            self._server_status_unknown()
            
    def check_dependencies(self):
        """Check and display dependency status"""
        missing = []
        if not HAS_REQUESTS:
            missing.append("requests")
        if not HAS_PSUTIL:
            missing.append("psutil")
            
        if missing:
            self.dependency_label.config(
                text=f"⚠️ Missing dependencies: {', '.join(missing)}. Limited functionality.",
                foreground='orange'
            )
        else:
            self.dependency_label.config(
                text="✅ All dependencies available. Full functionality enabled.",
                foreground='green'
            )
        
    def update_status_indicator(self):
        """Update the status indicator circle"""
        self.status_indicator.delete("all")
        if self.server_running:
            color = "#28a745" if self.server_managed else "#ffc107"
        else:
            color = "#dc3545"
        self.status_indicator.create_oval(2, 2, 18, 18, fill=color, outline=color)
        
    def _check_server_status(self):
        """Check if server is running and update UI accordingly"""
        if not HAS_REQUESTS:
            self.root.after(0, self._server_status_unknown)
            return
            
        try:
            response = requests.get(self.health_url, timeout=3)
            if response.status_code == 200:
                # Server is running
                self.root.after(0, self._server_detected_external)
            else:
                self.root.after(0, self._server_not_running)
        except requests.exceptions.RequestException:
            # Server not running or not accessible
            self.root.after(0, self._server_not_running)
            
    def _server_status_unknown(self):
        """Handle unknown server status due to missing dependencies"""
        self.server_running = False
        self.server_managed = False
        self.status_label.config(text="Server Status Unknown")
        self.server_type_label.config(text="(Cannot detect - missing 'requests' library)")
        self.message_label.config(text="Basic functionality available")
        
        # Enable basic functions
        self.start_button.config(text="Start Server", command=self.start_server, state='normal')
        self.stop_button.config(state='disabled')
        self.restart_button.config(state='disabled')
        self.copy_button.config(state='normal')  # Always allow copy
        self.browser_button.config(state='normal')  # Always allow browser
        
        self.update_status_indicator()
            
    def _server_detected_external(self):
        """Handle detection of external server"""
        self.server_running = True
        self.server_managed = False
        self.status_label.config(text="Server Running")
        self.server_type_label.config(text="(External - not managed by launcher)")
        self.message_label.config(text="Server detected! You can access it or take control.")
        
        # Update button states
        self.start_button.config(text="Take Control", command=self.take_control)
        self.stop_button.config(state='disabled')
        self.restart_button.config(state='disabled')
        self.copy_button.config(state='normal')
        self.browser_button.config(state='normal')
        
        self.update_status_indicator()
        
    def _server_not_running(self):
        """Handle no server detected"""
        self.server_running = False
        self.server_managed = False
        self.status_label.config(text="Server Stopped")
        self.server_type_label.config(text="")
        self.message_label.config(text="Ready to start server")
        
        # Update button states
        self.start_button.config(text="Start Server", command=self.start_server, state='normal')
        self.stop_button.config(state='disabled')
        self.restart_button.config(state='disabled')
        self.copy_button.config(state='normal')  # Always allow copy
        self.browser_button.config(state='normal')  # Always allow browser
        
        self.update_status_indicator()
        
    def _server_running_managed(self):
        """Handle managed server running"""
        self.server_running = True
        self.server_managed = True
        self.status_label.config(text="Server Running")
        self.server_type_label.config(text="(Managed by launcher)")
        self.message_label.config(text=f"Server ready at {self.server_url}")
        
        # Update button states
        self.start_button.config(state='disabled')
        self.stop_button.config(state='normal')
        self.restart_button.config(state='normal')
        self.copy_button.config(state='normal')
        self.browser_button.config(state='normal')
        
        self.update_status_indicator()
        
    def take_control(self):
        """Take control of external server by killing it and starting managed one"""
        if not HAS_PSUTIL:
            messagebox.showwarning("Limited Functionality", 
                                 "Cannot take control of external server.\n"
                                 "Missing 'psutil' dependency.\n\n"
                                 "Please stop the server manually and use 'Start Server'.")
            return
            
        result = messagebox.askyesno("Take Control", 
                                   "This will stop the external server and start a managed one.\n"
                                   "Continue?")
        if result:
            self.message_label.config(text="Taking control...")
            threading.Thread(target=self._take_control_thread, daemon=True).start()
            
    def _take_control_thread(self):
        """Kill external server and start managed one"""
        try:
            # Kill any Python processes running on port 5000
            self._kill_server_processes()
            time.sleep(1)
            
            # Start our managed server
            self._start_managed_server()
            
        except Exception as e:
            self.root.after(0, lambda: self._control_error(str(e)))
            
    def _kill_server_processes(self):
        """Kill existing server processes"""
        if not HAS_PSUTIL:
            return
            
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if 'python' in proc.info['name'].lower():
                    if proc.info['cmdline'] and any('start_server.py' in cmd for cmd in proc.info['cmdline']):
                        proc.terminate()
                        proc.wait(timeout=3)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.TimeoutExpired):
                continue
                
    def start_server(self):
        """Start managed server"""
        if not os.path.exists(self.project_path):
            messagebox.showerror("Error", f"Project path not found:\n{self.project_path}")
            return
            
        if not os.path.exists(os.path.join(self.project_path, "start_server.py")):
            messagebox.showerror("Error", "start_server.py not found in project directory")
            return
            
        self.start_button.config(state='disabled')
        self.message_label.config(text="Starting server...")
        
        threading.Thread(target=self._start_managed_server, daemon=True).start()
        
    def _start_managed_server(self):
        """Start server in managed mode"""
        try:
            # Start server process
            self.server_process = subprocess.Popen(
                ["python", "start_server.py"],
                cwd=self.project_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
            
            # Monitor startup
            server_started = False
            if self.server_process.stdout:
                for line in iter(self.server_process.stdout.readline, ''):
                    if "Running on http://127.0.0.1:5000" in line:
                        server_started = True
                        self.root.after(0, self._server_running_managed)
                        break
                    elif self.server_process.poll() is not None:
                        break
                        
            if not server_started:
                self.root.after(0, self._server_start_failed)
                
        except Exception as e:
            self.root.after(0, lambda: self._server_start_error(str(e)))
            
    def _server_start_failed(self):
        """Handle server start failure"""
        self.message_label.config(text="Server failed to start")
        self.start_button.config(state='normal')
        messagebox.showerror("Error", "Server failed to start. Check if port 5000 is available.")
        
    def _server_start_error(self, error_msg):
        """Handle server start error"""
        self.message_label.config(text="Error starting server")
        self.start_button.config(state='normal')
        messagebox.showerror("Error", f"Failed to start server:\n{error_msg}")
        
    def _control_error(self, error_msg):
        """Handle take control error"""
        self.message_label.config(text="Failed to take control")
        messagebox.showerror("Error", f"Failed to take control:\n{error_msg}")
        
    def stop_server(self):
        """Stop managed server"""
        if not self.server_managed:
            messagebox.showwarning("Warning", "Cannot stop external server")
            return
            
        try:
            if self.server_process:
                self.server_process.terminate()
                self.server_process.wait(timeout=5)
                self.server_process = None
                
            self._server_not_running()
            self.message_label.config(text="Server stopped")
            
        except subprocess.TimeoutExpired:
            if self.server_process:
                self.server_process.kill()
                self.server_process = None
            self._server_not_running()
            messagebox.showwarning("Warning", "Server was forcefully terminated")
        except Exception as e:
            messagebox.showerror("Error", f"Error stopping server:\n{str(e)}")
            
    def restart_server(self):
        """Restart managed server"""
        if not self.server_managed:
            messagebox.showwarning("Warning", "Cannot restart external server")
            return
            
        self.message_label.config(text="Restarting server...")
        threading.Thread(target=self._restart_server_thread, daemon=True).start()
        
    def _restart_server_thread(self):
        """Restart server in background"""
        try:
            # Stop current server
            if self.server_process:
                self.server_process.terminate()
                self.server_process.wait(timeout=5)
                self.server_process = None
                
            time.sleep(1)
            
            # Start new server
            self._start_managed_server()
            
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", f"Restart failed:\n{str(e)}"))
            
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
        if self.server_running and self.server_managed:
            result = messagebox.askyesno("Confirm Exit", 
                                       "Managed server is running. Stop it and exit?")
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
        app = SmartTeachingContentLauncher()
        app.run()
    except Exception as e:
        # Show error in a message box instead of crashing silently
        root = tk.Tk()
        root.withdraw()  # Hide main window
        messagebox.showerror("Launch Error", f"Failed to start launcher:\n\n{str(e)}\n\nTry running from command line to see full error.")
        root.destroy() 