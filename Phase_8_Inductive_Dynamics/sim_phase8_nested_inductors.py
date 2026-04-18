import numpy as np
import scipy.integrate as spi
import matplotlib.pyplot as plt

# ================================================================
# COSMIC CONSTANTS
# ================================================================
m_e = 9.10938e-31; q_e = 1.60217e-19; h_planck = 6.626e-34
h_bar = 1.0545e-34; mu_0 = 4*np.pi*1e-7; eps_0 = 8.854e-12

# ================================================================
# FTA PHASE 8: DUAL-VIEW PHYSICS ENGINE (Nested Inductors)
# ================================================================

def wkb_tunnel(E_field, B_field, d_gap, Phi_eV=1.0, m_ratio=0.5):
    """Quantum tunneling with B-field quenching."""
    m_eff = m_ratio * m_e; Phi = Phi_eV * q_e
    cE = q_e * E_field; Gs = 3e8; cB = Gs * abs(B_field) * q_e
    alpha = cE - cB
    if alpha == 0:
        integ = np.sqrt(2*m_eff*Phi)*d_gap/h_bar
    else:
        xc = min(Phi/alpha, d_gap) if alpha > 0 else d_gap
        t1 = Phi**1.5; t2 = max(0.0, Phi - alpha*xc)**1.5
        integ = (np.sqrt(2*m_eff)/h_bar)*(2.0/(3.0*alpha))*(t1-t2)
    A = (q_e**3)/(8*np.pi*h_planck*Phi)*(m_e/m_eff)
    if integ > 300: return 0.0
    return A*(E_field**2)*np.exp(-2*integ)

class Geometry:
    def __init__(self, length=100e-6, width=10e-6, thickness=100e-9, arm_length=40e-6):
        self.length = length
        self.width = width
        self.thickness = thickness
        self.arm_length = arm_length
        self.R_plate = 500.0 # Ohms per plate (more realistic for nano-scale)
        self.gap_thickness = 10e-9 
        # Layer vertical positions (Z-axis)
        self.positions = np.array([i * (thickness + self.gap_thickness) for i in range(6)])

class DualView_6Plate_System:
    def __init__(self, geometry):
        self.geo = geometry
        self.L_matrix = self.build_inductance_matrix()
        self.L_inv = np.linalg.inv(self.L_matrix)
        
        # Simple Capacitance Matrix (based on parallel plate approximation)
        self.C_matrix = np.eye(6) * (eps_0 * self.geo.length * self.geo.width / self.geo.gap_thickness)
        self.C_inv = np.linalg.inv(self.C_matrix)
        
    def u_plate_self_inductance(self, L, W, arm_len):
        """Self-inductance of a U-shaped plate."""
        # Straight path + 2 arms
        L_straight = (mu_0 * L / (2*np.pi)) * (np.log(2*L/W) + 0.5)
        L_arms = (mu_0 * (2 * arm_len) / (4*np.pi))
        return (L_straight + L_arms) * 0.5 # half turn
        
    def mutual_inductance(self, L1, L2, d, alignment='parallel'):
        """Mutual inductance with exponential decay over distance."""
        char_len = 500e-9 # 0.5 micrometers coupling range
        k = np.exp(-d / char_len)
        M = k * np.sqrt(L1 * L2)
        return M if alignment == 'parallel' else -M

    def build_inductance_matrix(self):
        L = np.zeros((6, 6))
        for i in range(6):
            L[i,i] = self.u_plate_self_inductance(self.geo.length, self.geo.width, self.geo.arm_length)
            for j in range(i+1, 6):
                d = abs(self.geo.positions[i] - self.geo.positions[j])
                alignment = 'parallel' if (i%2 == j%2) else 'anti_parallel'
                M = self.mutual_inductance(L[i,i], L[i,i], d, alignment)
                L[i,j] = L[j,i] = M
        return L

    def compute_magnetic_energy(self, I_long):
        """E = 0.5 * I^T * L * I"""
        return 0.5 * np.dot(I_long, np.dot(self.L_matrix, I_long))

    def solve_dynamic(self, t_span, V_gate_pulse):
        def system_deriv(t, state):
            V = state[0:6]        # Node voltages
            I_long = state[6:12]  # Longitudinal currents
            
            # 1. Gate Driving (P2)
            V_gate = V_gate_pulse(t)
            V_drive = np.zeros(6)
            V_drive[1] = V_gate # Pulse on P2 (Gate 1)
            V_drive[0] = 50.0   # Source P1 Bias (50V for higher E-field)
            V_drive[4] = 0.0    # Drain P5 Bias (0V)
            
            # 2. dI/dt from Inductance (Full 6x6 Coupling)
            V_L = V_drive - self.geo.R_plate * I_long - V
            dI_dt = self.L_inv @ V_L
            
            # 3. Faraday's Induced Currents (V_ind = -M dI/dt)
            # This is implicitly handled by the L_matrix solver, 
            # but we track the 'induced' component for visibility.
            V_induced = -self.L_matrix @ dI_dt
            
            # 4. Total Magnetic Field (Geometric Superposition)
            # Higher resolution: Central plate gap B-field
            B_total = np.zeros(6)
            mu_r_eff = 100.0 # Realistic for iron-powder enhancement
            for i in range(6):
                # Biot-Savart approximation with mu_r boost
                B_total[i] = (mu_r_eff * mu_0 * abs(I_long[i]) / (2 * self.geo.width)) * np.sign(I_long[i])
            
            # Resultant field in gap i-j
            B_gap = np.zeros(5)
            for i in range(5):
                B_gap[i] = B_total[i] + B_total[i+1] # Combined fields in the gap

            # 5. Tunneling Current (WKB)
            I_tunnel = np.zeros(6)
            # From P1 to P2 gap
            E = abs(V[0] - V[1]) / self.geo.gap_thickness
            J = wkb_tunnel(E, B_gap[0], self.geo.gap_thickness)
            It = J * (self.geo.length * self.geo.width)
            I_tunnel[0] -= It
            I_tunnel[1] += It
            
            # 6. dV/dt from Capacitance
            dV_dt = self.C_inv @ I_tunnel
            
            return np.concatenate([dV_dt, dI_dt])

        y0 = np.zeros(12)
        sol = spi.solve_ivp(system_deriv, t_span, y0, method='BDF', t_eval=np.linspace(t_span[0], t_span[1], 1000))
        return sol

