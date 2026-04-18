"""
U-Plate Cross-Field Magnetron Device Model.
Integrates FDM capacitance, Biot-Savart magnetics, WKB tunneling,
and Spintronic TMR into a coupled 12D ODE system.
"""
import numpy as np
from dataclasses import dataclass, field
from ..constants import q_e, m_e, h_bar, mu_0, eps_0
from ..solvers.fdm_laplace import solve_capacitance_matrix
from ..solvers.ode_system import solve_ode
from ..physics.magnetic_fields import plate_biot_savart, build_inductance_matrix, gap_field
from ..physics.quantum_tunneling import wkb_tunneling_current


@dataclass
class UPlateParams:
    """All parameters for a U-Plate device."""
    n_plates: int = 6
    plate_length: float = 100e-6
    plate_width: float = 10e-6
    plate_x_cells: list = field(default_factory=lambda: [10, 15, 20, 50, 80, 95])
    nx: int = 120
    ny: int = 100
    dx: float = 1e-9
    eps_r: float = 4.0
    plate_depth: float = 0.01
    Phi_B_eV: float = 1.0
    m_eff_ratio: float = 0.5
    mu_r: float = 50000.0
    B_sat: float = 1.0
    Gamma_spin: float = 3e8
    V_DD: float = 12.0
    I_gate: float = 2e-3
    R_plate: float = 500.0
    R_load: float = 1000.0
    gate_index: int = 1
    use_smf: bool = True  # Self-Magnetic Feedback (SMF)


class UPlateDevice:
    """
    A complete U-Plate Cross-Field Magnetron Transistor device.

    Usage:
        device = UPlateDevice(UPlateParams(V_DD=12, mu_r=50000))
        result = device.simulate(gate_fn, t_span=(0, 1e-7))
    """

    def __init__(self, params: UPlateParams = None):
        self.p = params or UPlateParams()
        self._build()

    def _build(self):
        """Pre-compute capacitance and inductance matrices."""
        self.C_matrix, self.dist_matrix = solve_capacitance_matrix(
            nx=self.p.nx, ny=self.p.ny,
            plate_x_cells=self.p.plate_x_cells,
            plate_y_range=(20, 80),
            eps_r=self.p.eps_r,
            plate_depth=self.p.plate_depth,
            dx=self.p.dx
        )

        self.L_matrix = build_inductance_matrix(
            self.p.n_plates,
            self.p.plate_length,
            self.p.plate_width,
            self.dist_matrix
        )

        # Pre-compute inverse matrices
        N = self.p.n_plates
        self.C_diag = np.abs(np.diag(self.C_matrix))
        self.C_diag = np.where(self.C_diag > 0, self.C_diag, 1e-18)
        self.L_diag = np.abs(np.diag(self.L_matrix))
        self.L_diag = np.where(self.L_diag > 0, self.L_diag, 1e-18)

    def _system(self, t, y, gate_fn):
        """12D ODE system: 6 voltages + 6 currents."""
        N = self.p.n_plates
        V = y[:N]
        I_long = y[N:]
        
        dV = np.zeros(N)
        dI = np.zeros(N)
        p = self.p
        
        for i in range(N):
            # Capacitive coupling: dV/dt = (1/C_ii) * sum(C_ij * dV_j) + I_tunnel
            coupling = 0.0
            for j in range(N):
                if i != j:
                    d = self.dist_matrix[i, j]
                    if d > 0:
                        E = abs(V[i] - V[j]) / d
                        B_i = plate_biot_savart(I_long[i], p.plate_width, p.plate_length, p.mu_r, p.B_sat)
                        B_j = plate_biot_savart(I_long[j], p.plate_width, p.plate_length, p.mu_r, p.B_sat)
                        B_gap_ij = gap_field(B_i, B_j, I_long[i], I_long[j])
                        
                        # First estimate of J to compute self-magnetic field
                        J_est = wkb_tunneling_current(E, B_gap_ij, d, p.Phi_B_eV, p.m_eff_ratio, p.Gamma_spin)
                        
                        # Apply Self-Magnetic Feedback (SMF)
                        if p.use_smf:
                            # B_self depends on the current current density J
                            B_self = mu_0 * J_est * p.plate_width * 0.5 
                            B_gap_ij += B_self
                            
                        # Final Tunneling Current with feedback
                        J = wkb_tunneling_current(E, B_gap_ij, d, p.Phi_B_eV, p.m_eff_ratio, p.Gamma_spin)
                        A_plate = p.plate_width * p.plate_length
                        I_tunnel = J * A_plate
                        coupling += I_tunnel * np.sign(V[j] - V[i])
            
            dV[i] = coupling / self.C_diag[i]
            
            # Inductive: dI/dt = (V_applied - I*R) / L
            if i == p.gate_index:
                V_applied = gate_fn(t)
            elif i == 0:
                V_applied = p.V_DD
            else:
                V_applied = 0.0
            
            dI[i] = (V_applied - I_long[i] * p.R_plate) / self.L_diag[i]
        
        return np.concatenate([dV, dI])

    def simulate(self, gate_fn, t_span=(0, 1e-7), n_points=1000):
        """
        Run a full simulation of the U-Plate device.
        
        Parameters
        ----------
        gate_fn : callable
            Gate signal function: gate_fn(t) -> V_gate.
        t_span : tuple
            (t_start, t_end) in seconds.
        n_points : int
            Number of output time points.
        
        Returns
        -------
        result : dict
            'time': array, 'voltages': (n_plates, n_points),
            'currents': (n_plates, n_points)
        """
        N = self.p.n_plates
        y0 = np.zeros(2 * N)
        y0[0] = self.p.V_DD * 0.01
        t_eval = np.linspace(t_span[0], t_span[1], n_points)

        sol = solve_ode(
            lambda t, y: self._system(t, y, gate_fn),
            y0, t_span, t_eval=t_eval, method='Radau',
            rtol=1e-6, atol=1e-9
        )

        return {
            'time': sol.t,
            'voltages': sol.y[:N, :],
            'currents': sol.y[N:, :],
            'success': sol.success,
            'params': self.p,
        }
