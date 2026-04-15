import numpy as np
import matplotlib.pyplot as plt

def sim_magnetic_coupling():
    """
    Simulates cross-chamber induction within an FTA stack.
    Chamber A (Source): Pulse induces magnetic field.
    Chamber B (Target): Biased near threshold, triggered by induction.
    """
    time = np.linspace(0, 5, 2000)
    
    # Chamber A: Source Pulse (dV/dt is high)
    v_a = 5.0 * np.exp(-((time - 1.0)**2) / 0.05) # Gaussian Pulse at t=1.0s
    dv_dt = np.gradient(v_a, time)
    
    # Magnetic Induction (Simplified: Induced EMF proportional to dv/dt)
    # This represents the "Stress" transfer between chambers
    k_coupling = 0.05 # Coupling coefficient
    induced_bias = k_coupling * dv_dt
    
    # Chamber B: Biased at 4.5V (Threshold = 5.0V)
    base_bias_b = 4.8
    total_bias_b = base_bias_b + induced_bias
    
    # Logic Output of Chamber B (Threshold Triggering)
    threshold = 5.0
    output_b = np.where(total_bias_b > threshold, 0.0, 5.0) # Blocking logic
    
    # Visualization
    plt.figure(figsize=(12, 10))
    
    plt.subplot(3, 1, 1)
    plt.plot(time, v_a, color='blue', label='Chamber A (Source Pulse)')
    plt.ylabel("Voltage (V)")
    plt.title("Cross-Chamber Induction & Triggering")
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    plt.subplot(3, 1, 2)
    plt.plot(time, induced_bias, color='purple', label='Induced EMF (from dV/dt)')
    plt.axhline(threshold - base_bias_b, color='red', linestyle='--', label='Trigger Threshold')
    plt.ylabel("Induced Bias (V)")
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    plt.subplot(3, 1, 3)
    plt.plot(time, output_b, color='green', lw=2, label='Chamber B (Triggered Output)')
    plt.ylabel("Output Level (V)")
    plt.xlabel("Time (Arbitrary Units)")
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('fta_magnetic_coupling.png')
    print("[+] Electromagnetic coupling graph generated: fta_magnetic_coupling.png")

if __name__ == "__main__":
    sim_magnetic_coupling()