def run_phase8_simulation():
    print("=" * 60)
    print(" PHASE 8: NESTED INDUCTORS & DUAL-VIEW ELECTROMAGNETICS")
    print("=" * 60)
    
    geo = Geometry()
    fta = DualView_6Plate_System(geo)
    
    # Pulse Function (100ns pulse)
    def v_pulse(t):
        return 1.0 if (1e-8 < t < 1.1e-7) else 0.0
    
    t_span = (0, 2e-7)
    sol = fta.solve_dynamic(t_span, v_pulse)
    
    # Analyze Energy Conservation
    I_final = sol.y[6:12, -1]
    E_mag = fta.compute_magnetic_energy(I_final)
    
    # Geometric Sweep: Sensitivity to arm length
    arms = [10e-6, 40e-6, 80e-6]
    max_gain = []
    
    for a in arms:
        g_temp = Geometry(arm_length=a)
        fta_temp = DualView_6Plate_System(g_temp)
        s_temp = fta_temp.solve_dynamic(t_span, v_pulse)
        # Calculate max output voltage change on P5 (state index 4)
        max_gain.append(np.max(np.abs(s_temp.y[4])))

    print(f"\nSimulation Results:")
    print(f"   Final Magnetic Energy (E_mag): {E_mag*1e12:.3f} pJ")
    print(f"   Inductance Matrix Non-zero Mutuals: {np.count_nonzero(fta.L_matrix) - 6}")
    print(f"   Geometric Sensitivity (Arm Length):")
    for i, a in enumerate(arms):
        print(f"      Arm {a*1e6:.0f}um -> Max Output Delta: {max_gain[i]:.2f} V")

    # Plotting
    plt.figure(figsize=(12, 6))
    
    plt.subplot(1, 2, 1)
    plt.plot(sol.t * 1e9, sol.y[1], label='P2 Gate Voltage (V)')
    plt.plot(sol.t * 1e9, sol.y[4], label='P5 Drain Voltage (V)')
    plt.xlabel('Time (ns)')
    plt.ylabel('Voltage (V)')
    plt.title('Transient Response: Nested Inductor Model')
    plt.legend(); plt.grid(True)
    
    plt.subplot(1, 2, 2)
    plt.plot(sol.t * 1e9, sol.y[7] * 1e3, label='I_long P2 (mA)')
    plt.plot(sol.t * 1e9, sol.y[10] * 1e3, label='I_long P5 (mA)')
    plt.xlabel('Time (ns)')
    plt.ylabel('Current (mA)')
    plt.title('Longitudinal Inductive Currents')
    plt.legend(); plt.grid(True)
    
    plt.tight_layout()
    image_path = r'C:\Users\allmy\Desktop\oos\field_transistor_alternative\phase2_foundations\images\fta_phase8_nested_inductors.png'
    plt.savefig(image_path, dpi=150)
    print(f"\n-> Phase 8 Complete. Visualization saved to {image_path}")

if __name__ == "__main__":
    run_phase8_simulation()
