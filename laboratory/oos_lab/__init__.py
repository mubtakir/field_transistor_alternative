# OOS-Lab: Open-Source Physics Simulation Laboratory
"""
A unified, researcher-friendly physics simulation toolkit for
nano-scale electro-magneto-quantum device simulation.

DUAL-ENGINE ARCHITECTURE:
=========================

Engine 1: SciPy CPU (Design & Analysis)
  - solvers/    : FDM Laplace (C-matrix), ODE system (Radau)
  - physics/    : WKB tunneling, Biot-Savart, Spintronics TMR
  - devices/    : U-Plate 12D ODE model
  - analysis/   : AC sweep, Transient pulse, Power consumption

  Purpose: Fast analytical design, parameter sweeps, Bode plots.
  When to use: Initial device design, optimization, circuit analysis.

Engine 2: Taichi GPU (3D Visualization & EM)
  - gpu_engines/ : FDTD Maxwell, PIC particles, Electro-Thermal

  Purpose: Full 3D field simulation, particle transport, thermal validation.
  When to use: After geometry is finalized, for RF characterization,
               electron flow visualization, thermal hotspot detection.
  Requires: pip install taichi (optional dependency)

TYPICAL WORKFLOW:
  1. Design device geometry -> devices/u_plate.py
  2. Optimize parameters   -> analysis/ac_sweep.py, analysis/transient.py
  3. Validate RF behavior  -> gpu_engines/fdtd_maxwell.py
  4. Check thermal limits  -> gpu_engines/electro_thermal.py
  5. Visualize electrons   -> gpu_engines/pic_simulator.py
"""

# API Exports for OOS-Lab v1.1
from .devices.u_plate import UPlateDevice
from .fta_lab.device_models.natural_fta import NaturalFTA
from .physics.quantum_tunneling import wkb_tunneling_current, fowler_nordheim_tfe
from .solvers.fta_solver import FTASolver
from .analysis.fta_lab_bench import FTALabBench

from .api import simulate

__version__ = "1.1.0 Professional"
__author__ = "Basel Yahya Abdullah"
__all__ = [
    'UPlateDevice', 'NaturalFTA', 'FTASolver', 
    'FTALabBench', 'wkb_tunneling_current', 'fowler_nordheim_tfe',
    'simulate'
]
