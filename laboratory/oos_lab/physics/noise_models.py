
import numpy as np

def calculate_shot_noise(I, bandwidth=1.0e9):
    """
    S_id = 2 * q * I
    Spectral density of shot noise in Amperes^2/Hz
    """
    q_e = 1.602e-19
    return 2.0 * q_e * I * bandwidth

def calculate_thermal_noise(R, T=300.0, bandwidth=1.0e9):
    """
    S_v = 4 * k * T * R
    Spectral density of thermal noise in Volts^2/Hz
    """
    k_b = 1.38e-23
    return 4.0 * k_b * T * R * bandwidth

def calculate_flicker_noise(I, f, K=1e-25):
    """
    S_f = K * I^2 / f
    Simplified 1/f noise model for FTA tunneling defects
    """
    return K * (I**2) / (f + 1e-3)

def apply_noise_to_current(I, T=300.0, bandwidth=1.0e9):
    """
    Returns total RMS noise current including shot and thermal contributions
    """
    shot_n = calculate_shot_noise(abs(I), bandwidth)
    # Estimated resistance from FTA current rise
    R_eff = 1.0 / (abs(I) / 1.0 + 1e-12) 
    thermal_n_v = calculate_thermal_noise(R_eff, T, bandwidth)
    thermal_n_i = thermal_n_v / (R_eff**2 + 1e-12)
    
    total_noise_rms = np.sqrt(shot_n + thermal_n_i)
    return total_noise_rms
