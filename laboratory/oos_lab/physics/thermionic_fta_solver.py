import numpy as np

class ThermionicFTASolver:
    """
    محاكي فيزيائي متقدم للمُبعثات الهجينة (حراري + كمومي).
    V1.0 - مارس 2026
    
    This solver handles the combined current from thermionic emission (Richardson-Dushman)
    and quantum tunneling (Fowler-Nordheim) in the context of the Field Transistor Alternative.
    """
    def __init__(self, config=None, **kwargs):
        """
        Initialize the solver with physical configuration.
        Supports both dictionary config and keyword arguments.
        """
        if isinstance(config, dict):
            self.phi = config.get('work_function', 4.5)
            self.gap = config.get('gap_distance', 50e-9)
            self.area = config.get('emitter_area', 1e-12)
            self.R_heater = config.get('heater_resistance', 28.0)
            self.R_th = config.get('thermal_resistance', 1.45e6)
            self.S0 = config.get('shielding_factor', 0.0076)
        else:
            self.phi = kwargs.get('phi_work_function', 4.5)
            self.gap = kwargs.get('gap_nm', 50) * 1e-9
            self.area = 1e-12
            self.R_heater = 28.0
            self.R_th = 1.45e6
            self.S0 = 0.0076

        self.T_ambient = 300.0
        self.kB = 8.617e-5 # eV/K
        self.q_e = 1.602e-19
        self.h = 6.626e-34

    def calculate_total_current(self, voltage_v, temp_k, gap_m=None):
        """Standard Hybrid Emission calculation at a given temperature."""
        gap = gap_m or self.gap
        E = (voltage_v / gap)
        
        # 1. Thermionic (Richardson-Dushman + Schottky)
        beta = 1.2e-4
        phi_eff = max(0.1, self.phi - beta * np.sqrt(E))
        A_richardson = 1.2e6
        j_thermionic = A_richardson * (temp_k**2) * np.exp(-phi_eff / (self.kB * temp_k))
        
        # 2. Quantum (Fowler-Nordheim)
        A_fn = 1.5e-6 
        B_fn = 6.83e9
        j_tunneling = (A_fn * E**2 / self.phi) * np.exp(-B_fn * (self.phi**1.5) / E)
        
        return j_thermionic + j_tunneling, j_thermionic, j_tunneling, phi_eff

    def solve_steady_state(self, v_ds, v_gate, v_heater):
        """
        Solves for the thermal equilibrium where Pin = Ploss + Pcooling.
        Returns total current and a detailed breakdown.
        """
        # Power In from heater
        P_in = (v_heater**2) / self.R_heater if self.R_heater > 0 else 0
        
        # Effective driving voltage (Shielded)
        v_eff = max(0, v_ds - (v_gate * self.S0))
        
        # Iterative solver for Temperature
        T_guess = self.T_ambient + (P_in * self.R_th)
        for _ in range(10): # Rapid convergence for thermal loops
            j_tot, j_th, j_fn, phi_eff = self.calculate_total_current(v_eff, T_guess)
            I_tot = j_tot * self.area
            
            # Quantum Cooling (QTMS): Energy removed by escaping electrons
            # Each electron carries approx (phi_eff + 2kT) of energy
            avg_energy_ev = phi_eff + (2 * self.kB * T_guess)
            P_cooling = I_tot * avg_energy_ev
            
            # Update Temperature
            T_new = self.T_ambient + ((P_in - P_cooling) * self.R_th)
            if abs(T_new - T_guess) < 0.1:
                break
            T_guess = 0.5 * (T_guess + T_new) # Damping
            
        return j_tot, {
            'I_total': I_tot,
            'J_thermionic': j_th,
            'J_FN': j_fn,
            'T_emitter': T_guess,
            'P_cooling': P_cooling,
            'P_in': P_in,
            'phi_eff': phi_eff
        }

if __name__ == "__main__":
    solver = ThermionicFTASolver(phi_work_function=2.4)
    print("--- Solver Self-Test ---")
    j, res = solver.solve_steady_state(v_ds=10.0, v_gate=0.0, v_heater=5.0)
    print(f"Results: I={res['I_total']*1e6:.2f} uA, T={res['T_emitter']:.1f} K")
