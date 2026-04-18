# oos_lab/analysis/thermionic_fta_demo.py

import os
import sys
import numpy as np
import matplotlib.pyplot as plt

# Ensure oos_lab is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from oos_lab.physics.thermionic_fta_solver import ThermionicFTASolver

def run_simulation_demo():
    print("Starting Thermionic-FTA Hybrid Simulation Demo...")
    
    # Configuration
    config = {
        'gap_distance': 50e-9,      # 50 nm
        'work_function': 2.7,       # LaB6 (Low work function)
        'heater_resistance': 100.0, # Ohms (Higher R for lower P)
        'thermal_resistance': 5000.0, # K/W (Realistic micro-isolation)
        'shielding_factor': 0.0076,
    }
    
    solver = ThermionicFTASolver(config)
    
    # 1. Sweep Heater Voltage (0 to 10V)
    V_heater_sweep = np.linspace(0, 10, 100)
    V_ds_fixed = 10.0
    V_gate_fixed = 0.0
    
    I_totals = []
    I_th_only = []
    I_fn_only = []
    temps = []
    p_coolings = []
    
    for vh in V_heater_sweep:
        j_tot, breakdown = solver.solve_steady_state(V_ds_fixed, V_gate_fixed, vh)
        I_totals.append(breakdown['I_total'] * 1e6) # µA
        I_th_only.append(breakdown['J_thermionic'] * solver.emitter_area * 1e6)
        I_fn_only.append(breakdown['J_FN'] * solver.emitter_area * 1e6)
        temps.append(breakdown['T_emitter'])
        p_coolings.append(breakdown['P_cooling'] * 1e6) # µW
        
    # 2. Plotting
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 10), sharex=True)
    
    # Subplot 1: Currents
    ax1.plot(V_heater_sweep, I_totals, 'k-', linewidth=3, label='Total Current (Hybrid)')
    ax1.plot(V_heater_sweep, I_th_only, 'r--', label='Thermionic Component')
    ax1.plot(V_heater_sweep, I_fn_only, 'b:', label='Tunneling (FN) Component')
    ax1.set_ylabel('Current (µA)', fontsize=12)
    ax1.set_title(f'Thermionic-FTA Hybrid Emission vs Heater Voltage\n(Work Function = {config["work_function"]} eV, Vds = {V_ds_fixed}V)', fontsize=14)
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    ax1.set_yscale('log')
    ax1.set_ylim(bottom=1e-6)
    
    # Subplot 2: Temperature and Cooling Power
    ax2_twin = ax2.twinx()
    lns1 = ax2.plot(V_heater_sweep, temps, 'g-', label='Emitter Temperature (K)')
    lns2 = ax2_twin.plot(V_heater_sweep, p_coolings, 'm-', label='Quantum Cooling (µW)')
    
    ax2.set_xlabel('Heater Voltage (V)', fontsize=12)
    ax2.set_ylabel('Temperature (K)', color='g', fontsize=12)
    ax2_twin.set_ylabel('Cooling Power (µW)', color='m', fontsize=12)
    
    # Combine legends
    lns = lns1 + lns2
    labs = [l.get_label() for l in lns]
    ax2.legend(lns, labs, loc='upper left')
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    # Save results
    save_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../field_transistor_alternative/phase2_foundations/images/sim_thermionic_hybrid_demo.png'))
    plt.savefig(save_path)
    print(f"Simulation complete. Plot saved to: {save_path}")
    
    # Print insights
    print("\nSimulation Insights:")
    print(f"- Max Temperature attained: {np.nanmax(temps):.1f} K")
    
    # Find mode transition (Tunneling to Thermionic)
    transitions = np.where(np.array(I_th_only) > np.array(I_fn_only))[0]
    if len(transitions) > 0:
        v_trans = V_heater_sweep[transitions[0]]
        print(f"- Mode Transition: Transition from Tunneling to Thermionic dominance occurs at V_heater ~ {v_trans:.2f} V")
    else:
        print("- Mode Transition: Tunneling remains dominant in this range (or vice versa).")
        
    print(f"- Quantum Cooling: At max emission, the device sheds {np.nanmax(p_coolings):.2f} µW through electron evaporation.")

if __name__ == "__main__":
    run_simulation_demo()
