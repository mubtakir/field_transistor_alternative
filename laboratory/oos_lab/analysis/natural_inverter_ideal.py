import numpy as np
import matplotlib.pyplot as plt
import scipy.integrate as spi
from ..physics.quantum_tunneling import fowler_nordheim_tfe, buriti_ndr_correction

def simulate_ideal_natural_inverter():
    """
    Simulates an ideal 2-plate FTA Inverter with Natural NDR.
    This model simplifies the stack to ensure numerical stability while 
    demonstrating the logic level improvement.
    """
    
    v_cc = 50.0
    r_load = 1e5    # 100k load
    c_out = 10e-12  # 10pF output capacitance
    area = 100e-6 * 10e-6
    d_gap = 10e-9
    
    # Scaling to achieve mA range currents for full 50V swing
    j_scale = 5e13 
    v_shield = 12.0 # Shielding effectiveness
    
    def get_current(v_in, v_out, use_buriti=False):
        # The Output node (v_out) is pulled to Vcc.
        # Input node (v_in) turns the device ON by enhancing the local field (Inverter logic).
        v_ds = v_out
        v_gate_effective = max(0.1, abs(v_in)) # Prevent log(0)
        e_shielded = (abs(v_ds) / d_gap) * (v_gate_effective / 30.0) # 30V is gate ref
        
        # Base Fowler-Nordheim
        j = fowler_nordheim_tfe(e_shielded, T=300.0)
        
        # Natural NDR (Buriti)
        if use_buriti:
            # NDR works on the effective field E_shielded
            j += buriti_ndr_correction(e_shielded) * 1.8
            
        return j * area * j_scale * np.sign(v_ds)

    def system_deriv(t, v_out, v_in_fn, use_buriti):
        vin = v_in_fn(t)
        # i_load = i_device
        # C * dv_out/dt = (Vcc - v_out)/R - i_device
        i_device = get_current(vin, v_out, use_buriti)
        i_load = (v_cc - v_out) / r_load
        
        dv_dt = (i_load - i_device) / c_out
        return dv_dt

    # Input Pulse
    t_span = (0, 10e-6)
    t_eval = np.linspace(0, 10e-6, 1000)
    def v_in_pulse(t):
        # Smoother pulse to help solver convergence
        if t < 2e-6: return 0.0
        if t < 2.5e-6: return 30.0 * (t - 2e-6) / 0.5e-6
        if t < 7e-6: return 30.0
        if t < 7.5e-6: return 30.0 * (1 - (t - 7e-6) / 0.5e-6)
        return 0.0

    print("Simulating Buriti FTA Inverter...")
    # Using more robust solver settings
    sol_buriti = spi.solve_ivp(lambda t, y: [system_deriv(t, y[0], v_in_pulse, True)], 
                              t_span, [v_cc], method='BDF', t_eval=t_eval, 
                              rtol=1e-8, atol=1e-10, max_step=1e-8)
    
    print("Simulating Standard FTA Inverter...")
    sol_std = spi.solve_ivp(lambda t, y: [system_deriv(t, y[0], v_in_pulse, False)], 
                           t_span, [v_cc], method='BDF', t_eval=t_eval,
                           rtol=1e-8, atol=1e-10, max_step=1e-8)

    # Visualization
    t_us = sol_buriti.t * 1e6
    v_in_plot = [v_in_pulse(ti) for ti in sol_buriti.t]
    
    plt.figure(figsize=(12, 10))
    
    plt.subplot(2, 1, 1)
    plt.plot(t_us, v_in_plot, 'k', linewidth=2, label='Input (V_in)')
    plt.ylabel('Input Voltage (V)')
    plt.title('Idealized FTA Inverter Performance: Natural NDR (Buriti) vs Standard', fontsize=14)
    plt.grid(True, alpha=0.3)
    plt.legend()
    
    plt.subplot(2, 1, 2)
    plt.plot(t_us, sol_buriti.y[0], 'g-', linewidth=2.5, label='V_out (Buriti Linearized)')
    plt.plot(t_us, sol_std.y[0], 'r--', alpha=0.7, label='V_out (Standard Non-linear)')
    plt.ylabel('Output Voltage (V)')
    plt.xlabel('Time (us)')
    plt.grid(True, alpha=0.3)
    plt.legend()
    
    plt.tight_layout()
    output_path = r"c:\Users\allmy\Desktop\oos\oos_lab\analysis\natural_inverter_ideal_results.png"
    plt.savefig(output_path, dpi=150)
    print(f"Idealized logic simulation saved to {output_path}")

if __name__ == "__main__":
    simulate_ideal_natural_inverter()
