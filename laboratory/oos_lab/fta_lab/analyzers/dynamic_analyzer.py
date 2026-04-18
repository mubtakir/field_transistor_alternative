import numpy as np
from typing import Dict, Any, List

class DynamicAnalyzer:
    """
    Analyzer for transient and energy-efficiency simulations of FTA devices.
    """
    
    def __init__(self, config: Dict):
        self.config = config
        
    def run_pulse_test(self, device: Any, pulse_params: Dict) -> Dict:
        """
        Run a transient pulse simulation and return metrics.
        
        Args:
            device: An instance of NestedInductorFTA.
            pulse_params: Dictionary with 'v_high', 'v_low', 'duration_ns', 't_total_ns'.
        """
        t_total = pulse_params.get('t_total_ns', 200) * 1e-9
        dur = pulse_params.get('duration_ns', 100) * 1e-9
        vh = pulse_params.get('v_high', 1.0)
        vl = pulse_params.get('v_low', 0.0)
        
        def gate_fn(t):
            return vh if (1e-8 < t < (1e-8 + dur)) else vl
            
        sol = device.solve_transient((0, t_total), gate_fn)
        
        # Calculate Energy Metrics
        i_long_final = sol.y[6:12, -1]
        energy_pj = device.get_magnetic_energy(i_long_final) * 1e12
        
        return {
            "time_ns": (sol.t * 1e9).tolist(),
            "v_gate": sol.y[1].tolist(),
            "v_drain": sol.y[4].tolist(),
            "i_long_gate": (sol.y[7] * 1e3).tolist(),  # mA
            "i_long_drain": (sol.y[10] * 1e3).tolist(), # mA
            "final_energy_pj": energy_pj,
            "gain_peak": float(np.max(np.abs(sol.y[4])))
        }
