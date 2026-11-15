# FlowDraft Light Production Simulator v1.0


## Overview

FlowDraft Light is a lightweight production line simulator designed for small to medium-sized manufacturing environments. It provides a practical way to model, test and optimize production flows through a simple and configurable interface.
The project also serves as an experiment in LLM-assisted GUI programming for building tools for production planning, analysis and visualization.
Originally developed as a personal tool, this version includes only the essential components required for practical use and modification, with sensitive or proprietary elements removed.

## Why?

Visualizing how small disruptions ripple through a production line shouldn't require a massive software suite or weeks of setup
— especially when a straightforward visual tool makes it much easier for teams to see what is happening and agree on changes.
FlowDraft Light started as a personal tool to quickly sketch out production flows, test break schedules, and see where queues build up.
It is intentionally kept lightweight and easy to modify—serving both as a practical planning aid for small-to-medium setups and a playground for experimenting with LLM-assisted GUI development.

## Purpose

The simulator allows users to:

- Model production sections with adjustable parameters such as length, step time, and buffer limits.
- Simulate the movement of units through each section, accounting for real-world constraints like pauses and temperature sensitivity (v1.0; currently only framework included).
- Monitor key metrics such as work-in-progress (WIP), cycle times, and congestion levels.
- Visualize the production process in a clear, color-coded GUI for immediate feedback.

FlowDraft Light is intended for engineers, planners, tinkerers and managers who need a straightforward tool to test configurations and identify potential inefficiencies before implementation.



## Core Features

### 1. Section Configuration

Each production line section can be customized with the following parameters:

- **Length**: Number of slots in the section.
- **Step Time**: Time (in seconds) required for a unit to move from one slot to the next.
- **Buffer Limit**: Maximum number of units allowed in the buffer before congestion is flagged.
- **Color Coding**: Visual indicators for section status (green for normal, yellow for caution, red for critical).

*Example*: A section with a step time of 120 seconds and a buffer limit of 2 could be configured to simulate a specific stage of the production process.



### 2. Pause Management

The simulator supports both scheduled and dynamic pauses:

- **Scheduled Pauses**: Predefined breaks, shift changes, or maintenance windows.
- **Dynamic Pauses**: Triggered by conditions such as buffer overflow or temperature thresholds.
- **Pause Modes**:
  - **Hole Size**: Pauses introduce gaps ("holes") in the production line.
  - **Time-Based**: Pauses halt the section for a specified duration.

*Example*: A scheduled pause from 12:00 to 13:00 can be applied to specific sections to simulate a lunch break, either by empty slots or as a duration-based break.



### 3. Real-Time Simulation

- **Tick-Based Engine**: The simulation advances in configurable time increments, mimicking real-time production.
- **Unit Tracking**: Each unit is assigned a unique ID, start time, and finish time. Holes (empty slots) represent disruptions, which is particularly critical in industries such as food production.
- **Traffic Light System**: Provides possibilities for visual feedback on section status:
  - **Green**: Normal operation.
  - **Yellow**: Approaching buffer capacity.
  - **Red**: Congestion or pause detected.

*Example*: If a section’s buffer reaches its limit, the traffic light turns red, and a congestion warning is logged.



### 4. Predictive Analytics

The simulator includes basic predictive capabilities:

- **Starvation Detection**: Identifies sections at risk of running out of units.
- **Cycle Time Estimation**: Calculates the total time for a unit to pass through the line.
- **Bottleneck Identification**: Highlights sections that may slow down the entire process.

*Example*: The system may indicate that a section will starve in 10 minutes if an upstream pause is not resolved.



### 5. Visual Feedback

- **GUI Dashboard**: Intuitive interface for configuring sections, pauses, and factory settings.
- **Live Stats Window**: Displays real-time metrics such as WIP, cycle times, and traffic status.
- **Color-Coded Slots**: Visual representation of unit movement, holes, and pauses.

*Example*: A red slot indicates a paused unit, while a yellow slot signals a section nearing its buffer limit.



### 6. Factory-Wide Settings

Global parameters can be adjusted, including:

