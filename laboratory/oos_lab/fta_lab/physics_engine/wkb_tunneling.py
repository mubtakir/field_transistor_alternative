"""
Quantum Tunneling Module - WKB and Fowler-Nordheim Physics
----------------------------------------------------------
Implements the core tunneling physics with Lorentz force quenching.
"""

import numpy as np
from ..constants import q_e, m_e, h_bar, h_planck

def wkb_tunneling_current(E_field, B_field, d_gap, Phi_eV=1.0, m_ratio=0.5, Gamma=3e8):
    """
    Solves the WKB approximation for tunneling through a triangular/trapezoidal barrier.
    Incorporates B-field quenching (Lorentz shift).
    
    Args:
        E_field: Local electric field (V/m).
        B_field: Local magnetic field (T).
        d_gap: Tunnel gap (m).
        Phi_eV: Barrier height (eV).
        m_ratio: Effective mass ratio (m_eff/m_e).
        Gamma: Spintronic coupling factor (Hz).
        
    Returns:
        J: Tunneling current density (A/m^2).
    """
    m_eff = m_ratio * m_e
    Phi = Phi_eV * q_e
    
    # Lorentz quenching: Quasiparticle energy shift
    # Effective driving force = qE - qvB. In semi-classic WKB:
    Gs = Gamma # Orbital/Spin factor
    cB = Gs * abs(B_field) * q_e
    
    alpha = q_e * E_field - cB
    
    if abs(alpha) < 1e-15:
        # Purely rectangular barrier limit
        integ = np.sqrt(2 * m_eff * Phi) * d_gap / h_bar
    else:
        # Effective tunneling distance
        xc = min(Phi / alpha, d_gap) if alpha > 0 else d_gap
        
        # WKB integral: Int(sqrt(2m(Phi - alpha*x)))
        t1 = Phi**1.5
        t2 = max(0.0, Phi - alpha * xc)**1.5
        integ = (np.sqrt(2 * m_eff) / h_bar) * (2.0 / (3.0 * alpha)) * (t1 - t2)
        
    # Pre-exponential factor (Fowler-Nordheim like)
    A = (q_e**3) / (8 * np.pi * h_planck * Phi) * (m_e / m_eff)
    
    # Probability transmission
    if integ > 300: return 0.0 # Numerical floor
    
    return A * (E_field**2) * np.exp(-2 * integ)
