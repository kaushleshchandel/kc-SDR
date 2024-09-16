import tkinter as tk
from tkinter import ttk
import pulsectl
import threading

class VolumeControl:
    def __init__(self, root):
        self.root = root
        self.pulse = pulsectl.Pulse('volume-control')
        self.setup_volume_control()
        self.start_pulse_thread()

    def setup_volume_control(self):
        self.sink = self.pulse.get_sink_by_name(self.pulse.server_info().default_sink_name)

        self.volume_var = tk.DoubleVar()
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

    def start_pulse_thread(self):
        self.pulse_thread = threading.Thread(target=self.pulse_event_loop, daemon=True)
        self.pulse_thread.start()

    def pulse_event_loop(self):
        with pulsectl.Pulse('event-listener') as pulse:
            def event_callback(ev):
                if ev.facility == 'sink':
                    self.root.after(0, self.update_volume_display)
                return True
            pulse.event_mask_set('sink')
            pulse.event_callback_set(event_callback)
            pulse.event_listen()

    def cleanup(self):
        self.pulse.close()