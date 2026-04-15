import numpy as np
import matplotlib.pyplot as plt

def simulate_nested_threshold(v_internal_range, v_external_applied):
    """
    Simulates a 4-plate nested capacitor system.
    P1-P2 (Internal), P3-P4 (External).
    Models the 'Potential Blocking' effect.
    """
    # Threshold behavior: V_out_detectable = max(0, V_ext_applied - V_int_bias * coefficient)
    k = 1.2 # Coupling coefficient (Sensitivity)
    
    v_detectable = np.maximum(0, v_external_applied - v_internal_range * k)
    
    return v_detectable

# Setup ranges
v_int = np.linspace(0, 5, 100) # Internal bias from 0 to 5V
v_ext_fixed = 3.0 # Fixed external pressure of 3V

v_res = simulate_nested_threshold(v_int, v_ext_fixed)

plt.figure(figsize=(10, 6))
plt.plot(v_int, v_res, label='Detected External Voltage', color='blue', lw=2)
plt.axvline(v_ext_fixed/1.2, color='red', linestyle='--', label='Threshold Point (Barrier)')
plt.title("Nested Capacitor: Threshold Blocking Effect")
plt.xlabel("Internal Bias (V_in)")
plt.ylabel("Detectable Output (V_out)")
plt.grid(True, alpha=0.3)
plt.legend()
plt.savefig('threshold_effect.png')
print("[+] Simulation complete. threshold_effect.png generated.")

# Analyze Sensitivity (dR/dC like behavior)
# Let's model Capacitance C = epsilon * A / d
# If a small change in dielectric resistance R_d changes effectively 'd' or 'epsilon'
resistance = np.linspace(1, 100, 100)
capacitance = 1000 / (resistance**0.5) # Non-linear sensitivity

plt.figure(figsize=(10, 6))
plt.plot(resistance, capacitance, color='green', lw=2)
plt.title("R-C Sensitivity: Small R change -> Large C change")
plt.xlabel("Dielectric Resistance (Ω)")
plt.ylabel("Capacitance (pF)")
plt.grid(True, alpha=0.3)
plt.savefig('rc_sensitivity.png')
print("[+] Sensitivity analysis complete. rc_sensitivity.png generated.")
