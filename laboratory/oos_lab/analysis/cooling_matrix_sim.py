# oos_lab/analysis/cooling_matrix_sim.py

import os
import sys
import numpy as np
import matplotlib.pyplot as plt
from scipy.ndimage import gaussian_filter

# Ensure oos_lab is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from oos_lab.physics.thermionic_fta_solver import ThermionicFTASolver

def run_cooling_matrix_demo():
    print("Starting Quantum-Thermal Management System (QTMS) Matrix Simulation...")
    
    # Grid configuration
    grid_size = 20  # 20x20 micron grid for the chip area
    dx = 1e-6       # 1 micron per cell
    
    # Base chip temperature with a Hot Spot (e.g., a localized CPU core at 100% load)
    T_chip = np.ones((grid_size, grid_size)) * 340.0 # Start at 340 K (67 C)
    T_chip[7:13, 7:13] += 80.0  # Add a hot spot in the center (up to 420 K / 147 C)
    # Smooth the hot spot to simulate real heat diffusion in silicon
    T_chip = gaussian_filter(T_chip, sigma=1.5)
    
    T_initial = T_chip.copy()
    
    # Define Thermionic-FTA cells configuration
    config = {
        'gap_distance': 30e-9,      # 30 nm for higher FN/Thermionic efficiency
        'work_function': 2.1,       # Optimized low-work function emitter
        'heater_resistance': 100.0,
        'thermal_resistance': 1000.0,
        'emitter_area': 0.5e-12,    # 0.5 µm² per cell
    }
    solver = ThermionicFTASolver(config)
    
    # Active Cooling: Apply Vds/Vgate to extract electrons (and heat)
    V_ds_active = 5.0
    V_gate_active = 2.0 # Optimal shielding for high emission
    
    T_cooled = T_chip.copy()
    cool_map = np.zeros_like(T_chip)
    
    # Iterate through the grid
    for i in range(grid_size):
        for j in range(grid_size):
            # Only activate cells in high-temp areas (Autonomous Cooling Path)
            if T_cooled[i, j] > 360.0:
                # Set ambient as CURRENT local chip temp
                solver.T_ambient = T_cooled[i, j]
                
                # Run solver - we don't apply V_heater, the chip IS the heater!
                # Heat scavenging mode
                j_tot, breakdown = solver.solve_steady_state(V_ds_active, V_gate_active, 0)
                
                # Active cooling extraction (P_cooling is in Watts)
                # Convert Watts to Local Delta T reduction in this cell
                dt_reduction = breakdown['P_cooling'] * config['thermal_resistance']
                T_cooled[i, j] -= dt_reduction
                cool_map[i, j] = dt_reduction
                
    # Heat Map Visualization
    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(18, 5))
    
    im1 = ax1.imshow(T_initial, cmap='hot', interpolation='gaussian')
    ax1.set_title('Chip Temperature (Before QTMS)\n"Thermal Throttling Hazard"')
    fig.colorbar(im1, ax=ax1, label='Temp (K)')
    
    im2 = ax2.imshow(T_cooled, cmap='hot', interpolation='gaussian')
    ax2.set_title('Chip Temperature (With QTMS Matrix)\n"Active Scavenging Active"')
    fig.colorbar(im2, ax=ax2, label='Temp (K)')
    
    im3 = ax3.imshow(cool_map, cmap='viridis', interpolation='gaussian')
    ax3.set_title('Cooling Potency Map\n(Active Heat Extraction)')
    fig.colorbar(im3, ax=ax3, label='Delta T Reduction (K)')
    
    plt.tight_layout()
    
    # Save results
    save_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../field_transistor_alternative/phase2_foundations/images/sim_qtms_matrix_demo.png'))
    plt.savefig(save_path)
    print(f"Simulation complete. Heat Map saved to: {save_path}")
    
    # Insights
    print("\nSimulation Insights:")
    print(f"- Initial Peak Temperature: {np.max(T_initial):.1f} K")
    print(f"- Final Peak Temperature: {np.max(T_cooled):.1f} K")
    print(f"- Net Thermal Reduction: {np.max(T_initial) - np.max(T_cooled):.1f} K")
    print(f"- Cooling State: The matrix successfully converted thermal energy into {np.max(cool_map)*1e6/config['thermal_resistance']:.1f} µW of scavenged power per hotspot cell.")

if __name__ == "__main__":
    run_cooling_matrix_demo()
