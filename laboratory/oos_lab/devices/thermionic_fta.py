# oos_lab/devices/thermionic_fta.py

import numpy as np
from dataclasses import dataclass
from ..physics.thermionic_fta_solver import ThermionicFTASolver
from ..physics.materials_library import get_material_params

@dataclass
class ThermionicParams:
    """Parameters for the Thermionic-FTA hybrid device."""
    gap_distance: float = 50e-9
    emitter_area: float = 1e-12
    emitter_material: str = 'LaB6'
    insulator_material: str = 'h-BN'
    heater_resistance: float = 28.0
    thermal_resistance: float = 1.45e6
    shielding_factor: float = 0.0076

class ThermionicFTADevice:
    """
    Formalized Thermionic-FTA device model integrated into oos_lab.
    Supports hybrid emission, active cooling (QTMS), and shielding.
    """
    
    def __init__(self, params: ThermionicParams = None):
        self.p = params or ThermionicParams()
        
        # Pull material constants from library
        m_emitter = get_material_params(self.p.emitter_material)
        m_insulator = get_material_params(self.p.insulator_material)
        
        config = {
            'gap_distance': self.p.gap_distance,
            'emitter_area': self.p.emitter_area,
            'work_function': m_emitter.get('work_function', 4.5),
            'heater_resistance': self.p.heater_resistance,
            'thermal_resistance': self.p.thermal_resistance,
            'shielding_factor': self.p.shielding_factor,
        }
        
        self.solver = ThermionicFTASolver(config)
        
    def simulate_iv(self, v_ds_range, v_gate=0.0, v_heater=0.0):
        """Standard IV sweep for this thermionic device."""
        results = []
        for v_ds in v_ds_range:
            j_tot, breakdown = self.solver.solve_steady_state(v_ds, v_gate, v_heater)
            results.append(breakdown)
        return results

    def simulate_cooling(self, t_ambient_range, v_ds=5.0, v_gate=2.0):
        """Simulate heat scavenging efficiency (QTMS mode)."""
        results = []
        for t_amb in t_ambient_range:
            self.solver.T_ambient = t_amb
            j_tot, breakdown = self.solver.solve_steady_state(v_ds, v_gate, 0.0)
            results.append(breakdown)
        return results
