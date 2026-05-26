# main.py
# Main screen with GUI for FlowDraft Light Production Simulator

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os, copy
from shared import BG, PANEL, TEXT, GREEN, YELLOW, RED, GRAY, save_config, set_current_project_file, CURRENT_PROJECT_FILE
from default import DEFAULT_CONFIG
from simulator import Simulator
from gui_windows import SectionConfigWindow, PauseConfigWindow, TimeConfigWindow
from stats_window import StatsWindow
import json
from json import JSONDecodeError


def migrate_config(config):
    config.setdefault("factory", {})
    f = config["factory"]
    f.setdefault("start_time", "06:00"); f.setdefault("end_time", "16:00")
    if "max_cycle_time_min" not in f:
        f["max_cycle_time_min"] = max(1, int(f.get("max_cycle_time_sec", 3600) // 60))
    f.setdefault("tick_ms", 100); f.pop("max_cycle_time_sec", None)
    config.setdefault("visual", {})
    config["visual"].setdefault("cell_size", 42); config["visual"].setdefault("font_size", 10)
    config.setdefault("sections", []); config.setdefault("pauses", [])
    for s in config["sections"]:
        s.setdefault("pause_mode", "hole_size")
    return config

def load_config(file_path=None):
    path = file_path or CURRENT_PROJECT_FILE
    if not os.path.exists(path):
        save_config(DEFAULT_CONFIG, path)
    try:
        with open(path, "r") as f:
            config = json.load(f)
    except (JSONDecodeError, ValueError):
        try:
            bak = path + ".bak"
            if os.path.exists(path):
                os.replace(path, bak)
        except Exception:
            pass
        save_config(DEFAULT_CONFIG, path)
        config = copy.deepcopy(DEFAULT_CONFIG)
    return migrate_config(config)


class Application(tk.Frame):
    def __init__(self, master, simulator):
        super().__init__(master)
        self.master, self.simulator = master, simulator
        self.running = False
        self.stopped = False
        self.configure(bg=BG); self.pack(fill="both", expand=True)
        self.speed_var = tk.StringVar(value="1.0x")
        self.time_limit_var = tk.StringVar(value=str(self.simulator.config["factory"].get("max_cycle_time_min", 60)))
        self.build()

    def build(self):
        top = tk.Frame(self, bg=PANEL); top.pack(fill="x")
        self.btn_new = ttk.Button(top, text="New", command=self.new_proj); self.btn_new.pack(side="left", padx=5, pady=5)
        self.btn_load = ttk.Button(top, text="Load", command=self.load_proj); self.btn_load.pack(side="left", padx=5, pady=5)
        self.btn_save = ttk.Button(top, text="Save", command=self.save_proj); self.btn_save.pack(side="left", padx=5, pady=5)
        self.btn_saveas = ttk.Button(top, text="Save As", command=self.save_as_proj); self.btn_saveas.pack(side="left", padx=5, pady=5)
        self.btn_start = ttk.Button(top, text="Start", command=self.toggle_start_pause); self.btn_start.pack(side="left", padx=5, pady=5)
        self.btn_reset = ttk.Button(top, text="Reset", command=self.reset); self.btn_reset.pack(side="left", padx=5, pady=5)
        self.btn_sections = ttk.Button(top, text="Sections", command=self.open_sec); self.btn_sections.pack(side="left", padx=5, pady=5)
        self.btn_pauses = ttk.Button(top, text="Pauses", command=self.open_pau); self.btn_pauses.pack(side="left", padx=5, pady=5)
        self.btn_time = ttk.Button(top, text="Time Configurations", command=self.open_time); self.btn_time.pack(side="left", padx=5, pady=5)
        self.btn_stats = ttk.Button(top, text="Statistics", command=lambda: StatsWindow(self, self.simulator)); self.btn_stats.pack(side="left", padx=5, pady=5)

        sb = ttk.Combobox(top, textvariable=self.speed_var, values=["0.5x", "1.0x", "2.0x", "4.0x"], width=5, state="readonly")
        sb.pack(side="right", padx=5); sb.bind("<<ComboboxSelected>>", self.change_speed)
        ttk.Label(top, text="Speed:", background=PANEL, foreground=TEXT).pack(side="right", padx=5)

        self.canvas_container = tk.Frame(self)
        self.canvas_container.pack(fill="both", expand=True)

        self.canvas = tk.Canvas(self.canvas_container, bg=BG, highlightthickness=0)
        self.canvas.pack(side="left", fill="both", expand=True)

        self.vsb = ttk.Scrollbar(self.canvas_container, orient="vertical", command=self.canvas.yview)
        self.vsb.pack(side="right", fill="y")
        self.canvas.configure(yscrollcommand=self.vsb.set)

        self.hsb = ttk.Scrollbar(self, orient="horizontal", command=self.canvas.xview)
        self.hsb.pack(fill="x")
        self.canvas.configure(xscrollcommand=self.hsb.set)

        self.update_gui()

    def change_speed(self, e=None):
        self.simulator.speed_factor = float(self.speed_var.get().replace("x", ""))

    def open_sec(self): SectionConfigWindow(self.master, self.simulator, self.on_config_changed)
    def open_pau(self): PauseConfigWindow(self.master, self.simulator, self.on_config_changed)
    def open_time(self): TimeConfigWindow(self.master, self.simulator, self.on_config_changed)

    def on_config_changed(self):
        self.time_limit_var.set(str(self.simulator.config["factory"].get("max_cycle_time_min", 60)))
        self.update_gui()

    def toggle_start_pause(self):
        if self.stopped:
            messagebox.showinfo("Stopped", "Simulation has been stopped.")
            return
        self.running = not self.running
        if self.running:
            self.btn_start.config(text="Pause")
            self.simulate()
        else:
            self.btn_start.config(text="Start")

    def stop_full(self):
        self.running = False
        self.stopped = True
        self.btn_start.config(text="Start")

    def reset(self):
        self.running = False
        self.stopped = False
        self.btn_start.config(text="Start")
        self.simulator.reset()
        self.update_gui()

    def simulate(self):
        if self.running:
            if not self.simulator.tick():
                self.running = False
                self.btn_start.config(text="Start")
                messagebox.showinfo("End", "Simulation finished.")
                return
            self.update_gui()
            delay = max(10, int(self.simulator.config["factory"]["tick_ms"] / self.simulator.speed_factor))
            self.after(delay, self.simulate)

    def save_proj(self):
        try:
            path = save_config(self.simulator.config)
            messagebox.showinfo("Saved", f"Project saved to {os.path.abspath(path)}")
        except Exception as e:
            messagebox.showerror("Save error", f"Could not save project: {e}")

    def save_as_proj(self):
        path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON", "*.json")])
        if not path:
            return
        try:
            save_config(self.simulator.config, path, update_current=True)
            set_current_project_file(path)
            self.master.title(f"Production Simulator - {os.path.basename(path)}")
            messagebox.showinfo("Saved", f"Project saved to {os.path.abspath(path)}")
        except Exception as e:
            messagebox.showerror("Save error", f"Could not save project: {e}")

    def load_proj(self):
        path = filedialog.askopenfilename(filetypes=[("JSON", "*.json")])
        if path:
            self.simulator.config = load_config(path)
            set_current_project_file(path)
            self.master.title(f"FlowDraft Light Production Simulator - {os.path.basename(path)}")
            self.simulator.__init__(self.simulator.config)
            self.update_gui()

    def new_proj(self):
        self.simulator.config = copy.deepcopy(DEFAULT_CONFIG)
        self.simulator.__init__(self.simulator.config)
        self.update_gui()

    def draw_unit(self, x, y, size, unit):
        if unit.is_hole: color, text = "#111111", "GAP"
        else:
            age = self.simulator.time - unit.start_time
            color = RED if age >= 3600 else YELLOW if age >= 3000 else GREEN
            text = f"U{unit.uid}\n{int(age)//60}m"
        self.canvas.create_rectangle(x, y, x+size, y+size, fill=color, outline="#666666")
        self.canvas.create_text(x+size/2, y+size/2, text=text, fill="white", font=("Consolas", 9, "bold"))

    def update_gui(self):
        self.canvas.delete("all")
        limit = self.simulator.config["factory"].get("max_cycle_time_min", 60)
        self.canvas.create_text(1200, 10, text=f"Limit: {limit} min", fill="white", font=("Segoe UI", 12, "bold"))
        self.canvas.create_text(1200, 40, text=self.simulator.current_clock(), fill="white", font=("Consolas", 22, "bold"))
        self.canvas.create_rectangle(20, 20, 250, 80, fill=self.simulator.traffic_color(), outline="")
        self.canvas.create_text(135, 50, text=f"WIP: {self.simulator.wip()}", fill="white", font=("Segoe UI", 18, "bold"))
        if self.simulator.section3_starved: self.canvas.create_text(850, 40, text="SECTION 3 STARVING", fill=RED, font=("Segoe UI", 18, "bold"))

        y, size = 120, self.simulator.config["visual"]["cell_size"]
        for sec in self.simulator.sections:
            self.canvas.create_text(60, y-20, text=sec.title, fill=TEXT, anchor="w", font=("Segoe UI", 14, "bold"))
            x = 60
            for slot in sec.slots:
                if slot.unit: self.draw_unit(x, y, size, slot.unit)
                else: self.canvas.create_rectangle(x, y, x+size, y+size, fill=GRAY, outline="#666666")
                x += size + 6
            y += 100

        bbox = self.canvas.bbox("all")
        if bbox:
            self.canvas.configure(scrollregion=bbox)
        else:
            self.canvas.configure(scrollregion=(0, 0, 1600, 900))

def main():
    config = load_config()
    sim = Simulator(config)
    root = tk.Tk(); root.title("FlowDraft Light Production Simulator"); root.geometry("1600x900")
    Application(root, sim); root.mainloop()

if __name__ == "__main__": main()
