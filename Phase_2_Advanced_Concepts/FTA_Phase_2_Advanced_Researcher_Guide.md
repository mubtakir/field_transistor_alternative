# Phase 2 Advanced Researcher's Guide: NICL Experimental Procedures

## 1. Overview
This guide provides practical laboratory steps for verifying the **Nested Inductive-Capacitive Loop (NICL)** and **Resonant Logic** breakthroughs documented in Phase 2.

## 2. Equipment Required
- Precision Function Generator (10kHz - 50MHz).
- High-Frequency Oscilloscope.
- Concentric Wire-Loops (Silver-plated or Graphene-coated).
- High-k Ceramic Dielectric Spacers (PZT or TiO2).
- Ferrite Core material (optional for freq-shifting).

## 3. Experiment 1: Resonant Frequency Detection
**Goal**: Verify the natural resonance of a 2-loop NICL.
1. **Setup**: Nest two silver loops with a thin PZT dielectric.
2. **Procedure**: Sweep the frequency from 10kHz to 1MHz using the function generator.
3. **Observation**: Measure the signal gain on the secondary loop. Identify the sharp peak ($f_r$).

## 4. Experiment 2: Multi-Frequency Multiplexing
**Goal**: Verify two independent logic channels in a single stack.
1. **Setup**: Use three concentric loops ($L_1, L_2, L_3$).
2. **Procedure**: Sweep the system and identify two distinct resonant peaks ($f_{LF}$ and $f_{HF}$).
3. **Trigger**: Modulate the gap between $L_1$ and $L_2$.
4. **Result**: Observe the shift in $f_{LF}$ while $f_{HF}$ remains stable.

## 5. Experiment 3: Resonant Latch Persistence
**Goal**: Verify frequency-locked state storage.
1. **Setup**: Connect the NICL output back to its trigger via a high-speed amplifier (Feedback Loop).
2. **Procedure**: Inject a 500kHz "Write" pulse.
3. **Result**: Observe the system self-sustaining the 500kHz oscillation after the input is removed.

---
**Lead Architect**: Basel Yahya Abdullah  
**Status**: MASTER ADVANCED PROCEDURES VERIFIED
