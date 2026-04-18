import unittest
import numpy as np
from oos_lab.physics.quantum_tunneling import wkb_tunneling_current, fowler_nordheim_tfe

class TestFTAPhysics(unittest.TestCase):
    def test_fn_tunneling_positive(self):
        # Basic check: current should be positive for positive field
        E = 1e9 # 1 V/nm
        J = fowler_nordheim_tfe(E, T=300, Phi_B_eV=1.0)
        self.assertGreater(J, 0, "FN current should be positive for positive E-field")

    def test_target_linearity_ndr(self):
        # Check if NDR material is active in the model (heuristic)
        from oos_lab.physics.quantum_tunneling import buriti_ndr_correction
        E = 1.2e8 # Near peak field
        cor = buriti_ndr_correction(E)
        self.assertGreater(cor, 1e-8, "NDR current density should be significant at peak")

    def test_inverse_gate_logic(self):
        # PANI/rGO should have inverse behavior
        from oos_lab.physics.quantum_tunneling import inverse_material_correction
        low_v = inverse_material_correction(0.1)
        high_v = inverse_material_correction(5.0)
        self.assertGreater(low_v, high_v, "Inverse gate current must be higher at low voltage")

if __name__ == '__main__':
    unittest.main()
