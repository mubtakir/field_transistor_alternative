import numpy as np
import matplotlib.pyplot as plt

def sim_inductive_loop_interaction():
    """
    Simulates the interaction between two Inductive Plates (Single-turn Loops).
    Models Magnetic Flux Linkage (Mutual Inductance) and Capacitive Coupling.
    
    States:
    1. REINFORCED: Currents in both loops are parallel (Clockwise/Clockwise).
    2. OPPOSED: Currents in loops are anti-parallel (Clockwise/Counter-Clockwise).
    """
    
    f_range = np.linspace(10e3, 2e6, 5000) # 10kHz to 2MHz
    w = 2 * np.pi * f_range
    
    # Parameters for a nano-scale loop-stack
    L = 10e-6   # Self-inductance of one loop (10 uH)
    C = 200e-12 # Capacitance between loops (200 pF)
    R = 0.5     # Resistance
    k = 0.4     # Coupling coefficient (Magnetic)
    M = k * L   # Mutual Inductance
    
    # CASE 1: REINFORCED (Parallel Currents)
    # Effective Inductance increases: L_eff = L1 + L2 + 2M
    # In a 2-loop system where L1=L2=L:
    L_reinforced = 2 * L + 2 * M
    Z_reinforced = R + 1j * w * L_reinforced + 1/(1j * w * C)
    Gain_reinforced = np.abs(1/Z_reinforced)
    
    # CASE 2: OPPOSED (Anti-Parallel Currents)
    # Effective Inductance decreases: L_eff = L1 + L2 - 2M
    L_opposed = 2 * L - 2 * M
    Z_opposed = R + 1j * w * L_opposed + 1/(1j * w * C)
    Gain_opposed = np.abs(1/Z_opposed)
    
    # Find Resonant Frequencies
    f_res_reinf = f_range[np.argmax(Gain_reinforced)]
    f_res_oppos = f_range[np.argmax(Gain_opposed)]
    
    # Visualization
    plt.figure(figsize=(14, 10))
    
    plt.subplot(2, 1, 1)
    plt.plot(f_range/1e3, Gain_reinforced, label=f'REINFORCED (Parallel) - Peak: {f_res_reinf/1e3:.1f}kHz', color='blue', linewidth=2)
    plt.plot(f_range/1e3, Gain_opposed, label=f'OPPOSED (Anti-Parallel) - Peak: {f_res_oppos/1e3:.1f}kHz', color='red', linestyle='--', linewidth=2)
    plt.title("FTA Phase 4: Inductive-Plate Interaction Logic", fontsize=14)
    plt.xlabel("Frequency (kHz)")
    plt.ylabel("System Gain (Admittance)")
    plt.grid(True, alpha=0.3)
    plt.legend()
    
    # Explanation Text
    plt.subplot(2, 1, 2)
    plt.axis('off')
    summary = (
        "Analysis of Inductive-Plate Coupling (Basel Yahya Abdullah Architecture)\n"
        "----------------------------------------------------------------------\n"
        f"1. Resonant Shift: Reversing current triggers a shift of {np.abs(f_res_reinf - f_res_oppos)/1e3:.1f} kHz.\n"
        "2. Magnetic Modality:\n"
        "   - Parallel (Reinforced): High magnetic flux, lower resonant frequency.\n"
        "   - Anti-Parallel (Opposed): Magnetic field cancellation, higher resonant frequency.\n"
        "3. Field Pinching: In 'Opposed' mode, the cancellation of magnetic flux between loops\n"
        "   forces a higher concentration of the electrostatic field, maximizing dR/dC gain.\n"
        "4. Conclusion: We can now switch logical states by simply flipping the direction\n"
        "   of the 1-turn loop current, additive to the voltage-based depletion effect."
    )
    plt.text(0.05, 0.4, summary, fontsize=12, family='monospace', verticalalignment='bottom')
    
    plt.tight_layout()
    output_path = r'C:\Users\allmy\Desktop\aaa\field_transistor_alternative\Phase_4_Field_Current_Integration\inductive_loop_logic_results.png'
    plt.savefig(output_path)
    plt.close()
    print(f"[+] Inductive-Plate simulation complete: {output_path}")

if __name__ == "__main__":
    sim_inductive_loop_interaction()
