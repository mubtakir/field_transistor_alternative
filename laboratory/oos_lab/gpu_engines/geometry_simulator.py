import taichi as ti
import numpy as np
import matplotlib.pyplot as plt
import os
import time
import sys

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

ti.init(arch=ti.gpu)

nx, ny, nz = 80, 80, 80

sigma = ti.field(dtype=ti.f32, shape=(nx, ny, nz))
V = ti.field(dtype=ti.f32, shape=(nx, ny, nz))
V_new = ti.field(dtype=ti.f32, shape=(nx, ny, nz))

# المعامل المداري (نصف قطر العنق الذي يتحكم به الترانزستور)
current_radius = ti.field(dtype=ti.f32, shape=())

@ti.kernel
def init_materials():
    for i, j, k in sigma:
        # الوضع الافتراضي: فضاء عازل
        sigma[i, j, k] = 1e-4
        V[i, j, k] = 0.0

    # توصيل القواعد العلوية والسفلية لبناء العمود
    for i, j, k in ti.ndrange((20, 60), (20, 60), (0, nz)):
        sigma[i, j, k] = 1.0

    # تفريغ المسار الأوسط ليخضع لنصف قطر العنق المتغير
    center_x, center_y = 40.0, 40.0
    r = current_radius[None]
    for i, j, k in ti.ndrange((20, 60), (20, 60), (30, 50)):
        dist_sq = (i - center_x)**2 + (j - center_y)**2
        if dist_sq > r**2:
            sigma[i, j, k] = 1e-4

    # الأقطاب المرجعية (Source & Drain)
    for i, j in ti.ndrange((20, 60), (20, 60)):
        sigma[i, j, 0] = 1.0
        sigma[i, j, nz-1] = 1.0
        
        # تعيين الجهد المصدري هنا لكي يبقى ثابتاً (Dirichlet Boundary Conditions)
        V[i, j, 0] = 0.0
        V[i, j, nz-1] = 100.0
        V_new[i, j, 0] = 0.0
        V_new[i, j, nz-1] = 100.0

@ti.kernel
def solve_voltage():
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

        # المصدر والمصرف ثابتين مكانياً ولا يتم تغييرهم داخل حلقة التكرار

    for i, j, k in ti.ndrange((1, nx-1), (1, ny-1), (1, nz-1)):
        V[i, j, k] = V_new[i, j, k]

@ti.kernel
def compute_current() -> ti.f32:
    total_current = 0.0
    k_mid = nz // 2
    for i, j in ti.ndrange((1, nx-1), (1, ny-1)):
        # التيار = التوصيلية الموضعية * الانحدار الكهربائي
        # ناخذ القيمة المطلقة لانحدار الجهد للتبسيط والتعبير عن التدفق
        dv_dz = (V[i, j, k_mid+1] - V[i, j, k_mid-1]) * 0.5
        J_z = sigma[i, j, k_mid] * dv_dz
        total_current += J_z
    return total_current

def main():
    # قيم التوسعة الجيومترية (من عنق ضيق جداً إلى مفتوح بالكامل)
    radii = [2.0, 4.0, 6.0, 8.0, 10.0, 12.0, 14.0, 16.0, 18.0, 20.0]
    currents = []

    print("="*60)
    print("بدء محاكاة خصائص (Geometry-to-Current) لابتكار FTA...")
    print("="*60)
    
    t_start = time.time()
    
    for r in radii:
        current_radius[None] = r
        init_materials()
        
        # تركيز المجال الكهربائي حتى الاستقرار (3000 دورة كافية جداً)
        for _ in range(3000):
            solve_voltage()
            
        I = compute_current()
        currents.append(I)
        print(f"[>] فتحة العنق المكانية (Radius): {r:4.1f} | التيار الصافي: {I:8.2f} A")

    print(f"\nتمت المحاكاة الكاملة لعشرة ترانزستورات بأشكال مختلفة في {time.time()-t_start:.2f} ثانية!")

    # رسم الأسطورة! (منحنى الخصائص)
    plt.figure(figsize=(10, 6))
    
    # تحويل البيانات إلى مصفوفات لسهولة التعامل
    r_arr = np.array(radii)
    i_arr = np.array(currents)
    
    plt.plot(r_arr, i_arr, 'o-', color='#e74c3c', linewidth=2.5, markersize=8, label="Simulated Curve")
    
    # منحنى تربيعي كمرجع مثالي (لأن المساحة تتناسب مع مربع نصف القطر)
    max_i = max(currents)
    ideal_quadratic = max_i * (r_arr / max(r_arr))**2
    plt.plot(r_arr, ideal_quadratic, '--', color='#7f8c8d', alpha=0.7, label="Ideal Area Relation (r^2)")

    plt.title("خصائص ترانزستور الحقل البديل (FTA) - التحكم بالتيار عبر شكل العائق", fontsize=14, fontweight='bold')
    plt.xlabel("المقدار الهندسي (Radius of Constriction)", fontsize=12)
    plt.ylabel("التيار الكلي المار (Total Current)", fontsize=12)
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.legend()
    
    plt.fill_between(r_arr, i_arr, alpha=0.1, color='#e74c3c')
    
    output_path = os.path.join(os.path.dirname(__file__), "fta_characteristics.png")
    plt.savefig(output_path, dpi=150)
    print(f"تم حفظ منحنيات الإثبات الوظيفي بنجاح في:\n{os.path.abspath(output_path)}")

if __name__ == "__main__":
    main()
