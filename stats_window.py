# stats_window.py
# Full stand alone file for creating and configurating window for statistics and charts on completed sessions

import os
import json
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from shared import BG, PANEL, TEXT, GRAY, CURRENT_PROJECT_FILE
from datetime import datetime

class StatsWindow(tk.Toplevel):
    def __init__(self, parent, simulator):
        super().__init__(parent)
        self.simulator = simulator
        self.title("Statistics")
        self.geometry("900x600")
        self.configure(bg=BG)

        self.projects_dir = os.path.join(os.path.dirname(os.path.abspath(CURRENT_PROJECT_FILE)), "Projects")
        if not os.path.isdir(self.projects_dir):
            self.projects_dir = os.path.dirname(os.path.abspath(CURRENT_PROJECT_FILE))

        self.files = self._list_project_files()
        self.current_index = self._find_current_index()

        self.header_label = tk.Label(self, text="", bg=BG, fg=TEXT, font=("Segoe UI", 12, "bold"))
        self.header_label.pack(pady=5)

        top_frame = tk.Frame(self, bg=BG)
        top_frame.pack(fill="x", padx=10, pady=5)

        ttk.Button(top_frame, text="⟨ Older", command=self.show_older).pack(side="left", padx=5)
        ttk.Button(top_frame, text="Newer ⟩", command=self.show_newer).pack(side="left", padx=5)
        ttk.Button(top_frame, text="Export CSV", command=self.export_csv).pack(side="right", padx=5)

        self.canvas_frame = tk.Frame(self, bg=BG)
        self.canvas_frame.pack(fill="x", padx=10, pady=5)

        self.canvas = tk.Canvas(self.canvas_frame, bg=BG, highlightthickness=0, height=250)
        self.canvas.pack(side="left", fill="both", expand=True)

        self.canvas_vsb = ttk.Scrollbar(self.canvas_frame, orient="vertical", command=self.canvas.yview)
        self.canvas_vsb.pack(side="right", fill="y")
        self.canvas.configure(yscrollcommand=self.canvas_vsb.set)

        self.canvas_hsb = ttk.Scrollbar(self, orient="horizontal", command=self.canvas.xview)
        self.canvas_hsb.pack(fill="x")
        self.canvas.configure(xscrollcommand=self.canvas_hsb.set)

        self.tree_frame = tk.Frame(self)
        self.tree_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.tree = ttk.Treeview(self.tree_frame, columns=("uid", "start", "end", "total"), show="headings")
        self.tree.heading("uid", text="Unit")
        self.tree.heading("start", text="Start time (s)")
        self.tree.heading("end", text="End time (s)")
        self.tree.heading("total", text="Total time (s)")
        self.tree.pack(side="left", fill="both", expand=True)

        self.tree_vsb = ttk.Scrollbar(self.tree_frame, orient="vertical", command=self.tree.yview)
        self.tree_vsb.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=self.tree_vsb.set)

        self.tree_hsb = ttk.Scrollbar(self, orient="horizontal", command=self.tree.xview)
        self.tree_hsb.pack(fill="x")
        self.tree.configure(xscrollcommand=self.tree_hsb.set)

        self.style = ttk.Style(self)
        self.style.configure("Treeview", background=BG, fieldbackground=BG, foreground=TEXT)

        self.load_from_current_run()
        self.update_view()

    def _list_project_files(self):
        files = []
        for name in os.listdir(self.projects_dir):
            if name.lower().endswith(".json"):
                files.append(os.path.join(self.projects_dir, name))
        files.sort(key=lambda p: os.path.getmtime(p))
        return files

    def _find_current_index(self):
        cur = os.path.abspath(CURRENT_PROJECT_FILE)
        for i, f in enumerate(self.files):
            if os.path.abspath(f) == cur:
                return i
        return len(self.files) - 1 if self.files else -1

    def load_from_current_run(self):
        if self.simulator.finished:
            stats = []
            for u in self.simulator.finished:
                if u.is_hole or u.finished_time is None:
                    continue
                stats.append({
                    "uid": u.uid,
                    "start_time": u.start_time,
                    "finished_time": u.finished_time,
                    "total_time": u.finished_time - u.start_time
                })
            self.simulator.config["last_run_stats"] = {
                "timestamp": datetime.now().isoformat(timespec="seconds"),
                "units": stats
            }

    def load_stats_from_file(self, path):
        try:
            with open(path, "r") as f:
                cfg = json.load(f)
        except Exception as e:
            messagebox.showerror("Error", f"Could not load {path}: {e}")
            return None
        return cfg.get("last_run_stats")

    def update_view(self):
        self.tree.delete(*self.tree.get_children())
        self.canvas.delete("all")

        if self.current_index < 0 or not self.files:
            self.header_label.config(text="No project files found.")
            return

        path = self.files[self.current_index]
        stats = self.load_stats_from_file(path)
        if not stats or not stats.get("units"):
            self.header_label.config(text=f"{os.path.basename(path)} – no stats saved yet.")
            return

        ts = stats.get("timestamp", "")
        try:
            dt = datetime.fromisoformat(ts)
            ts_str = dt.strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            ts_str = ts

        self.header_label.config(text=f"{os.path.basename(path)} – Last run: {ts_str}")

        units = stats["units"]
        for u in units:
            self.tree.insert("", "end", values=(
                u["uid"],
                f"{u['start_time']:.1f}",
                f"{u['finished_time']:.1f}",
                f"{u['total_time']:.1f}"
            ))

        times = [u["total_time"] for u in units]
        if not times:
            return
        w = int(self.canvas.winfo_width() or 800)
        h = int(self.canvas["height"])
        min_t = min(times)
        max_t = max(times)
        if max_t == min_t:
            max_t += 1.0

        margin = 40
        x0, y0 = margin, margin
        x1, y1 = w - margin, h - margin

        self.canvas.create_rectangle(x0, y0, x1, y1, outline=GRAY)
        self.canvas.configure(scrollregion=(0, 0, w, h))

        n = len(times)
        if n == 1:
            xs = [ (x0 + x1) / 2 ]
        else:
            xs = [x0 + i * (x1 - x0) / (n - 1) for i in range(n)]
        ys = [y1 - (t - min_t) / (max_t - min_t) * (y1 - y0) for t in times]

        for i in range(1, n):
            self.canvas.create_line(xs[i-1], ys[i-1], xs[i], ys[i], fill="#4CAF50", width=2)
        for i in range(n):
            self.canvas.create_oval(xs[i]-3, ys[i]-3, xs[i]+3, ys[i]+3, fill="#4CAF50", outline="")

        self.canvas.create_text(x0, y0-10, text="Cycle time (s)", fill=TEXT, anchor="w")
        self.canvas.create_text(x1, y1+10, text="Units", fill=TEXT, anchor="e")

    def show_older(self):
        if self.current_index > 0:
            self.current_index -= 1
            self.update_view()

    def show_newer(self):
        if self.current_index < len(self.files) - 1:
            self.current_index += 1
            self.update_view()

    def export_csv(self):
        if self.current_index < 0 or not self.files:
            messagebox.showinfo("Export", "No project selected.")
            return
        path = self.files[self.current_index]
        stats = self.load_stats_from_file(path)
        if not stats or not stats.get("units"):
            messagebox.showinfo("Export", "No stats to export for this project.")
            return

        save_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv")],
            title="Export stats to CSV"
        )
        if not save_path:
            return

        try:
            import csv
            with open(save_path, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["uid", "start_time", "finished_time", "total_time"])
                for u in stats["units"]:
                    writer.writerow([u["uid"], u["start_time"], u["finished_time"], u["total_time"]])
            messagebox.showinfo("Export", f"Stats exported to {save_path}")
        except Exception as e:
            messagebox.showerror("Export error", f"Could not export CSV: {e}")
