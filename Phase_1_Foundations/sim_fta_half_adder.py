import numpy as np
import matplotlib.pyplot as plt

def fta_unit_nand(a_v, b_v):
    """
    Simplified FTA NAND Unit.
    """
    threshold = 7.0
    if (a_v + b_v) > threshold:
        return 0.0 # Logic 0
    else:
        return 5.0 # Logic 1

def fta_logic_and(a, b):
    # NAND(A, B) -> NAND(result, result)
    r1 = fta_unit_nand(a, b)
    return fta_unit_nand(r1, r1)

def fta_logic_xor(a, b):
    # NAND(NAND(A, NAND(A, B)), NAND(B, NAND(A, B)))
    r_ab = fta_unit_nand(a, b)
    r_a_ab = fta_unit_nand(a, r_ab)
    r_b_ab = fta_unit_nand(b, r_ab)
    return fta_unit_nand(r_a_ab, r_b_ab)

def fta_half_adder(a_bool, b_bool):
    # Convert bool to FTA voltages (0V and 5V)
    va = 5.0 if a_bool else 0.0
    vb = 5.0 if b_bool else 0.0
    
    # Calculate Sum (XOR) and Carry (AND)
    v_sum = fta_logic_xor(va, vb)
    v_carry = fta_logic_and(va, vb)
    
    # Logic detection
    sum_out = 1 if v_sum > 2.5 else 0
    carry_out = 1 if v_carry > 2.5 else 0
    
    return sum_out, carry_out

# Test all combinations
inputs = [(0,0), (0,1), (1,0), (1,1)]
print("="*40)
print("FTA 1-BIT HALF-ADDER TRUTH TABLE")
print("="*40)
print("A | B | Sum (S) | Carry (C)")
print("-" * 40)

plot_data = []

for a, b in inputs:
    s, c = fta_half_adder(a, b)
    print(f"{a} | {b} |   {s}     |    {c}")
    plot_data.append((s, c))

# Visualization
fig, ax = plt.subplots(figsize=(10, 6))
labels = ['0+0', '0+1', '1+0', '1+1']
sums = [d[0] for d in plot_data]
carrys = [d[1] for d in plot_data]

x = np.arange(len(labels))
width = 0.35

ax.bar(x - width/2, sums, width, label='Sum (S)', color='skyblue')
ax.bar(x + width/2, carrys, width, label='Carry (C)', color='navy')

ax.set_title("FTA Half-Adder: Arithmetic Logic Verification")
ax.set_xticks(x)
ax.set_xticklabels(labels)
ax.set_ylabel("Logic State (0/1)")
ax.legend()
plt.savefig('fta_half_adder_results.png')
print("\n[+] Adder verification visual generated: fta_half_adder_results.png")
