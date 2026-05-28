# gui_windows.py
# GUI for configuration windows

import tkinter as tk
from tkinter import ttk, messagebox
from shared import BG, PANEL, TEXT, GREEN, save_config
import re

_time_re = re.compile(r"^\d{2}:\d{2}$")

def is_valid_time(s):
    if not _time_re.match(s):
        return False
    h, m = map(int, s.split(":"))
    return 0 <= h < 24 and 0 <= m < 60


# Scrollable container
class ScrollableFrame(tk.Frame):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.canvas = tk.Canvas(self, bg=BG, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.inner = tk.Frame(self.canvas, bg=BG)
        self.window_id = self.canvas.create_window((0, 0), window=self.inner, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        self.inner.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", self._on_canvas_configure)

    def _on_canvas_configure(self, event):
        self.canvas.itemconfig(self.window_id, width=event.width)


def make_modal(window, parent):
    window.transient(parent)
    window.grab_set()
    window.focus_set()
    try:
        window.wait_visibility()
    except Exception:
        pass


# Windows for Section configurations
class SectionConfigWindow(tk.Toplevel):
    def __init__(self, parent, simulator, refresh_callback):
        super().__init__(parent)
        self.simulator, self.refresh_callback = simulator, refresh_callback
        self.title("Configuration - Sections")
        self.geometry("800x600")
        self.configure(bg=BG)
        make_modal(self, parent)

        self.entries = {}
        self.scroll_frame = None
        self.build_sections()

    def build_sections(self):
        if self.scroll_frame:
            self.scroll_frame.destroy()

        self.entries.clear()
        self.scroll_frame = ScrollableFrame(self)
        self.scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)

        for index, sec in enumerate(self.simulator.config["sections"]):
            frame = tk.LabelFrame(self.scroll_frame.inner, text=sec["title"], bg=PANEL, fg=TEXT)
            frame.pack(fill="x", padx=5, pady=5)

            labels = ["title", "length", "step_time", "temp_sensitivity",
                      "buffer_limit", "earliest_start", "pause_mode"]

            for i, label in enumerate(labels):
                tk.Label(frame, text=label, bg=PANEL, fg=TEXT).grid(row=i, column=0, padx=5, pady=2, sticky="w")

                if label == "pause_mode":
                    cb = ttk.Combobox(frame, values=["hole_size", "duration"], state="readonly", width=12)
                    cb.set(sec.get("pause_mode", "hole_size"))
                    cb.grid(row=i, column=1, padx=5, pady=2, sticky="w")
                    self.entries[f"section.{index}.{label}"] = cb
                else:
                    entry = tk.Entry(frame)
                    entry.insert(0, str(sec.get(label, "")))
                    entry.grid(row=i, column=1, padx=5, pady=2, sticky="w")
                    self.entries[f"section.{index}.{label}"] = entry

            ttk.Button(frame, text="- Remove",
                       command=lambda idx=index: self.remove_section(idx)).grid(
                row=len(labels), column=0, columnspan=2, pady=5
            )

        btn_f = tk.Frame(self, bg=BG)
        btn_f.pack(fill="x", padx=10, pady=5)

        ttk.Button(btn_f, text="+ Add section", command=self.add_section).pack(side="left", padx=5)
        ttk.Button(btn_f, text="Save", command=self.save_all).pack(side="right", padx=5)

    def add_section(self):
        new_id = max([s["id"] for s in self.simulator.config["sections"]], default=0) + 1
        self.simulator.config["sections"].append({
            "id": new_id,
            "title": f"Section {new_id}",
            "length": 5,
            "step_time": 120,
            "temp_sensitivity": 1.0,
            "buffer_limit": 2,
            "color": GREEN,
            "earliest_start": "06:00",
            "pause_mode": "hole_size"
        })
        save_config(self.simulator.config)
        self.build_sections()

    def remove_section(self, index):
        if len(self.simulator.config["sections"]) <= 1:
            if not messagebox.askyesno("Confirm", "This is the last section. Remove anyway?"):
                return
        del self.simulator.config["sections"][index]
        save_config(self.simulator.config)
        self.build_sections()

    def save_all(self):
        try:
            for index, sec in enumerate(self.simulator.config["sections"]):
                sec["title"] = self.entries[f"section.{index}.title"].get()
                sec["length"] = int(self.entries[f"section.{index}.length"].get())
                sec["step_time"] = int(self.entries[f"section.{index}.step_time"].get())
                sec["temp_sensitivity"] = float(self.entries[f"section.{index}.temp_sensitivity"].get())
                sec["buffer_limit"] = int(self.entries[f"section.{index}.buffer_limit"].get())
                sec["earliest_start"] = self.entries[f"section.{index}.earliest_start"].get()
                sec["pause_mode"] = self.entries[f"section.{index}.pause_mode"].get()

                if not is_valid_time(sec["earliest_start"]):
                    raise ValueError(f"Invalid time for section {index+1}: {sec['earliest_start']}")

            save_config(self.simulator.config)
            self.simulator.load_sections()
            self.refresh_callback()

        except ValueError as ve:
            messagebox.showerror("Error", str(ve))


# Window for pause configurations
class PauseConfigWindow(tk.Toplevel):
    def __init__(self, parent, simulator, refresh_callback):
        super().__init__(parent)
        self.simulator, self.refresh_callback = simulator, refresh_callback
        self.title("Configuration - Pauses")
        self.geometry("800x600")
        self.configure(bg=BG)
        make_modal(self, parent)

        self.entries = {}
        self.check_vars = []
        self.scroll_frame = None

        self.build_pauses()

    def build_pauses(self):
        if self.scroll_frame:
            self.scroll_frame.destroy()

        self.entries.clear()
        self.check_vars = []

        self.scroll_frame = ScrollableFrame(self)
        self.scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)

        for index, pause in enumerate(self.simulator.config["pauses"]):
            frame = tk.LabelFrame(self.scroll_frame.inner, text=pause.get("name", f"Pause {index+1}"),
                                  bg=PANEL, fg=TEXT)
            frame.pack(fill="x", padx=5, pady=5)

            labels = ["name", "start_time", "duration_min", "hole_size"]

            for i, label in enumerate(labels):
                tk.Label(frame, text=label, bg=PANEL, fg=TEXT).grid(row=i, column=0, padx=5, pady=2, sticky="w")
                e = tk.Entry(frame)
                e.insert(0, str(pause.get(label, "")))
                e.grid(row=i, column=1, padx=5, pady=2, sticky="w")
                self.entries[f"pause.{index}.{label}"] = e

            # Affected sections
            tk.Label(frame, text="affected_sections", bg=PANEL, fg=TEXT).grid(
                row=len(labels), column=0, padx=5, pady=2, sticky="nw"
            )

            sec_frame = tk.Frame(frame, bg=PANEL)
            sec_frame.grid(row=len(labels), column=1, padx=5, pady=2, sticky="w")

            sec_vars = []
            for s in self.simulator.config["sections"]:
                var = tk.BooleanVar(value=(s["id"] in pause.get("affected_sections", [])))
                cb = tk.Checkbutton(sec_frame, text=s["title"], variable=var,
                                    bg=PANEL, fg=TEXT, selectcolor=PANEL)
                cb.pack(anchor="w")
                sec_vars.append((s["id"], var))

            self.check_vars.append(sec_vars)

            ttk.Button(frame, text="Remove",
                       command=lambda idx=index: self.remove_pause(idx)).grid(
                row=len(labels)+1, column=0, columnspan=2, pady=5
            )

        bf = tk.Frame(self, bg=BG)
        bf.pack(fill="x", padx=10, pady=5)

        ttk.Button(bf, text="+ Add pause", command=self.add_pause).pack(side="left", padx=5)
        ttk.Button(bf, text="Save", command=self.save_all).pack(side="right", padx=5)

    def add_pause(self):
        self.simulator.config["pauses"].append({
            "name": f"Pause {len(self.simulator.config['pauses'])+1}",
            "start_time": "10:00",
            "duration_min": 15,
            "affected_sections": [s["id"] for s in self.simulator.config["sections"][:2]],
            "hole_size": 5
        })
        save_config(self.simulator.config)
        self.build_pauses()

    def remove_pause(self, index):
        if len(self.simulator.config["pauses"]) <= 1:
            if not messagebox.askyesno("Confirm", "This is the last pause. Remove anyway?"):
                return
        del self.simulator.config["pauses"][index]
        save_config(self.simulator.config)
        self.build_pauses()

    def save_all(self):
        try:
            for index, p in enumerate(self.simulator.config["pauses"]):
                p["name"] = self.entries[f"pause.{index}.name"].get()
                p["start_time"] = self.entries[f"pause.{index}.start_time"].get()

                if not is_valid_time(p["start_time"]):
                    raise ValueError(f"Invalid time for pause {index+1}: {p['start_time']}")

                p["duration_min"] = int(self.entries[f"pause.{index}.duration_min"].get())
                p["hole_size"] = int(self.entries[f"pause.{index}.hole_size"].get())

                ids = []
                for sid, var in self.check_vars[index]:
                    if var.get():
                        ids.append(sid)
                p["affected_sections"] = ids

            save_config(self.simulator.config)
            self.simulator.load_pauses()
            self.refresh_callback()

        except ValueError as ve:
            messagebox.showerror("Error", str(ve))


