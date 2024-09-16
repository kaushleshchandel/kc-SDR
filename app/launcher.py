import tkinter as tk
from tkinter import ttk
from tkinter import messagebox  # Add this import
import subprocess
import os
import signal
from Xlib import display, X, Xatom
import pulsectl
import threading

class TaskbarLauncher:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Taskbar Launcher")

        # Get screen width and height
        self.screen_width = self.root.winfo_screenwidth()
        self.screen_height = self.root.winfo_screenheight()

        # Set taskbar dimensions and position
        self.taskbar_height = 30
        self.root.geometry(f"{self.screen_width}x{self.taskbar_height}+0+{self.screen_height - self.taskbar_height}")

        self.root.attributes('-topmost', True)  # Always on top
        self.root.overrideredirect(True)  # Remove window decorations

        self.apps = [
            ("SDR-Trunk", "/home/pi/sdr-trunk-linux-aarch64-v0.6.0/bin/sdr-trunk"),
            ("GQRX", "/usr/bin/gqrx"),
            ("Boondock", "/usr/bin/boondock"),
        ]

        self.buttons = []
        for app_name, app_command in self.apps:
            btn = tk.Button(self.root, text=app_name, command=lambda cmd=app_command, name=app_name: self.launch_app(cmd, name))
            btn.pack(side=tk.LEFT, padx=5)
            self.buttons.append(btn)

        # Add Close Current App button
        self.close_app_btn = tk.Button(self.root, text="Close App", command=self.close_current_app, state=tk.DISABLED)
        self.close_app_btn.pack(side=tk.LEFT, padx=5)

        # Add status label
        self.status_label = tk.Label(self.root, text="Ready", fg="green")
        self.status_label.pack(side=tk.LEFT, padx=5)

        # Add volume control
        self.setup_volume_control()

        # Add shutdown button
        shutdown_btn = tk.Button(self.root, text="Shutdown", command=self.shutdown_raspberry_pi, bg="red", fg="white")
        shutdown_btn.pack(side=tk.RIGHT, padx=5)

        quit_btn = tk.Button(self.root, text="X", command=self.quit, bg="red", fg="white")
        quit_btn.pack(side=tk.RIGHT, padx=5)

        self.process = None
        self.current_app = None

        # Set up the strut after a short delay to ensure the window is fully created
        self.root.after(100, self.set_strut)

        # Start PulseAudio event loop in a separate thread
        self.pulse_thread = threading.Thread(target=self.pulse_event_loop, daemon=True)
        self.pulse_thread.start()

    def setup_volume_control(self):
        self.pulse = pulsectl.Pulse('volume-control')

        # Get the default sink (output device)
        self.sink = self.pulse.get_sink_by_name(self.pulse.server_info().default_sink_name)

        # Create volume slider
        self.volume_var = tk.DoubleVar()
        self.volume_slider = ttk.Scale(self.root, from_=0, to=100, orient=tk.HORIZONTAL,
                                       command=self.change_volume, variable=self.volume_var,
                                       length=100)
        self.volume_slider.pack(side=tk.RIGHT, padx=5)

        # Create volume icon button
        self.volume_icon = tk.StringVar()
        self.volume_btn = tk.Button(self.root, textvariable=self.volume_icon,
                                    command=self.toggle_mute, width=2)
        self.volume_btn.pack(side=tk.RIGHT)

        # Initialize volume and mute state
        self.update_volume_display()

    def change_volume(self, value):
        volume = float(value) / 100
        with self.pulse as pulse:
            pulse.volume_set_all_chans(self.sink, volume)
        self.update_volume_display()

    def toggle_mute(self):
        with self.pulse as pulse:
            pulse.mute(self.sink, not self.sink.mute)
        self.update_volume_display()

    def update_volume_display(self):
        with self.pulse as pulse:
            volume = pulse.volume_get_all_chans(self.sink)
            muted = self.sink.mute == 1

        self.volume_var.set(volume * 100)

        if muted:
            self.volume_icon.set("🔇")
        elif volume > 0.66:
            self.volume_icon.set("🔊")
        elif volume > 0.33:
            self.volume_icon.set("🔉")
        else:
            self.volume_icon.set("🔈")

    def pulse_event_loop(self):
        with pulsectl.Pulse('event-listener') as pulse:
            def event_callback(ev):
                if ev.facility == 'sink':
                    self.root.after(0, self.update_volume_display)
                return True
            pulse.event_mask_set('sink')
            pulse.event_callback_set(event_callback)
            pulse.event_listen()

    def set_strut(self):
        # Get the X11 display and root window
        d = display.Display()
        root = d.screen().root

        # Get the window ID of our taskbar
        win_id = self.root.winfo_id()
        win = d.create_resource_object('window', win_id)

        # Set up the strut
        strut = [0, 0, 0, self.taskbar_height, 0, 0, 0, 0, 0, 0, 0, self.screen_width]
        win.change_property(d.intern_atom('_NET_WM_STRUT_PARTIAL'),
                            d.intern_atom('CARDINAL'), 32,
                            strut)

        # Make sure the window is always on the bottom layer
        win.configure(stack_mode=X.Below)

        d.sync()

    def launch_app(self, app_command, app_name):
        if self.process:
            self.status_label.config(text=f"Close {self.current_app} first", fg="orange")
            self.root.after(3000, lambda: self.status_label.config(text=f"Running: {self.current_app}", fg="blue"))
            return

        try:
            env = os.environ.copy()
            env['LD_LIBRARY_PATH'] = '/usr/local/lib:' + env.get('LD_LIBRARY_PATH', '')
            env['DISPLAY'] = ':0'  # Ensure the launched app uses the main display
            
            if app_name == "GNU Radio Companion":
                # Use gtk-launch for GNU Radio Companion
                launch_command = f"gtk-launch gnuradio-grc.desktop"
            else:
                launch_command = app_command
            
            self.process = subprocess.Popen(launch_command, shell=True, env=env, preexec_fn=os.setsid)
            self.current_app = app_name
            self.close_app_btn.config(state=tk.NORMAL)  # Enable the Close App button
            self.status_label.config(text=f"Running: {app_name}", fg="blue")
            self.root.after(100, self.check_process)
        except Exception as e:
            self.status_label.config(text=f"Error: {str(e)}", fg="red")
            self.root.after(3000, lambda: self.status_label.config(text="Ready", fg="green"))

    def close_current_app(self):
        if self.process:
            try:
                os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
                self.process = None
                self.close_app_btn.config(state=tk.DISABLED)  # Disable the Close App button
                self.status_label.config(text=f"Closed: {self.current_app}", fg="green")
                self.current_app = None
                self.root.after(3000, lambda: self.status_label.config(text="Ready", fg="green"))
            except Exception as e:
                self.status_label.config(text=f"Error closing app: {str(e)}", fg="red")
                self.root.after(3000, lambda: self.status_label.config(text="Ready", fg="green"))
        else:
            self.status_label.config(text="No app running", fg="orange")
            self.root.after(3000, lambda: self.status_label.config(text="Ready", fg="green"))

    def check_process(self):
        if self.process and self.process.poll() is not None:
            self.process = None
            self.close_app_btn.config(state=tk.DISABLED)  # Disable the Close App button
            self.status_label.config(text=f"{self.current_app} closed", fg="green")
            self.current_app = None
            self.root.after(3000, lambda: self.status_label.config(text="Ready", fg="green"))
        if self.process:
            self.root.after(100, self.check_process)

    def shutdown_raspberry_pi(self):
        if messagebox.askyesno("Shutdown", "Are you sure you want to shutdown the Raspberry Pi?"):
            self.status_label.config(text="Shutting down...", fg="red")
            self.root.update()
            os.system("sudo shutdown -h now")

    def quit(self):
        if self.process:
            os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
        self.pulse.close()
        self.root.quit()

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    # Ensure the script uses the main display
    os.environ['DISPLAY'] = ':0'
    app = TaskbarLauncher()
    app.run()