import numpy as np
from typing import Dict, Any, Optional, Tuple
from ..constants import q_e, m_e, mu_0, eps_0
import scipy.integrate as spi

class NestedInductorFTA:
    """
    High-fidelity FTA device model incorporating the Phase 8 Nested Inductors perspective.
    Features: 6x6 L-matrix, Mutual Induction, and Dynamic Tunneling.
    """

    def __init__(self, geometry: Dict, materials: Dict = None, **kwargs):
        self.geometry = geometry
        self.materials = materials or {}
        
        # Physics Parameters
        self.R_plate = kwargs.get('R_plate', 500.0)
        self.mu_r = kwargs.get('mu_r', 100.0)
        self.gap_thickness = geometry.get('gap', 10e-9)
        self.area = geometry.get('length', 100e-6) * geometry.get('width', 10e-6)
        
        # Build 6x6 Matrices
        self.L_matrix = self._build_inductance_matrix()
        self.L_inv = np.linalg.inv(self.L_matrix)
        self.C_matrix = np.eye(6) * (eps_0 * self.area / self.gap_thickness)
        self.C_inv = np.linalg.inv(self.C_matrix)

    def _u_plate_self_inductance(self, L, W, arm_len):
        L_straight = (mu_0 * L / (2*np.pi)) * (np.log(2*L/W) + 0.5)
        L_arms = (mu_0 * (2 * arm_len) / (4*np.pi))
        return (L_straight + L_arms) * 0.5

    def _mutual_inductance(self, L1, L2, d):
        char_len = 500e-9
        k = np.exp(-d / char_len)
        return k * np.sqrt(L1 * L2)

    def _build_inductance_matrix(self):
        L = np.zeros((6, 6))
        positions = np.array([i * (self.geometry.get('thickness', 100e-9) + self.gap_thickness) for i in range(6)])
        L_self = self._u_plate_self_inductance(self.geometry.get('length', 100e-6), 
                                               self.geometry.get('width', 10e-6), 
                                               self.geometry.get('arm_length', 40e-6))
        for i in range(6):
            L[i,i] = L_self
            for j in range(i+1, 6):
                d = abs(positions[i] - positions[j])
                alignment = 1 if (i%2 == j%2) else -1
                M = self._mutual_inductance(L_self, L_self, d)
                L[i,j] = L[j,i] = M * alignment
        return L

    def solve_transient(self, t_span, v_gate_fn, v_source=50.0, v_drain=0.0):
        """
        Run a high-fidelity transient simulation.
        """
        def system_deriv(t, state):
            V = state[0:6]
            I_long = state[6:12]
            
            V_drive = np.zeros(6)
            V_drive[1] = v_gate_fn(t)
            V_drive[0] = v_source
            V_drive[4] = v_drain
            
            # dI/dt with full coupling
            V_L = V_drive - self.R_plate * I_long - V
            dI_dt = self.L_inv @ V_L
            
            # Magnetic Field Calculation (Mu_r boost)
            B_total = (self.mu_r * mu_0 * np.abs(I_long) / (2 * self.geometry.get('width', 10e-6))) * np.sign(I_long)
            
            # Tunneling Current (Simplified for Lab v1.2)
            I_tunnel = np.zeros(6)
            B_eff = B_total[0] + B_total[1]
            E = abs(V[0] - V[1]) / self.gap_thickness
            
            # WKB logic (placeholder for engine call)
            # From ..physics_engine import wkb_tunneling_current (we'll avoid circular imports)
            J = 1e-4 * (E**2) * np.exp(-1e6/E) # Highly simplified WKB for speed
            It = J * self.area
            I_tunnel[0] -= It
            I_tunnel[1] += It
            
            dV_dt = self.C_inv @ I_tunnel
            return np.concatenate([dV_dt, dI_dt])

        y0 = np.zeros(12)
        sol = spi.solve_ivp(system_deriv, t_span, y0, method='BDF', t_eval=np.linspace(t_span[0], t_span[1], 200))
        return sol

    def get_magnetic_energy(self, I_long):
        return 0.5 * np.dot(I_long, np.dot(self.L_matrix, I_long))
