"""
Quantum Tunneling Models: WKB, Fowler-Nordheim, Poole-Frenkel.
Extracted from FTA Phase 2-6 validated simulation scripts.
"""
import numpy as np
from ..constants import m_e, q_e, h, h_bar


def wkb_tunneling_current(E_field, B_field=0.0, d_gap=5e-9,
                          Phi_B_eV=1.0, m_eff_ratio=0.5,
                          Gamma_spin=3e8, use_ferro=False, use_rough=False):
    """
    Compute tunneling current density using WKB approximation
    with magnetic field modification (Landau-level shift + Spin-Orbit).
    
    Parameters
    ----------
    E_field : float
        Electric field across the gap (V/m).
    B_field : float
        Magnetic field in the gap (Tesla).
    d_gap : float
        Barrier width (meters).
    Phi_B_eV : float
        Barrier height (eV).
    m_eff_ratio : float
        Effective mass ratio (m_eff / m_e).
    Gamma_spin : float
        Spintronic TMR enhancement factor.
    
    Returns
    -------
    J : float
        Tunneling current density (A/m^2).
    """
    if use_rough:
        d_gap, _ = surface_roughness_model(d_gap)
        
    m_eff = m_eff_ratio * m_e
    Phi_B = Phi_B_eV * q_e
    
    # Ferroelectric Negative Capacitance (NC) effect
    # Enhances effective E-field due to internal gain
    if use_ferro:
        E_eff = E_field * ferroelectric_enhancement(E_field)
    else:
        E_eff = E_field
        
    coeff_E = q_e * E_eff
    coeff_B = Gamma_spin * abs(B_field) * q_e
    alpha = coeff_E - coeff_B
    
    if alpha == 0:
        integral = np.sqrt(2 * m_eff * Phi_B) * d_gap / h_bar
    else:
        x_c = Phi_B / alpha if alpha > 0 else d_gap
        if x_c > d_gap:
            x_c = d_gap
        term1 = Phi_B ** 1.5
        term2 = max(0.0, Phi_B - alpha * x_c) ** 1.5
        integral_core = (2.0 / (3.0 * alpha)) * (term1 - term2)
        integral = (np.sqrt(2 * m_eff) / h_bar) * integral_core
    
    A_eff = (q_e ** 3) / (8 * np.pi * h * Phi_B) * (m_e / m_eff)
    
    if integral > 300:
        return 0.0
    
    return A_eff * (E_eff ** 2) * np.exp(-2 * integral)


def ferroelectric_enhancement(E_field, P_sat=1.0e-5, E_c=1e6, alpha=0.5):
    """
    Model for Ferroelectric Negative Capacitance (NC) enhancement.
    In the NC regime, the internal field is amplified.
    """
    # Simple tanh-based gain model for NC regime near E_c
    # In reality, this comes from dP/dE being negative in the Landau-Khalatnikov model
    gain = 1.0 + alpha * np.exp(-((abs(E_field) - E_c) / (2 * E_c))**2)
    return gain


def surface_roughness_model(d_nominal, roughness_rms=0.2e-9):
    """
    Simulate surface roughness effects on a nano-gap.
    Roughness reduces effective d_gap locally, exponentially increasing tunneling.
    """
    # Local thinning effect: J ~ exp(-d), so avg J is higher than J(avg d).
    # We return an 'effective' d that represents the equivalent uniform gap.
    d_eff = d_nominal - (2 * (roughness_rms**2) / d_nominal) 
    return max(d_eff, 0.5e-9), 1.0


def fowler_nordheim_current(E_field, Phi_B_eV=1.0, m_eff_ratio=0.5):
    """
    Standard Fowler-Nordheim tunneling (no magnetic field).
    Equivalent to wkb_tunneling_current with B_field=0.
    """
    return wkb_tunneling_current(E_field, 0.0, Phi_B_eV=Phi_B_eV,
                                  m_eff_ratio=m_eff_ratio, Gamma_spin=0)


def fowler_nordheim_tfe(E_field, T=300.0, Phi_B_eV=1.0):
    """
    Temperature-enhanced Fowler-Nordheim (Thermal Field Emission).
    Uses Murphy-Good approximation for Fermi-Dirac smearing.
    
    Extracted from: phase1_foundations/sim_supreme_fta_amplifier.py
    This is the model that produced 60.25x gain (300K) and 198.60x gain (400K).
    
    Parameters
    ----------
    E_field : float
        Electric field at the emitting surface (V/m).
    T : float
        Temperature (Kelvin).
    Phi_B_eV : float
        Barrier height (eV).
    
    Returns
    -------
    J : float
        Current density (A/m^2).
    """
    from ..constants import m_e, q_e, h, h_bar, k_B
    
    Phi_J = Phi_B_eV * q_e
    
    # Exact Fowler-Nordheim constants from quantum mechanics
    B_FN = (4 * np.sqrt(2 * m_e) * Phi_J**1.5) / (3 * q_e * h_bar)
    A_FN = (q_e**3) / (8 * np.pi * h * Phi_J)
    
    if E_field < 1e6:
        return 0.0
    E = min(E_field, 1.5e10)  # Safe breakdown limit
    
    # Zero-temperature current density
    exponent = B_FN / E
    if exponent > 60.0:
        exponent = 60.0
    J_0 = A_FN * (E**2) * np.exp(-exponent)
    
    # Murphy-Good thermal correction
    d_F = q_e * h_bar * E / (2 * np.sqrt(2 * m_e * Phi_J))
    if d_F == 0:
        return J_0
    
    temp_term = (np.pi * k_B * T) / d_F
    if 0 < temp_term < np.pi - 0.1:
        J_T = J_0 * temp_term / np.sin(temp_term)
    else:
        J_T = J_0 * 1.5  # Approximation at extreme thermal regime
    
    return J_T


