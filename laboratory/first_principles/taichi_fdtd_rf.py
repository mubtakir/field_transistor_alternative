import taichi as ti
import numpy as np
import matplotlib.pyplot as plt
import os
import sys
import time

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

ti.init(arch=ti.gpu)

# ------------------------------------------------------------------------
# 1. إعدادات الشبكة والفضاء الزمني لـ FDTD (Yee Lattice)
# ------------------------------------------------------------------------
nx, ny, nz = 50, 50, 80
dx = 1e-6 # دقة المايكرومتر
dt = 0.9 * dx / (3e8 * np.sqrt(3)) # شرط استقرار كولانت (Courant Condition)
max_steps = 30000 # عدد اللقطات الزمنية لضمان مرور النبضة واستقرارها

# الثوابت الفيزيائية الكونية
eps0 = 8.854e-12
mu0 = 4.0 * np.pi * 1e-7

# ------------------------------------------------------------------------
# 2. الحقول الكهرومغناطيسية (E & H)
# ------------------------------------------------------------------------
Ex = ti.field(dtype=ti.f32, shape=(nx, ny, nz))
Ey = ti.field(dtype=ti.f32, shape=(nx, ny, nz))
Ez = ti.field(dtype=ti.f32, shape=(nx, ny, nz))

Hx = ti.field(dtype=ti.f32, shape=(nx, ny, nz))
Hy = ti.field(dtype=ti.f32, shape=(nx, ny, nz))
Hz = ti.field(dtype=ti.f32, shape=(nx, ny, nz))

# خصائص المواد
eps_r = ti.field(dtype=ti.f32, shape=(nx, ny, nz))
sigma_e = ti.field(dtype=ti.f32, shape=(nx, ny, nz))

# معاملات تحديث FDTD
Ceye = ti.field(dtype=ti.f32, shape=(nx, ny, nz))
Cexh = ti.field(dtype=ti.f32, shape=(nx, ny, nz))

@ti.kernel
def init_materials():
    for i, j, k in eps_r:
        # هواء / فراغ
        eps_r[i, j, k] = 1.0
        sigma_e[i, j, k] = 0.0

    # تشكيل المادة (FTA)
    # استخدام سماحية وموصلية تسمح باختراق الموجة للمحاكاة (Semi-conductor/Dielectric blend)
    center_x, center_y = nx/2, ny/2
    for i, j, k in ti.ndrange((10, 40), (10, 40), (10, 70)):
        eps_r[i, j, k] = 4.0
        sigma_e[i, j, k] = 200.0 # موصلية كافية لتسريب التيار

    # عنق الزجاجة (الترانزستور) هندسياً في المنتصف
    for i, j, k in ti.ndrange((10, 40), (10, 40), (35, 45)):
        dist_sq = (i - center_x)**2 + (j - center_y)**2
        if dist_sq > 5.0**2: # Radius = 5
            eps_r[i, j, k] = 1.0
            sigma_e[i, j, k] = 0.0 # إزالة الموصلية (عازل)

    # تجهيز المعاملات الحسابية للمعادلات التفاضلية
    for i, j, k in eps_r:
        eps = eps_r[i, j, k] * eps0
        sig = sigma_e[i, j, k]
        
        den = 1.0 + (sig * dt) / (2.0 * eps)
        Ceye[i, j, k] = (1.0 - (sig * dt) / (2.0 * eps)) / den
        Cexh[i, j, k] = (dt / eps) / den / dx

@ti.kernel
def update_H():
    # قانون فاراداي للمغناطيسية
    for i, j, k in ti.ndrange((0, nx-1), (0, ny-1), (0, nz-1)):
        Hx[i, j, k] -= (dt / mu0 / dx) * ((Ez[i, j+1, k] - Ez[i, j, k]) - (Ey[i, j, k+1] - Ey[i, j, k]))
        Hy[i, j, k] -= (dt / mu0 / dx) * ((Ex[i, j, k+1] - Ex[i, j, k]) - (Ez[i+1, j, k] - Ez[i, j, k]))
        Hz[i, j, k] -= (dt / mu0 / dx) * ((Ey[i+1, j, k] - Ey[i, j, k]) - (Ex[i, j+1, k] - Ex[i, j+1, k]))

