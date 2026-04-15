import numpy as np
import matplotlib.pyplot as plt

def solve_asymmetric_plates(plate_voltages, gap_resistances):
    """
    Generalized Solver for N-Plate Asymmetric System.
    plate_voltages: List of V for each plate [V0, V1, ... VN-1]
    gap_resistances: List of R for each gap [R01, R12, ... RN-2,N-1]
    """
    n = len(plate_voltages)
    x_coords = np.linspace(0, n-1, 1000)
    potentials = np.zeros_like(x_coords)
    
    # Calculate Potential Gradient across each gap
    for i in range(n - 1):
        v_start = plate_voltages[i]
        v_end = plate_voltages[i+1]
        r_gap = gap_resistances[i]
        
        # Heuristic: Lower resistance makes the potential more uniform (saturated)
        # Higher resistance allows for a steeper gradient (depleted)
        # Gradient is dV/dx. 
        mask = (x_coords >= i) & (x_coords <= i+1)
        sub_x = x_coords[mask] - i
        
        # Non-linear potential distribution based on R (Heuristic)
        # As R -> 0, potential remains at V_start.
        # As R -> infinity, potential drops linearly.
        alpha = 1.0 / (1.0 + 1.0/r_gap) # Saturation factor
        potentials[mask] = v_start + (v_end - v_start) * (sub_x**alpha)
        
    return x_coords, potentials

def run_scenarios():
    print("="*60)
    print("ASYMMETRIC FIELD DYNAMICS SIMULATION")
    print("="*60)
    
    # Scene 1: 3-Plates A,B,C. AB-Saturated (10 Ohm), BC-Depleted (10k Ohm)
    # Voltages: A=5V, B=5V, C=0V
    v1 = [5.0, 5.0, 0.0]
    r1 = [10, 10000]
    x1, p1 = solve_asymmetric_plates(v1, r1)
    
    # Scene 2: Same, but Reversed Bias
    # Voltages: A=0V, B=5V, C=5V
    v2 = [0.0, 5.0, 5.0]
    r2 = [10000, 10]
    x2, p2 = solve_asymmetric_plates(v2, r2)
    
    # Scene 3: 5-Plate Scale (Balanced vs Asymmetric)
    v3 = [5, 5, 0, 0, 5]
    r3 = [10, 10000, 10, 10000]
    x3, p3 = solve_asymmetric_plates(v3, r3)

    # Plotting
    plt.figure(figsize=(14, 10))
    
    plt.subplot(2, 2, 1)
    plt.plot(x1, p1, color='blue', lw=2)
    plt.title("3-Plate Asymmetric: AB-Saturated / BC-Depleted")
    plt.ylabel("Potential (V)")
    plt.grid(True, alpha=0.3)
    
    plt.subplot(2, 2, 2)
    plt.plot(x2, p2, color='red', lw=2)
    plt.title("3-Plate Reversed: AB-Depleted / BC-Saturated")
    plt.ylabel("Potential (V)")
    plt.grid(True, alpha=0.3)
    
    plt.subplot(2, 1, 2)
    plt.plot(x3, p3, color='green', lw=2)
    plt.title("5-Plate Scaling: Multimodal Field Trapping")
    plt.xlabel("Plate Indices (0 to 4)")
    plt.ylabel("Potential (V)")
    plt.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('asymmetric_field_dynamics.png')
    print("[+] Asymmetric field dynamics graph generated: asymmetric_field_dynamics.png")

if __name__ == "__main__":
    run_scenarios()
