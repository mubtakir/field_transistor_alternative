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
    coeff_B = (q * h_bar * abs(B_field)) / m_eff
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
    factor = length / np.sqrt(length**2 + (width/2.0)**2)
    return (mu_0 * I / (2.0 * width)) * factor

def solve_fdm_capacitance_matrix():
    print("-> Solving 2D FDM Laplace for 6-Plate Capacitor Array...")
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
        V_full = V_fixed.copy()
        V_full[free] = V_F
        Q_full = L * V_full
        for i in range(6):
            charge = sum(Q_full[n] for n in plates[i]) * eps_0 * eps_r * plate_depth
            C_mat[i, j] = charge
            
    distances = np.zeros((6, 6))
    for i in range(6):
        for j in range(6):
            distances[i, j] = abs(plate_x_cells[i] - plate_x_cells[j]) * dx
            
    return C_mat, distances

def run_phase3_6plate_magnetron():
    print("==========================================================")
    print(" PHASE 3: 6-PLATE U-SHAPE MAGNETRON (CROSS-FIELD GAIN)")
    print("==========================================================")
    
    C_matrix, dist_matrix = solve_fdm_capacitance_matrix()
    C_inv = np.linalg.inv(C_matrix)
    
    length = 100e-6; width = 10e-6; Area = length * width
    L_self = (mu_0 * length / (2 * np.pi)) * (np.log(2.0 * length / width) + 0.5)
    
    # 6x6 Mutual Inductance Matrix Calculation
    L_matrix = np.zeros((6, 6))
    for i in range(6):
        for j in range(6):
            if i == j:
                L_matrix[i, j] = L_self
            else:
                d = dist_matrix[i, j]
                # Empirically dense mutual formulation for nano-gaps
                L_matrix[i, j] = L_self * 0.999 * np.exp(-d * 1e6) 
                
    L_inv = np.linalg.inv(L_matrix)
    
    R_plate = 50.0 # ohms 
    V_DD = 80.0  # High Transverse Drain Voltage to sustain active tunneling
    R_load = 50.0  # Tight load to visualize high-current Gain
    
    # P2 acts as a purely MAGNETIC GATES controlling the longitudinal flux
    f_AC = 1000; w = 2 * np.pi * f_AC
    I_gate_AC_amp = 1.5 # 1.5 Amp peak-to-peak magnetic control stream
    
    def system_ode(t, y):
        V = y[0:6]; I_long = y[6:12]
        
        # Longitudinal Voltages (V_ext)
        V_ext = np.zeros(6)
        V_ext[1] = I_gate_AC_amp * R_plate * np.sin(w * t) # Driving P2 purely magnetically
        
        # Standard LR circuit dI/dt solution
        V_L = V_ext - R_plate * I_long
        dI_dt = L_inv @ V_L
        
        # Absolute exact B-fields via Biot-Savart
        B_individual = np.zeros(6)
        for i in range(6):
            B_individual[i] = u_plate_biot_savart_center(I_long[i], width, length)
            
        I_tunnel = np.zeros(6)
        
        # Multi-Path Cascaded Tunneling P1 -> P2 -> P3 -> P4 -> P5
        for i in range(5):
            j = i + 1
            V_gap = V[i] - V[j]
            d_gap = dist_matrix[i, j]
            E_field = abs(V_gap) / d_gap if d_gap > 0 else 0
            
            # The net B-field penetrating the gap
            B_gap = B_individual[i] + B_individual[j]
            
            if E_field > 1e6:
                J_tun = wkb_tunneling_with_B_fast(E_field, B_gap, d_gap, 1.0, 0.5)
                I_tun = J_tun * Area * np.sign(V_gap)
            else:
                I_tun = 0.0
            
            I_tunnel[i] -= I_tun
            I_tunnel[j] += I_tun

        # Transverse Power Array (DC Power)
        I_source = np.zeros(6)
        # We attach P1 (Source) to V_DD via R_load, and P5 (Drain) to Ground.
        I_source[0] = (V_DD - V[0]) / R_load 
        I_source[4] = (0.0 - V[4]) / 1e-3     
        
        dV_dt = C_inv @ (I_source + I_tunnel)
        
        return np.concatenate([dV_dt, dI_dt])

    t_span = (0, 0.003)
    t_eval = np.linspace(0, 0.003, 1500)
    
    print("-> Solving the 12-Dimensional Quantum 6-Plate Electrodynamic ODE System...")
    sol = spi.solve_ivp(system_ode, t_span, np.zeros(12), t_eval=t_eval, method='Radau')
    
    # Analyze the true signal outputs
    I_magnetic_control_signal = sol.y[7] # I_long array index 1 (P2)
    V_channel_output = sol.y[0] # Transverse Voltage on P1 output node
    
    plt.figure(figsize=(10, 8))
    plt.subplot(2, 1, 1)
    plt.plot(t_eval*1000, I_magnetic_control_signal, label='Control Magnetic Valve Current ($I_{P2}$)', color='green', linewidth=2)
    plt.ylabel('Longitudinal Current (A)')
    plt.grid(True); plt.legend()
    
    plt.subplot(2, 1, 2)
    plt.plot(t_eval*1000, V_channel_output, label='Channel Amplification Voltage $V_{P1}$ (Source)', color='purple', linewidth=2)
    plt.ylabel('Transverse Voltage (V)')
    plt.xlabel('Time (ms)')
    plt.grid(True); plt.legend()
    
    plt.suptitle('Phase 3: Deep Quantum 6-Plate U-Shape Magnetron Transistor', fontsize=14)
    plt.tight_layout()
    plt.savefig(r'C:\Users\allmy\.gemini\antigravity\brain\a6c09de4-fcab-4ea6-b2a8-c4b15d487fd3\fta_6plate_magnetron.png', dpi=150)
    print("-> Phase 3 6-Plate U-Shape Simulation Complete. Plot Saved.")

if __name__ == '__main__':
    run_phase3_6plate_magnetron()
