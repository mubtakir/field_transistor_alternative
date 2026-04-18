"""
U-Plate FTA Device Model - Modular V2.0
---------------------------------------
Consolidates all physics into a coupled device class.
"""

import numpy as np
from typing import Dict, Any, Optional, Tuple
from ..physics_engine import solve_capacitance_matrix, wkb_tunneling_current
from ..constants import q_e, m_e, mu_0

class UPlateFTA:
    """
    Modular implementation of the Field Transistor Alternative (FTA).
    """

    def __init__(self, geometry: Dict, **kwargs):
        """
        Initialize the device with dimensions and electrical params.
        """
        self.geometry = geometry
        self.V_DD = kwargs.get('V_DD', 50.0)
        self.R_load = kwargs.get('R_load', 1000.0)
        self.R_gate = kwargs.get('R_gate', 500.0)
        self.mu_r = kwargs.get('mu_r', 50000.0)
        
        # Pre-calculated matrices
        self.C_matrix = None
        self.dist_matrix = None
        self._build_physics()
        
    def _build_physics(self):
        """Pre-compute the capacitance matrix for the geometry."""
        print("[FTA] Building electrostatic model...")
        self.C_matrix, self.dist_matrix = solve_capacitance_matrix(
            nx=self.geometry.get('nx', 120),
            ny=self.geometry.get('ny', 100),
            plate_x_cells=self.geometry.get('plate_positions', [10, 15, 20, 50, 80, 95]),
            eps_r=self.geometry.get('eps_r', 4.0)
        )
        
    def calculate_biot_savart(self, I: float) -> float:
        """Calculate B-field from plate current."""
        L = self.geometry.get('length', 100e-6)
        w = self.geometry.get('width', 10e-6)
        f = L / np.sqrt(L**2 + (w/2)**2)
        B = self.mu_r * mu_0 * abs(I) / (2 * w) * f
        return min(B, 1.0) * np.sign(I) # Saturation at 1T

    def solve_quiescent_state(self, V_gate: float) -> Dict[str, float]:
        """
        Compute the DC operating point.
        """
        # 1. Gate Current
        I_gate = V_gate / self.R_gate
        B_gate = self.calculate_biot_savart(I_gate)
        
        # 2. Iterate for Drain Current (Self-consistent)
        I_drain = 0.0 # Initial guess
        for _ in range(10):
            V_drain = max(0.0, min(self.V_DD, self.V_DD - I_drain * self.R_load))
            
            # Field across gap (Source to Gate-Plate)
            d = self.dist_matrix[0, 1]
            E = abs(V_drain) / d + 1e6 # Background field to avoid zero
            
            J = wkb_tunneling_current(E, B_gate, d)
            A = self.geometry.get('length', 100e-6) * self.geometry.get('width', 10e-6)
            
            # Damping for stability
            I_new = J * A
            I_drain = 0.5 * I_drain + 0.5 * I_new
            
        return {
            'V_gate': V_gate,
            'I_gate': I_gate,
            'V_drain': max(0.0, self.V_DD - I_drain * self.R_load),
            'I_drain': I_drain,
            'B_gate': B_gate
        }

    def __repr__(self) -> str:
        return f"UPlateFTA(V_DD={self.V_DD}V, plates={len(self.C_matrix)})"
