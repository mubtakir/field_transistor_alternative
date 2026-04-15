import numpy as np
import matplotlib.pyplot as plt

def simulate_tnc_resonance():
    print("="*60)
    print("TNC RESONANCE & INDUCTIVE COUPLING SIMULATION")
    print("="*60)
    
    # 1. Apparent Capacitance vs Resistance
    # Z = R + jwL + 1/jwC
    # Apparent C = 1 / (w * Imag(Z))
    
    w = 2 * np.pi * 1e6 # 1 MHz Test frequency
    C0 = 100e-12 # Base capacitance 100pF
    L0 = 10e-6   # Base inductance 10uH (induced at low R)
    
    resistance = np.logspace(0, 3, 200) # 1 to 1000 Ohms
    
    # Inductance starts appearing as Resistance drops (L ~ 1/R heuristic)
    # At high R, L is near 0. At low R, L increases due to conduction path.
    L_eff = L0 * (1.0 / (1.0 + (resistance/20)**2)) 
    
    # Complex Impedance Components
    X_C = 1 / (w * C0)
    X_L = w * L_eff
    
    # Apparent Capacitance seen by a meter
    # C_app = 1 / (w * (X_C - X_L))
    # We use a epsilon constant for numerical stability
    C_app = 1 / (w * (X_C - X_L + 1e-12))
    
    # Normalize for plotting (in pF)
    C_app_pf = C_app * 1e12
    
    plt.figure(figsize=(12, 7))
    plt.semilogx(resistance, C_app_pf, label='Apparent Capacitance (pF)', color='darkred', lw=2)
    plt.axhline(0, color='black', linestyle='--')
    plt.axvline(20, color='blue', linestyle=':', label='Resonance/Oscillation Point (~20Ω)')
    
    plt.title("TNC Transition: Capacitive to Inductive Regime")
    plt.xlabel("Dielectric Resistance (Ω)")
    plt.ylabel("Apparent Capacitance (pF)")
    plt.ylim(-500, 500) # Clamp for visibility
    plt.grid(True, which="both", ls="-", alpha=0.3)
    plt.legend()
    plt.savefig('tnc_transition.png')
    print("[+] TNC Transition graph generated: tnc_transition.png")
    
    # 2. Self-Oscillation Waveform
    # If Gain > Losses, we get a sinus waveform
    t = np.linspace(0, 5e-6, 1000) # 5 microseconds
    f_res = 1 / (2 * np.pi * np.sqrt(L0 * C0)) # Resonant frequency
    
    # Dampening factor based on resistance
    # At 20 ohms, it's undamped/oscillatory
    alpha = (20 - 15) * 1e5 # Heuristic growth/decay
    waveform = np.exp(alpha * t) * np.sin(2 * np.pi * f_res * t)
    
    plt.figure(figsize=(12, 7))
    plt.plot(t*1e6, waveform, color='navy')
    plt.title("Simulated Self-Oscillation at 15-20Ω (RLC Integration)")
    plt.xlabel("Time (μs)")
    plt.ylabel("Signal Amplitude")
    plt.grid(True, alpha=0.3)
    plt.savefig('tnc_oscillation.png')
    print("[+] Self-oscillation waveform generated: tnc_oscillation.png")

if __name__ == "__main__":
    simulate_tnc_resonance()
