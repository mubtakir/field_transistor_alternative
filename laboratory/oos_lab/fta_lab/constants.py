"""
Physical Constants for the FTA Virtual Laboratory.
"""
import numpy as np

# Fundamental Constants
m_e = 9.1093837e-31       # Electron mass (kg)
q_e = 1.6021766e-19       # Elementary charge (C)
h = 6.62607015e-34        # Planck constant (J·s)
h_bar = 1.0545718e-34     # Reduced Planck constant (J·s)
h_planck = h              # Alias

mu_0 = 4.0 * np.pi * 1e-7  # Vacuum permeability (H/m)
eps_0 = 8.8541878e-12     # Vacuum permittivity (F/m)
k_B = 1.380649e-23        # Boltzmann constant (J/K)
c_0 = 299792458.0         # Speed of light (m/s)

# Conversion Factors
eV_to_J = q_e
J_to_eV = 1.0 / q_e
nm_to_m = 1e-9
um_to_m = 1e-6
ps_to_s = 1e-12
fs_to_s = 1e-15
GHz_to_Hz = 1e9
THz_to_Hz = 1e12
