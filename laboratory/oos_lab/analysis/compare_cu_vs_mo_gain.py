
import numpy as np
import matplotlib.pyplot as plt
import os
import sys

# Add the project root to path to import materials_library
sys.path.append('c:/Users/allmy/Desktop/oos')
from oos_lab.physics.materials_library import MATERIALS

def fowler_nordheim(E, phi, B_const=2.5e8):
    if E <= 0: return 0
    A = 1e-6
    return (A * E**2 / phi) * np.exp(-B_const * phi**1.5 / E)

def simulate_gain_comparison():
    # Parameters
    gap_300 = 5e-9  # 5 nm (More realistic for tunneling at low V)
    area = 1e-12
    R_load = 100e3   # 100k Ohm
    V_DD = 5.0
    V_gate = np.linspace(0.5, 4.0, 200)
    
    # Constants from materials_library (simplified B)
    # B for SiO2 is ~2.5e8 in our library, much lower than vacuum
    B_const = 5e8 
    
    # Temperatures
    T_ambient = 300
    T_hot = 400
    dT = T_hot - T_ambient
    
    # Materials Data
    # Copper (Cu) properties
    phi_cu = 4.5
    alpha_cu = 16.5e-6
    
    # Molybdenum (Mo) properties
    phi_mo = 4.6
    alpha_mo = 4.8e-6
    
    # Calculate Gaps at 400K (Simplified: gap decreases as plates expand)
    # L_eff is the effective expansion length, assume 10um
    L_eff = 10e-6 
    gap_cu_400 = gap_300 - (L_eff * alpha_cu * dT)
    gap_mo_400 = gap_300 - (L_eff * alpha_mo * dT)
    
    results = {}
    
    for label, phi, gap in [
        ("Cu @ 300K", phi_cu, gap_300),
        ("Cu @ 400K", phi_cu, gap_cu_400),
        ("Mo @ 300K", phi_mo, gap_300),
        ("Mo @ 400K", phi_mo, gap_mo_400)
    ]:
        I = []
        for Vg in V_gate:
            E = Vg / gap
            J = fowler_nordheim(E, phi, B_const=B_const)
            I.append(J * area)
        
        I = np.array(I)
        V_out = V_DD - I * R_load
        
        # Calculate Gain: dV_out / dVg
        gain = -np.gradient(V_out, V_gate)
        
        results[label] = {
            'V_gate': V_gate,
            'V_out': V_out,
            'gain': gain,
            'max_gain': np.max(gain),
            'gap_nm': gap * 1e9
        }

    # Plotting
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 7))
    
    colors = {'Cu @ 300K': '#ff7f0e', 'Cu @ 400K': '#d62728', 
              'Mo @ 300K': '#1f77b4', 'Mo @ 400K': '#2ca02c'}
    
    for label, data in results.items():
        ls = '-' if '400K' in label else '--'
        ax1.plot(data['V_gate'], data['V_out'], label=f"{label} (Gap: {data['gap_nm']:.1f}nm)", color=colors[label], linestyle=ls)
        ax2.plot(data['V_gate'], data['gain'], label=f"{label} (Max Gain: {data['max_gain']:.1f}x)", color=colors[label], linestyle=ls)
        
    ax1.set_title("V_out vs V_gate (Transfer Characteristic)")
    ax1.set_xlabel("V_gate (V)")
    ax1.set_ylabel("V_out (V)")
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    ax2.set_title("Voltage Gain (dV_out / dV_gate)")
    ax2.set_xlabel("V_gate (V)")
    ax2.set_ylabel("Gain (V/V)")
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plot_path = "c:/Users/allmy/Desktop/oos/oos_lab/analysis/mo_vs_cu_gain_comparison.png"
    plt.savefig(plot_path)
    print("\n" + "="*50)
    print("FTA Gain Stability Report: Copper vs Molybdenum")
    print("="*50)
    for label, data in results.items():
        print(f"{label:12} | Gap: {data['gap_nm']:.2f}nm | Max Gain: {data['max_gain']:.2f}x")
    print("="*50)
    
    return results

if __name__ == "__main__":
    simulate_gain_comparison()
