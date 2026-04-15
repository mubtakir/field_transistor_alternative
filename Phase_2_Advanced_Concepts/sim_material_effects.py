import numpy as np
import matplotlib.pyplot as plt

def sim_material_effects():
    """
    Simulates NICL performance across different materials.
    """
    freqs = np.logspace(4, 7, 2000)
    w = 2 * np.pi * freqs
    l_base = 20e-6
    c_base = 100e-12
    
    # Material Definitions (Resistance impacts Q-factor)
    materials = {
        'Copper': {'res': 0.5, 'color': 'orange', 'mu_r': 1},
        'Ferrite-Core': {'res': 0.5, 'color': 'brown', 'mu_r': 500},
        'Graphene (Ideal)': {'res': 0.05, 'color': 'black', 'mu_r': 1}
    }
    
    plt.figure(figsize=(12, 8))
    
    for name, props in materials.items():
        # Effect of Mu_r on L
        l_eff = l_base * props['mu_r']
        # Resonant Frequency
        res_f = 1 / (2 * np.pi * np.sqrt(l_eff * c_base))
        
        # Q-factor = (1/R) * sqrt(L/C)
        q = (1 / props['res']) * np.sqrt(l_eff / c_base)
        
        # Signal Gain
        gain = 1 / np.sqrt(1 + (q * (freqs/res_f - res_f/freqs))**2)
        
        plt.semilogx(freqs, gain, label=f'{name} (Q={q:.1f})', color=props['color'], lw=2)

    plt.title("NICL Material Optimization: Impact of Conductivity & Permeability")
    plt.xlabel("Frequency (Hz)")
    plt.ylabel("Normalized Signal Gain")
    plt.grid(True, which='both', alpha=0.3)
    plt.legend()
    plt.savefig(r'C:\Users\allmy\Desktop\aaa\field_transistor_alternative\Phase_2_Advanced_Concepts\nicl_material_effects.png')
    print("[+] Material effects graph generated: Phase_2_Advanced_Concepts/nicl_material_effects.png")

if __name__ == "__main__":
    sim_material_effects()
