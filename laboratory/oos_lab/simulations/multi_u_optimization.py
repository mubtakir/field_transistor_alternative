
import numpy as np
import os
import sys

# Ensure oos_lab package is in the path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from oos_lab.physics.quantum_tunneling import wkb_tunneling_current, poole_frenkel_current
from oos_lab.physics.magnetic_fields import plate_biot_savart
from oos_lab.constants import q_e

def simulate_multi_u(max_N=20, I_plate=0.5, dx=50e-9, lambda_decay=200e-9, d_gap=5e-9, V_ds=1.0, T=300.0):
    """
    Simulate the Multi-U (2D Array) magnetic quenching effect.
    
    Parameters:
    - max_N: Maximum number of U-plates in the array.
    - I_plate: Current through the U-plates (Amps).
    - dx: Spacing between plates (meters).
    - lambda_decay: Magnetic decay constant for distant plates (meters).
    - d_gap: Tunneling gap width (meters).
    - V_ds: Drain-Source voltage (Volts).
    - T: Temperature (Kelvin).
    """
    # Base magnetic field from one plate at the junction
    B0 = plate_biot_savart(I_plate)
    
    # E-field from V_ds
    E_field = V_ds / d_gap
    
    results = []
    
    print(f"{'N':<5} | {'B_total (T)':<12} | {'J_total (A/m^2)':<15}")
    print("-" * 40)
    
    for N in range(1, max_N + 1):
        # Calculate cumulative magnetic field with exponential decay
        # B_total = B0 * sum(exp(-i * dx / lambda))
        # This is a geometric series sum: B0 * (1 - r^N) / (1 - r) where r = exp(-dx/lambda)
        r = np.exp(-dx / lambda_decay)
        B_total = B0 * (1 - r**N) / (1 - r)
        
        # WKB Tunneling with Lorentz Quenching (Quantum effect)
        J_wkb = wkb_tunneling_current(E_field, B_field=B_total, d_gap=d_gap)
        
        # Lorentz Quenching (Classical bending effect)
        # B_crit: characteristic field for quenching (Tesla)
        B_crit = 0.5 
        quenching_factor = 1.0 / (1.0 + (B_total / B_crit)**2)
        
        # Poole-Frenkel for insulator defects
        J_pf = poole_frenkel_current(E_field, T=T)
        
        J_total = (J_wkb + J_pf) * quenching_factor
        
        results.append((N, B_total, J_total))
        print(f"{N:<5} | {B_total:<12.4f} | {J_total:<15.4e}")
        
    return results

if __name__ == "__main__":
    import matplotlib.pyplot as plt
    
    print("Running Multi-U Configuration Optimization...")
    data = simulate_multi_u()
    
    N_vals = [r[0] for r in data]
    B_vals = [r[1] for r in data]
    J_vals = [r[2] for r in data]
    
    # Normalizing J to witness the Quenching Factor
    J_norm = [j / J_vals[0] for j in J_vals]
    
    fig, ax1 = plt.subplots(figsize=(10, 6))
    
    color = 'tab:blue'
    ax1.set_xlabel('Number of Plates (N)')
    ax1.set_ylabel('Total Magnetic Field (Tesla)', color=color)
    ax1.plot(N_vals, B_vals, 'o-', color=color, label='B-Field (Tesla)')
    ax1.tick_params(axis='y', labelcolor=color)
    ax1.grid(True, linestyle='--', alpha=0.6)
    
    ax2 = ax1.twinx()
    color = 'tab:red'
    ax2.set_ylabel('Normalized Current Density (J/J_0)', color=color)
    ax2.plot(N_vals, J_norm, 's--', color=color, label='Quenching Factor')
    ax2.tick_params(axis='y', labelcolor=color)
    
    plt.title('Multi-U Configuration: Magnetic Accumulation & Current Quenching')
    fig.tight_layout()
    
    output_img = "multi_u_saturation_plot.png"
    plt.savefig(output_img)
    print(f"Saturation plot saved to: {output_img}")
    
    # Find Saturation Point (diminishing returns, e.g., < 1% improvement)
    for i in range(1, len(B_vals)):
        improvement = (B_vals[i] - B_vals[i-1]) / B_vals[i-1]
        if improvement < 0.01:
            print(f"\n>>> Saturation Point Reached at N = {i+1}")
            break
