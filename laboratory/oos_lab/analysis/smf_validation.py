import numpy as np
import matplotlib.pyplot as plt
from oos_lab.devices.u_plate import UPlateDevice, UPlateParams

def run_smf_validation():
    print("--- FTA Self-Magnetic Feedback (SMF) Validation ---")
    
    # Define time span for a slow ramp (to see DC-like behavior)
    t_span = (0, 1e-7)
    
    # Gate ramp function: 0 to 12V
    def gate_ramp(t):
        return (t / 1e-7) * 12.0
    
    # 1. Simulate WITHOUT SMF
    print("Simulating WITHOUT SMF...")
    # Increase Gamma_spin to make the effect visible at lower current densities
    params_no_smf = UPlateParams(use_smf=False, Gamma_spin=1e11, plate_width=1e-6) 
    device_no_smf = UPlateDevice(params_no_smf)
    res_no_smf = device_no_smf.simulate(gate_ramp, t_span=t_span)
    
    # 2. Simulate WITH SMF
    print("Simulating WITH SMF...")
    params_smf = UPlateParams(use_smf=True, Gamma_spin=1e11, plate_width=1e-6)
    device_smf = UPlateDevice(params_smf)
    res_smf = device_smf.simulate(gate_ramp, t_span=t_span)
    
    # Extract results
    # Index 1 is the gate, Index 5 is usually the collector in 6-plate config
    t = res_smf['time']
    V_gate = gate_ramp(t)
    
    # Total tunneling current can be estimated from voltage changes if not directly stored,
    # but here we can look at the output voltage V[5] (Collector)
    V_out_no_smf = res_no_smf['voltages'][5, :]
    V_out_smf = res_smf['voltages'][5, :]
    
    # Plotting
    plt.figure(figsize=(10, 6))
    plt.plot(V_gate, V_out_no_smf, '--', label='Without SMF (Pure Exponential)')
    plt.plot(V_gate, V_out_smf, '-', label='With SMF (NMSL Linearized)', linewidth=2)
    plt.xlabel('Gate Voltage (V)')
    plt.ylabel('Collector Voltage (V)')
    plt.title('FTA Nano-Magnetic Self-Linearization (NMSL) Effect')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # Save the result to tmp for verification
    plt.savefig('smf_validation_plot.png')
    print("Plot saved as smf_validation_plot.png")
    
    # Calculate Linearity Improvement (Metric: Second Derivative average)
    d2_no_smf = np.mean(np.abs(np.diff(V_out_no_smf, n=2)))
    d2_smf = np.mean(np.abs(np.diff(V_out_smf, n=2)))
    
    improvement = (d2_no_smf - d2_smf) / d2_no_smf * 100
    print(f"Linearity Improvement: {improvement:.2f}%")
    
    if improvement > 5:
        print("SUCCESS: SMF provides significant self-linearization.")
    else:
        print("NOTE: SMF effect limited at current current density levels.")

if __name__ == "__main__":
    run_smf_validation()
