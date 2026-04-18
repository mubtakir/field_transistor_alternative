import taichi as ti
import numpy as np
import pyvista as pv
import os, time
import sys

# ضمان طباعة الحروف العربية في موجه الأوامر بنجاح
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

ti.init(arch=ti.gpu)

# أبعاد الفضاء ثلاثي الأبعاد (نصف مليون خلية دقيقة)
nx, ny, nz = 80, 80, 80

# الحقول المكانية
sigma = ti.field(dtype=ti.f32, shape=(nx, ny, nz))   # توصيلية المادة
alpha = ti.field(dtype=ti.f32, shape=(nx, ny, nz))   # الانتشار الحراري
V = ti.field(dtype=ti.f32, shape=(nx, ny, nz))       # الجهد (الفولتية)
V_new = ti.field(dtype=ti.f32, shape=(nx, ny, nz))
T = ti.field(dtype=ti.f32, shape=(nx, ny, nz))       # الحرارة
T_new = ti.field(dtype=ti.f32, shape=(nx, ny, nz))

@ti.kernel
def init_materials():
    for i, j, k in sigma:
        # الفضاء العام (عازل وفراغ)
        sigma[i, j, k] = 1e-4
        alpha[i, j, k] = 1e-4
        V[i, j, k] = 0.0
        T[i, j, k] = 20.0

    # 1. نحت العمود الرئيسي للمادة الناقلة في المنتصف
    for i, j, k in ti.ndrange((20, 60), (20, 60), (0, nz)):
        sigma[i, j, k] = 1.0
        alpha[i, j, k] = 1.0

    # 2. نحت "عنق الزجاجة الأسطواني" في منتصف المحور Z
    # سنقوم بمسح المادة من الأطراف لنصنع أسطوانة ضيقة نصف قطرها 8
    center_x, center_y = 40.0, 40.0
    for i, j, k in ti.ndrange((20, 60), (20, 60), (30, 50)):
        dist_sq = (i - center_x)**2 + (j - center_y)**2
        if dist_sq > 8.0**2:  # إزالة أي شيء خارج دائرة نصف قطرها 8
            sigma[i, j, k] = 1e-4
            alpha[i, j, k] = 1e-4

    # 3. الأقطاب الكهربائية (القواعد الكبيرة الثقيلة)
    for i, j in ti.ndrange((20, 60), (20, 60)):
        sigma[i, j, 0] = 1.0
        sigma[i, j, nz-1] = 1.0

@ti.kernel
def solve_voltage():
    for i, j, k in ti.ndrange((1, nx-1), (1, ny-1), (1, nz-1)):
        # التفاعلات الموضعية الفائقة في الـ 3D
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

        # شروط أقطاب البطارية
        if k == 0:
            V_new[i, j, k] = 0.0
        if k == nz-1:
            V_new[i, j, k] = 100.0

    for i, j, k in ti.ndrange((1, nx-1), (1, ny-1), (1, nz-1)):
        V[i, j, k] = V_new[i, j, k]

@ti.kernel
def update_thermal(dt: ti.f32):
    for i, j, k in ti.ndrange((1, nx-1), (1, ny-1), (1, nz-1)):
        # تأثير التسخين عبر 3D
        dv_dx = (V[i+1, j, k] - V[i-1, j, k]) * 0.5
        dv_dy = (V[i, j+1, k] - V[i, j-1, k]) * 0.5
        dv_dz = (V[i, j, k+1] - V[i, j, k-1]) * 0.5
        Q = sigma[i, j, k] * (dv_dx**2 + dv_dy**2 + dv_dz**2) * 8.0 

        # الانتشار الحراري ثلاثي الأبعاد
        a_xp = 0.5 * (alpha[i, j, k] + alpha[i+1, j, k])
        a_xm = 0.5 * (alpha[i, j, k] + alpha[i-1, j, k])
        a_yp = 0.5 * (alpha[i, j, k] + alpha[i, j+1, k])
        a_ym = 0.5 * (alpha[i, j, k] + alpha[i, j-1, k])
        a_zp = 0.5 * (alpha[i, j, k] + alpha[i, j, k+1])
        a_zm = 0.5 * (alpha[i, j, k] + alpha[i, j, k-1])

        laplace_T = (a_xp * (T[i+1, j, k] - T[i, j, k]) - a_xm * (T[i, j, k] - T[i-1, j, k]) +
                     a_yp * (T[i, j+1, k] - T[i, j, k]) - a_ym * (T[i, j, k] - T[i, j-1, k]) +
                     a_zp * (T[i, j, k+1] - T[i, j, k]) - a_zm * (T[i, j, k] - T[i, j, k-1]))

        T_new[i, j, k] = T[i, j, k] + dt * laplace_T + dt * Q

        if k == 0 or k == nz-1:
            T_new[i, j, k] = 20.0

    for i, j, k in ti.ndrange((1, nx-1), (1, ny-1), (1, nz-1)):
        T[i, j, k] = T_new[i, j, k]

def main():
    print("> تهيئة الفضاء ثلاثي الأبعاد والأسطوانة الوسطية...")
    init_materials()

    print("> يتم الآن حل كثافة المجال الكهربائي مكانياً (3D Poisson)...")
    t0 = time.time()
    for _ in range(3000): # 3000 دورة لضبط المجال في نصف مليون نقطة
        solve_voltage()
    print(f"[+] استقر المجال الكهربائي بنجاح في {time.time()-t0:.2f} ثانية!")

    print("> تفريغ طاقة الاحتكاك (تأثير جول) وانتشارها للترموديناميك...")
    t1 = time.time()
    for step in range(2000):
        update_thermal(0.01)
    print(f"[+] اكتملت دورة الحرارة في {time.time()-t1:.2f} ثانية!")

    print("\n> نقل البيانات لمكتبة PyVista وتجهيز المجسم 3D...")
    V_np = V.to_numpy()
    T_np = T.to_numpy()
    sigma_np = sigma.to_numpy()

    # استخدام ImageData للهياكل المنتظمة
    grid = pv.ImageData()
    grid.dimensions = np.array([nx, ny, nz])
    grid.origin = (0, 0, 0)
    grid.spacing = (1, 1, 1)

    grid.point_data["Voltage"] = V_np.flatten(order='F')
    grid.point_data["Temperature"] = T_np.flatten(order='F')
    grid.point_data["Conductivity"] = sigma_np.flatten(order='F')

    # عزل السطح الخارجي للموصل
    conductor = grid.threshold([0.1, 1.0], scalars="Conductivity")

    plotter = pv.Plotter(title="First Principles 3D - Field Transistor Alternative Simulator")
    
    # 1. رسم الغلاف الخارجي للمادة لتوضيح شكل عنق الزجاجة الأسطواني بخفة
    plotter.add_mesh(conductor, color="whitesmoke", opacity=0.15, label="Conductor Space (Shape)")
    
    # 2. أخذ مقاطع عرضية مسطحة لترشيد درجات الحرارة والجهد
    slices = grid.slice_orthogonal(x=40, y=40, z=40)
    plotter.add_mesh(slices, scalars="Temperature", cmap="inferno", opacity=0.95, label="Temperature Cross-section")
    
    plotter.add_axes()
    print("===========================================")
    print("سيتم فتح النافذة التفاعلية المجسمة الآن! (تخيل هذا الترانزستور القادم)")
    print("===========================================")
    plotter.show()

if __name__ == "__main__":
    main()
