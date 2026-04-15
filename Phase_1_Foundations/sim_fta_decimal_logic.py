import numpy as np
import matplotlib.pyplot as plt

def solve_decimal_staircase(input_digit):
    """
    Simulates a 10-state Decimal FTA unit.
    Input_digit: integer 0-9
    returns: the field distribution across 11 plates.
    """
    n_plates = 11
    # Base staircase: 0.5V steps
    base_voltages = np.linspace(0, 4.5, n_plates)
    
    # Activation: The input digit selects which 'pocket' is active/depleted.
    # We model this by increasing the resistance (depletion) at gap [input_digit]
    resistances = [10] * (n_plates - 1)
    if 0 <= input_digit < 10:
        resistances[input_digit] = 10000 # The Active "Decimal Pocket"
        
    # Potential calculation (heuristic expansion)
    x = np.linspace(0, 10, 1000)
    potentials = np.zeros_like(x)
    
    for i in range(10):
        v_start = base_voltages[i]
        v_end = base_voltages[i+1]
        r = resistances[i]
        
        mask = (x >= i) & (x <= i+1)
        sub_x = x[mask] - i
        
        # Scale the gradient based on R
        alpha = 1.0 / (1.0 + 1.0/r)
        potentials[mask] = v_start + (v_end - v_start) * (sub_x**alpha)
        
    return x, potentials

def run_decimal_sim():
    print("="*60)
    print("FTA DECIMAL LOGIC (0-9) SIMULATION")
    print("="*60)
    
    digits_to_test = [0, 3, 7, 9]
    colors = ['blue', 'green', 'orange', 'red']
    
    plt.figure(figsize=(12, 8))
    
    for digit, color in zip(digits_to_test, colors):
        x, p = solve_decimal_staircase(digit)
        plt.plot(x, p, label=f'Decimal Digit: {digit}', color=color, lw=2)
        
    plt.title("FTA 10-State Potential Staircase (Decimal Logic)")
    plt.xlabel("Plate Index (0 to 10)")
    plt.ylabel("Internal Potential (V)")
    plt.xticks(range(11))
    plt.yticks(np.linspace(0, 4.5, 10))
    plt.grid(True, which='both', alpha=0.3)
    plt.legend()
    plt.savefig('fta_decimal_staircase.png')
    print("[+] Decimal staircase graph generated: fta_decimal_staircase.png")

if __name__ == "__main__":
    run_decimal_sim()
