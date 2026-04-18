
import numpy as np
from typing import Dict, Any
from oos_lab.fta_lab.device_models.nested_inductor_fta import NestedInductorFTA
from oos_lab.constants import eps_0, mu_0
from oos_lab.physics.quantum_tunneling import wkb_tunneling_current, fowler_nordheim_tfe

class GrapheneFTA(NestedInductorFTA):
    """
    Graphene-Gate FTA Model.
    Optimized for THz switching by leveraging Graphene's atomic thinness, 
    low parasitic capacitance, and field transparency.
    """
    
    def __init__(self, geometry: Dict, materials: Dict = None, **kwargs):
        # Override materials for Graphene transparency
        if materials is None:
            materials = {}
        materials['gate_transparency'] = kwargs.get('transparency', 0.95)
        materials['gate_work_function'] = kwargs.get('phi_gate', 4.5)
        
        super().__init__(geometry, materials, **kwargs)
        
        # Scaling Capacitance: Graphene is atomically thin, reducing geometric cap
        # We model this by a '2D geometric factor'
        self.C_2D_factor = kwargs.get('c_factor', 0.05) # 95% reduction in parasitic cap
        self.C_matrix *= self.C_2D_factor
        self.C_inv = np.linalg.inv(self.C_matrix)
        
        # Scaling Resistance: Graphene has ultra-high mobility
        self.R_plate_graphene = kwargs.get('R_graphene', 50.0) # Lower than standard 500 Ohm
        
    def solve_thz_transient(self, t_span, v_gate_fn, v_source=5.0, v_drain=0.0, resolution=1000):
        """
        Specialized transient solver for THz range with field transparency.
        """
        import scipy.integrate as spi
        
        transparency = self.materials.get('gate_transparency', 0.95)
        phi = self.materials.get('gate_work_function', 4.5)
        
        def system_deriv(t, state):
            V = state[0:6]
            I_long = state[6:12]
            
            V_drive = np.zeros(6)
            V_drive[1] = v_gate_fn(t)
            V_drive[0] = v_source
            V_drive[4] = v_drain
            
            # dI/dt (Longitudinal Magnetic Field path)
            R_vector = np.full(6, self.R_plate)
            R_vector[1] = self.R_plate_graphene
            
            V_L = V_drive - R_vector * I_long - V
            dI_dt = self.L_inv @ V_L
            
            # dV/dt (Capacitive Charging path)
            I_tunnel = np.zeros(6)
            V_gap_01 = V[0] - V[1]
            E_eff = (abs(V_gap_01) + transparency * abs(V[4] - V[1])) / self.gap_thickness
            
            J = fowler_nordheim_tfe(E_eff, T=300.0, Phi_B_eV=phi)
            It = J * self.area
            I_tunnel[0] -= It
            I_tunnel[1] += It
            
            # Recharge current from Source/Gate-Drive to the Plates
            # I_ch = (V_drive - V) / R_recharge
            I_recharge = (V_drive - V) / R_vector
            
            # Total current charging the capacitors
            # C dV/dt = I_tunnel + I_recharge
            dV_dt = self.C_inv @ (I_tunnel + I_recharge)
            
            return np.concatenate([dV_dt, dI_dt])

        y0 = np.zeros(12)
        # Using 'Radau' or 'BDF' for stiff THz dynamics
        sol = spi.solve_ivp(system_deriv, t_span, y0, method='Radau', 
                           t_eval=np.linspace(t_span[0], t_span[1], resolution))
        return sol
