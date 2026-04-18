"""
Transient Analysis: Pulse response, rise/fall time measurement.
"""
import numpy as np
from ..devices.u_plate import UPlateDevice, UPlateParams
from ..solvers.ode_system import solve_ode


def pulse_response(device, pulse_amplitude=1.0, pulse_width=1e-9,
                   t_window=None, output_plate=4, n_points=2000):
    """
    Apply a step pulse to the gate and measure transient response.
    
    Parameters
    ----------
    device : UPlateDevice
        The device to analyze.
    pulse_amplitude : float
        Pulse height (V).
    pulse_width : float
        Pulse ON duration (seconds).
    t_window : float
        Total analysis window (seconds). Default: 3x pulse_width.
    output_plate : int
        Index of output plate.
    n_points : int
        Number of sample points.
    
    Returns
    -------
    metrics : dict
        'rise_time_ps', 'fall_time_ps', 'V_max', 'V_min', 'swing',
        'time', 'voltage'.
    """
    if t_window is None:
        t_window = pulse_width * 3
    
    def gate_fn(t):
        return pulse_amplitude if t < pulse_width else 0.0
    
    sol = device.simulate(gate_fn, t_span=(0, t_window), n_points=n_points)
    
    V_out = sol['voltages'][output_plate, :]
    t = sol['time']
    V_max = np.max(V_out)
    V_min = np.min(V_out)
    swing = V_max - V_min
    
    # Rise time (10% to 90%)
    th_10 = V_min + 0.1 * swing
    th_90 = V_min + 0.9 * swing
    rise_time_ps = 0
    
    try:
        t_10 = t[np.where(V_out >= th_10)[0][0]]
        t_90 = t[np.where(V_out >= th_90)[0][0]]
        rise_time_ps = (t_90 - t_10) * 1e12
    except (IndexError, ValueError):
        rise_time_ps = float('inf')
    
    # Fall time (90% to 10%)
    fall_time_ps = float('inf')
    peak_idx = np.argmax(V_out)
    V_after = V_out[peak_idx:]
    t_after = t[peak_idx:]
    
    try:
        t_f90 = t_after[np.where(V_after <= th_90)[0][0]]
        t_f10 = t_after[np.where(V_after <= th_10)[0][0]]
        fall_time_ps = (t_f10 - t_f90) * 1e12
    except (IndexError, ValueError):
        pass
    
    return {
        'rise_time_ps': rise_time_ps,
        'fall_time_ps': fall_time_ps,
        'V_max': V_max,
        'V_min': V_min,
        'swing': swing,
        'time': t,
        'voltage': V_out,
    }


def print_pulse_metrics(metrics):
    """Pretty-print pulse response metrics."""
    print(f"Rise Time:     {metrics['rise_time_ps']:.2f} ps")
    print(f"Fall Time:     {metrics['fall_time_ps']:.2f} ps")
    print(f"V_max:         {metrics['V_max']:.4f} V")
    print(f"V_min:         {metrics['V_min']:.4f} V")
    print(f"Output Swing:  {metrics['swing']:.4f} V")
