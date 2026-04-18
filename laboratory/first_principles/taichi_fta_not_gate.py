import taichi as ti
import numpy as np
import matplotlib.pyplot as plt
import os
import time
import sys

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

ti.init(arch=ti.gpu)

nx, ny, nz = 80, 80, 120 # برج أطول ليتسع لترانزستورين عموديين

sigma = ti.field(dtype=ti.f32, shape=(nx, ny, nz))
V = ti.field(dtype=ti.f32, shape=(nx, ny, nz))
V_new = ti.field(dtype=ti.f32, shape=(nx, ny, nz))

# المعاملات المكانية للترانزستورين
r1_field = ti.field(dtype=ti.f32, shape=()) # Pull-up (FTA1)
r2_field = ti.field(dtype=ti.f32, shape=()) # Pull-down (FTA2)

@ti.kernel
def init_materials():
    for i, j, k in sigma:
        sigma[i, j, k] = 1e-4
        V[i, j, k] = k / 119.0 * 100.0

    # توصيل البرج الرئيسي
    for i, j, k in ti.ndrange((20, 60), (20, 60), (0, nz)):
        sigma[i, j, k] = 1.0

    center_x, center_y = 40.0, 40.0
    
    # عنق الزجاجة السفلي (FTA2) بين ارتفاع 30 و 50
    r2 = r2_field[None]
    for i, j, k in ti.ndrange((20, 60), (20, 60), (30, 50)):
        dist_sq = (i - center_x)**2 + (j - center_y)**2
        if dist_sq > r2**2:
            sigma[i, j, k] = 1e-4

    # عنق الزجاجة العلوي (FTA1) بين ارتفاع 70 و 90
    r1 = r1_field[None]
    for i, j, k in ti.ndrange((20, 60), (20, 60), (70, 90)):
        dist_sq = (i - center_x)**2 + (j - center_y)**2
        if dist_sq > r1**2:
            sigma[i, j, k] = 1e-4

    # الأقطاب والجذور (Boundary Conditions - Dirichlet)
    for i, j in ti.ndrange((20, 60), (20, 60)):
        sigma[i, j, 0] = 1.0     # Ground (0V)
        sigma[i, j, nz-1] = 1.0  # VCC (100V)
        
        V[i, j, 0] = 0.0
        V_new[i, j, 0] = 0.0
        
        V[i, j, nz-1] = 100.0
        V_new[i, j, nz-1] = 100.0

@ti.kernel
def solve_voltage():
    # نطاق الحل يستثني القطاعات العلوية والسفلية (k=0, k=nz-1)
    for i, j, k in ti.ndrange((1, nx-1), (1, ny-1), (1, nz-1)):
        s_xp = 0.5 * (sigma[i, j, k] + sigma[i+1, j, k])
        s_xm = 0.5 * (sigma[i, j, k] + sigma[i-1, j, k])
        s_yp = 0.5 * (sigma[i, j, k] + sigma[i, j+1, k])
        s_ym = 0.5 * (sigma[i, j, k] + sigma[i, j-1, k])
        s_zp = 0.5 * (sigma[i, j, k] + sigma[i, j, k+1])
        s_zm = 0.5 * (sigma[i, j, k] + sigma[i, j, k-1])

        sum_s = s_xp + s_xm + s_yp + s_ym + s_zp + s_zm

        if sum_s > 0.0:
            V_new[i, j, k] = (s_xp * V[i+1, j, k] + s_xm * V[i-1, j, k] +
                              s_yp * V[i, j+1, k] + s_ym * V[i, j-1, k] +
                              s_zp * V[i, j, k+1] + s_zm * V[i, j, k-1]) / sum_s
        else:
            V_new[i, j, k] = V[i, j, k]

    for i, j, k in ti.ndrange((1, nx-1), (1, ny-1), (1, nz-1)):
        V[i, j, k] = V_new[i, j, k]

@ti.kernel
def read_vout() -> ti.f32:
    # النقطة المشتركة (Output Node) في المنتصف عند k=60
    total_v = 0.0
    count = 0.0
    for i, j in ti.ndrange((35, 45), (35, 45)):
        if sigma[i, j, 60] > 0.5:
            total_v += V[i, j, 60]
            count += 1.0
    return total_v / count

def main():
    # محاكاة إدخال الجهد كنسبة من 0 (0V) إلى 1 (Logic 1)
    inputs = np.linspace(0.0, 1.0, 11)
    v_outs = []

    print("="*60)
    print("بدء محاكاة بناء أول بوابة مكانية في التاريخ (FTA NOT Gate)...")
    print("="*60)
    
    t_start = time.time()
    
    for inp in inputs:
        # ديناميكية العنق الموازية لمنطق البوابة
        r1 = 2.0 + (1.0 - inp) * 14.0 # Pull-UP logic (inverse of input)
        r2 = 2.0 + (inp) * 14.0       # Pull-DOWN logic (matches input)
        
        r1_field[None] = r1
        r2_field[None] = r2
        init_materials()
        
        # 8000 تكرار مع التدرج الأولي يضمن استقرارا تاما لآلاف الخلايا
        for _ in range(8000):
            solve_voltage()
            
        vout = read_vout()
        v_outs.append(vout)
        print(f"[>] Input Level: {inp:4.2f} | R-Upper: {r1:5.1f}, R-Lower: {r2:5.1f} | Output V: {vout:6.2f} V")

    print(f"\nتمت محاكاة منحنى VTC في {time.time()-t_start:.2f} ثانية!")

    # رسم منحنى نقل الجهد للبوابة المنطقية
    plt.figure(figsize=(10, 6))
    
    inp_arr = np.array(inputs)
    vout_arr = np.array(v_outs)
    
    plt.plot(inp_arr, vout_arr, 'o-', color='#2ecc71', linewidth=3, markersize=10, label="FTA NOT Gate VTC")
    
    # محاور التوضيح
    plt.axhline(50, color='gray', linestyle='--', alpha=0.5)
    plt.axvline(0.5, color='gray', linestyle='--', alpha=0.5)
    
    plt.title("منحنى الدخل والخرج (VTC) لبوابة NOT باستخدام هندسة العوائق (FTA)", fontsize=14, fontweight='bold')
    plt.xlabel("المُدخل المنطقي (Logic Input Level) [0.0 to 1.0]", fontsize=12)
    plt.ylabel("الجهد المحصل للخرج (Output Voltage) [V]", fontsize=12)
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.legend()
    
    output_path = os.path.join(os.path.dirname(__file__), "fta_not_gate_vtc.png")
    plt.savefig(output_path, dpi=150)
    print(f"تم حفظ نتائج بوابة NOT بنجاح في:\n{os.path.abspath(output_path)}")

if __name__ == "__main__":
    main()
