
import numpy as np
import matplotlib.pyplot as plt
import os
import sys

# Ensure oos_lab package is in the path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from oos_lab.solvers.fta_solver import FTASolver

from scipy.optimize import minimize

def run_linearization_demo():
    print("Initializing FTASolver and Optimizing NDR parameters...")
    solver = FTASolver(n_plates=2, T=300.0)
    V_range = np.linspace(1.2, 1.8, 20) # Focusing on the operating window
    d_gap = 10e-9 
    solver.dist_matrix = np.array([[0, d_gap], [d_gap, 0]])
    B_gaps = [0.0]

    def objective(params):
        J_peak, sigma, E_peak = params
        test_ndr = {'J_peak': J_peak, 'sigma': sigma, 'E_peak': E_peak}
        J_vals = []
        for V in V_range:
            J = solver.solve_quantum([0, V], B_gaps, use_linearization=True, ndr_params=test_ndr)[0]
            J_vals.append(J)
        
        # Calculate R-squared (minimize 1-R^2)
        correlation_matrix = np.corrcoef(V_range, J_vals)
        r_squared = correlation_matrix[0,1]**2
        return 1.0 - r_squared

    # Initial guess and bounds
    x0 = [5e-6, 1e8, 1.5e8]
    # Use bounds to keep parameters physical
    bounds = [(1e-7, 1e-4), (1e7, 1e10), (1e7, 1e10)]
    
    # Minimize 1-R^2 using a bounded method
    from scipy.optimize import minimize
    res = minimize(objective, x0, method='Nelder-Mead', tol=1e-4) # Nelder-Mead doesn't strictly take bounds but we can try minimize with bounds
    # Better: L-BFGS-B for bounds
    res = minimize(objective, x0, method='L-BFGS-B', bounds=bounds)
    
    best_params = {'J_peak': res.x[0], 'sigma': res.x[1], 'E_peak': res.x[2]}
    
    print(f"Optimal NDR Params found: {best_params}")
    
    # Run full plot range with best params
    V_full = np.linspace(0.8, 2.2, 50)
    J_base_list = []
    J_linear_list = []
    for V in V_full:
        J_base = solver.solve_quantum([0, V], [0.0], use_linearization=False)[0]
        J_linear = solver.solve_quantum([0, V], [0.0], use_linearization=True, ndr_params=best_params)[0]
        J_base_list.append(J_base)
        J_linear_list.append(J_linear)
        
    return V_full, J_base_list, J_linear_list, res.fun

if __name__ == "__main__":
    V, J_base, J_linear, error = run_linearization_demo()
    
    plt.figure(figsize=(10, 6))
    plt.plot(V, np.array(J_base) * 1e6, 'b--', label='Base Response (Fowler-Nordheim)', alpha=0.7)
    plt.plot(V, np.array(J_linear) * 1e6, 'g-', label='Linearized Response (with NDR)', linewidth=2.5)
    
    plt.title('OOS-Lab: Linearization Development & Verification')
    plt.xlabel('Operation Voltage (V)')
    plt.ylabel('Current Density (uA/m^2)')
    plt.legend()
    plt.grid(True, linestyle=':', alpha=0.5)
    
    # Adding a simple linear trendline for comparison
    z = np.polyfit(V[10:40], np.array(J_linear)[10:40] * 1e6, 1)
    p = np.poly1d(z)
    plt.plot(V, p(V), 'k:', alpha=0.4, label='Ideal Linear Trend')
    
    output_path = "linearization_verification_lab.png"
    plt.savefig(output_path)
    print(f"Verification plot saved to: {output_path}")
    
    # Calculate R-squared for the linear region (1.2V to 1.8V)
    indices = np.where((V >= 1.2) & (V <= 1.8))
    correlation_matrix = np.corrcoef(V[indices], np.array(J_linear)[indices])
    correlation_xy = correlation_matrix[0,1]
    r_squared = correlation_xy**2
    print(f"Linearity R-squared (1.2V - 1.8V): {r_squared:.4f}")
