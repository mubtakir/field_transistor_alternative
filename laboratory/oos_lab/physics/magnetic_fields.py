"""
Magnetic Field Models: Biot-Savart, Mutual Inductance.
Extracted from FTA Phase 2-6 validated simulation scripts.
"""
import numpy as np
from ..constants import mu_0, B_sat_mu_metal


def curie_temp_permeability(T, mu_r=50000.0):
    """Calculate temperature-dependent permeability for Mu-metal."""
    from ..constants import T_curie_mu_metal
    return 1.0 + (mu_r - 1.0) * max(0.0, (T_curie_mu_metal - T) / T_curie_mu_metal)

def plate_biot_savart(I, width=10e-6, length=100e-6, mu_r=50000.0, T=300.0):
    """
    Computes magnetic field B from a finite-width plate.
     Expert suggestion: Added temperature-dependent permeability.
    """
    mu_r_eff = curie_temp_permeability(T, mu_r)
    factor = length / np.sqrt(length**2 + (width / 2.0)**2)
    B_raw = (mu_r_eff * mu_0 * abs(I) / (2.0 * width)) * factor
    return min(B_raw, B_sat_mu_metal) * np.sign(I)


def compute_skin_depth(freq, rho=1.68e-8, mu_r=1.0):
    """
    Compute Skin Depth (delta) for conductors at high frequency.
    
    Parameters
    ----------
    freq : float
        Frequency (Hz).
    rho : float
        Resistivity (Ohm*m), default for Copper.
    mu_r : float
        Relative permeability.
    """
    omega = 2 * np.pi * freq
    if omega == 0:
        return np.inf
    delta = np.sqrt(2 * rho / (omega * mu_r * mu_0))
    return delta


def wave_impedance(freq, eps_r=3.9, mu_r=1.0):
    """
    Compute Wave Impedance in the dielectric gap.
    Requested by expert for nano-gap behavior.
    """
    from ..constants import eps_0
    eta = np.sqrt((mu_r * mu_0) / (eps_r * eps_0))
    return eta


def build_inductance_matrix(n_plates, length, width, dist_matrix, k_coupling=0.999):
    """
    Build the mutual inductance matrix for a multi-plate system.
    
    Parameters
    ----------
    n_plates : int
        Number of plates.
    length : float
        Plate length (meters).
    width : float
        Plate width (meters).
    dist_matrix : ndarray
        Distance matrix between plates (meters).
    k_coupling : float
        Near-field coupling coefficient (0 to 1).
    
    Returns
    -------
    L_matrix : ndarray (n_plates x n_plates)
        Inductance matrix (Henries).
    """
    L_self = (mu_0 * length / (2 * np.pi)) * (np.log(2.0 * length / width) + 0.5)
    L_matrix = np.zeros((n_plates, n_plates))
    for i in range(n_plates):
        for j in range(n_plates):
            if i == j:
                L_matrix[i, j] = L_self
            else:
                L_matrix[i, j] = L_self * k_coupling * np.exp(-dist_matrix[i, j] * 1e6)
    return L_matrix


def gap_field(B_plate_i, B_plate_j, I_i, I_j):
    """
    Compute the effective magnetic field in the gap between two plates,
    accounting for current direction (Spin-Valve effect).
    
    Parameters
    ----------
    B_plate_i, B_plate_j : float
        B-field from each plate.
    I_i, I_j : float
        Current through each plate.
    
    Returns
    -------
    B_gap : float
        Effective gap field (Tesla).
    """
    if np.sign(I_i) == np.sign(I_j):
        # Parallel: fields cancel in gap
        return abs(B_plate_i - B_plate_j)
    else:
        # Anti-parallel: fields add in gap
        return abs(B_plate_i) + abs(B_plate_j)
