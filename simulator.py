# simulator.py
# Main functions for the simulator

from models import Section, Unit
from shared import RED, YELLOW, GREEN


class Simulator:
    def __init__(self, config):
        self.config = config
        self.speed_factor = 1.0 # Init standard speed for avoiding crashes
        self.sections = []
        self.pauses = []

        # Time window
        self.start_time_str = config["factory"].get("start_time", "06:00")
        self.end_time_str = config["factory"].get("end_time", "16:00")
        self.start_time_sec = self.time_str_to_sec(self.start_time_str)
        self.end_time_sec = self.time_str_to_sec(self.end_time_str)
        if self.end_time_sec <= self.start_time_sec:
            self.end_time_sec += 24 * 3600

        # Starvation
        self.starvation_threshold_sec = config["factory"].get("starvation_threshold_min", 5) * 60

        # Load config
        self.load_sections()
        self.load_pauses()

        # Reset state
        self.reset_state()

    # Reset
    def reset_state(self):
        self.time = 0.0
        self.unit_counter = 0
        self.finished = []
        self.predicted_late = 0

        # Global starvation
        self.section3_starved = False
        self.section3_starved_duration = 0.0

        # Inflow timer
        self.last_inflow_time = 0.0

    def reset(self):
        self.reset_state()
        self.load_sections()
        self.load_pauses()

    # Helpers for timekeeping
    def time_str_to_sec(self, time_str: str) -> int:
        h, m = map(int, time_str.split(":"))
        return h * 3600 + m * 60

    def current_abs_time(self):
        return self.start_time_sec + self.time

    def current_clock(self):
        total = self.start_time_sec + int(self.time)
        h = (total // 3600) % 24
        m = (total % 3600) // 60
        s = total % 60
        return f"{h:02}:{m:02}:{s:02}"

    # Load config
    def load_sections(self):
        self.sections.clear()
        for cfg in self.config["sections"]:
            sec = Section(cfg)
            sec.earliest_start_sec = self.time_str_to_sec(sec.earliest_start_str)
            self.sections.append(sec)

    def load_pauses(self):
        self.pauses.clear()
        for p in self.config.get("pauses", []):
            start = self.time_str_to_sec(p["start_time"])
            dur = p.get("duration_min", 0) * 60
            self.pauses.append({
                "name": p.get("name", ""),
                "start_sec": start,
                "end_sec": start + dur,
                "affected_sections": p.get("affected_sections", []),
                "hole_size": p.get("hole_size", 0),
                "holes_created": 0,
                "was_active": False
            })

    # Pause helpers
    def active_pauses(self):
        now = self.current_abs_time()
        return [p for p in self.pauses if p["start_sec"] <= now < p["end_sec"]]

    def section_in_pause(self, sec_id):
        now = self.current_abs_time()
        for p in self.pauses:
            if p["start_sec"] <= now < p["end_sec"]:
                if sec_id in p["affected_sections"]:
                    return True
        return False

    # Work In Progress // Formatting
    def wip(self):
        return sum(
            1 for sec in self.sections for slot in sec.slots
            if slot.unit and not slot.unit.is_hole
        )

    def traffic_color(self):
        w = self.wip()
        f = self.config["factory"]
        if w >= f["critical_wip"]:
            return RED
        if w >= f["warning_wip"]:
            return YELLOW
        return GREEN

    # Inflow
    def add_unit(self):
        first = self.sections[0]
        if first.slots[0].unit is None:
            first.slots[0].unit = Unit(self.unit_counter, self.time)
            self.unit_counter += 1
            return True
        return False

    def add_hole(self):
        first = self.sections[0]
        if first.slots[0].unit is None:
            first.slots[0].unit = Unit(-1, self.time, is_hole=True)
            return True
        return False

    # Logics for moving
    def move_section(self, idx):
        sec = self.sections[idx]
        now_abs = self.current_abs_time()

        if now_abs < sec.earliest_start_sec:
            return

        step = max(1, int(sec.step_time * sec.temp_sensitivity))
        if (self.time - sec.last_move) < step:
            return

        # Internal shift
        for i in range(sec.length - 1, 0, -1):
            if sec.slots[i - 1].unit and not sec.slots[i].unit:
                sec.slots[i].unit = sec.slots[i - 1].unit
                sec.slots[i - 1].unit = None

        # Output
        last = sec.slots[-1].unit
        if last:
            if idx + 1 < len(self.sections):
                nxt = self.sections[idx + 1]
                if nxt.slots[0].unit is None:
                    nxt.slots[0].unit = last
                    sec.slots[-1].unit = None
            else:
                last.finished_time = self.time
                self.finished.append(last)
                sec.slots[-1].unit = None

        sec.last_move = self.time

    # Prediction
    def update_prediction(self):
        self.predicted_late = 0
        limit = self.config["factory"]["max_cycle_time_min"] * 60

        for i, sec in enumerate(self.sections):
            step = max(1, int(sec.step_time * sec.temp_sensitivity))
            for j, slot in enumerate(sec.slots):
                if slot.unit and not slot.unit.is_hole:
                    rem = (sec.length - 1 - j) * step
                    for nxt in self.sections[i + 1:]:
                        rem += nxt.length * max(1, int(nxt.step_time * nxt.temp_sensitivity))
                    if (self.time - slot.unit.start_time + rem) > limit:
                        self.predicted_late += 1

    # Starvation, section 3
    def update_starvation(self):
        now_abs = self.current_abs_time()

        starving = False
        for sec in self.sections:
            if now_abs < sec.earliest_start_sec:
                continue
            if not self.section_in_pause(sec.id) and sec.slots[0].unit is None:
                starving = True
                break

        if starving:
            self.section3_starved_duration += self.speed_factor
        else:
            self.section3_starved_duration = 0.0

        self.section3_starved = (
            self.section3_starved_duration >= self.starvation_threshold_sec
        )

    # Ticker
    def tick(self):
        if self.start_time_sec + self.time >= self.end_time_sec:
            return False

        self.time += self.speed_factor
        now_abs = self.current_abs_time()

        # Pause
        for p in self.pauses:
            active = p["start_sec"] <= now_abs < p["end_sec"]
            if active and not p["was_active"]:
                p["was_active"] = True
                p["holes_created"] = 0
                self.last_inflow_time = self.time - 10
            elif not active and p["was_active"]:
                p["was_active"] = False

        # Move sections
        for i in range(len(self.sections)):
            self.move_section(i)

        self.update_prediction()
        self.update_starvation()

        # Inflow
        if (self.time - self.last_inflow_time) >= 10:
            active = self.active_pauses()
            if active:
                # Duration mode?
                duration_mode = any(
                    sec.pause_mode == "duration"
                    for p in active
                    for sec in self.sections
                    if sec.id in p["affected_sections"]
                )

                if duration_mode:
                    self.add_hole()
                else:
                    for p in active:
                        if p["holes_created"] < p["hole_size"]:
                            if self.add_hole():
                                p["holes_created"] += 1
            else:
                self.add_unit()

            self.last_inflow_time = self.time

        return True
