"""
Example: Basic FTA Device Simulation
------------------------------------
Demonstrates the V2.0 Virtual Laboratory workflow.
"""

import sys, os
# Add parent of fta_lab to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from fta_lab.lab_manager import FTALaboratory

def main():
    # 1. Initialize Laboratory
    lab = FTALaboratory()
    
    # 2. Create Device
    device = lab.create_device(
        device_type='u_plate',
        geometry={
            'length': 100e-6,
            'width': 10e-6,
            'gap': 5e-9,
            'plate_positions': [10, 15, 20, 50, 80, 95]
        },
        V_DD=50.0,
        R_load=1000.0
    )
    
    # 3. Simulate and Analyze
    print("\n[STEP] Running DC Characterization...")
    # Using the lab_manager (simplified implementation)
    from fta_lab.analyzers import IVAnalyzer
    iva = IVAnalyzer(lab.config)
    res_iv = iva.run_sweep(device, (0.0, 10.0, 50))
    
    print("\n[STEP] Running Frequency Analysis...")
    from fta_lab.analyzers import FrequencyAnalyzer
    fa = FrequencyAnalyzer(lab.config)
    res_freq = fa.run_ac_sweep(device, (1e6, 1e12, 100))
    
    # Final Summary
    lab.summary()
    print("\n[SUCCESS] Example simulation finished successfully!")

if __name__ == "__main__":
    main()