# Time configuration window
class TimeConfigWindow(tk.Toplevel):
    def __init__(self, parent, simulator, refresh_callback):
        super().__init__(parent)
        self.simulator, self.refresh_callback = simulator, refresh_callback
        self.title("Configuration - Time")
        self.geometry("400x260")
        self.configure(bg=BG)
        make_modal(self, parent)

        f = tk.Frame(self, bg=BG)
        f.pack(fill="both", expand=True, padx=10, pady=10)

        factory = self.simulator.config["factory"]

        # Start time
        tk.Label(f, text="Start time (HH:MM)", bg=BG, fg=TEXT).grid(row=0, column=0, sticky="w", pady=2)
        self.start_entry = tk.Entry(f)
        self.start_entry.insert(0, factory.get("start_time", "06:00"))
        self.start_entry.grid(row=0, column=1, pady=2, sticky="w")

        # End time
        tk.Label(f, text="End time (HH:MM)", bg=BG, fg=TEXT).grid(row=1, column=0, sticky="w", pady=2)
        self.end_entry = tk.Entry(f)
        self.end_entry.insert(0, factory.get("end_time", "16:00"))
        self.end_entry.grid(row=1, column=1, pady=2, sticky="w")

        # Max cycle time
        tk.Label(f, text="Max cycle time (min)", bg=BG, fg=TEXT).grid(row=2, column=0, sticky="w", pady=2)
        self.limit_entry = tk.Entry(f)
        self.limit_entry.insert(0, str(factory.get("max_cycle_time_min", 60)))
        self.limit_entry.grid(row=2, column=1, pady=2, sticky="w")

        # Starvation
        tk.Label(f, text="Starvation threshold (min)", bg=BG, fg=TEXT).grid(row=3, column=0, sticky="w", pady=2)
        self.starv_entry = tk.Entry(f)
        self.starv_entry.insert(0, str(factory.get("starvation_threshold_min", 5)))
        self.starv_entry.grid(row=3, column=1, pady=2, sticky="w")

        ttk.Button(f, text="Save", command=self.save_all).grid(row=4, column=0, columnspan=2, pady=10)

    def save_all(self):
        try:
            start = self.start_entry.get()
            end = self.end_entry.get()

            if not is_valid_time(start):
                raise ValueError(f"Invalid start time: {start}")
            if not is_valid_time(end):
                raise ValueError(f"Invalid end time: {end}")

            limit = int(self.limit_entry.get())
            starv = int(self.starv_entry.get())

            f = self.simulator.config["factory"]
            f["start_time"] = start
            f["end_time"] = end
            f["max_cycle_time_min"] = limit
            f["starvation_threshold_min"] = starv

            save_config(self.simulator.config)

            # Update start/stop time
            self.simulator.start_time_str = f["start_time"]
            self.simulator.end_time_str = f["end_time"]
            self.simulator.start_time_sec = self.simulator.time_str_to_sec(self.simulator.start_time_str)
            self.simulator.end_time_sec = self.simulator.time_str_to_sec(self.simulator.end_time_str)

            if self.simulator.end_time_sec <= self.simulator.start_time_sec:
                self.simulator.end_time_sec += 24 * 3600

            self.simulator.starvation_threshold_sec = starv * 60

            self.refresh_callback()

        except ValueError as ve:
            messagebox.showerror("Error!", str(ve))
