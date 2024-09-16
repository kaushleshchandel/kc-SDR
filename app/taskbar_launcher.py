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

        reboot_btn = tk.Button(self.root, text="Reboot", command=self.reboot_raspberry_pi, bg="blue", fg="white")
        reboot_btn.pack(side=tk.RIGHT, padx=5)

    def update_status(self, message, color):
        self.status_label.config(text=message, fg=color)
        if color != "blue":  # If it's not a "Running" status
            self.root.after(3000, lambda: self.status_label.config(text="Ready", fg="green"))

    def create_centered_dialog(self, title, message):
        dialog = tk.Toplevel(self.root)
        dialog.title(title)
        dialog.geometry(f"+{self.screen_width//2 - 150}+{self.screen_height//2 - 50}")
        dialog.attributes('-topmost', True)

        tk.Label(dialog, text=message, padx=20, pady=10).pack()
        
        button_frame = tk.Frame(dialog)
        button_frame.pack(pady=10)

        yes_button = tk.Button(button_frame, text="Yes", command=lambda: dialog.destroy() or setattr(dialog, 'result', True))
        yes_button.pack(side=tk.LEFT, padx=10)
        
        no_button = tk.Button(button_frame, text="No", command=lambda: dialog.destroy() or setattr(dialog, 'result', False))
        no_button.pack(side=tk.LEFT, padx=10)

        dialog.transient(self.root)
        dialog.grab_set()
        self.root.wait_window(dialog)
        return getattr(dialog, 'result', False)

    def shutdown_raspberry_pi(self):
        if self.create_centered_dialog("Shutdown", "Are you sure you want to shutdown the Raspberry Pi?"):
            self.update_status("Shutting down...", "red")
            self.root.update()
            os.system("sudo shutdown -h now")

    def reboot_raspberry_pi(self):
        if self.create_centered_dialog("Reboot", "Are you sure you want to reboot the Raspberry Pi?"):
            self.update_status("Rebooting...", "red")
            self.root.update()
            os.system("sudo shutdown -r now")

    def quit(self):
        self.app_launcher.close_current_app()
        self.volume_control.cleanup()
        self.root.quit()

    def run(self):
        self.root.mainloop()