"""
FTA NOT Gate Model - Phase 7
---------------------------
Implements a single-input inverter using the FTA modular architecture.
"""

import numpy as np
from typing import Dict, Any
from .u_plate_fta import UPlateFTA

class FTANotGate:
    """
    FTA-based Inverter (NOT Gate).
    Consists of a single FTA device and a pull-up resistor.
    """
    
    def __init__(self, geometry: Dict, **kwargs):
        self.device = UPlateFTA(geometry, **kwargs)
        self.V_DD = kwargs.get('V_DD', 5.0) # Standard logic voltage
        self.R_load = kwargs.get('R_load', 5000.0)
        
    def solve(self, V_in: float) -> Dict[str, float]:
        """
        Solve the logic state.
        V_High (Logic 1) -> Low V_out (Logic 0)
        V_Low (Logic 0) -> High V_out (Logic 1)
        """
        res = self.device.solve_quiescent_state(V_in)
        V_out = res['V_drain']
        
        # Logic thresholds
        logic_out = 1 if V_out > 0.7 * self.V_DD else 0
        
        return {
            'V_in': V_in,
            'V_out': V_out,
            'logic_out': logic_out,
            'I_static': res['I_drain']
        }

class FTAAndGate:
    """
    FTA-based AND Gate (2-input).
    Uses two series FTA devices (Simplified Wired-AND).
    """
    def __init__(self, geometry: Dict, **kwargs):
        self.dev1 = UPlateFTA(geometry, **kwargs)
        self.dev2 = UPlateFTA(geometry, **kwargs)
        self.V_DD = kwargs.get('V_DD', 5.0)

    def solve(self, V1: float, V2: float) -> Dict[str, float]:
        res1 = self.dev1.solve_quiescent_state(V1)
        res2 = self.dev2.solve_quiescent_state(V2)
        
        # Wired-AND approximation: Output is high only if both pull-downs are OFF
        # (Assuming depletion-mode like behavior for Logic 1)
        # For our U-Plate: Logic 0 = 0V (Current Blocking), Logic 1 = 10V (Current Flowing)
        # This implementation matches the project's 'Differential' logic where 
        # higher input voltage increases drain current.
        
        v_out = (res1['V_drain'] + res2['V_drain']) / 2
        logic_out = 1 if v_out > 0.8 * self.V_DD else 0
        
        return {'V_out': v_out, 'logic_out': logic_out}

class FTAOrGate:
    """
    FTA-based OR Gate (2-input).
    Uses two parallel FTA devices.
    """
    def __init__(self, geometry: Dict, **kwargs):
        self.dev1 = UPlateFTA(geometry, **kwargs)
        self.dev2 = UPlateFTA(geometry, **kwargs)
        self.V_DD = kwargs.get('V_DD', 5.0)

    def solve(self, V1: float, V2: float) -> Dict[str, float]:
        res1 = self.dev1.solve_quiescent_state(V1)
        res2 = self.dev2.solve_quiescent_state(V2)
        
        # Parallel OR: Output is high if either device is OFF (High R)
        v_out = max(res1['V_drain'], res2['V_drain'])
        logic_out = 1 if v_out > 0.4 * self.V_DD else 0
        
        return {'V_out': v_out, 'logic_out': logic_out}
