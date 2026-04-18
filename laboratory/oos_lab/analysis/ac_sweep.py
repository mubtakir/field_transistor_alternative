"""
AC Analysis: Frequency sweep and Bode plot generation.
"""
import numpy as np
from ..devices.u_plate import UPlateDevice, UPlateParams
from ..solvers.ode_system import solve_ode


def bode_plot(device, freq_range=None, V_signal=0.5, output_plate=4):
    """
    Run a frequency sweep and compute voltage gain at each frequency.
    
    Parameters
    ----------
    device : UPlateDevice
        The device to analyze.
    freq_range : list of float
        Frequencies to test (Hz).
    V_signal : float
        AC signal amplitude (V).
    output_plate : int
        Index of the output plate to measure.
    
    Returns
    -------
    results : list of dict
        Each has 'frequency', 'gain', 'gain_dB', 'phase_deg'.
    """
    if freq_range is None:
        freq_range = [100, 1e3, 5e3, 10e3, 25e3, 50e3]
    
    results = []
    
    for freq in freq_range:
        period = 1.0 / freq
        n_cycles = max(3, int(freq / 100))
        t_end = n_cycles * period
        
        def gate_fn(t):
            return V_signal * np.sin(2 * np.pi * freq * t)
        
        sol = device.simulate(gate_fn, t_span=(0, t_end), n_points=500)
        
        if sol['success']:
            V_out = sol['voltages'][output_plate, :]
            V_out_pp = np.max(V_out) - np.min(V_out)
            gain = V_out_pp / (2 * V_signal) if V_signal > 0 else 0
            gain_dB = 20 * np.log10(gain) if gain > 0 else -100
        else:
            gain = 0
            gain_dB = -100
        
        results.append({
            'frequency': freq,
            'gain': gain,
            'gain_dB': gain_dB,
        })
    
    return results


def print_bode(results):
    """Pretty-print Bode plot results."""
    print(f"{'Frequency':>12} | {'Gain':>8} | {'Gain (dB)':>10}")
    print("-" * 40)
    for r in results:
        f = r['frequency']
        if f >= 1e9:
            f_str = f"{f/1e9:.1f} GHz"
        elif f >= 1e6:
            f_str = f"{f/1e6:.1f} MHz"
        elif f >= 1e3:
            f_str = f"{f/1e3:.1f} kHz"
        else:
            f_str = f"{f:.0f} Hz"
        print(f"{f_str:>12} | {r['gain']:>8.3f} | {r['gain_dB']:>10.2f}")
