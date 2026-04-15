# FTA Researcher's Guide: Laboratory Procedures
### Conceptual Architect: Basel Yahya Abdullah (باسل يحيى عبدالله)

## 1. Safety & Preparation
- **Safety**: Ensure all power sources are fused and grounded. When using wet dielectrics, use low voltages ($< 12V$) to avoid electrolysis or shock.
- **Tools**: Oscilloscope (min. 1MHz), Precision Capacitor Meter, Multi-meter, Regulated Power Supply.

## 2. Experiment 1: Triple-Plate Threshold
**Goal**: Verify the "Electrostatic Gate" effect.
1.  **Setup**: Place three conductive plates ($P_1, P_2, P_3$) in parallel.
2.  **Dielectric**: Insert a high-resistance insulator between $P_1-P_2$ and $P_2-P_3$.
3.  **Procedure**:
    - Apply a fixed voltage ($5V$) to the external plate ($P_3$).
    - Measure the detectable field on $P_1$ (should be visible as a base capacitance).
    - Gradually apply a negative bias to the center plate ($P_2$).
4.  **Result**: Observe the "Blocking" point where $P_2$'s field prevents $P_3$'s field from reaching $P_1$.

## 3. Experiment 2: Nested 4-Plate (Capacitor-in-Capacitor)
**Goal**: Verify the "Diode-like" threshold.
1.  **Setup**: Create two independent capacitors (A and B). Insert Capacitor A *inside* the field of Capacitor B (Nested Architecture).
2.  **Procedure**:
    - Power Capacitor A (Internal) to $5V$.
    - Attempt to power Capacitor B (External).
3.  **Result**: $V_{ext}$ should remain "trapped" or undetectable until it exceeds the $V_{int}$ threshold.

## 4. Experiment 3: Resonant Oscillation (Wet Dielectric)
**Goal**: Verify the "Negative Capacitance" flip.
1.  **Setup**: Use a Triple-Nested Capacitor (6 plates).
2.  **Dielectric**: Use a towel moistened with distilled water.
3.  **Procedure**:
    - Slowly increase the conductivity (e.g., add a drop of salt or use non-distilled water).
    - Monitor capacitance on a meter.
4.  **Result**: Observe the "Pointer Swing" or the meter flipping to negative values as the system self-oscillates at $R \approx 15-20\Omega$.

## 5. Experiment 4: Logic Implementation (NAND)
**Goal**: Physically implement binary logic.
1.  **Setup**: Connect two FTA units (from Exp 1/2) in parallel to a common power source.
2.  **Procedure**: Treat the two internal plates as Inputs A and B.
3.  **Result**: Verify the NAND Truth Table: Only when A AND B are powered does the Output drop to zero.

## 6. Experiment 5: Asymmetric Bias & Field Diode
**Goal**: Verify unidirectional field concentration.
1.  **Setup**: Use a 3-plate stack. Moisten Gap 1 (AB) with conductive water and Gap 2 (BC) with distilled water (Isolator).
2.  **Procedure**: Apply 5V to A/B and 0V to C.
3.  **Result**: Measure the potential gradient. Gap AB should show nearly 0V drop, while BC shows the full 5V drop.

## 7. Experiment 6: 10-State Decimal Staircase
**Goal**: Verify Multi-Valued Logic (MVL) potential.
1.  **Setup**: Stack 11 plates with uniform thin insulators.
2.  **Procedure**: Apply a resistive voltage divider to all 11 plates in 0.5V increments (creating a staircase).
3.  **Intervention**: Introduce a "Depletion Zone" by significantly increasing the resistance of a single gap.
4.  **Result**: Observe the "Field Pocket" shifting in location as different gaps are modulated. This identifies the stored decimal digit.

---
**Lead Architect**: Basel Yahya Abdullah  
**Status**: MASTER EXPERIMENTAL PROCEDURES VERIFIED
