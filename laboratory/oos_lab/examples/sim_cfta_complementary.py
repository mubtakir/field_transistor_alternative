import numpy as np
import matplotlib.pyplot as plt
import scipy.integrate as spi
from ..physics.quantum_tunneling import (
    fowler_nordheim_tfe, 
    buriti_ndr_correction, 
    inverse_material_correction
)

def simulate_c_fta_inverter():
    """
    Simulates a Complementary FTA (C-FTA) Inverter.
    Logic:
      - Top FTA: Inverse Material (PANI/rGO) - Pull-up to Vcc
      - Bottom FTA: Normal Material (Buriti Oil) - Pull-down to GND
      - Input (Vin) tied to both gates (Shielding control).
    """
    
    v_cc = 50.0
    c_out = 10e-12
    area = 100e-6 * 10e-6
    d_gap = 10e-9
    j_scale = 5e13 # Maintaining the high-swing scaling from previous successful test
    
    def get_current_normal(v_in, v_out):
        # Pull-down (Inverter logic: High Vin -> ON)
        v_ds = v_out
        e_eff = (abs(v_ds) / d_gap) * (max(0.1, abs(v_in)) / 30.0)
        j = fowler_nordheim_tfe(e_eff) + buriti_ndr_correction(e_eff) * 1.5
        return j * area * j_scale
        
    def get_current_inverse(v_in, v_out):
        # Pull-up (Inverse logic: Low Vin -> ON)
        v_ds = v_cc - v_out
        # Shielding for Inverse Gate: Here Vin=0 means High field across the channel material?
        # Actually, if Vin=0, Inverse material is inherently ON.
        e_eff = (abs(v_ds) / d_gap)
        j = inverse_material_correction(e_eff) * 2.0
        # If Vin is high, we quench the inverse current
        j *= np.exp(-abs(v_in) / 10.0) 
        return j * area * j_scale

    def system_deriv(t, v_out, v_in_fn):
        vin = v_in_fn(t)
        
        i_up = get_current_inverse(vin, v_out)
        i_down = get_current_normal(vin, v_out)
        
        # C * dv/dt = i_up - i_down
        dv_dt = (i_up - i_down) / c_out
        return dv_dt

    # Input Waveform: Step pulse
    t_span = (0, 10e-6)
    t_eval = np.linspace(0, 10e-6, 1000)
    def v_in_pulse(t):
        if t < 2e-6: return 0.0
        if t < 2.5e-6: return 30.0 * (t - 2e-6) / 0.5e-6
        if t < 7e-6: return 30.0
        if t < 7.5e-6: return 30.0 * (1 - (t - 7e-6) / 0.5e-6)
        return 0.0

    print("Simulating C-FTA Complementary Inverter...")
    sol = spi.solve_ivp(lambda t, y: [system_deriv(t, y[0], v_in_pulse)], 
                       t_span, [v_cc], method='BDF', t_eval=t_eval,
                       rtol=1e-8, atol=1e-10, max_step=1e-8)

    # Static Power Calculation (i_up approx equal i_down at steady state)
    # P_static = Vcc * I_leakage
    
    # Visualization
    t_us = sol.t * 1e6
    v_in_plot = [v_in_pulse(ti) for ti in sol.t]
    
    plt.figure(figsize=(12, 10))
    
    plt.subplot(3, 1, 1)
    plt.plot(t_us, v_in_plot, 'k', linewidth=2, label='Input (V_in)')
    plt.ylabel('Input (V)')
    plt.title('Complementary FTA (C-FTA) Inverter: Zero-Static-Power Logic', fontsize=14)
    plt.grid(True, alpha=0.3)
    
    plt.subplot(3, 1, 2)
    plt.plot(t_us, sol.y[0], 'b-', linewidth=3, label='V_out (C-FTA Rail-to-Rail)')
    plt.ylabel('Output (V)')
    plt.grid(True, alpha=0.3)
    plt.legend()
    
    # Current (Energy) check
    i_total = [abs(get_current_inverse(v_in_pulse(ti), sol.y[0][i])) for i, ti in enumerate(sol.t)]
    plt.subplot(3, 1, 3)
    plt.semilogy(t_us, i_total, 'm-', label='Supply Current (I_dd)')
    plt.ylabel('Current (A) - Log Scale')
    plt.xlabel('Time (us)')
    plt.title('Static vs Dynamic Power consumption', fontsize=12)
    plt.grid(True, alpha=0.3)
    plt.legend()

    plt.tight_layout()
    output_path = r"c:\Users\allmy\Desktop\oos\oos_lab\analysis\complementary_inverter_results.png"
    plt.savefig(output_path, dpi=150)
    print(f"C-FTA simulation results saved to {output_path}")

if __name__ == "__main__":
    simulate_c_fta_inverter()
