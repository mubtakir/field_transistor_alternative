import numpy as np
import matplotlib.pyplot as plt

def fta_unit_nand(a_v, b_v):
    threshold = 7.0
    return 0.0 if (a_v + b_v) > threshold else 5.0

def fta_logic_or(a, b):
    # NAND(NAND(A,A), NAND(B,B))
    r1 = fta_unit_nand(a, a)
    r2 = fta_unit_nand(b, b)
    return fta_unit_nand(r1, r2)

def fta_half_adder(a, b):
    # XOR for Sum, AND for Carry
    # XOR = NAND(NAND(A, NAND(A, B)), NAND(B, NAND(A, B)))
    # AND = NAND(NAND(A, B), NAND(A, B))
    v_nand_ab = fta_unit_nand(a, b)
    
    # Sum (XOR)
    v_s1 = fta_unit_nand(a, v_nand_ab)
    v_s2 = fta_unit_nand(b, v_nand_ab)
    v_sum = fta_unit_nand(v_s1, v_s2)
    
    # Carry (AND)
    v_carry = fta_unit_nand(v_nand_ab, v_nand_ab)
    
    return v_sum, v_carry

def fta_full_adder(a, b, cin):
    # FA = 2 HAs + 1 OR
    s1, c1 = fta_half_adder(a, b)
    s2, c2 = fta_half_adder(s1, cin)
    cout = fta_logic_or(c1, c2)
    return s2, cout

def fta_4bit_adder(a_bits, b_bits):
    """
    a_bits, b_bits: list of 4 bools [bit0, bit1, bit2, bit3]
    """
    va = [5.0 if b else 0.0 for b in a_bits]
    vb = [5.0 if b else 0.0 for b in b_bits]
    
    results_s = []
    current_carry = 0.0
    
    for i in range(4):
        s, c = fta_full_adder(va[i], vb[i], current_carry)
        results_s.append(1 if s > 2.5 else 0)
        current_carry = c
        
    final_carry = 1 if current_carry > 2.5 else 0
    return results_s, final_carry

# Test Case: 7 (0111) + 5 (0101) = 12 (1100)
a = [1, 1, 1, 0] # LSB first: 1, 2, 4, 8 -> 7
b = [1, 0, 1, 0] # LSB first: 1, 2, 4, 8 -> 5

print("="*40)
print("FTA 4-BIT PARALLEL ADDER TEST")
print("="*40)
print(f"Adding A: {a[::-1]} (7) and B: {b[::-1]} (5)")

s_bits, carry = fta_4bit_adder(a, b)
result_val = sum([bit * (2**i) for i, bit in enumerate(s_bits)]) + (carry * 16)

print(f"Result bits: {s_bits[::-1]} Carry: {carry}")
print(f"Calculated Value: {result_val}")

if result_val == 12:
    print("\n[SUCCESS] 7 + 5 = 12 verified.")
else:
    print(f"\n[FAILURE] Expected 12, got {result_val}")

# Visualization of Signal Propagation
plt.figure(figsize=(10, 6))
plt.step(range(4), s_bits, where='post', label='Sum Bits', lw=2, color='blue')
plt.axhline(carry, color='red', linestyle='--', label='Final Carry')
plt.title("4-Bit FTA Adder Output Signals (LSB to MSB)")
plt.xlabel("Bit Position")
plt.ylabel("Logic Level (0/1)")
plt.xticks(range(4))
plt.grid(True, alpha=0.3)
plt.legend()
plt.savefig('fta_4bit_adder_test.png')
print("\n[+] Adder verification visual generated: fta_4bit_adder_test.png")
