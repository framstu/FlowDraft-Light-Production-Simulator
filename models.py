# models.py
# Configurations for production model

from dataclasses import dataclass
from typing import Optional
from shared import GREEN

@dataclass
class Unit:
    uid: int
    start_time: float
    is_hole: bool = False
    finished_time: Optional[float] = None

class Slot:
    def __init__(self):
        self.unit = None

class Section:
    def __init__(self, config):
        self.id = config.get("id", 0)
        self.title = config.get("title", "Section")
        self.length = config.get("length", 5)
        self.step_time = config.get("step_time", 120)
        self.temp_sensitivity = config.get("temp_sensitivity", 1.0)
        self.buffer_limit = config.get("buffer_limit", 2)
        self.color = config.get("color", GREEN)
        self.earliest_start_str = config.get("earliest_start", "06:00")
        self.earliest_start_sec = 0
        self.last_move = 0.0
        self.blocked_time = 0.0
        self.slots = [Slot() for _ in range(self.length)]
        # Pause mode: "hole_size" or "duration"
        self.pause_mode = config.get("pause_mode", "hole_size")
