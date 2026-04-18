"""
OOS-Lab v1.1: Unified Simulation API
Provides a single entry point for all device simulations.
"""

def simulate(device_type='u_plate', analysis='iv', **params):
    """
    Unified simulation interface.
    
    Args:
        device_type (str): 'u_plate', 'natural', 'nested_inductor', 'differential'
        analysis (str): 'iv', 'ac', 'transient', 'logic', 'bench'
        **params: Arguments passed to the device and solver.
    """
    import numpy as np
    
    # 1. Device Selection
    if device_type == 'u_plate':
        from .devices.u_plate import UPlateDevice
        device = UPlateDevice(**params)
    elif device_type == 'natural':
        from .fta_lab.device_models.natural_fta import NaturalFTA
        device = NaturalFTA(**params)
    elif device_type == 'thermionic_fta':
        from .devices.thermionic_fta import ThermionicFTADevice, ThermionicParams
        import dataclasses
        # Filter params to only include valid ThermionicParams fields
        valid_fields = {f.name for f in dataclasses.fields(ThermionicParams)}
        device_params = {k: v for k, v in params.items() if k in valid_fields}
        device = ThermionicFTADevice(ThermionicParams(**device_params))
    else:
        raise ValueError(f"Unknown device type: {device_type}")
    
    # 2. Analysis Routing
    if analysis == 'iv':
        if device_type == 'thermionic_fta':
            # Analysis-specific params and defaults
            v_ds_range = params.get('v_ds_range', np.linspace(0, 5, 50))
            v_gate = params.get('v_gate', 0.0)
            v_heater = params.get('v_heater', 0.0)
            return device.simulate_iv(v_ds_range, v_gate, v_heater)
        
        from .analysis.fta_lab_bench import FTALabBench
        bench = FTALabBench() # Uses shared physics
        return bench.sweep_IV(**params)
    
    elif analysis == 'ac':
        from .analysis.ac_sweep import bode_plot
        return bode_plot(device, **params)
    
    elif analysis == 'transient':
        from .analysis.transient import pulse_response
        return pulse_response(device, **params)
        
    elif analysis == 'bench':
        from .analysis.fta_lab_bench import FTALabBench
        bench = FTALabBench(**params)
        return bench.multimeter.measure_all()
    
    else:
        raise ValueError(f"Unknown analysis type: {analysis}")
