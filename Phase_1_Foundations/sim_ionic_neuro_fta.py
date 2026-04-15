import numpy as np
import matplotlib.pyplot as plt

def simulate_ionic_spiking():
    print("="*60)
    print("IONIC SLOW-OSCILLATION & NEUROMORPHIC SPIKING")
    print("="*60)
    
    # Time scale: seconds (Hertz range)
    t = np.linspace(0, 5, 2000) # 5 seconds
    
    # 1. Ionic Charge Accumulation (Slow charging)
    tau_charge = 0.5 # 500ms RC constant due to high ionic capacitance
    v_charge = 1.0 * (1 - np.exp(-t % 1.2 / tau_charge)) # 1.2s cycle
    
    # 2. Threshold Trigger (The "Basirah" logic in the plate)
    v_threshold = 0.7 
    spikes = np.zeros_like(t)
    trigger_indices = np.where(v_charge > v_threshold)[0]
    
    # Reset mechanism (Ionic redistribution after firing)
    for i in range(len(t)-1):
        if v_charge[i] > v_threshold:
            # Shift the next charging cycle slightly
            spikes[i] = 1.2 # Spike amplitude
            
    # 3. Simulated Meter Reading (Damped/Slow response)
    # This mimics the needle movement or digital meter lag
    meter_reading = np.zeros_like(t)
    for i in range(1, len(t)):
        meter_reading[i] = meter_reading[i-1] + (v_charge[i] - meter_reading[i-1]) * 0.05
    
    plt.figure(figsize=(12, 8))
    
    # Subplot 1: Charging & Threshold
    plt.subplot(2, 1, 1)
    plt.plot(t, v_charge, label='Ionic Charge ($V_{cap}$)', color='darkorange', lw=2)
    plt.axhline(v_threshold, color='red', linestyle='--', label='Firing Threshold')
    plt.title("Slow Ionic Charging cycle (FTA-Neuro)")
    plt.ylabel("Voltage (V)")
    plt.grid(True, alpha=0.3)
    plt.legend()
    
    # Subplot 2: Meter Response (The Slow oscillation the user saw)
    plt.subplot(2, 1, 2)
    plt.plot(t, meter_reading, label='Meter Needle Position', color='indigo', lw=2)
    plt.title("Simulated Meter Movement (Needle/Pointer Swing)")
    plt.xlabel("Time (s)")
    plt.ylabel("Visual Amplitude")
    plt.grid(True, alpha=0.3)
    plt.legend()
    
    plt.tight_layout()
    plt.savefig('ionic_slow_oscillation.png')
    print("[+] Ionic slow-oscillation graph generated: ionic_slow_oscillation.png")

if __name__ == "__main__":
    simulate_ionic_spiking()
