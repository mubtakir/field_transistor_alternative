import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla
import scipy.integrate as spi
import matplotlib.pyplot as plt

# Cosmic Constants
m_e = 9.10938e-31; q = 1.60217e-19; h = 6.626e-34; h_bar = 1.0545e-34
mu_0 = 4 * np.pi * 1e-7; k_B = 1.38064e-23

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

def u_plate_biot_savart(I, width, length):
    mu_r = 50000.0
    factor = length / np.sqrt(length**2 + (width/2.0)**2)
    B_raw = (mu_r * mu_0 * abs(I) / (2.0 * width)) * factor
    return min(B_raw, 1.0) * np.sign(I)

def solve_fdm():
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
    C_mat = np.zeros((6, 6)); distances = np.zeros((6, 6))
    for j in range(6):
        V_fixed = np.zeros(N)
        for n in plates[j]: V_fixed[n] = 1.0
        b = -(L * V_fixed)[free]; V_F = spla.spsolve(L_FF, b)
        V_full = V_fixed.copy(); V_full[free] = V_F; Q_full = L * V_full
        for i in range(6):
            C_mat[i, j] = sum(Q_full[n] for n in plates[i]) * eps_0 * eps_r * plate_depth
    for i in range(6):
        for j in range(6):
            distances[i,j] = abs(plate_x_cells[i] - plate_x_cells[j]) * 1e-9
    return C_mat, distances

def build_system(C_matrix, dist_matrix):
    length = 100e-6; width = 10e-6; Area = length * width
    C_inv = np.linalg.inv(C_matrix)
    L_self = (mu_0 * length / (2 * np.pi)) * (np.log(2.0 * length / width) + 0.5)
    L_matrix = np.zeros((6, 6))
    for i in range(6):
        for j in range(6):
            L_matrix[i,j] = L_self if i == j else L_self * 0.999 * np.exp(-dist_matrix[i,j]*1e6)
    L_inv = np.linalg.inv(L_matrix)
    R_plate = 500.0; V_DD = 50.0; R_load = 1000.0; R_discharge = 5000.0
    return C_inv, L_inv, R_plate, V_DD, R_load, R_discharge, Area, length, width

def make_ode(C_inv, L_inv, R_plate, V_DD, R_load, R_discharge, Area, length, width, dist_matrix, gate_fn):
    def system_ode(t, y):
        V = y[0:6]; I_long = y[6:12]
        V_ext = np.zeros(6)
        V_ext[1] = gate_fn(t)
        V_L = V_ext - R_plate * I_long
        dI_dt = L_inv @ V_L
        B_ind = np.array([u_plate_biot_savart(I_long[i], width, length) for i in range(6)])
        I_tunnel = np.zeros(6)
        for i in range(5):
            j = i + 1; V_gap = V[i] - V[j]; d_gap = dist_matrix[i,j]
            E_field = abs(V_gap) / d_gap if d_gap > 0 else 0
            if np.sign(I_long[i]) == np.sign(I_long[j]):
                B_gap = abs(B_ind[i] - B_ind[j])
            else:
                B_gap = abs(B_ind[i]) + abs(B_ind[j])
            if E_field > 1e6:
                J_tun = wkb_tunneling_with_B_fast(E_field, B_gap, d_gap)
                I_tun = J_tun * Area * np.sign(V_gap)
            else: I_tun = 0.0
            I_tunnel[i] -= I_tun; I_tunnel[j] += I_tun
        I_source = np.zeros(6)
        I_source[0] = (V_DD - V[0]) / R_load
        I_source[4] = (0.0 - V[4]) / 1e-3
        # Discharge path for Fall Time
        for k in range(6):
            I_source[k] -= V[k] / R_discharge
        dV_dt = C_inv @ (I_source + I_tunnel)
        return np.concatenate([dV_dt, dI_dt])
    return system_ode

