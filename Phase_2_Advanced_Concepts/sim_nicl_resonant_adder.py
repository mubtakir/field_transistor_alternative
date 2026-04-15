import numpy as np
import matplotlib.pyplot as plt

def sim_resonant_adder():
    """
    Simulates a 1-bit Adder using Resonant Frequency Shifts.
    """
    freqs = np.linspace(100e3, 1000e3, 5000)
    
    # Base Parameters
    l = 100e-6
    c_base = 200e-12
    delta_c = 100e-12 # Shift per '1' input
    
    def get_response(num_inputs):
        c_eff = c_base + num_inputs * delta_c
        res_f = 1 / (2 * np.pi * np.sqrt(l * c_eff))
        q = 50
        gain = 1 / np.sqrt(1 + (q * (freqs/res_f - res_f/freqs))**2)
        return res_f, gain

    # 4 Scenarios: 0+0, 1+0, 0+1, 1+1
    f0, g00 = get_response(0) # [0+0]
    f1, g10 = get_response(1) # [1+0] or [0+1]
    f2, g11 = get_response(2) # [1+1]
    
    # Logic Decoding (Threshold detection at specific bands)
    # Band S (Sum): Detects f1
    # Band C (Carry): Detects f2
    
    plt.figure(figsize=(12, 8))
    plt.plot(freqs/1e3, g00, label='Input [0+0]: No Shift', color='gray', alpha=0.5)
    plt.plot(freqs/1e3, g10, label='Input [1+0]: Shift to f1 (SUM=1)', color='blue', lw=2)
    plt.plot(freqs/1e3, g11, label='Input [1+1]: Shift to f2 (CARRY=1)', color='red', lw=2)
    
    # Highlight detection zones
    plt.axvspan(f1/1e3 - 5, f1/1e3 + 5, color='blue', alpha=0.1, label='SUM Detection Zone')
    plt.axvspan(f2/1e3 - 5, f2/1e3 + 5, color='red', alpha=0.1, label='CARRY Detection Zone')
    
    plt.title("FTA Phase 2: 1-Bit Resonant Logic Adder")
    plt.xlabel("Frequency (kHz)")
    plt.ylabel("Output Magnitude")
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    plt.savefig(r'C:\Users\allmy\Desktop\aaa\field_transistor_alternative\Phase_2_Advanced_Concepts\nicl_resonant_adder.png')
    print("[+] Resonant adder graph generated: Phase_2_Advanced_Concepts/nicl_resonant_adder.png")
    
    # Printed Verification
    print(f"Base Freq (0+0): {f0/1e3:.1f} kHz")
    print(f"Sum Freq  (1+0): {f1/1e3:.1f} kHz")
    print(f"Carry Freq(1+1): {f2/1e3:.1f} kHz")

if __name__ == "__main__":
    sim_resonant_adder()
