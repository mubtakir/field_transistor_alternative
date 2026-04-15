import numpy as np
import matplotlib.pyplot as plt

def sim_resonant_memory():
    """
    Simulates a Resonant Memory Cell (Phase-Locked Latch).
    State is stored as a persistent frequency oscillation.
    """
    time = np.linspace(0, 50, 5000) # Microseconds
    dt = (time[1] - time[0]) / 1e6
    
    # State frequencies
    f0 = 200e3 # 200kHz (Logic 0)
    f1 = 500e3 # 500kHz (Logic 1)
    
    # Write Pulse indices
    write_start = 1500
    write_end = 2000
    
    # Latch Output Transition
    latch_output = np.zeros_like(time)
    latch_output[:write_start] = np.sin(2 * np.pi * f0 * (time[:write_start]/1e6))
    latch_output[write_start:write_end] = 1.5 * np.sin(2 * np.pi * f1 * (time[write_start:write_end]/1e6))
    latch_output[write_end:] = np.sin(2 * np.pi * f1 * (time[write_end:]/1e6))
    
    plt.figure(figsize=(12, 10))
    
    # Time Domain
    plt.subplot(2, 1, 1)
    plt.plot(time, latch_output, color='blue', alpha=0.7)
    plt.axvspan(time[write_start], time[write_end], color='red', alpha=0.2, label='WRITE PULSE (f1)')
    plt.title("NICL Resonant Memory: Phase-Locked State Storage")
    plt.ylabel("Signal Amplitude")
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # Spectral Analysis
    plt.subplot(2, 1, 2)
    # Extract segments
    seg0 = latch_output[:write_start]
    seg1 = latch_output[write_end:]
    
    # FFT 0
    fft0 = np.abs(np.fft.rfft(seg0))
    freqs0 = np.fft.rfftfreq(len(seg0), d=dt)
    
    # FFT 1
    fft1 = np.abs(np.fft.rfft(seg1))
    freqs1 = np.fft.rfftfreq(len(seg1), d=dt)
    
    plt.plot(freqs0/1e3, fft0/max(fft0), label='Initial State (READ 0)', color='gray')
    plt.plot(freqs1/1e3, fft1/max(fft1), label='Final State (READ 1)', color='green', lw=2)
    
    plt.xlim(0, 1000)
    plt.title("Memory Read: Frequency Profile Transition")
    plt.xlabel("Frequency (kHz)")
    plt.ylabel("Normalized Magnitude")
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(r'C:\Users\allmy\Desktop\aaa\field_transistor_alternative\Phase_2_Advanced_Concepts\nicl_resonant_memory.png')
    print("[+] Resonant memory graph generated: Phase_2_Advanced_Concepts/nicl_resonant_memory.png")

if __name__ == "__main__":
    sim_resonant_memory()
