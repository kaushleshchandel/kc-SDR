import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import os
from volume_control import VolumeControl
from app_launcher import AppLauncher
from utils import set_strut

class TaskbarLauncher:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Taskbar Launcher")

        self.setup_window()
        self.create_buttons()
        self.volume_control = VolumeControl(self.root)
        self.app_launcher = AppLauncher(self.root, self.update_status)

        self.root.after(100, lambda: set_strut(self.root, self.taskbar_height))

    def setup_window(self):
        self.screen_width = self.root.winfo_screenwidth()
        self.screen_height = self.root.winfo_screenheight()
        self.taskbar_height = 30
        self.root.geometry(f"{self.screen_width}x{self.taskbar_height}+0+{self.screen_height - self.taskbar_height}")
        self.root.attributes('-topmost', True)
        self.root.overrideredirect(True)

    def create_buttons(self):
        self.status_label = tk.Label(self.root, text="Ready", fg="green")
        self.status_label.pack(side=tk.LEFT, padx=5)

        shutdown_btn = tk.Button(self.root, text="Shutdown", command=self.shutdown_raspberry_pi, bg="red", fg="white")
        shutdown_btn.pack(side=tk.RIGHT, padx=5)

        quit_btn = tk.Button(self.root, text="X", command=self.quit, bg="red", fg="white")
        quit_btn.pack(side=tk.RIGHT, padx=5)

    def update_status(self, message, color):
        self.status_label.config(text=message, fg=color)
        if color != "blue":  # If it's not a "Running" status
            self.root.after(3000, lambda: self.status_label.config(text="Ready", fg="green"))

    def shutdown_raspberry_pi(self):
        if messagebox.askyesno("Shutdown", "Are you sure you want to shutdown the Raspberry Pi?"):
            self.update_status("Shutting down...", "red")
            self.root.update()
            os.system("sudo shutdown -h now")

    def quit(self):
        self.app_launcher.close_current_app()
        self.volume_control.cleanup()
        self.root.quit()

    def run(self):
        self.root.mainloop()