@ti.kernel
def update_E():
    # قانون أمبير للكهربائية
    for i, j, k in ti.ndrange((1, nx), (1, ny), (1, nz)):
        Ex[i, j, k] = Ceye[i, j, k] * Ex[i, j, k] + Cexh[i, j, k] * ((Hz[i, j, k] - Hz[i, j-1, k]) - (Hy[i, j, k] - Hy[i, j, k-1]))
        Ey[i, j, k] = Ceye[i, j, k] * Ey[i, j, k] + Cexh[i, j, k] * ((Hx[i, j, k] - Hx[i, j, k-1]) - (Hz[i, j, k] - Hz[i-1, j, k]))
        Ez[i, j, k] = Ceye[i, j, k] * Ez[i, j, k] + Cexh[i, j, k] * ((Hy[i, j, k] - Hy[i-1, j, k]) - (Hx[i, j, k] - Hx[i, j-1, k]))

@ti.kernel
def add_source(step: ti.i32):
    # نبضة جاوسية (Gaussian Pulse) تحوي طيفاً واسعاً من الترددات (Up to THz)
    t = float(step) * dt
    t0 = 100.0 * dt
    spread = 30.0 * dt
    pulse = ti.exp(-((t - t0) ** 2) / (spread ** 2))
    
    # حقن النبضة على شكل موجة جهدية في المنفذ 1 (Port 1)
    for i, j in ti.ndrange((20, 30), (20, 30)):
        Ez[i, j, 15] += pulse

@ti.kernel
def read_ports(v1: ti.template(), i1: ti.template(), v2: ti.template(), i2: ti.template(), step: ti.i32):
    # مراقبة الجهد والتيار عند منفذ الإدخال (Port 1) Z=15
    v1_sum, i1_sum = 0.0, 0.0
    for i, j in ti.ndrange((20, 30), (20, 30)):
        v1_sum += Ez[i, j, 15] * dx
        i1_sum += (Hx[i, j+1, 15] - Hx[i, j, 15] - Hy[i+1, j, 15] + Hy[i, j, 15]) * dx
    v1[step] = v1_sum
    i1[step] = i1_sum
    
    # مراقبة الاستجابة عند منفذ الإخراج (Port 2) Z=65 بعد الاختناق
    v2_sum, i2_sum = 0.0, 0.0
    for i, j in ti.ndrange((20, 30), (20, 30)):
        v2_sum += Ez[i, j, 65] * dx
        i2_sum += (Hx[i, j+1, 65] - Hx[i, j, 65] - Hy[i+1, j, 65] + Hy[i, j, 65]) * dx
    v2[step] = v2_sum
    i2[step] = i2_sum

v1_arr = ti.field(dtype=ti.f32, shape=max_steps)
i1_arr = ti.field(dtype=ti.f32, shape=max_steps)
v2_arr = ti.field(dtype=ti.f32, shape=max_steps)
i2_arr = ti.field(dtype=ti.f32, shape=max_steps)

