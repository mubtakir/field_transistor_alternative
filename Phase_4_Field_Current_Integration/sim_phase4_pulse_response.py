import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla
import scipy.integrate as spi
import matplotlib.pyplot as plt

# Cosmic Constants
m_e = 9.10938e-31; q = 1.60217e-19; h = 6.626e-34; h_bar = 1.0545e-34
mu_0 = 4 * np.pi * 1e-7

def wkb_tunneling_with_B_fast(E_field, B_field, d_gap, Phi_B_eV=1.0, m_eff_ratio=0.5):
    m_eff = m_eff_ratio * m_e
    Phi_B = Phi_B_eV * q
    coeff_E = q * E_field
    Gamma_spin = 3e8
    coeff_B = Gamma_spin * abs(B_field) * q
    alpha = coeff_E - coeff_B
    
    if alpha == 0:
        integral = np.sqrt(2 * m_eff * Phi_B) * d_gap / h_bar
    else:
        x_c = Phi_B / alpha if alpha > 0 else d_gap
        if x_c > d_gap: x_c = d_gap
        term1 = Phi_B**1.5
        term2 = max(0.0, Phi_B - alpha * x_c)**1.5
        integral_core = (2.0 / (3.0 * alpha)) * (term1 - term2)
        integral = (np.sqrt(2 * m_eff) / h_bar) * integral_core
        
    A_eff = (q**3) / (8 * np.pi * h * Phi_B) * (m_e / m_eff)
    if integral > 300: return 0.0
    return A_eff * (E_field**2) * np.exp(-2 * integral)

def u_plate_biot_savart_center(I, width, length):
    mu_r = 50000.0
    factor = length / np.sqrt(length**2 + (width/2.0)**2)
    B_raw = (mu_r * mu_0 * abs(I) / (2.0 * width)) * factor
    B_sat = 1.0
    return min(B_raw, B_sat) * np.sign(I)

def solve_fdm_capacitance_matrix():
    dx = 1e-9; eps_0 = 8.854e-12; eps_r = 4.0; plate_depth = 0.01
    nx, ny = 120, 100; N = nx * ny
    L = sp.lil_matrix((N, N))
    def idx(i, j): return i + j * nx
    for j in range(ny):
        for i in range(nx):
            k = idx(i, j)
            L[k, k] = 4
            if i > 0: L[k, idx(i-1, j)] = -1
            if i < nx-1: L[k, idx(i+1, j)] = -1
            if j > 0: L[k, idx(i, j-1)] = -1
            if j < ny-1: L[k, idx(i, j+1)] = -1
    L = L.tocsr()
    plate_x_cells = [10, 15, 20, 50, 80, 95]
    plates = [[idx(x, j) for j in range(20, 80)] for x in plate_x_cells]
    all_p = set([n for p in plates for n in p])
    bounds = set()
    for i in range(nx): bounds.add(idx(i,0)); bounds.add(idx(i,ny-1))
    for j in range(ny): bounds.add(idx(0,j)); bounds.add(idx(nx-1,j))
    fixed = all_p.union(bounds)
    free = np.array([i for i in range(N) if i not in fixed])
    L_FF = L[free, :][:, free]
    C_mat = np.zeros((6, 6))
    for j in range(6):
        V_fixed = np.zeros(N)
        for n in plates[j]: V_fixed[n] = 1.0
        b = - (L * V_fixed)[free]
        V_F = spla.spsolve(L_FF, b)
        V_full = V_fixed.copy(); V_full[free] = V_F
        Q_full = L * V_full
        for i in range(6):
            charge = sum(Q_full[n] for n in plates[i]) * eps_0 * eps_r * plate_depth
            C_mat[i, j] = charge
    distances = np.zeros((6, 6))
    for i in range(6):
        for j in range(6):
            distances[i, j] = abs(plate_x_cells[i] - plate_x_cells[j]) * 1e-9
    return C_mat, distances

