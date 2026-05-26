# shared.py
# Shared variables and configurations

import json
import os

# Theme colors
BG = "#1E1E1E"
PANEL = "#2B2B2B"
TEXT = "#F2F2F2"
GREEN = "#43A047"
YELLOW = "#FDD835"
RED = "#E53935"
GRAY = "#444444"

CURRENT_PROJECT_FILE = "config.json" # Hard-coded; might be a good idea for several purposes to change this, preferred  like this only for my own purposes.

def save_config(config, file_path=None, update_current=False):

    # Save configuration to file_path (or CURRENT_PROJECT_FILE if None).
    # By default this function does NOT mutate the global CURRENT_PROJECT_FILE.
    # If update_current=True, the global CURRENT_PROJECT_FILE will be updated.
    # Returns the path written to.
   
    global CURRENT_PROJECT_FILE
    if file_path is None:
        file_path = CURRENT_PROJECT_FILE
    # Ensure directory exists
    os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
    with open(file_path, "w") as f:
        json.dump(config, f, indent=4)
    if update_current:
        CURRENT_PROJECT_FILE = file_path
    return file_path

def set_current_project_file(path):
    global CURRENT_PROJECT_FILE
    CURRENT_PROJECT_FILE = path