- **Operating Hours**: Define factory start and end times.
- **Max Cycle Time**: Set efficiency targets for the production line.
- **Visual Customization**: Adjust GUI elements such as cell size and font size.



## Technical Structure

### Simulator Engine (`simulator.py`)

- Manages the state of units and holes in each section.
- Handles time conversions (e.g., "10:30" to seconds) for more precise calculations.
- Updates predictions, starvation warnings and traffic lights with each simulation tick.

### Model Layer (`models.py`)

- **Unit**: Represents a product or part moving through the line.
- **Slot**: A position in a section that can hold a unit or a hole.
- **Section**: A segment of the production line with defined rules and status.

### GUI (`main.py`, `gui_windows.py`, `stats_window.py`)

- **Main Window**: Provides an overview of all sections and simulation controls.
- **Configuration Windows**: Allow editing of section, pause, and factory settings.
- **Stats Window**: Displays real-time performance metrics.



## Getting Started

### Installation

FlowDraft Light is written in Python and uses the `tkinter` library. No additional dependencies are required. To run:

```bash
python main.py
```

### Configuration

1. Load a configuration file (default: `config.json`).
2. Define production sections and their parameters via the GUI.
3. Set pauses for breaks or disruptions.
4. Start the simulation to observe the production flow.

### Example Configuration (`config.json`)

```json
{
  "factory": {
    "start_time": "06:00",
    "end_time": "16:00",
    "max_cycle_time_min": 60,
    "tick_ms": 100
  },
  "visual": {
    "cell_size": 42,
    "font_size": 10
  },
  "sections": [
    {
      "id": 1,
      "title": "Assembly",
      "length": 5,
      "step_time": 120,
      "temp_sensitivity": 1.0,
      "buffer_limit": 2,
      "color": "#4CAF50",
      "earliest_start": "06:00",
      "pause_mode": "hole_size"
    }
  ],
  "pauses": [
    {
      "id": 1,
      "title": "Lunch Break",
      "start_time": "12:00",
      "end_time": "13:00",
      "affected_sections": [1, 2]
    }
  ]
}
```



## Use Cases

### 1. Bottleneck Analysis

*Scenario*: Production output is below target.  
*Action*: Use FlowDraft Light to identify sections causing congestion and adjust step times or buffer limits.

### 2. Shift Planning

*Scenario*: Introducing a new shift.  
*Action*: Simulate the shift schedule to predict its impact on cycle times and identify potential issues.

### 3. Environmental Constraints

*Scenario*: A section is sensitive to temperature.  
*Action*: Configure temperature sensitivity and simulate different conditions to optimize production.

### 4. Training

*Scenario*: Training new staff on production line dynamics.  
*Action*: Use the simulator to demonstrate how pauses and buffer limits affect the overall process.



## Project Context

FlowDraft Light is an experiment in using LLM-supported GUI programming to create a practical, adaptable tool for production environments. The goal is to provide a simple yet effective simulator that can be modified and extended to fit specific needs. The codebase is designed to be clear and modular, making it accessible for further development or integration into larger systems.



## Known Quirks

- Some features were intentionally removed to keep the project lightweight and publicly shareable. FlowDraft Light is not an officially deployed industrial tool, but rather an experimental simulation platform. Future updates will refine and extend its capabilities.
- The GUI currently has a few minor quirks in edge cases. I am continuing work on improving stability and making the interface more deterministic.



## Future Developments

 - Refactored variants of the original functions
 - Support for parallel production lines
 - Enhanced temperature and starvation settings
 - Data export for external analysis
 - Integration with optimization algorithms
 - Enhanced visualization options
 - Redesigned GUI for optimized tkinter usage
 - Web-based or compiled application version



## Project Status
FlowDraft Light is an actively evolving tool and will continue to receive updates and additional releases over time.



## Contributing

Contributions are welcome in the form of bug reports, feature suggestions, or code improvements. The project is open to modifications and extensions to better serve production planning needs.



## License

This project is licensed under the MIT-License. Users are free to use, modify, and distribute the software as needed.



## Author

Core ideas, architecture, simulation logic, and most of the implementation were created by Matias Back (matias.back@gmail.com).
Some GUI components and feature extensions were developed using LLM-assisted programming workflows.


