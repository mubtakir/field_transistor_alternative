import numpy as np
import matplotlib.pyplot as plt

def sim_ufe_amplification():
    """
    Simulates the Universal Field Element (UFE) "Collapse Trigger" mechanism.
    Inspired by Basel Yahya Abdullah's theory of tense depleted regions.
    
    1. A 'Power Chamber' is biased at 99.5% of its dielectric breakdown limit (Critical Tension).
    2. A tiny 'Inductive Trigger' current generates a local B-field that nudges the 
       dielectric into a 'Avalanche Collapse' (Switching ON).
    """
    
    time = np.linspace(0, 50, 1000) # 50ns window
    
    # --- POWER CHAMBER PARAMETERS ---
    v_bias = 0.995 # Near-critical tension (99.5%)
    noise = np.random.normal(0, 0.001, len(time)) 
    power_tension = v_bias + noise
    
    # --- TRIGGER CONTROL ---
    # A small pulse at T=20ns
    trigger_pulse = np.zeros(len(time))
    trigger_pulse[400:450] = 0.01 # 1% additional inductive nudge
    
    # --- THE COLLAPSE PHYSICS ---
    # Breakdown happens when Total Energy (Tension + Trigger) > Critical (1.0)
    total_stress = power_tension + trigger_pulse
    is_collapsed = total_stress > 1.0
    
    # Power Output: Zero before collapse, High current after collapse
    power_output = np.zeros(len(time))
    breakdown_indices = np.where(is_collapsed)[0]
    
    if len(breakdown_indices) > 0:
        first_break = breakdown_indices[0]
        # Simulate exponential avalanche rise and sustained conduction
        power_output[first_break:] = 10.0 * (1 - np.exp(-(time[first_break:] - time[first_break])/2.0))
    
    # --- VISUALIZATION ---
    plt.figure(figsize=(12, 8))
    
    plt.subplot(2, 1, 1)
    plt.plot(time, power_tension, label='Chamber Tension (Quiescent)', color='blue', alpha=0.5)
    plt.plot(time, total_stress, label='Total Stress (Inductive Nudge)', color='red', linewidth=2)
    plt.axhline(y=1.0, color='black', linestyle='--', label='Breakdown Threshold')
    plt.title("UFE Mechanism: Field-Collapse Triggering (Basel's Tense Region)", fontsize=14)
    plt.ylabel("Normalized Energy Density")
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    plt.subplot(2, 1, 2)
    plt.fill_between(time, trigger_pulse * 10, label='Control Input (uA)', color='cyan', alpha=0.4)
    plt.plot(time, power_output, label='Power Output (A)', color='darkred', linewidth=3)
    plt.title("Gain Analysis: Trigger Input vs. Conductive Output")
    plt.ylabel("Magnitude")
    plt.xlabel("Time (nanoseconds)")
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # Gain Calculation
    input_energy = np.sum(trigger_pulse)
    output_energy = np.sum(power_output)
    gain_factor = output_energy / input_energy if input_energy > 0 else 0
    
    plt.tight_layout()
    output_path = r'C:\Users\allmy\Desktop\aaa\field_transistor_alternative\Phase_6_Universal_Field_Element\ufe_trigger_results.png'
    plt.savefig(output_path)
    plt.close()
    
    print(f"[+] UFE Simulation Complete.")
    print(f"[+] Trigger Status: {'SUCCESSFUL COLLAPSE' if gain_factor > 0 else 'STABLE'}")
    print(f"[+] Calculated Gain: {gain_factor:.2f}x")
    print(f"[+] Result file: {output_path}")

if __name__ == "__main__":
    sim_ufe_amplification()