def main():
    print("="*60)
    print("بدء بناء وتطبيق معادلات ماكسويل الكاملة بالبعد الزمني (3D FDTD)...")
    print("="*60)

    init_materials()
    print("تم توليد الهيكل المادي. إطلاق الموجة الكهرومغناطيسية وحساب الانكسارات والحيود...")
    
    t_start = time.time()
    for step in range(max_steps):
        update_H()
        update_E()
        add_source(step)
        read_ports(v1_arr, i1_arr, v2_arr, i2_arr, step)
        
        if step > 0 and step % 3000 == 0:
            print(f"- إطار زمني: {step} محاكاة النبضة...")
            
    print(f"تم التقاط جميع الإشارات في {time.time()-t_start:.2f} ثانية من معالجة الـ GPU!")

    print("\nتطبيق تحويل فورييه (FFT) واستخراج دوال الدائرة المكافئة (S-Params, C, L)...")
    v1 = v1_arr.to_numpy()
    i1 = i1_arr.to_numpy()
    v2 = v2_arr.to_numpy()
    
    # تحويل من الزمن إلى التردد
    V1_f = np.fft.fft(v1)
    I1_f = np.fft.fft(i1)
    V2_f = np.fft.fft(v2)
    freqs = np.fft.fftfreq(max_steps, d=dt)
    
    # اختيار النطاق الترددي الواقعي (GHz)
    valid_idx = (freqs > 10e9) & (freqs < 1000e9) 
    f_valid = freqs[valid_idx]
    
    V1_v = V1_f[valid_idx]
    I1_v = I1_f[valid_idx]
    V2_v = V2_f[valid_idx]
    
    # الممانعة الجوهرية للجهاز (Input Impedance)
    Z_in = V1_v / (I1_v + 1e-15)
    
    # معامل الانبعاث والتشتت (S21 - Transmission)
    S21 = V2_v / (V1_v + 1e-15)
    S21_dB = 20 * np.log10(np.abs(S21) + 1e-15)
    
    # استخراج السعة الطفيلية (Parasitic Equivalent Capacitance) 
    omega = 2.0 * np.pi * f_valid
    Im_Y = np.imag(1.0 / Z_in)
    Capacitance_pF = (Im_Y / omega) * 1e12 # تحويل إلى بيكو فاراد
    
    # الرسم البياني المتقدم (SPICE equivalent modeling graphs)
    plt.figure(figsize=(16, 5))
    
    # المنحنى الزمني الفعلي
    plt.subplot(1, 3, 1)
    time_axis = np.arange(max_steps) * dt * 1e12 # بالبيكو-ثانية
    plt.plot(time_axis, v1, label="Input Pulse (V1)", color='b', alpha=0.8)
    plt.plot(time_axis, v2, label="Transmitted Pulse (V2)", color='r')
    plt.title("الموجات الكهرومغناطيسية الزمنية (Time Domain)", weight='bold')
    plt.xlabel("الزمن الزمن المطلق (picoseconds)")
    plt.ylabel("الجهد المحتث V")
    plt.grid(True, linestyle=':')
    plt.legend()

    # S21 معامل التشتت (حجر الأساس لمهندسي RF)
    plt.subplot(1, 3, 2)
    plt.plot(f_valid / 1e9, S21_dB, color='purple', linewidth=2)
    plt.title("معامل نقل الإشارة S21 (Transmission / Loss)", weight='bold')
    plt.xlabel("التردد (GHz)")
    plt.ylabel("الطاقة المنقولة (dB)")
    plt.grid(True, linestyle=':')
    
    # السعة الطفيلية المكافئة (البيانات الجوهرية لمنتقدي الـ Delay)
    plt.subplot(1, 3, 3)
    # تصفية القيم الشاذة لتنظيف الرسم الرياضي
    C_clean = np.clip(np.abs(Capacitance_pF), 0, np.percentile(np.abs(Capacitance_pF), 95)) if len(Capacitance_pF) > 0 else np.abs(Capacitance_pF)
    plt.plot(f_valid / 1e9, C_clean, color='green', linewidth=2)
    plt.title("السعة المكافئة (Eq. Capacitance)", weight='bold')
    plt.xlabel("التردد (GHz)")
    plt.ylabel("السعة C (بيكو فاراد pF)")
    plt.grid(True, linestyle=':')

    plt.tight_layout()
    output_path = os.path.join(os.path.dirname(__file__), "fdtd_rf_spice_model.png")
    plt.savefig(output_path, dpi=180)
    print(f"\n[نجاح علمي] تم حساب النماذج الراديوية المكافئة بنجاح وحفظ التقرير الهندسي في:\n{os.path.abspath(output_path)}")

if __name__ == "__main__":
    main()
