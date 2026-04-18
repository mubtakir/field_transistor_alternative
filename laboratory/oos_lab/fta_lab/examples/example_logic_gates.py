"""
Example: FTA Logic Gate Verification
-------------------------------------
Demonstrates the Phase 7 Logic Models.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from fta_lab.device_models.logic_gates import FTANotGate, FTAAndGate, FTAOrGate

def verify_not():
    print("\n--- Verifying NOT Gate ---")
    gate = FTANotGate({'length': 100e-6, 'width': 10e-6, 'gap': 5e-9})
    for v_in in [0.0, 10.0]:
        res = gate.solve(v_in)
        print(f"Input: {v_in}V | Output: {res['V_out']:.2f}V | Logic: {res['logic_out']}")

def verify_and():
    print("\n--- Verifying AND Gate ---")
    gate = FTAAndGate({'length': 100e-6, 'width': 10e-6, 'gap': 5e-9})
    for v1, v2 in [(0.0, 0.0), (10.0, 0.0), (0.0, 10.0), (10.0, 10.0)]:
        res = gate.solve(v1, v2)
        print(f"Inputs: ({v1}, {v2})V | Output: {res['V_out']:.2f}V | Logic: {res['logic_out']}")

if __name__ == "__main__":
    verify_not()
    verify_and()
    print("\n[SUCCESS] Logic gate verification completed.")
