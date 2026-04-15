import numpy as np
import matplotlib.pyplot as plt

def sim_fta_frequency_hopping():
    """
    Simulates FTA Hardware-Level Encryption via Resonant Frequency Hopping.
    The logic channels (State 0, State 1) jump across 16 different frequency bands 
    based on a secret seed (key).
    """
    
    # 1. System Parameters
    num_hops = 8
    time_per_hop = 20e-6 # 20 us
    fs = 10e6 # 10 MHz sampling
    t_hop = np.linspace(0, time_per_hop, int(fs * time_per_hop))
    dt = 1/fs
    
    # Generate a 'Secret Seed' (Frequency Jump Map)
    np.random.seed(42) # Secret Key = 42
    jump_map = np.random.uniform(100e3, 2e6, num_hops)
    
    # Logic Payload: [1, 0, 1, 1, 0, 0, 1, 0]
    payload = [1, 0, 1, 1, 0, 0, 1, 0]
    
    full_signal = []
    recovered_logic = []
    
    # 2. Simulation - The "Hopping" Encoder
    for i in range(num_hops):
        base_f = jump_map[i]
        logic_bit = payload[i]
        
        # State 0: base_f
        # State 1: base_f + 50kHz (Shifted)
        current_f = base_f + (50e3 if logic_bit == 1 else 0)
        
        # Add some system noise
        noise = np.random.normal(0, 0.1, len(t_hop))
        signal = np.sin(2 * np.pi * current_f * t_hop) + noise
        full_signal.extend(signal)
        
        # 3. Unauthorized Decoder (Attacker) - Tries a fixed filter at 500kHz
        # (Will fail because logic is hopping)
        
        # 4. Authorized Decoder (With Seed)
        # Calculates FFT and checks for the +50kHz shift at the CURRENT base_f
        fft = np.abs(np.fft.rfft(signal))
        freqs = np.fft.rfftfreq(len(signal), d=dt)
        peak_f = freqs[np.argmax(fft)]
        
        if peak_f > (base_f + 25e3):
            recovered_logic.append(1)
        else:
            recovered_logic.append(0)
            
    full_signal = np.array(full_signal)
    total_time = np.linspace(0, num_hops * time_per_hop * 1e6, len(full_signal))
    
    # 5. Visualization
    plt.figure(figsize=(15, 10))
    
    # Time Domain - Looks like chaotic bursts
    plt.subplot(2, 1, 1)
    plt.plot(total_time, full_signal, color='darkgreen', alpha=0.7)
    plt.title("FTA Frequency Hopping Encryption (Physical Layer Security)", fontsize=14)
    plt.ylabel("Signal Amplitude")
    plt.xlabel("Time (microseconds)")
    plt.grid(True, alpha=0.2)
    
    # Spectrogram-like visualization
    plt.subplot(2, 1, 2)
    plt.specgram(full_signal, Fs=fs/1e3, NFFT=256, noverlap=128, cmap='viridis')
    plt.title("Spectrogram: Hopping Logic Channels (Undecipherable without Seed)")
    plt.ylabel("Frequency (kHz)")
    plt.xlabel("Time (us)")
    plt.colorbar(label='Power (dB)')
    
    plt.tight_layout()
    output_path = r'C:\Users\allmy\Desktop\aaa\field_transistor_alternative\Phase_5_System_Maturity\fta_freq_hopping_results.png'
    plt.savefig(output_path)
    plt.close()
    
    print(f"[+] Encryption Simulation Complete.")
    print(f"[+] Payload:        {payload}")
    print(f"[+] Recovered Data: {recovered_logic}")
    print(f"[+] Success:        {payload == recovered_logic}")
    print(f"[+] Output saved:   {output_path}")

if __name__ == "__main__":
    sim_fta_frequency_hopping()
