"""
FTA Virtual Lab - منصة محاكاة تجريبية لمكون الحقول المتقاطعة
Author: Basel Yahya
Version: 1.0
Date: March 2026

هذه المنصة تحاكي أدوات القياس الفعلية في المختبر:
- مقياس متعدد (DMM) لقياس R, C, L, V, I
- محلل معاوقة (Impedance Analyzer) لقياس Z, θ, |Z|, Phase
- راسم إشارة (Oscilloscope) لعرض أشكال الموجات
- محلل طيف (Spectrum Analyzer) لتحليل الترددات
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import fsolve
from scipy.signal import welch
from dataclasses import dataclass
from typing import Tuple, Optional
import os
import warnings
warnings.filterwarnings('ignore')

# ============================================================
# النماذج الفيزيائية الأساسية
# ============================================================

@dataclass
class FTAParameters:
    """معاملات FTA القابلة للضبط من قبل الباحث"""
    # معاملات العازل
    A_FN: float = 1e-6          # معامل Fowler-Nordheim [A·V⁻²]
    B_FN: float = 2.5e8         # معامل الحاجز [V/m]
    tox: float = 20e-9          # سمك العازل [m]
    area: float = 1e-12         # مساحة الجهاز [m²]
    eps_r: float = 3.9          # ثابت العزل النسبي (SiO2)
    
    # معاملات NDR (من المواد الطبيعية أو الهندسية)
    J_peak: float = 4.2e-6      # ذروة تيار NDR [A/m²]
    sigma_NDR: float = 1.0e8    # عرض NDR [V/m]
    E_peak: float = 1.2e8       # مجال ذروة NDR [V/m]
    
    # معاملات البوابة المعكوسة (PANI/rGO) لـ C-FTA
    use_inverse_gate: bool = False
    J_inv_max: float = 1e-3     # أقصى تيار للبوابة المعكوسة [A]
    V_inv_th: float = 2.0       # جهد عتبة البوابة المعكوسة [V]
    
    # معاملات كهربائية
    R_load: float = 1e3         # مقاومة الحمل [Ohm]
    C_parasitic: float = 1e-15  # سعة طفيلية [F]
    L_parasitic: float = 1e-12  # محاثة طفيلية [H]
    
    # ظروف التشغيل
    temperature: float = 300    # درجة الحرارة [K]
    V_bias: float = 0.0         # جهد الانحياز [V]


class FTADevice:
    """النموذج الفيزيائي لجهاز FTA"""
    
    def __init__(self, params: FTAParameters):
        self.params = params
        
    def J_FN(self, E: float) -> float:
        """تيار فاولر-نوردهايم (A/m²)"""
        if E <= 0:
            return 0
        return self.params.A_FN * E**2 * np.exp(-self.params.B_FN / E)
    
    def J_NDR(self, E: float) -> float:
        """تيار NDR من المواد الطبيعية أو الهندسية (A/m²)"""
        return self.params.J_peak * np.exp(-((E - self.params.E_peak)**2) / (self.params.sigma_NDR**2))
    
    def J_inverse_gate(self, V: float) -> float:
        """تيار البوابة المعكوسة (PANI/rGO) - للمنطق المكمّل"""
        if not self.params.use_inverse_gate:
            return 0
        # عند V=0: تيار عالٍ (ON)، عند V>V_th: تيار منخفض (OFF)
        return self.params.J_inv_max * (1 - 1/(1 + np.exp(-5*(V - self.params.V_inv_th))))
    
    def current_density(self, E: float) -> float:
        """كثافة التيار الكلية (A/m²)"""
        J_fn = self.J_FN(E)
        J_ndr = self.J_NDR(E)
        return J_fn - J_ndr
    
    def current(self, V: float) -> float:
        """التيار الكلي (A)"""
        # المجال الكهربائي مع مراعاة جهد الانحياز
        E = (V - self.params.V_bias) / self.params.tox
        if E < 0:
            E = 0
        J_total = self.current_density(E)
        I = J_total * self.params.area
        # إضافة تيار البوابة المعكوسة إن وجد
        I += self.J_inverse_gate(V) * self.params.area
        return I
    
    def conductance(self, V: float) -> float:
        """الموصلية التفاضلية (S)"""
        dV = 1e-6
        I_plus = self.current(V + dV)
        I_minus = self.current(V - dV)
        return (I_plus - I_minus) / (2 * dV)
    
    def impedance(self, V: float, f: float) -> complex:
        """المعاوقة عند تردد معين (Ohm)"""
        # المقاومة التفاضلية عند نقطة العمل
        G = self.conductance(V)
        R_diff = 1 / G if abs(G) > 1e-15 else 1e15
        
        # السعة الديناميكية (تقديرية من سمك العازل والمساحة + شحنة النفق)
        C_geo = (self.params.eps_r * 8.854e-12 * self.params.area) / self.params.tox
        
        # المعاوقة الكلية: Z = R || (1/jwc) + jwL
        omega = 2 * np.pi * f
        Z_rc = R_diff / (1 + 1j * omega * R_diff * (C_geo + self.params.C_parasitic))
        Z_total = Z_rc + 1j * omega * self.params.L_parasitic
        return Z_total


# ============================================================
# أدوات القياس الافتراضية
# ============================================================

class VirtualMultimeter:
    """مقياس متعدد افتراضي - يقيس R, C, L, V, I"""
    
    def __init__(self, device: FTADevice):
        self.device = device
    
    def measure_resistance(self, V_test: float = 0.1) -> float:
        """قياس المقاومة"""
        I = self.device.current(V_test)
        if I == 0:
            return float('inf')
        return V_test / I
    
    def measure_capacitance(self, V_test: float = 0.1, f_test: float = 1e3) -> float:
        """قياس السعة (طريقة التوصيلية التخيلية - Parallel Model)"""
        Z = self.device.impedance(V_test, f_test)
        if abs(Z) < 1e-15:
            return float('inf')
        Y = 1 / Z
        omega = 2 * np.pi * f_test
        return Y.imag / omega
    
    def measure_inductance(self, V_test: float = 0.1, f_test: float = 1e6) -> float:
        """قياس المحاثة"""
        Z = self.device.impedance(V_test, f_test)
        omega = 2 * np.pi * f_test
        if Z.imag <= 0:
            return 0
        return Z.imag / omega
    
    def measure_all(self, V_test: float = 0.1, f_test: float = 1e3) -> dict:
        return {
            'resistance': self.measure_resistance(V_test),
            'capacitance': self.measure_capacitance(V_test, f_test),
            'inductance': self.measure_inductance(V_test, f_test),
            'voltage': V_test,
            'current': self.device.current(V_test),
        }


class VirtualImpedanceAnalyzer:
    """محلل معاوقة افتراضي - يقيس Z, θ, |Z|, Phase"""
    
    def __init__(self, device: FTADevice):
        self.device = device
    
    def analyze(self, V_bias: float, f_start: float = 10, f_stop: float = 1e12, points: int = 100) -> dict:
        frequencies = np.logspace(np.log10(f_start), np.log10(f_stop), points)
        Z_mag = []
        Z_phase = []
        
        for f in frequencies:
            Z = self.device.impedance(V_bias, f)
            Z_mag.append(abs(Z))
            Z_phase.append(np.angle(Z, deg=True))
        
        return {
            'frequency': frequencies,
            'magnitude': np.array(Z_mag),
            'phase': np.array(Z_phase)
        }


class VirtualOscilloscope:
    """راسم إشارة افتراضي"""
    
    def __init__(self, device: FTADevice):
        self.device = device
    
    def capture_step_response(self, V_step: float, t_rise: float = 1e-12, t_stop: float = 100e-12, points: int = 500) -> dict:
        t = np.linspace(0, t_stop, points)
        V_input = V_step * (1 - np.exp(-t / t_rise))
        I_output = np.array([self.device.current(Vi) for Vi in V_input])
        
        # Rise time estimate
        I_min = I_output.min()
        I_max = I_output.max()
        I_10 = I_min + 0.1 * (I_max - I_min)
        I_90 = I_min + 0.9 * (I_max - I_min)
        
        t_10 = t[np.where(I_output >= I_10)[0][0]] if len(np.where(I_output >= I_10)[0]) > 0 else 0
        t_90 = t[np.where(I_output >= I_90)[0][0]] if len(np.where(I_output >= I_90)[0]) > 0 else t_stop
        
        return {
            'time': t,
            'input_voltage': V_input,
            'output_current': I_output,
            'rise_time': t_90 - t_10
        }


class FTALabBench:
    """منصة مختبر FTA الافتراضية"""
    
    def __init__(self, params: FTAParameters = None):
        if params is None:
            params = FTAParameters()
        self.params = params
        self.device = FTADevice(params)
        self.multimeter = VirtualMultimeter(self.device)
        self.impedance_analyzer = VirtualImpedanceAnalyzer(self.device)
        self.oscilloscope = VirtualOscilloscope(self.device)
    
    def sweep_IV(self, V_start: float = 0, V_stop: float = 5, points: int = 200) -> dict:
        V = np.linspace(V_start, V_stop, points)
        I = np.array([self.device.current(v) for v in V])
        return {'voltage': V, 'current': I}
    
    def plot_bench_results(self, output_path: str):
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        
        # 1. IV Curve
        iv_data = self.sweep_IV(0, 5)
        ax1.plot(iv_data['voltage'], iv_data['current'] * 1e6, 'b-', linewidth=2)
        ax1.set_xlabel('Voltage (V)')
        ax1.set_ylabel('Current (uA)')
        ax1.set_title('FTA virtual DMM: IV Curve')
        ax1.grid(True, alpha=0.3)
        
        # 2. Bode Plot
        bode = self.impedance_analyzer.analyze(1.2) # Bias at peak
        ax2.semilogx(bode['frequency'], 20 * np.log10(bode['magnitude']), 'r-')
        ax2.set_xlabel('Frequency (Hz)')
        ax2.set_ylabel('Impedance (dB Ohms)')
        ax2.set_title('FTA Impedance Analyzer: Bode Magnitude')
        ax2.grid(True, alpha=0.3)
        
    def export_to_csv(self, filename: str, data: dict):
        """Export measurement data to CSV for external analysis."""
        import pandas as pd
        df = pd.DataFrame(data)
        df.to_csv(filename, index=False)
        print(f"Data exported to {filename}")

    def export_to_spice(self, filename: str):
        """Export FTA device as a SPICE subcircuit (.subckt)."""
        with open(filename, 'w') as f:
            f.write("* FTA Device Subcircuit - Generated by OOS-Lab v1.1\n")
            f.write(".SUBCKT FTA_UNIT drain gate source substrate\n")
            f.write(f"* Params: tox={self.params.tox} area={self.params.area}\n")
            f.write("G_IV drain source VALUE={ J_FN(V(drain,source)) * area }\n")
            f.write(".ENDS\n")
        print(f"SPICE model exported to {filename}")

def main():
    bench = FTALabBench()
    print("\n" + "="*50)
    print("OOS-Lab: Virtual Lab Bench Measurement Report")
    print("="*50)
    
    meas = bench.multimeter.measure_all(V_test=1.0)
    print(f"DC Resistance: {meas['resistance']:.2f} Ohms")
    print(f"Capacitance:   {meas['capacitance']*1e15:.2f} fF")
    print(f"Inductance:    {meas['inductance']*1e12:.2f} pH")
    print(f"Total Current: {meas['current']*1e6:.2f} uA")
    
    bench.plot_bench_results("c:/Users/allmy/Desktop/oos/oos_lab/analysis/fta_lab_bench_demo.png")

if __name__ == "__main__":
    main()
