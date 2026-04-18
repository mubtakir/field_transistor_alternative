import numpy as np
from typing import Dict, Any, Optional
from ..constants import eps_0
from .nested_inductor_fta import NestedInductorFTA
from ...physics.quantum_tunneling import (
    fowler_nordheim_tfe, 
    buriti_ndr_correction, 
    vo2_ndr_correction
)

class NaturalFTA(NestedInductorFTA):
    """
    FTA device model that incorporates Natural NDR materials (Buriti Oil or VO2)
    for intrinsic linearization.
    """
    
    def __init__(self, geometry: Dict, materials: Dict = None, **kwargs):
        super().__init__(geometry, materials, **kwargs)
        self.material_type = kwargs.get('material_type', 'buriti') # 'buriti' or 'vo2'
        self.compensation_factor = kwargs.get('compensation_factor', 1.0)
        
    def solve_transient(self, t_span, v_gate_fn, v_source=50.0, v_drain=0.0):
        """
        Modified transient solver with natural NDR compensation.
        """
        import scipy.integrate as spi
        
        def system_deriv(t, state):
            # Same dynamics as NestedInductorFTA
            V = state[0:6]
            I_long = state[6:12]
            
            V_drive = np.zeros(6)
            V_drive[1] = v_gate_fn(t)
            V_drive[0] = v_source
            V_drive[4] = v_drain
            
            V_L = V_drive - self.R_plate * I_long - V
            dI_dt = self.L_inv @ V_L
            
            # Tunneling with Natural NDR
            I_tunnel = np.zeros(6)
            E = abs(V[0] - V[1]) / self.gap_thickness
            
            # 1. Base Fowler-Nordheim (The "Convex" part)
            J_fn = fowler_nordheim_tfe(E, T=300.0)
            
            # 2. Natural NDR Correction (The "Concave" part)
            if self.material_type == 'buriti':
                J_cor = buriti_ndr_correction(E)
            elif self.material_type == 'vo2':
                J_cor = vo2_ndr_correction(E)
            elif self.material_type == 'pani_rgo':
                from ...physics.quantum_tunneling import inverse_material_correction
                J_cor = inverse_material_correction(E)
            else:
                J_cor = 0.0
                
            J_total = J_fn + J_cor * self.compensation_factor
            
            It = J_total * self.area
            I_tunnel[0] -= It
            I_tunnel[1] += It
            
            dV_dt = self.C_inv @ I_tunnel
            return np.concatenate([dV_dt, dI_dt])

        y0 = np.zeros(12)
        sol = spi.solve_ivp(system_deriv, t_span, y0, method='BDF', t_eval=np.linspace(t_span[0], t_span[1], 500))
        return sol
