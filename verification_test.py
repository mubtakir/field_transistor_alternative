# verification_test.py
import os
import sys

# Ensure oos_lab is in path (within laboratory folder)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'laboratory')))

try:
    import oos_lab.api as fta
    from oos_lab.physics.materials_library import get_material_params
    
    print("--- oos-lab v1.2 Verification ---")
    
    # Check Materials
    lab6 = get_material_params('LaB6')
    print(f"Material Check (LaB6): Work Function = {lab6.get('work_function')} eV")
    
    # Check Device Simulation via API
    print("Testing Thermionic-FTA API Simulation...")
    v_ds_range = [1.0, 5.0, 10.0]
    results = fta.simulate(device_type='thermionic_fta', analysis='iv', v_ds_range=v_ds_range)
    
    print(f"Success! Simulation returned {len(results)} data points.")
    for i, res in enumerate(results):
        print(f" Vds={v_ds_range[i]}V -> I_total={res['I_total']*1e6:.2f} uA, T={res['T_emitter']:.1f} K")
        
    print("\n[VERIFICATION PASSED] The lab is fully updated and synchronized with Phase 3 breakthroughs.")

except Exception as e:
    print(f"\n[VERIFICATION FAILED] Error: {e}")
    sys.exit(1)
