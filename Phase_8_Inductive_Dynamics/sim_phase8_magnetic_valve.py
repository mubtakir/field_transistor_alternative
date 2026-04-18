import numpy as np
import matplotlib.pyplot as plt
import sys
import os

# Ensure laboratory is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'laboratory')))

import oos_lab.api as fta
from oos_lab.physics.quantum_tunneling import wkb_tunneling_current, fowler_nordheim_tfe
from oos_lab.constants import mu_0, q_e

def simulate_qmv():
    print("=" * 60)
    print(" PHASE 8: QUANTUM MAGNETIC VALVE (QMV) SIMULATION")
    print("=" * 60)
    
    # Geometry Specs
    d_gap = 2e-9  # 2nm gap for higher sensitivity
    area = 100e-6 * 10e-6 # 100um x 10um
    u_width = 20e-6
    
    # Range of Modulation Currents (through U-plate)
    i_mod_range = np.linspace(0, 0.1, 100) # 0 to 100mA
    
    # Bias Voltage between inner plates
    v_ds = 1.5 
    e_field = v_ds / d_gap
    
    j_output_tunnel = []
    j_output_thermal = []
    
    for i_mod in i_mod_range:
        # 1. Calculate B-field in the center of the U-plate
        r_eff = 1e-6 # Closer proximity to the U-plate center
        b_field = (mu_0 * i_mod) / (2 * np.pi * r_eff)
        
        # 2. Compute Tunneling Current (WKB) with magnetic quenching
        j_tunnel = wkb_tunneling_current(e_field, b_field, d_gap=d_gap, Phi_B_eV=1.2)
        
        # 3. Compute Thermal Emission (considering ohmic heating from i_mod as a grid effect)
        # T_grid = 300K + delta_T(i_mod)
        t_grid = 300 + (i_mod**2 * 5000) # Simple resistive heating model
        j_thermal = fowler_nordheim_tfe(e_field, T=t_grid, Phi_B_eV=1.2)
        
        j_output_tunnel.append(j_tunnel)
        j_output_thermal.append(j_thermal)
        
    j_total = np.array(j_output_tunnel) + np.array(j_output_thermal)
    i_total = j_total * area
    
    # Calculate Transconductance (gm = dI_out / dI_mod)
    gm = np.gradient(i_total, i_mod_range)
    
    print(f"Max Transconductance (gm): {np.max(np.abs(gm)):.4e} A/A")
    print(f"Quenching Factor (I_max / I_min): {np.max(i_total)/np.min(i_total):.2f}x")

    # Plotting
    plt.figure(figsize=(12, 6))
    
    plt.subplot(1, 2, 1)
    plt.plot(i_mod_range * 1000, i_total * 1e6, 'b-', linewidth=2, label='Total Output Current')
    plt.axvline(x=10, color='r', linestyle='--', alpha=0.5, label='Shutdown Threshold')
    plt.xlabel('Modulation Current I_mod (mA)')
    plt.ylabel('Output Current (uA)')
    plt.title('QMV Quench Curve (Magnetic Valve Effect)')
    plt.grid(True, alpha=0.3); plt.legend()
    
    plt.subplot(1, 2, 2)
    plt.plot(i_mod_range * 1000, np.abs(gm), 'g-', label='Transconductance (gm)')
    plt.xlabel('Modulation Current I_mod (mA)')
    plt.ylabel('gm (dI_out/dI_mod)')
    plt.title('Sensitivity Analysis')
    plt.grid(True, alpha=0.3); plt.legend()
    
    plt.tight_layout()
    image_path = 'assets/images1/fta_qmv_quench_curve.png'
    plt.savefig(image_path, dpi=150)
    print(f"\n-> Simulation Successful. Plot saved to {image_path}")

if __name__ == "__main__":
    simulate_qmv()
