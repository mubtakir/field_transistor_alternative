"""
Differential FTA Pair Model - Modular V2.0
-----------------------------------------
Enables anti-phase cancellation for high-linearity amplification.
"""

import numpy as np
from typing import Dict, Any, Tuple
from .u_plate_fta import UPlateFTA

class DifferentialFTA:
    """
    Two matched UPlateFTA units in a differential configuration.
    """
    
    def __init__(self, geometry: Dict, **kwargs):
        self.unit1 = UPlateFTA(geometry, **kwargs)
        self.unit2 = UPlateFTA(geometry, **kwargs)
        
    def solve_differential(self, V_sig: float, V_cm: float = 10.0) -> Dict[str, float]:
        """
        Solve for a differential input signal.
        """
        Vg1 = V_cm + V_sig / 2
        Vg2 = V_cm - V_sig / 2
        
        res1 = self.unit1.solve_quiescent_state(Vg1)
        res2 = self.unit2.solve_quiescent_state(Vg2)
        
        v_out_diff = res1['V_drain'] - res2['V_drain']
        gain = v_out_diff / V_sig if abs(V_sig) > 1e-9 else 0.0
        
        return {
            'V_in_diff': V_sig,
            'V_out_diff': v_out_diff,
            'gain': gain,
            'V_out1': res1['V_drain'],
            'V_out2': res2['V_drain']
        }
