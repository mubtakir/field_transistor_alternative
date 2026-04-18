# User Guide: FTA Virtual Laboratory v1.0
## Comprehensive Guide for Researchers and Engineers

This guide provides step-by-step instructions for utilizing the **FTA Virtual Laboratory** for advanced semiconductor R&D.

---

## 1. Quick Start: The GUI Control Center
The easiest way to interact with the laboratory is through the web-based **Control Center**.

### How to Launch:
1. Open a terminal in the project root.
2. Run: `python fta_lab/gui/server.py`
3. Open your browser to: `http://localhost:8000`

### Dashboard Features:
- **Geometry Sliders**: Adjust device length, width, and gap (nm) in real-time.
- **Run Simulation**: Triggers the underlying physics engines to calculate IV characteristics.
- **Live Plotting**: View the Drain Current (Id) vs. Gate Voltage (Vg) curve instantly.
- **Material Status**: View the properties of current active materials (Copper, SiO2, Mu-Metal).

---

## 2. Advanced Research: Python API
For custom simulations and bulk analysis, use the Python API.

### The Lab Manager
The `FTALaboratory` class handles configuration and session management.
```python
from fta_lab.lab_manager import FTALaboratory
lab = FTALaboratory()
```

### Creating Devices
Instantiate a specific architecture (e.g., `u_plate`):
```python
device = lab.create_device('u_plate', geometry={'length': 100e-6, 'gap': 5e-9})
```

---

## 3. Logic Gate Simulation (Phase 7)
The laboratory supports modular logic gate modeling.

### NOT Gate Example:
```python
from fta_lab.device_models.logic_gates import FTANotGate
gate = FTANotGate({'length': 100e-6, 'gap': 5e-9}, V_DD=5.0)
result = gate.solve(V_in=5.0) # Simulate a 'High' input
print(f"Logic Output: {result['logic_out']}")
```

### AND/OR Gates:
Use `FTAAndGate` and `FTAOrGate` from the same module to test complex logic functions.

---

## 4. Physics Engine Customization
The laboratory is built on a **Tiered Architecture**:
1. **Tier 1 (Physics Engines)**: Found in `physics_engine/`. Includes Laplace, WKB, FDTD, and Thermal solvers.
2. **Tier 2 (Device Models)**: Found in `device_models/`. Orchestrates physics solvers to model a functional device.
3. **Tier 3 (Analyzers)**: Found in `analyzers/`. High-level tools for IV and AC frequency response.

### Steps to Add a New Engine:
1. Create your solver in `physics_engine/my_new_solver.py`.
2. Add the export to `physics_engine/__init__.py`.
3. Import and use it in your device model classes.

---

## 5. Configuration (config.yaml)
Modify `config.yaml` to change:
- **Default Resolution**: Accuracy of the FDM solvers.
- **Material Properties**: Conductivity, Permittivity, and Permeability.
- **Hardware Profile**: Toggle between **CPU** and **GPU (Taichi)** execution.

---
© 2026 FTA Virtual Laboratory Research Group | Author: Basel Yahya Abdullah
