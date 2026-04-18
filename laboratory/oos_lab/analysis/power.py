"""
Power Analysis: Energy-per-operation, dynamic power.
"""
import numpy as np
from ..constants import q_e


def energy_per_operation(C_load, V_DD):
    """
    Compute energy per switching operation.
    E = C * V^2 (dynamic switching energy).
    
    Parameters
    ----------
    C_load : float
        Load capacitance (Farads).
    V_DD : float
        Supply voltage (V).
    
    Returns
    -------
    energy_fJ : float
        Energy in femtojoules.
    """
    return C_load * V_DD ** 2 * 1e15


def dynamic_power(energy_fJ, frequency):
    """
    Compute dynamic power dissipation.
    P = E * f.
    
    Parameters
    ----------
    energy_fJ : float
        Energy per operation (femtojoules).
    frequency : float
        Switching frequency (Hz).
    
    Returns
    -------
    power_mW : float
        Power in milliwatts.
    """
    return energy_fJ * frequency * 1e-15 * 1e3


def power_report(C_load, voltages=[5, 12, 50], frequencies=[1e9, 10e9, 100e9]):
    """
    Generate a comprehensive power analysis report.
    
    Returns
    -------
    report : list of dict
    """
    report = []
    for V in voltages:
        e_fJ = energy_per_operation(C_load, V)
        for f in frequencies:
            p_mW = dynamic_power(e_fJ, f)
            report.append({
                'V_DD': V,
                'E_fJ': e_fJ,
                'freq_GHz': f / 1e9,
                'P_mW': p_mW,
            })
    return report