def run_phase4_pulse_response():
    print("==========================================================")
    print(" PHASE 4: PULSE RESPONSE & SWITCHING SPEED ANALYSIS")
    print("==========================================================")
    
    C_matrix, dist_matrix = solve_fdm_capacitance_matrix()
    C_inv = np.linalg.inv(C_matrix)
    
    length = 100e-6; width = 10e-6; Area = length * width
    L_self = (mu_0 * length / (2 * np.pi)) * (np.log(2.0 * length / width) + 0.5)
    
    L_matrix = np.zeros((6, 6))
    for i in range(6):
        for j in range(6):
            L_matrix[i, j] = L_self if i == j else L_self * 0.999 * np.exp(-dist_matrix[i, j] * 1e6)
    L_inv = np.linalg.inv(L_matrix)
    
    R_plate = 500.0
    V_DD = 50.0
    R_load = 1000.0
    I_gate_pulse = 2.0e-3  # 2 mA step pulse
    
    # Sharp step pulse: OFF for t < t_on, ON for t_on < t < t_off, OFF after
    t_on = 20e-9    # Turn ON at 20 ns
    t_off = 200e-9  # Turn OFF at 200 ns
    
    def gate_pulse(t):
        if t_on <= t <= t_off:
            return I_gate_pulse * R_plate  # Step voltage = I * R
        return 0.0
    
    def system_ode(t, y):
        V = y[0:6]; I_long = y[6:12]
        V_ext = np.zeros(6)
        V_ext[1] = gate_pulse(t)  # P2 Magnetic Gate pulse
        
        V_L = V_ext - R_plate * I_long
        dI_dt = L_inv @ V_L
        
        B_individual = np.zeros(6)
        for i in range(6):
            B_individual[i] = u_plate_biot_savart_center(I_long[i], width, length)
            
        I_tunnel = np.zeros(6)
        for i in range(5):
            j = i + 1
            V_gap = V[i] - V[j]
            d_gap = dist_matrix[i, j]
            E_field = abs(V_gap) / d_gap if d_gap > 0 else 0
            
            if np.sign(I_long[i]) == np.sign(I_long[j]):
                B_gap = abs(B_individual[i] - B_individual[j])
            else:
                B_gap = abs(B_individual[i]) + abs(B_individual[j])
            
            if E_field > 1e6:
                J_tun = wkb_tunneling_with_B_fast(E_field, B_gap, d_gap, 1.0, 0.5)
                I_tun = J_tun * Area * np.sign(V_gap)
            else:
                I_tun = 0.0
            I_tunnel[i] -= I_tun
            I_tunnel[j] += I_tun

        I_source = np.zeros(6)
        I_source[0] = (V_DD - V[0]) / R_load
        I_source[4] = (0.0 - V[4]) / 1e-3
        
        dV_dt = C_inv @ (I_source + I_tunnel)
        return np.concatenate([dV_dt, dI_dt])

    # Two-phase time array: ultra-dense around t_on and t_off edges
    t_span = (0, 300e-9)
    t_pre = np.linspace(0, t_on - 1e-12, 200)
    t_rise = np.linspace(t_on - 1e-12, t_on + 5e-9, 5000) # 1 ps resolution around rise
    t_mid = np.linspace(t_on + 5e-9, t_off - 1e-12, 500)
    t_fall = np.linspace(t_off - 1e-12, t_off + 5e-9, 5000) # 1 ps resolution around fall 
    t_post = np.linspace(t_off + 5e-9, 300e-9, 300)
    t_eval = np.unique(np.concatenate([t_pre, t_rise, t_mid, t_fall, t_post]))
    
    print("-> Solving 12D ODE for nanosecond Pulse Response (picosecond edge resolution)...")
    sol = spi.solve_ivp(system_ode, t_span, np.zeros(12), t_eval=t_eval, method='Radau')
    
    V_out = sol.y[0]    # P1 (Source) output voltage
    I_gate = sol.y[7]   # I_long of P2 (Gate longitudinal current)
    V_gate_input = np.array([gate_pulse(t) for t in t_eval])
    
    # ---- Timing Analysis ----
    V_out_min = np.min(V_out)
    V_out_max = np.max(V_out)
    V_swing = V_out_max - V_out_min
    
    if V_swing > 1e-6:
        V_10 = V_out_min + 0.1 * V_swing
        V_90 = V_out_min + 0.9 * V_swing
        
        # Rise time: first crossing of 10% to first crossing of 90% after t_on
        rise_start_idx = None; rise_end_idx = None
        for i in range(len(t_eval)):
            if t_eval[i] > t_on:
                if rise_start_idx is None and V_out[i] >= V_10:
                    rise_start_idx = i
                if rise_start_idx is not None and rise_end_idx is None and V_out[i] >= V_90:
                    rise_end_idx = i
                    break
        
        # Fall time: after t_off, first crossing of 90% down to 10%
        fall_start_idx = None; fall_end_idx = None
        for i in range(len(t_eval)):
            if t_eval[i] > t_off:
                if fall_start_idx is None and V_out[i] <= V_90:
                    fall_start_idx = i
                if fall_start_idx is not None and fall_end_idx is None and V_out[i] <= V_10:
                    fall_end_idx = i
                    break
        
        if rise_start_idx and rise_end_idx:
            rise_time = (t_eval[rise_end_idx] - t_eval[rise_start_idx])
            print(f"   Rise Time (10%-90%): {rise_time*1e9:.2f} ns")
        else:
            rise_time = None
            print("   Rise Time: Could not determine (signal may not reach 90%)")
            
        if fall_start_idx and fall_end_idx:
            fall_time = (t_eval[fall_end_idx] - t_eval[fall_start_idx])
            print(f"   Fall Time (90%-10%): {fall_time*1e9:.2f} ns")
        else:
            fall_time = None
            print("   Fall Time: Could not determine")
            
        # Propagation Delay: time from pulse edge to 50% output
        V_50 = V_out_min + 0.5 * V_swing
        prop_delay = None
        for i in range(len(t_eval)):
            if t_eval[i] > t_on and V_out[i] >= V_50:
                prop_delay = t_eval[i] - t_on
                print(f"   Propagation Delay (to 50%): {prop_delay*1e9:.2f} ns")
                break
        if prop_delay is None:
            print("   Propagation Delay: Could not determine")
            
        # Maximum Switching Freq estimate
        if rise_time is not None and fall_time is not None:
            f_max = 1.0 / (rise_time + fall_time)
            print(f"   Estimated Max Switching Freq: {f_max/1e6:.1f} MHz")
        elif rise_time is not None:
            f_max = 1.0 / (2 * rise_time)
            print(f"   Estimated Max Switching Freq: {f_max/1e6:.1f} MHz")
    else:
        print("   WARNING: No significant output swing detected.")
    
    print(f"\n   Output Voltage Swing: {V_swing:.4f} V")
    print(f"   V_out range: [{V_out_min:.4f} V, {V_out_max:.4f} V]")
    
    # ---- Plotting ----
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(10, 9), sharex=True)
    
    ax1.plot(t_eval*1e9, V_gate_input, color='green', linewidth=2)
    ax1.set_ylabel('Gate Pulse (V)')
    ax1.set_title('Phase 4: Nanosecond Pulse Response of U-Plate Magnetic Transistor', fontsize=13)
    ax1.grid(True); ax1.legend(['Gate Input Pulse'])
    ax1.axvline(x=t_on*1e9, color='gray', linestyle='--', alpha=0.5)
    ax1.axvline(x=t_off*1e9, color='gray', linestyle='--', alpha=0.5)
    
    ax2.plot(t_eval*1e9, I_gate*1000, color='orange', linewidth=2)
    ax2.set_ylabel('I_long P2 (mA)')
    ax2.grid(True); ax2.legend(['Gate Longitudinal Current'])
    
    ax3.plot(t_eval*1e9, V_out, color='purple', linewidth=2)
    ax3.set_ylabel('V_out P1 (V)')
    ax3.set_xlabel('Time (ns)')
    ax3.grid(True); ax3.legend(['Output Channel Voltage'])
    ax3.axvline(x=t_on*1e9, color='gray', linestyle='--', alpha=0.5)
    ax3.axvline(x=t_off*1e9, color='gray', linestyle='--', alpha=0.5)
    
    plt.tight_layout()
    plt.savefig(r'C:\Users\allmy\.gemini\antigravity\brain\a6c09de4-fcab-4ea6-b2a8-c4b15d487fd3\fta_pulse_response.png', dpi=150)
    print("\n-> Phase 4 Pulse Response Complete. Plot Saved.")

if __name__ == '__main__':
    run_phase4_pulse_response()
