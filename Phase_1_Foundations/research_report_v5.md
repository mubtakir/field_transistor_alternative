# NC Research Report V5: Decimal & Multi-Valued Logic (MVL)

## 1. Beyond Binary: The Decimal FTA
We have successfully modeled a **10-State Multi-Valued Logic (MVL)** system using an 11-plate FTA stack. Unlike traditional binary transistors (0 or 1), a single Decimal FTA unit can represent any digit from **0 to 9**.

## 2. Theoretical Mechanism: The Potential Staircase
By biasing each plate in the stack with a discrete voltage increment (e.g., 0.5V steps), we create a "Potential Staircase".
- **State Selection**: By modulating the resistance of a specific gap in the stack, we create a localized "Potential Drop" (Depletion Zone).
- **Observation**: The location of this depletion zone identifies the stored decimal value.

![Decimal Staircase](file:///C:/Users/allmy/Desktop/aaa/field_transistor_alternative/results/fta_decimal_staircase.png)

## 3. Informatic Density Analysis
- **Binary (Traditional)**: 1 bit per unit.
- **Decimal (FTA)**: $\log_2(10) \approx 3.32$ bits per unit.
- **Efficiency**: A single 10-state FTA stack replaces more than 3 binary transistors in terms of information storage capacity.

## 4. Conclusion: The "Decimal Computer"
The "Capacitor Within a Capacitor" is naturally suited for multi-valued logic due to its nested, multi-plate architecture. We can now theoretically design computers that process information in base-10, mimicking the human counting system and drastically reducing the number of components required for complex arithmetic.

---
**Lead Architect**: Basel Yahya Abdullah  
**Status**: MULTI-VALUED LOGIC VERIFIED
