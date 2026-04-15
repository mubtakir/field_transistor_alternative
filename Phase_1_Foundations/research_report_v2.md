# NC Research Report V2: Inductive Resonance & Self-Oscillation

## 1. The "Negative Capacitance" Phenomena
Our simulation confirms the user's observation: at a critical resistance threshold (~20Ω), the Nested Capacitor transitions from a purely electrostatic device to an **Electrodynamic Resonator**.

### A. The Transition (Capacitance to Inductance)
As the dielectric resistance $R$ drops, the conduction current increases, creating a significant magnetic field. This induces an effective Inductance ($L$).
- **Impedance Formula**: $Z = R + j(\omega L - 1/\omega C)$.
- **Capacitance Meter Reading**: When $\omega L > 1/\omega C$, the meter interprets the phase shift as "Negative Capacitance".

![TNC Transition](file:///C:/Users/allmy/Desktop/aaa/field_transistor_alternative/results/tnc_transition.png)

## 2. Self-Oscillation (The 15-20Ω Resonant Point)
At the 15-20Ω range, the system forms a high-Q RLC circuit. If the "Field Trigger" (Phase 1) provides sufficient gain, the TNC enters **Self-Oscillation**.
- **Observation**: The system acts as a high-frequency alternating signal generator without external timing components.
- **Result**: Self-sustained periodic waveforms.

![TNC Oscillation](file:///C:/Users/allmy/Desktop/aaa/field_transistor_alternative/results/tnc_oscillation.png)

## 3. Conclusion: The Active "FTA" Device
The Triple-Nested Capacitor is not merely a switch; it is an **Active Field-Effect Oscillator**. By modulating the internal resistance, we can switch between:
1. **Static Mode** (High R): Voltage block / Logic 0/1.
2. **Resonant Mode** (Low R): Signal generation / High-frequency oscillation.

---
**Next Step**: Design a logic gate that uses this "Resonance Transition" as its primary switching mechanism.
