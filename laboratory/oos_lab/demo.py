"""
OOS-Lab Demo: Quick test of the unified physics simulation toolkit.
Run: python -m oos_lab.demo
"""
import numpy as np
import sys, os

# Add parent directory to path so oos_lab can be imported
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')


def main():
    print("=" * 60)
    print("OOS-Lab v1.0 - Unified Physics Simulation Laboratory")
    print("Author: Basel Yahya Abdullah")
    print("=" * 60)

    # 1. Test constants
    from oos_lab.constants import m_e, q_e, h_bar, mu_0, eps_0
    print("\n[1] Physical Constants loaded:")
    print(f"    m_e = {m_e:.5e} kg")
    print(f"    q_e = {q_e:.5e} C")
    print(f"    h_bar = {h_bar:.5e} J*s")

    # 2. Test FDM solver
    from oos_lab.solvers.fdm_laplace import solve_capacitance_matrix
    print("\n[2] FDM Laplace Solver:")
    C, D = solve_capacitance_matrix(nx=60, ny=50,
                                     plate_x_cells=[5, 10, 15, 30, 45, 55],
                                     plate_y_range=(10, 40))
    print(f"    C_matrix shape: {C.shape}")
    print(f"    C_11 = {C[0,0]:.4e} F")
    print(f"    C_12 = {C[0,1]:.4e} F")

    # 3. Test quantum tunneling
    from oos_lab.physics.quantum_tunneling import wkb_tunneling_current
    print("\n[3] WKB Quantum Tunneling:")
    J_no_B = wkb_tunneling_current(E_field=1e9, B_field=0.0)
    J_with_B = wkb_tunneling_current(E_field=1e9, B_field=0.5)
    print(f"    J(B=0)   = {J_no_B:.4e} A/m^2 (ON state)")
    print(f"    J(B=0.5) = {J_with_B:.4e} A/m^2 (OFF state)")
    ratio = J_no_B / J_with_B if J_with_B > 0 else float('inf')
    print(f"    ON/OFF ratio = {ratio:.2f}x")

    # 4. Test magnetic fields
    from oos_lab.physics.magnetic_fields import plate_biot_savart
    print("\n[4] Biot-Savart Magnetic Field:")
    B_air = plate_biot_savart(I=2e-3, width=10e-6, length=100e-6, mu_r=1)
    B_mu = plate_biot_savart(I=2e-3, width=10e-6, length=100e-6, mu_r=50000)
    print(f"    B(air)      = {B_air:.4e} T")
    print(f"    B(Mu-metal) = {B_mu:.4e} T")

    # 5. Test spintronics
    from oos_lab.physics.spintronics import spin_valve_state
    print("\n[5] Spin-Valve Logic:")
    print(f"    Parallel currents:      {spin_valve_state(+1, +1)}")
    print(f"    Anti-parallel currents: {spin_valve_state(+1, -1)}")

    # 6. Test power analysis
    from oos_lab.analysis.power import energy_per_operation, dynamic_power
    print("\n[6] Power Analysis:")
    C_load = 8.64e-18  # from FTA Phase 6
    for V in [5, 12, 50]:
        e = energy_per_operation(C_load, V)
        p = dynamic_power(e, 100e9)
        print(f"    V_DD={V:2d}V: E={e:.1f} fJ, P@100GHz={p:.1f} mW")

    print("\n" + "=" * 60)
    print("All OOS-Lab modules loaded and tested successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()
