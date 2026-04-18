"""
Universal Physical Constants for OOS-Lab.
All values in SI units. Change values here to propagate everywhere.
"""
import numpy as np

# Electron
m_e = 9.10938e-31        # Electron rest mass (kg)
q_e = 1.60217e-19        # Elementary charge (C)

# Planck
h = 6.62607e-34          # Planck constant (J*s)
h_bar = 1.05457e-34      # Reduced Planck constant (J*s)

# Electromagnetic
mu_0 = 4 * np.pi * 1e-7  # Vacuum permeability (H/m)
eps_0 = 8.85418e-12       # Vacuum permittivity (F/m)
c_0 = 2.99792e8           # Speed of light (m/s)

# Thermal
k_B = 1.38064e-23        # Boltzmann constant (J/K)

# Material Constants (Specific to FTA)
T_curie_mu_metal = 473.0  # Curie temperature for Mu-metal (K) ~200C
B_sat_mu_metal = 0.75     # Saturation induction for Mu-metal (Tesla)
phi_trap_sio2 = 0.8       # Trap energy level for Poole-Frenkel in SiO2 (eV)
beta_pf_sio2 = 4.0e-24    # Poole-Frenkel coefficient (empirical)
eps_r_sio2 = 3.9          # Relative permittivity of SiO2
sigma_0_sio2 = 1e-5       # Empirical conductivity base for PF model

# Convenient conversions
eV_to_J = q_e            # 1 eV in Joules
J_to_eV = 1.0 / q_e      # 1 Joule in eV
