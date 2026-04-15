## Phase 2: Triple Nested Capacitor (TNC) & Resonant Logic
- [x] Model the 6-plate "Triple Nested" architecture ($C_1$ in $C_2$ in $C_3$).
- [x] Implement **L-C Interaction**: Model the transition from purely capacitive to inductive-capacitive ($C \rightarrow L$).
- [ ] Simulate **Slow Ionic Oscillation**: Model the 1-10 Hz resonant behavior using ionic mobility delay.
- [ ] Analyze **Neuromorphic Potential**: Use slow pulses as "Spiking Logic" nodes.

## Phase 3: FTA Logic Gate Design
- [x] Design the "Threshold NAND Gate" architecture (Dual-Internal Bias).
- [x] Simulate the logical response to [0,0], [0,1], [1,0], [1,1] inputs.
- [ ] Verify signal gain (Fan-out) for cascading gates.
- [ ] Benchmark switching noise vs. traditional transistors.

## Phase 4: Arithmetic Logic (Adder Concept)
- [x] Implement a 1-bit Half-Adder using cascaded FTA NAND units.
- [x] Simulate Sum ($S$) and Carry ($C$) truth tables.
- [x] Implement a **Full-Adder (FA)** unit with Carry-In support.
- [x] Design a **4-Bit Parallel Adder** (Ripple-Carry architecture).
- [x] Simulate multi-digit addition (e.g., 7 + 5).

## Phase 5: Memory & Sequential Logic
- [x] Implement an **RS-Latch** using cross-coupled FTA NAND units.
- [x] Simulate a **1-Bit D-Latch** for clocked data storage.
- [x] Verify data persistence (Write-Hold-Read cycles).
- [ ] Design an 8-bit Register architecture using FTA Latches.

## Phase 6: Final Documentation & Release
- [ ] Author the **FTA Technical Whitepaper** (Conceptual to Logic).
- [ ] Create the **FTA Researcher's Guide** (Practical Laboratory Procedures).
- [ ] Organise all simulation code and results into a distribution-ready format.
