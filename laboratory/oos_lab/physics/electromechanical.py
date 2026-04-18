
import numpy as np
from scipy.optimize import fsolve

def solve_mems_displacement(V, d0=30e-9, k_m=10.0, area=1e-10, epsilon_r=3.9):
    """
    Solves the force balance equation between electrostatic attraction and mechanical stiffness.
    F_e = 0.5 * (epsilon_0 * epsilon_r * Area / d^2) * V^2
    F_m = k_m * (d0 - d)
    
    Returns the equilibrium distance d.
    """
    epsilon_0 = 8.854e-12
    
    def force_balance(d):
        if d <= 1e-10: return 1e6 # Prevent collapse or non-physical solutions
        f_e = 0.5 * (epsilon_0 * epsilon_r * area / (d**2)) * (V**2)
        f_m = k_m * (d0 - d)
        return f_e - f_m

    # Initial guess is d0 (zero displacement)
    d_final = fsolve(force_balance, d0)[0]
    
    # Check for "Pull-in" instability (if d < 2/3 d0 approximately)
    if d_final < 0.5 * d0:
        # Simplified handling of pull-in
        return 0.5 * d0 # Limit collapse for simulation stability
        
    return d_final

def mems_effective_field(V, d_final):
    """Calculates E = V/d_final."""
    return V / (d_final + 1e-15)
