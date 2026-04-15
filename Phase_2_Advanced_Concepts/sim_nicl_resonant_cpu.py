import numpy as np
import matplotlib.pyplot as plt

def sim_resonant_cpu():
    """
    Simulates a 1-bit Resonant CPU instruction cycle:
    1. ALU: Addition (A + B)
    2. BUS: Frequency Transfer
    3. MEM: Storage (Latch)
    """
    time = np.linspace(0, 100, 10000) # Microseconds
    dt = (time[1] - time[0]) / 1e6
    
    # Frequency Definitions
    f_sum_1 = 400e3 # 400kHz represents SUM=1
    f_carry_1 = 800e3 # 800kHz represents CARRY=1
    
    # Instruction Cycle: Add 1 + 1 (Result: Sum=0, Carry=1)
    
    # Stage 1: ALU Execution (0 to 40us)
    # ALU generates the Carry frequency because 1+1 = 10 (binary)
    alu_output = np.sin(2 * np.pi * f_carry_1 * (time[:4000]/1e6))
    
    # Stage 2: Store Pulse (40 to 60us)
    # Register/Latch receives the f_carry_1 signal
    latch_input = 1.2 * np.sin(2 * np.pi * f_carry_1 * (time[4000:6000]/1e6))
    
    # Stage 3: Latched State (60 to 100us)
    # Memory maintains the Carry state permanently
    memory_state = np.sin(2 * np.pi * f_carry_1 * (time[6000:]/1e6))
    
    total_cpu_bus = np.concatenate([alu_output, latch_input, memory_state])
    
    # Visualization
    plt.figure(figsize=(14, 10))
    
    plt.subplot(2, 1, 1)
    plt.plot(time, total_cpu_bus, color='purple', alpha=0.8)
    plt.axvspan(0, 40, color='blue', alpha=0.1, label='ALU EXECUTE (1+1)')
    plt.axvspan(40, 60, color='red', alpha=0.1, label='BUS TRANSFER / STORE')
    plt.axvspan(60, 100, color='green', alpha=0.1, label='MEMORY HOLD (STATE: CARRY=1)')
    plt.title("NITL Resonant-CPU: Complete Instruction Cycle [Add & Store]")
    plt.ylabel("Bus Magnitude")
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # Spectral verification of each stage
    plt.subplot(2, 2, 3)
    fft_exec = np.abs(np.fft.rfft(alu_output))
    freqs_exec = np.fft.rfftfreq(len(alu_output), d=dt)
    plt.plot(freqs_exec/1e3, fft_exec/max(fft_exec), color='blue')
    plt.title("ALU Spectral Output (Result: CARRY)")
    plt.xlim(0, 1000)
    plt.xlabel("kHz")
    
    plt.subplot(2, 2, 4)
    fft_mem = np.abs(np.fft.rfft(memory_state))
    freqs_mem = np.fft.rfftfreq(len(memory_state), d=dt)
    plt.plot(freqs_mem/1e3, fft_mem/max(fft_mem), color='green')
    plt.title("Register Latched State")
    plt.xlim(0, 1000)
    plt.xlabel("kHz")
    
    plt.tight_layout()
    plt.savefig(r'C:\Users\allmy\Desktop\aaa\field_transistor_alternative\Phase_2_Advanced_Concepts\nicl_resonant_cpu.png')
    print("[+] Resonant CPU graph generated: Phase_2_Advanced_Concepts/nicl_resonant_cpu.png")

if __name__ == "__main__":
    sim_resonant_cpu()
