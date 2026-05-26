import sys
import os
import json
import tempfile

sys.path.insert(0, os.getcwd())

from default import DEFAULT_CONFIG
from shared import save_config, set_current_project_file
from models import Unit, Slot, Section
from simulator import Simulator

def test_function(func, *args, **kwargs):
    try:
        result = func(*args, **kwargs)
        print(f"{func.__name__}: Reviewed and OK!")
        return True
    except Exception as e:
        print(f"{func.__name__}: ERROR! {str(e)}")
        return False

def test_shared_functions():
    print("\n--- Testing shared.py ---")
    test_config = {"test": "value"}
    with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as tmp:
        test_file = tmp.name
    test_function(save_config, test_config, test_file)
    if os.path.exists(test_file):
        os.remove(test_file)
    test_function(set_current_project_file, "test_config.json")

def test_models_functions():
    print("\n--- Testing models.py ---")
    unit = Unit(uid=1, start_time=0.0)
    print("Unit: Reviewed and OK!")
    slot = Slot()
    print("Slot: Reviewed and OK!")
    section_config = {
        "id": 1,
        "title": "Test Section",
        "length": 5,
        "step_time": 60,
        "temp_sensitivity": 1.0,
        "buffer_limit": 2,
        "color": "#4CAF50",
        "earliest_start": "06:00",
        "pause_mode": "hole_size"
    }
    section = Section(section_config)
    print("Section: Reviewed and OK!")

def test_simulator_functions():
    print("\n--- Testing simulator.py ---")
    simulator = Simulator(DEFAULT_CONFIG)
    test_function(simulator.reset_state)
    test_function(simulator.reset)
    test_function(simulator.time_str_to_sec, "10:30")
    test_function(simulator.current_abs_time)
    test_function(simulator.current_clock)
    test_function(simulator.load_sections)
    test_function(simulator.load_pauses)
    test_function(simulator.active_pauses)
    test_function(simulator.section_in_pause, 1)
    test_function(simulator.wip)
    test_function(simulator.traffic_color)
    test_function(simulator.add_unit)
    test_function(simulator.add_hole)
    test_function(simulator.move_section, 0)
    test_function(simulator.update_prediction)
    test_function(simulator.update_starvation)
    test_function(simulator.tick)

if __name__ == "__main__":
    test_shared_functions()
    test_models_functions()
    test_simulator_functions()