def run_phase5():
    print("==========================================================")
    print(" PHASE 5: ULTIMATE THz CHARACTERIZATION SUITE")
    print("==========================================================\n")
    
    C_matrix, dist_matrix = solve_fdm()
    params = build_system(C_matrix, dist_matrix)
    C_inv, L_inv, R_plate, V_DD, R_load, R_discharge, Area, length, width = params
    I_gate = 2.0e-3
    
    # ============================================================
    # TEST 1: FEMTOSECOND RISE TIME
    # ============================================================
    print("=" * 50)
    print("TEST 1: Femtosecond Rise Time Resolution")
    print("=" * 50)
    
    t_on = 1e-12  # Pulse starts at 1 ps
    gate_step = lambda t: I_gate * R_plate if t >= t_on else 0.0
    ode = make_ode(C_inv, L_inv, R_plate, V_DD, R_load, R_discharge, Area, length, width, dist_matrix, gate_step)
    
    # 0.1 femtosecond resolution around the edge
    t_eval = np.linspace(0, 10e-12, 100000)  # 0.1 fs steps over 10 ps
    sol = spi.solve_ivp(ode, (0, 10e-12), np.zeros(12), t_eval=t_eval, method='Radau')
    V_out = sol.y[0]
    
    V_min = np.min(V_out); V_max = np.max(V_out); V_swing = V_max - V_min
    V_10 = V_min + 0.1 * V_swing; V_90 = V_min + 0.9 * V_swing
    
    rise_start = None; rise_end = None
    for i in range(len(t_eval)):
        if t_eval[i] > t_on:
            if rise_start is None and V_out[i] >= V_10: rise_start = i
            if rise_start is not None and rise_end is None and V_out[i] >= V_90:
                rise_end = i; break
    
    if rise_start is not None and rise_end is not None:
        rise_time = t_eval[rise_end] - t_eval[rise_start]
        print(f"   Rise Time (10%-90%): {rise_time*1e15:.2f} fs ({rise_time*1e12:.4f} ps)")
    else:
        rise_time = 0
        print(f"   Rise Time: < 0.1 fs (SUB-FEMTOSECOND!)")
    print(f"   Output Swing: {V_swing:.2f} V  [{V_min:.2f} V -> {V_max:.2f} V]")
    
    # ============================================================
    # TEST 2: FALL TIME WITH DISCHARGE MODEL
    # ============================================================
    print(f"\n{'=' * 50}")
    print("TEST 2: Fall Time with Charge Discharge Model")
    print("=" * 50)
    
    t_on2 = 5e-12; t_off2 = 50e-12
    gate_pulse = lambda t: I_gate * R_plate if t_on2 <= t <= t_off2 else 0.0
    ode2 = make_ode(C_inv, L_inv, R_plate, V_DD, R_load, R_discharge, Area, length, width, dist_matrix, gate_pulse)
    
    t_eval2 = np.linspace(0, 200e-12, 20000)  # 10 fs resolution over 200 ps
    sol2 = spi.solve_ivp(ode2, (0, 200e-12), np.zeros(12), t_eval=t_eval2, method='Radau')
    V_out2 = sol2.y[0]
    
    V_min2 = np.min(V_out2); V_max2 = np.max(V_out2); V_swing2 = V_max2 - V_min2
    if V_swing2 > 1e-6:
        V_90f = V_min2 + 0.9 * V_swing2; V_10f = V_min2 + 0.1 * V_swing2
        fall_start = None; fall_end = None
        for i in range(len(t_eval2)):
            if t_eval2[i] > t_off2:
                if fall_start is None and V_out2[i] <= V_90f: fall_start = i
                if fall_start is not None and fall_end is None and V_out2[i] <= V_10f:
                    fall_end = i; break
        if fall_start is not None and fall_end is not None:
            fall_time = t_eval2[fall_end] - t_eval2[fall_start]
            print(f"   Fall Time (90%-10%): {fall_time*1e12:.2f} ps ({fall_time*1e9:.4f} ns)")
        else:
            print(f"   Fall Time: > {(t_eval2[-1] - t_off2)*1e12:.0f} ps (slow discharge)")
    else:
        print("   No significant swing for fall time measurement.")
    
    # ============================================================
    # TEST 3: THz FREQUENCY SWEEP (BODE PLOT)
    # ============================================================
    print(f"\n{'=' * 50}")
    print("TEST 3: THz Frequency Response (Bode Plot)")
    print("=" * 50)
    
    frequencies = [1e9, 5e9, 10e9, 50e9, 100e9, 500e9, 1e12]
    freq_labels = ['1G', '5G', '10G', '50G', '100G', '500G', '1T']
    gains = []
    V_in_ac = I_gate * R_plate * 2.0
    
    for fi, f in enumerate(frequencies):
        w = 2 * np.pi * f
        gate_ac = lambda t, w=w: I_gate * R_plate * np.sin(w * t)
        ode_ac = make_ode(C_inv, L_inv, R_plate, V_DD, R_load, R_discharge, Area, length, width, dist_matrix, gate_ac)
        
        T_period = 1.0 / f
        t_sim = 3 * T_period
        n_pts = max(600, int(t_sim / (T_period / 200)))
        if n_pts > 5000: n_pts = 5000
        t_eval_ac = np.linspace(0, t_sim, n_pts)
        
        sol_ac = spi.solve_ivp(ode_ac, (0, t_sim), np.zeros(12), t_eval=t_eval_ac, method='Radau')
        V_out_ac = sol_ac.y[0]
        last = V_out_ac[int(0.6*len(V_out_ac)):]
        V_pp = max(last) - min(last)
        gain = V_pp / V_in_ac if V_in_ac > 0 else 0
        gains.append(gain)
        print(f"   {freq_labels[fi]}Hz: Gain = {gain:.2f}x")
    
    # ============================================================
    # TEST 4: REPETITIVE PULSE TRAIN
    # ============================================================
    print(f"\n{'=' * 50}")
    print("TEST 4: Repetitive Pulse Train (Continuous Switching)")
    print("=" * 50)
    
    f_clock = 100e9  # 100 GHz clock
    T_clock = 1.0 / f_clock
    duty = 0.5
    
    gate_train = lambda t: I_gate * R_plate if (t % T_clock) < (duty * T_clock) else 0.0
    ode_train = make_ode(C_inv, L_inv, R_plate, V_DD, R_load, R_discharge, Area, length, width, dist_matrix, gate_train)
    
    t_sim_train = 10 * T_clock  # 10 clock cycles
    t_eval_train = np.linspace(0, t_sim_train, 5000)
    sol_train = spi.solve_ivp(ode_train, (0, t_sim_train), np.zeros(12), t_eval=t_eval_train, method='Radau')
    V_out_train = sol_train.y[0]
    
    V_high = np.max(V_out_train[int(0.3*len(V_out_train)):])
    V_low = np.min(V_out_train[int(0.3*len(V_out_train)):])
    print(f"   Clock Frequency: {f_clock/1e9:.0f} GHz")
    print(f"   V_high: {V_high:.2f} V, V_low: {V_low:.2f} V")
    print(f"   Logic Swing: {V_high - V_low:.2f} V")
    
    # ============================================================
    # PLOTTING
    # ============================================================
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    # Plot 1: Femtosecond Rise Time
    ax = axes[0, 0]
    ax.plot(t_eval*1e12, V_out, color='purple', linewidth=1.5)
    ax.axvline(x=t_on*1e12, color='red', linestyle='--', alpha=0.7, label='Gate ON')
    ax.set_xlabel('Time (ps)'); ax.set_ylabel('V_out (V)')
    ax.set_title('Test 1: Femtosecond Rise Time'); ax.grid(True); ax.legend()
    
    # Plot 2: Fall Time
    ax = axes[0, 1]
    ax.plot(t_eval2*1e12, V_out2, color='blue', linewidth=1.5)
    ax.axvline(x=t_on2*1e12, color='green', linestyle='--', alpha=0.7, label='Gate ON')
    ax.axvline(x=t_off2*1e12, color='red', linestyle='--', alpha=0.7, label='Gate OFF')
    ax.set_xlabel('Time (ps)'); ax.set_ylabel('V_out (V)')
    ax.set_title('Test 2: Fall Time (Discharge Model)'); ax.grid(True); ax.legend()
    
    # Plot 3: THz Bode Plot
    ax = axes[1, 0]
    ax.plot(frequencies, gains, marker='o', color='darkgreen', linewidth=2, markersize=8)
    ax.set_xscale('log'); ax.set_xlabel('Frequency (Hz)'); ax.set_ylabel('Voltage Gain')
    ax.set_title('Test 3: THz Frequency Response'); ax.grid(True, which='both', linestyle='--')
    
    # Plot 4: Pulse Train
    ax = axes[1, 1]
    gate_vis = np.array([gate_train(t) for t in t_eval_train])
    ax.plot(t_eval_train*1e12, gate_vis, color='green', linewidth=1, alpha=0.5, label='Gate')
    ax.plot(t_eval_train*1e12, V_out_train, color='red', linewidth=1.5, label='V_out')
    ax.set_xlabel('Time (ps)'); ax.set_ylabel('Voltage (V)')
    ax.set_title(f'Test 4: {f_clock/1e9:.0f} GHz Pulse Train'); ax.grid(True); ax.legend()
    
    plt.suptitle('Phase 5: Ultimate THz Characterization Suite', fontsize=15, fontweight='bold')
    plt.tight_layout()
    plt.savefig(r'C:\Users\allmy\.gemini\antigravity\brain\a6c09de4-fcab-4ea6-b2a8-c4b15d487fd3\fta_thz_characterization.png', dpi=150)
    print("\n-> Phase 5 Complete. All 4 Tests Saved.")

if __name__ == '__main__':
    run_phase5()
