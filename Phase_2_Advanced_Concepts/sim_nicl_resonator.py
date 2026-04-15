import numpy as np
import matplotlib.pyplot as plt

def sim_nicl_resonator():
    """
    Simulates a Nested Inductive-Capacitive Loop (NICL).
    Models loop L, mutual M, and inter-loop C.
    """
    freqs = np.logspace(3, 7, 1000) # 1kHz to 10MHz
    
    # Loop Parameters
    l1 = 10e-6 # 10 uH
    l2 = 20e-6 # 20 uH
    c_inter = 100e-12 # 100 pF (Capacitance between nested loops)
    
    # Mutual Induction (high coupling in nested config)
    k = 0.9
    m = k * np.sqrt(l1 * l2)
    
    # Impedance calculation for the coupled system
    # Z = RL + jWL + 1/(jWC)
    # We look at the transfer function (Voltage on Loop 2 / Input on Loop 1)
    w = 2 * np.pi * freqs
    z1 = 1j * w * l1
    z2 = 1j * w * l2 + 1/(1j * w * c_inter)
    zm = 1j * w * m
    
    # Transfer Function H(s) = Zm / Ztot
    h_s = np.abs(zm / (z1 + z2 + zm))
    
    # Logic State: What if we "Trigger" the system?
    # Increasing local charge (C) shifts the resonance.
    c_triggered = 300e-12
    z2_trig = 1j * w * l2 + 1/(1j * w * c_triggered)
    h_s_trig = np.abs(zm / (z1 + z2_trig + zm))
    
    # Visualization
    plt.figure(figsize=(10, 6))
    plt.semilogx(freqs, h_s, label='Logical State 0 (Base C)', color='blue', lw=2)
    plt.semilogx(freqs, h_s_trig, label='Logical State 1 (Triggered C)', color='red', lw=2, linestyle='--')
    
    plt.title("NICL: Resonant Frequency Shift Logic")
    plt.xlabel("Frequency (Hz)")
    plt.ylabel("Signal Gain |H(f)|")
    plt.grid(True, which='both', alpha=0.3)
    plt.axvline(freqs[np.argmax(h_s)], color='blue', alpha=0.3)
    plt.axvline(freqs[np.argmax(h_s_trig)], color='red', alpha=0.3)
    plt.legend()
    
    plt.savefig(r'C:\Users\allmy\Desktop\aaa\field_transistor_alternative\Phase_2_Advanced_Concepts\nicl_resonant_logic.png')
    print("[+] NICL resonant logic graph generated: Phase_2_Advanced_Concepts/nicl_resonant_logic.png")

if __name__ == "__main__":
    sim_nicl_resonator()
