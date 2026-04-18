"""
IV Analyzer - DC Characterization Tool
--------------------------------------
Sweeps gate/drain voltages to extract device performance metrics.
"""

import numpy as np
import matplotlib.pyplot as plt
from typing import Dict, Any, Optional, Tuple

class IVAnalyzer:
    """
    Standard DC analyzer for FTA devices.
    """
    def __init__(self, config: Dict):
        self.config = config
        
    def run_sweep(self, device, vg_range: Tuple[float, float, int]) -> Dict[str, np.ndarray]:
        """
        Run a gate voltage sweep (V_gate vs I_drain).
        """
        vg_vals = np.linspace(vg_range[0], vg_range[1], vg_range[2])
        id_vals = []
        vd_vals = []
        
        print(f"[IV] Sweeping V_gate from {vg_range[0]}V to {vg_range[1]}V...")
        
        for vg in vg_vals:
            res = device.solve_quiescent_state(vg)
            id_vals.append(res['I_drain'])
            vd_vals.append(res['V_drain'])
            
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.plot(vg_vals, np.array(id_vals) * 1000, 'b-', label='I_drain (mA)')
        ax.set_xlabel('Gate Voltage (V)')
        ax.set_ylabel('Drain Current (mA)')
        ax.set_title(f'IV Characteristics - {device.__class__.__name__}')
        ax.grid(True, linestyle='--')
        
        return {
            'vg': vg_vals,
            'id': np.array(id_vals),
            'vd': np.array(vd_vals),
            'figure': fig
        }