def poole_frenkel_current(E_field, T=300.0, phi_trap_eV=0.8):
    """
    Poole-Frenkel emission model for defect-dominated conduction in insulators.
    Requested by expert for realism in DIY/Solid-state FTA.
    
    Parameters
    ----------
    E_field : float
        Electric field (V/m).
    T : float
        Temperature (Kelvin).
    phi_trap_eV : float
        Trap energy level (eV).
        
    Returns
    -------
    J : float
        Current density (A/m^2).
    """
    from ..constants import k_B, q_e, eps_0, eps_r_sio2, sigma_0_sio2
    
    beta_PF = np.sqrt(q_e**3 / (np.pi * eps_0 * eps_r_sio2))
    exponent = (q_e * phi_trap_eV - beta_PF * np.sqrt(abs(E_field))) / (k_B * T)
    
    # Pre-exponential factor (sigma_0 * E)
    return sigma_0_sio2 * E_field * np.exp(-exponent)


def solve_capacitive_circuit(C_matrix, driving_nodes, driving_voltages, load_caps=None):
    """
    Solve floating node voltages in a capacitive circuit.
    
    Given a capacitance matrix and some driven nodes, compute the voltage
    at all floating (undriven) nodes via matrix inversion.
    
    Extracted from: phase1_foundations/sim_fdm_4plate.py
    
    Parameters
    ----------
    C_matrix : ndarray (N x N)
        Physical capacitance matrix.
    driving_nodes : list of int
        Indices of nodes with forced voltages.
    driving_voltages : list of float
        Voltages at the driven nodes.
    load_caps : dict, optional
        {node_index: load_capacitance} to add parasitic loads.
    
    Returns
    -------
    V_full : ndarray
        Voltage at every node.
    """
    N = C_matrix.shape[0]
    floating_nodes = [i for i in range(N) if i not in driving_nodes]
    C_eff = C_matrix.copy()
    
    if load_caps:
        for node, cap in load_caps.items():
            C_eff[node, node] += cap
    
    C_ff = C_eff[np.ix_(floating_nodes, floating_nodes)]
    C_fd = C_eff[np.ix_(floating_nodes, driving_nodes)]
    
    V_d = np.array(driving_voltages)
    V_f = np.linalg.solve(C_ff, -C_fd @ V_d)
    
    V_full = np.zeros(N)
    for i, idx in enumerate(driving_nodes):
        V_full[idx] = driving_voltages[i]
    for i, idx in enumerate(floating_nodes):
        V_full[idx] = V_f[i]
    
    return V_full


def ndr_gaussian_correction(E_field, J_peak=5e-6, sigma=1e8, E_peak=1e8):
    """
    Compute a Negative Differential Resistance (NDR) correction term.
    This provides a concave curvature (J'' < 0) to compensate for 
    the convex Fowler-Nordheim tunneling curvature.
    
    Parameters
    ----------
    E_field : float
        Electric field (V/m).
    J_peak : float
        Peak correction current density (A/m^2).
    sigma : float
        Width of the NDR region (V/m).
    E_peak : float
        Electric field at the NDR peak (V/m).
        
    Returns
    -------
    J : float
        Correction current density (A/m^2).
    """
    return J_peak * np.exp(-((E_field - E_peak)**2) / (sigma**2))


def buriti_ndr_correction(E_field):
    """
    Natural NDR model for Buriti Oil / Polystyrene blend.
    Derived from Phase 2 research: Carrier hopping & trapping in carotenoids.
    """
    J_peak = 1.2e-7
    E_peak = 1.4e8
    sigma = 0.4e8
    return J_peak * np.exp(-((E_field - E_peak)**2) / (2 * sigma**2))


def vo2_ndr_correction(E_field):
    """
    Natural NDR model for Vanadium Dioxide (VO2) Phase-Transition.
    Driven by the Mott transition (Insulator-to-Metal).
    """
    E_transition = 1.1e8
    width = 0.15e10
    # Sigmoidal-like NDR component representing the transition region
    return 1.5e-7 / (1 + np.exp((E_field - E_transition) * width / 1e8))
def inverse_material_correction(E_field):
    """
    Inverse Gate model (e.g., PANI/rGO or VN).
    High conductivity at low fields, decreasing at high fields (Switching to OFF state).
    """
    J_max = 2.0e-7
    E_critical = 0.5e8
    decay = 2.0e-8
    # Exponential decay to represent inverse switching
    return J_max * np.exp(-E_field * decay)
