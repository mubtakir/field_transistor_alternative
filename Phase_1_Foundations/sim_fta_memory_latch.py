import numpy as np
import matplotlib.pyplot as plt

def fta_unit_nand(a_v, b_v):
    threshold = 7.0
    return 0.0 if (a_v + b_v) > threshold else 5.0

class FTADLatch:
    def __init__(self):
        self.q = 0.0 # Logic 0 (0V)
        self.q_bar = 5.0 # Logic 1 (5V)
        
    def step(self, d_in, enable):
        """
        D-Latch logic using 4 NAND gates + 1 NOT (NAND-based)
        """
        vd = 5.0 if d_in else 0.0
        ve = 5.0 if enable else 0.0
        
        # NOT D
        not_d = fta_unit_nand(vd, vd)
        
        # Input NANDs
        n1 = fta_unit_nand(vd, ve)
        n2 = fta_unit_nand(not_d, ve)
        
        # Cross-coupled Latch (Iterate for convergence)
        for _ in range(5):
            self.q = fta_unit_nand(n1, self.q_bar)
            self.q_bar = fta_unit_nand(n2, self.q)
            
        return 1 if self.q > 2.5 else 0

# Simulation Cycle
latch = FTADLatch()
time_steps = 20
data_in = [0, 1, 1, 0, 0, 1, 0, 0, 1, 1] * 2
enable_in = [1, 1, 0, 0, 1, 1, 0, 0, 1, 1] * 2

q_out = []

print("="*40)
print("FTA 1-BIT D-LATCH SIMULATION")
print("="*40)
print("Step | D | E | Q (Stored)")
print("-" * 25)

for i in range(time_steps):
    q = latch.step(data_in[i], enable_in[i])
    q_out.append(q)
    print(f"{i:^4} | {data_in[i]} | {enable_in[i]} |   {q}")

# Visualization
plt.figure(figsize=(12, 8))
t = np.arange(time_steps)

plt.subplot(3, 1, 1)
plt.step(t, data_in[:time_steps], label='Data Input (D)', color='green', where='post')
plt.ylabel("D (0/1)")
plt.legend()
plt.grid(True, alpha=0.3)

plt.subplot(3, 1, 2)
plt.step(t, enable_in[:time_steps], label='Enable Signal (E)', color='red', where='post')
plt.ylabel("E (0/1)")
plt.legend()
plt.grid(True, alpha=0.3)

plt.subplot(3, 1, 3)
plt.step(t, q_out, label='Stored Data (Q)', color='blue', lw=2, where='post')
plt.ylabel("Q (0/1)")
plt.xlabel("Clock Cycles")
plt.legend()
plt.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('fta_memory_latch_test.png')
print("\n[+] Memory Latch verification visual generated: fta_memory_latch_test.png")
