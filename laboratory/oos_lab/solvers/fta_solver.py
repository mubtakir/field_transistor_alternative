"""
Unified FTASolver: The central engine for FTA (Cross-Field Device) simulations.
Integrates FDM, Biot-Savart, WKB, and ODE solvers.
"""
import numpy as np
from ..physics.quantum_tunneling import wkb_tunneling_current, poole_frenkel_current, fowler_nordheim_tfe
from ..physics.magnetic_fields import plate_biot_savart, gap_field
from .fdm_laplace import solve_capacitance_matrix
from .ode_system import solve_ode

class FTASolver:
    def __init__(self, n_plates=6, T=300.0, dx=1e-9):
        self.n_plates = n_plates
        self.T = T
        self.dx = dx
        self.C_matrix = None
        self.dist_matrix = None
        self.shielding_factor = None
        self.plate_x_cells = [10, 15, 20, 50, 80, 95] if n_plates == 6 else None
        
    def solve_electrostatic(self, nx=120, ny=100):
        """Step 1: Solve Laplace equation and extract C-matrix."""
        from .fdm_laplace import solve_capacitance_matrix, compute_shielding_factor
        
        C, D = solve_capacitance_matrix(
            nx=nx, ny=ny, 
            plate_x_cells=self.plate_x_cells,
            dx=self.dx
        )
        self.C_matrix = C
        self.dist_matrix = D
        
        # We need the full potential for shielding factor, 
        # but for this class, we use a characteristic solution.
        # Here we use a saved shielding factor if already computed.
        if self.shielding_factor is None:
            # Characteristic ratio based on 6-plate geometry
            self.shielding_factor = 0.0075 
        
        return self.C_matrix, self.shielding_factor

    def solve_magnetic(self, currents):
        """Step 2: Solve Biot-Savart for gap fields."""
        B_gaps = []
        for i in range(self.n_plates - 1):
            B_i = plate_biot_savart(currents[i], width=10e-6, length=100e-6, T=self.T)
            B_j = plate_biot_savart(currents[i+1], width=10e-6, length=100e-6, T=self.T)
            B_gaps.append(gap_field(B_i, B_j, currents[i], currents[i+1]))
        return B_gaps

    def solve_quantum(self, voltages, B_gaps, use_linearization=False, ndr_params=None, **kwargs):
        """Step 3: Solve Quantum Tunneling (WKB + PF + NDR + MEMS). Supports noise calculation."""
        from ..physics.quantum_tunneling import ndr_gaussian_correction
        
        current_densities = []
        noise_stds = []
        use_mems = kwargs.get('use_mems', False)
        
        for i in range(self.n_plates - 1):
            d_gap = self.dist_matrix[i, i+1] if self.dist_matrix is not None else 30e-9
            V_diff = abs(voltages[i+1] - voltages[i])
            
            # MEMS Electromechanical Coupling
            if use_mems:
                from ..physics.electromechanical import solve_mems_displacement
                d_eff = solve_mems_displacement(V_diff, d0=d_gap, k_m=kwargs.get('k_m', 10.0))
            else:
                d_eff = d_gap
                
            E_eff = V_diff / d_eff
            
            # WKB + Poole-Frenkel
            from ..physics.quantum_tunneling import wkb_tunneling_current, poole_frenkel_current
            J_wkb = wkb_tunneling_current(E_eff, B_gaps[i], d_gap=d_eff)
            J_pf = poole_frenkel_current(E_eff, T=self.T)
            J_base = J_wkb + J_pf
            
            # Apply NDR Linearization if requested
            if use_linearization:
                params = ndr_params or {'J_peak': 5e-6, 'sigma': 1e8, 'E_peak': 1e8}
                J_ndr = ndr_gaussian_correction(E_eff, **params)
                J_total = J_base - J_ndr
            else:
                J_total = J_base
                
            current_densities.append(J_total)
            
            # Noise estimation if requested
            if kwargs.get('calculate_noise', False):
                from oos_lab.physics.noise_models import apply_noise_to_current
                I_approx = J_total * (100e-6 * 10e-6) # Estimated area
                noise_rms = apply_noise_to_current(I_approx, T=self.T)
                noise_stds.append(noise_rms / (100e-6 * 10e-6))
            else:
                noise_stds.append(0.0)

        if kwargs.get('calculate_noise', False):
            return current_densities, noise_stds
        return current_densities

    def solve_static_response(self, voltages, currents):
        """Combined static solver."""
        if self.C_matrix is None:
            self.solve_electrostatic()
        B_gaps = self.solve_magnetic(currents)
        J_total = self.solve_quantum(voltages, B_gaps)
        return J_total, B_gaps

    def solve_transient(self, t_span, y0, gfn):
        """
        Step 4: Solve ODE for dynamic response.
        y0 should be [V1...Vn, I1...In] where n is n_plates.
        """
        from .ode_system import solve_ode
        from ..physics.magnetic_fields import plate_biot_savart, gap_field
        
        # Build local parameter cache for performance
        Ci = np.linalg.inv(self.C_matrix)
        # Simplified L-matrix (inductance)
        Li = np.eye(self.n_plates) * 1e-9 # placeholder for extracted Li
        
        def system(t, y):
            n = self.n_plates
            V = y[0:n]
            Il = y[n:2*n]
            
            # Driving condition (example node 1 driven by gfn)
            Ve = np.zeros(n); Ve[1] = gfn(t)
            dI = Li @ (Ve - 500.0 * Il) # 500 is Rp
            
            # Quenching Fields
            B_gaps = self.solve_magnetic(Il)
            
            # Tunneling Currents
            It = np.zeros(n)
            for i in range(n-1):
                d_g = self.dist_matrix[i, i+1]
                E = abs(V[i+1]-V[i])/d_g
                J = wkb_tunneling_current(E, B_gaps[i], d_gap=d_g)
                In = J * (100e-6 * 10e-6) * np.sign(V[i+1]-V[i])
                It[i] -= In
                It[i+1] += In
            
            # Node balancing
            Is = -V / 500.0 # Discharge
            dV = Ci @ (Is + It)
            
            return np.concatenate([dV, dI])
            
        return solve_ode(system, y0, t_span)
