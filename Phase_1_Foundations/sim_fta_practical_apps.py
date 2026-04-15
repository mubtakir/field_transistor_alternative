import numpy as np
import matplotlib.pyplot as plt

def sim_nano_amplifier():
    """
    Simulates an FTA-based Nano-Amplifier.
    Tiny input signal (millivolts) triggers large output swing in a stressed chamber.
    """
    time = np.linspace(0, 10, 2000)
    # Tiny input signal (e.g., from a sensor) - 50mV peak
    v_in = 0.05 * np.sin(2 * np.pi * 1.0 * time) 
    
    # Stressed Chamber B: Biased at 4.95V (Threshold = 5.0V)
    # The tiny v_in induces a bias shift. Gain is achieved by the steepness of the field gradient.
    gain_factor = 40.0 # Theoretical field-gradient gain
    v_out = base_bias_sig = 4.95 + v_in * gain_factor
    
    # Clipped Output (Simulation of threshold behavior)
    v_out_filtered = np.clip(v_out, 0, 10)
    
    return time, v_in, v_out_filtered

def sim_magnetic_isolator():
    """
    Simulates a Logic Isolator.
    Input A (Square Wave) -> Output B (Induced Logic)
    """
    time = np.linspace(0, 10, 2000)
    # Input Clock (5V Square)
    v_clock = 5.0 * (np.sin(2 * np.pi * 0.5 * time) > 0)
    
    # Induced EMF (Spikes on edges dV/dt)
    v_induced = 0.1 * np.gradient(v_clock, time)
    
    # Triggering an RS-Latch (Simplified)
    v_latch = np.zeros_like(time)
    curr_state = 0.0
    for i in range(1, len(time)):
        if v_induced[i] > 2.0: # Set logic
            curr_state = 5.0
        elif v_induced[i] < -2.0: # Reset logic
            curr_state = 0.0
        v_latch[i] = curr_state
        
    return time, v_clock, v_latch

def run_app_sims():
    print("="*60)
    print("FTA PRACTICAL APPLICATIONS SIMULATION")
    print("="*60)
    
    t1, vin, vout = sim_nano_amplifier()
    t2, vclk, vlat = sim_magnetic_isolator()
    
    plt.figure(figsize=(12, 12))
    
    # Plot 1: Nano-Amplifier
    plt.subplot(2, 1, 1)
    plt.plot(t1, vin * 10, label='Input (x10 for visibility)', color='green') # Scaled for visibility
    plt.plot(t1, vout - 4.95, label='Amplified Out (Signal Swing)', color='red', lw=2)
    plt.title("FTA Nano-Amplifier: High-Sensitivity Signal Gain")
    plt.ylabel("Voltage Swing (V)")
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # Plot 2: Magnetic Isolator
    plt.subplot(2, 1, 2)
    plt.plot(t2, vclk, label='Input Clock A', color='blue', alpha=0.5)
    plt.plot(t2, vlat, label='Isolated Output B (Induced Logic)', color='orange', lw=2)
    plt.title("FTA Magnetic Logic Isolator: Zero-Ohm Isolation")
    plt.xlabel("Time (s)")
    plt.ylabel("Logic Level (V)")
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('fta_practical_apps.png')
    print("[+] Practical apps graph generated: fta_practical_apps.png")

if __name__ == "__main__":
    run_app_sims()
