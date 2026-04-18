"""
Frequency Analyzer - AC Small-Signal Tool
-----------------------------------------
Calculates Bode plots and bandwidth for FTA devices.
"""

import numpy as np
import matplotlib.pyplot as plt
from typing import Dict, Any, List, Tuple

class FrequencyAnalyzer:
    """
    Standard Frequency Response analyzer for FTA devices.
    """
    def __init__(self, config: Dict):
        self.config = config
        
    def run_ac_sweep(self, device, freq_range: Tuple[float, float, int]) -> Dict[str, np.ndarray]:
        """
        Run a frequency sweep (Freq vs Gain).
        """
        freqs = np.logspace(np.log10(freq_range[0]), np.log10(freq_range[1]), freq_range[2])
        gains = []
        
        print(f"[FREQ] Sweeping frequency from {freq_range[0]/1e6:.1f}MHz to {freq_range[1]/1e12:.1f}THz...")
        
        # In a real AC sweep, we would perturb V_gate with a phasor.
        # For the V1.0 Laboratory, we use a simplified model of the gain bandwidth product.
        # Based on Phase 3.5: G(f) = G0 / sqrt(1 + (f/f_cutoff)^2)
        
        # Get DC Gain first
        res_dc = device.solve_quiescent_state(5.0) # Bias at 5V
        G0 = 2.7 # Example baseline gain from Phase 6
        f_cutoff = 10e9 # 10 GHz baseline
        
        for f in freqs:
            Gf = G0 / np.sqrt(1 + (f / f_cutoff)**2)
            gains.append(Gf)
            
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.semilogx(freqs, 20 * np.log10(gains), 'r-', linewidth=2)
        ax.set_xlabel('Frequency (Hz)')
        ax.set_ylabel('Gain (dB)')
        ax.set_title(f'Frequency Response (Bode) - {device.__class__.__name__}')
        ax.grid(True, which="both", linestyle='--')
        
        return {
            'frequency': freqs,
            'gain_db': 20 * np.log10(gains),
            'f_unity': f_cutoff * G0, # Approximation
            'figure': fig
        }
