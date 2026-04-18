"""
Spintronic Models: Tunnel Magnetoresistance (TMR), Giant Magnetoresistance (GMR).
"""
import numpy as np


def tmr_modulation(B_field, Gamma_spin=3e8):
    """
    Compute the spintronic TMR enhancement factor.
    
    When B=0, factor=1 (no modulation).
    When B is strong, the factor exponentially suppresses tunneling.
    
    Parameters
    ----------
    B_field : float
        Magnetic field (Tesla).
    Gamma_spin : float
        Spin-Orbit coupling strength.
    
    Returns
    -------
    factor : float
        Multiplicative factor for tunneling current (0 to 1).
    """
    suppression = Gamma_spin * abs(B_field)
    return np.exp(-suppression) if suppression < 100 else 0.0


def spin_valve_state(I_source, I_gate):
    """
    Determine the Spin-Valve state based on current directions.
    
    Parameters
    ----------
    I_source : float
        Source plate current.
    I_gate : float
        Gate plate current.
    
    Returns
    -------
    state : str
        'ON' (parallel, B cancels) or 'OFF' (anti-parallel, B adds).
    """
    if np.sign(I_source) == np.sign(I_gate):
        return 'ON'
    else:
        return 'OFF'
