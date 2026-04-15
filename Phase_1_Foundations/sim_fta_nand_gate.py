import numpy as np
import matplotlib.pyplot as plt

def fta_nand_logic(a_in, b_in):
    """
    Simulates the FTA Threshold Logic.
    If A and B are HIGH, the combined field blocks the output.
    """
    v_source = 5.0 # External Power Source
    threshold = 7.0 # NAND threshold: (A+B) > threshold to block. A alone (5.0) is not enough.
    
    # Combined field (Heuristic additive model for plates)
    field_barrier = a_in + b_in
    
    # Output is the source minus the barrier (but we implement discrete logic here)
    if field_barrier > threshold:
        v_out = 0.0
    else:
        v_out = 5.0
    
    # Logic Level detection
    logic_out = 1 if v_out > 2.5 else 0
    return v_out, logic_out

# Inputs (Binary)
inputs = [(0,0), (0,5), (5,0), (5,5)]
results = []

print("="*40)
print("FTA THRESHOLD NAND GATE TRUTH TABLE")
print("="*40)
print("A (V) | B (V) | Output (V) | Logic")
print("-" * 40)

for a, b in inputs:
    v_out, l_out = fta_nand_logic(a, b)
    results.append(l_out)
    print(f"{a:^5} | {b:^5} | {v_out:^10.2f} | {l_out:^5}")

# Visualization of Signal Levels
fig, ax = plt.subplots(figsize=(10, 6))
labels = ['[0,0]', '[0,1]', '[1,0]', '[1,1]']
v_outs = [fta_nand_logic(a, b)[0] for a, b in inputs]

ax.bar(labels, v_outs, color=['green', 'green', 'green', 'red'], alpha=0.7)
ax.axhline(2.5, color='gray', linestyle='--', label='Logic Threshold (2.5V)')
ax.set_title("FTA Logic Gate: Voltage Levels per Input state")
ax.set_ylabel("Output Voltage (V)")
ax.set_ylim(0, 6)
ax.legend()
plt.savefig('fta_nand_truth_table.png')
print("\n[+] Truth table visual generated: fta_nand_truth_table.png")

# Verify NAND Logic
expected_nand = [1, 1, 1, 0]
if results == expected_nand:
    print("\n[SUCCESS] The FTA Threshold Gate successfully behaves as a NAND GATE.")
else:
    print("\n[FAILURE] Logic mismatch. Current results:", results)
