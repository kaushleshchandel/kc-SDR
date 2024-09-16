import tkinter as tk
import subprocess
import os
import signal

class AppLauncher:
    def __init__(self, root, status_callback):
        self.root = root
        self.status_callback = status_callback
        self.process = None
        self.current_app = None

        self.apps = [
            ("SDR-Trunk", "/home/pi/sdr-trunk-linux-aarch64-v0.6.0/bin/sdr-trunk"),
            ("GQRX", "/usr/bin/gqrx"),
            ("Boondock", "/usr/bin/boondock"),
        ]

        self.create_buttons()

    def create_buttons(self):
        for app_name, app_command in self.apps:
            btn = tk.Button(self.root, text=app_name, command=lambda cmd=app_command, name=app_name: self.launch_app(cmd, name))
            btn.pack(side=tk.LEFT, padx=5)

        self.close_app_btn = tk.Button(self.root, text="Close App", command=self.close_current_app, state=tk.DISABLED)
        self.close_app_btn.pack(side=tk.LEFT, padx=5)

    def launch_app(self, app_command, app_name):
        if self.process:
            self.status_callback(f"Close {self.current_app} first", "orange")
            return

        try:
            env = os.environ.copy()
            env['LD_LIBRARY_PATH'] = '/usr/local/lib:' + env.get('LD_LIBRARY_PATH', '')
            env['DISPLAY'] = ':0'

            if app_name == "GNU Radio Companion":
                launch_command = "gtk-launch gnuradio-grc.desktop"
            else:
                launch_command = app_command

            self.process = subprocess.Popen(launch_command, shell=True, env=env, preexec_fn=os.setsid)
            self.current_app = app_name
            self.close_app_btn.config(state=tk.NORMAL)
            self.status_callback(f"Running: {app_name}", "blue")
            self.root.after(100, self.check_process)
        except Exception as e:
            self.status_callback(f"Error: {str(e)}", "red")

    def close_current_app(self):
        if self.process:
            try:
                os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
                self.process = None
                self.close_app_btn.config(state=tk.DISABLED)
                self.status_callback(f"Closed: {self.current_app}", "green")
                self.current_app = None
            except Exception as e:
                self.status_callback(f"Error closing app: {str(e)}", "red")
        else:
            self.status_callback("No app running", "orange")

    def check_process(self):
        if self.process and self.process.poll() is not None:
            self.process = None
            self.close_app_btn.config(state=tk.DISABLED)
            self.status_callback(f"{self.current_app} closed", "green")
            self.current_app = None
        if self.process:
            self.root.after(100, self.check_process)