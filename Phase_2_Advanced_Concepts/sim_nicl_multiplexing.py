import numpy as np
import matplotlib.pyplot as plt

def sim_nicl_multiplexing():
    """
    Simulates a 3-loop NICL with two independent resonant logic channels.
    """
    freqs = np.logspace(4, 7, 2000) # 10kHz to 10MHz
    w = 2 * np.pi * freqs
    
    # Loop Parameters
    # Channel 1 (LF): Large loops, High L
    l1 = 100e-6
    l2 = 150e-6
    c12_base = 200e-12
    
    # Channel 2 (HF): Small internal loops, Low L
    l3 = 10e-6
    c23_base = 50e-12
    
    # Base states
    def get_gain(c12, c23):
        # Mutuals
        m12 = 0.9 * np.sqrt(l1 * l2)
        m23 = 0.9 * np.sqrt(l2 * l3)
        
        # Simple stacked model of resonances
        # Channel 1 resonance frequency
        res1 = 1 / (2 * np.pi * np.sqrt(l1 * c12)) 
        # Channel 2 resonance frequency
        res2 = 1 / (2 * np.pi * np.sqrt(l3 * c23))
        
        # Lorentzian-like signal response
        q = 10 
        gain1 = 1 / np.sqrt(1 + (q * (freqs/res1 - res1/freqs))**2)
        gain2 = 0.8 / np.sqrt(1 + (q * (freqs/res2 - res2/freqs))**2)
        
        return gain1 + gain2

    # Scenarios
    base_gain = get_gain(c12_base, c23_base)
    ch1_shifted = get_gain(c12_base * 4, c23_base) # Trigger Channel 1
    ch2_shifted = get_gain(c12_base, c23_base * 4) # Trigger Channel 2
    both_shifted = get_gain(c12_base * 4, c23_base * 4) # Trigger Both
    
    # Visualization
    plt.figure(figsize=(12, 10))
    
    plt.subplot(2, 1, 1)
    plt.semilogx(freqs, base_gain, label='State [0, 0] (Base)', color='blue', lw=2)
    plt.semilogx(freqs, ch1_shifted, label='State [1, 0] (CH1 Shift)', color='red', linestyle='--')
    plt.title("NICL Multiplexing: Independent Channel Control")
    plt.ylabel("Signal Gain")
    plt.legend()
    plt.grid(True, which='both', alpha=0.3)
    
    plt.subplot(2, 1, 2)
    plt.semilogx(freqs, base_gain, label='State [0, 0] (Base)', color='blue', lw=2)
    plt.semilogx(freqs, ch2_shifted, label='State [0, 1] (CH2 Shift)', color='green', linestyle='--')
    plt.semilogx(freqs, both_shifted, label='State [1, 1] (BOTH Shift)', color='black', linestyle='--')
    plt.xlabel("Frequency (Hz)")
    plt.ylabel("Signal Gain")
    plt.legend()
    plt.grid(True, which='both', alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(r'C:\Users\allmy\Desktop\aaa\field_transistor_alternative\Phase_2_Advanced_Concepts\nicl_multiplexing.png')
    print("[+] NICL multiplexing graph generated: Phase_2_Advanced_Concepts/nicl_multiplexing.png")

if __name__ == "__main__":
    sim_nicl_multiplexing()
