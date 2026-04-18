import sys
import os
import numpy as np
import matplotlib.pyplot as plt

# Add the lab path to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from analysis.fta_lab_bench import FTALabBench, FTAParameters

def verify_decimal_level_separation():
    """
    Tests if a single FTA device can distinguish 10 levels of input voltage (0.0 to 5.0V)
    with enough current separation to be used as 'Decimal Logic'.
    """
    print("\n--- [Decimal Logic Physical Feasibility] ---")
    
    # We use a sensitive setup for multi-level detection
    params = FTAParameters(
        tox=10e-9,      # 10nm (very sensitive)
        area=1e-12,
        eps_r=4.0
    )
    
    bench = FTALabBench(params)
    
    # 10 Logic Levels (0-9)
    levels = np.arange(10)
    v_inputs = np.linspace(0.5, 4.5, 10) # 0.5V to 4.5V range
    
    currents = []
    print(f"{'Digit':<10} | {'Input Voltage (V)':<20} | {'Output Current (uA)':<25}")
    print("-" * 60)
    
    for digit, v in zip(levels, v_inputs):
        I = bench.device.current(v)
        I_uA = I * 1e6
        currents.append(I_uA)
        print(f"{digit:<10} | {v:<20.2f} | {I_uA:<25.4f}")
    
    currents = np.array(currents)
    
    # Calculate Ratio (Separation) between adjacent levels
    # A good decimal logic needs stable separation
    ratios = currents[1:] / (currents[:-1] + 1e-15)
    
    # Visualization
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
    
    # 1. Level Distribution
    ax1.semilogy(levels, currents, 'bo-', lw=2)
    ax1.set_title("Decimal Levels vs Output Current (Log Scale)")
    ax1.set_xlabel("Decimal Digit (0-9)")
    ax1.set_ylabel("Current (uA)")
    ax1.grid(True, which='both', alpha=0.3)
    
    # 2. Level Separation (Ratio)
    ax2.bar(levels[1:], ratios, color='orange', alpha=0.7)
    ax2.axhline(1.5, color='red', linestyle='--', label='Minimum Safe Ratio (1.5x)')
    ax2.set_title("Separation Ratio (Level N / Level N-1)")
    ax2.set_xlabel("Level Transition")
    ax2.set_ylabel("Multiplicative Gain")
    ax2.legend()
    ax1.grid(True, alpha=0.3)
    
    plt.savefig('decimal_feasibility_analysis.png')
    print("\n[+] Analysis complete: decimal_feasibility_analysis.png generated.")
    
    # Conclusion logic
    avg_ratio = np.mean(ratios)
    if avg_ratio > 2.0:
        conc = "PHYSICALLY VALID: Levels are highly distinct due to exponential tunneling."
    elif avg_ratio > 1.2:
        conc = "MARGINAL: Levels can be distinguished but require high-precision ADCs."
    else:
        conc = "NOT RECOMMENDED: Levels are too crowded for reliable decimal logic."
        
    print(f"\n[CONCLUSION] {conc}")
    return avg_ratio

if __name__ == "__main__":
    verify_decimal_level_separation()
