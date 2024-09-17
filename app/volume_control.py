import tkinter as tk
from tkinter import ttk
import subprocess

class VolumeControl:
    def __init__(self, root):
        self.root = root
        self.setup_volume_control()

    def setup_volume_control(self):
        self.volume_var = tk.IntVar()
        self.volume_slider = ttk.Scale(self.root, from_=0, to=100, orient=tk.HORIZONTAL,
                                       command=self.change_volume, variable=self.volume_var,
                                       length=100)
        self.volume_slider.pack(side=tk.RIGHT, padx=5)

        self.volume_icon = tk.StringVar()
        self.volume_btn = tk.Button(self.root, textvariable=self.volume_icon,
                                    command=self.toggle_mute, width=2)
        self.volume_btn.pack(side=tk.RIGHT)

        self.update_volume_display()

    def change_volume(self, value):
        volume = int(float(value))
        subprocess.run(['amixer', 'sset', 'Master', f'{volume}%'])
        self.update_volume_display()

    def toggle_mute(self):
        subprocess.run(['amixer', 'sset', 'Master', 'toggle'])
        self.update_volume_display()

    def update_volume_display(self):
        try:
            output = subprocess.check_output(['amixer', 'sget', 'Master']).decode()
            volume_line = [line for line in output.split('\n') if 'Playback' in line][0]
            volume = int(volume_line.split('[')[1].split('%')[0])
            muted = '[off]' in volume_line
        except Exception:
            volume = 0
            muted = True

        self.volume_var.set(volume)

        if muted:
            self.volume_icon.set("🔇")
        elif volume > 66:
            self.volume_icon.set("🔊")
        elif volume > 33:
            self.volume_icon.set("🔉")
        else:
            self.volume_icon.set("🔈")

    def cleanup(self):
        pass  # No cleanup needed