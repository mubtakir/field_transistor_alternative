import taichi as ti
import numpy as np
import pyvista as pv
import os, time
import sys

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

ti.init(arch=ti.gpu)

nx, ny, nz = 80, 80, 80

sigma = ti.field(dtype=ti.f32, shape=(nx, ny, nz))
alpha = ti.field(dtype=ti.f32, shape=(nx, ny, nz))
V = ti.field(dtype=ti.f32, shape=(nx, ny, nz))
V_new = ti.field(dtype=ti.f32, shape=(nx, ny, nz))
T = ti.field(dtype=ti.f32, shape=(nx, ny, nz))
T_new = ti.field(dtype=ti.f32, shape=(nx, ny, nz))

# Material properties for typical Copper
E_young = 110e9 # 110 GPa 
alpha_T = 1.7e-5 # 17 * 10^-6 / K

stress = ti.field(dtype=ti.f32, shape=(nx, ny, nz))
strain = ti.field(dtype=ti.f32, shape=(nx, ny, nz))

@ti.kernel
def init_materials():
    for i, j, k in sigma:
        sigma[i, j, k] = 1e-4
        alpha[i, j, k] = 1e-4
        V[i, j, k] = k / 79.0 * 20.0 # 20 Volt initial gradient
        T[i, j, k] = 20.0

    for i, j, k in ti.ndrange((20, 60), (20, 60), (0, nz)):
        sigma[i, j, k] = 1.0
        alpha[i, j, k] = 1.0

    # Bottleneck 
    center_x, center_y = 40.0, 40.0
    for i, j, k in ti.ndrange((20, 60), (20, 60), (30, 50)):
        dist_sq = (i - center_x)**2 + (j - center_y)**2
        if dist_sq > 6.0**2: # radius 6
            sigma[i, j, k] = 1e-4
            alpha[i, j, k] = 1e-4

    for i, j in ti.ndrange((20, 60), (20, 60)):
        sigma[i, j, 0] = 1.0
        sigma[i, j, nz-1] = 1.0
        V[i, j, 0] = 0.0
        V_new[i, j, 0] = 0.0
        V[i, j, nz-1] = 20.0 
        V_new[i, j, nz-1] = 20.0

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

    for i, j, k in ti.ndrange((1, nx-1), (1, ny-1), (1, nz-1)):
        V[i, j, k] = V_new[i, j, k]

@ti.kernel
def update_thermal(dt: ti.f32):
    for i, j, k in ti.ndrange((1, nx-1), (1, ny-1), (1, nz-1)):
        dv_dx = (V[i+1, j, k] - V[i-1, j, k]) * 0.5
        dv_dy = (V[i, j+1, k] - V[i, j-1, k]) * 0.5
        dv_dz = (V[i, j, k+1] - V[i, j, k-1]) * 0.5
        Q = sigma[i, j, k] * (dv_dx**2 + dv_dy**2 + dv_dz**2) * 5.0 

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

@ti.kernel
def compute_mechanics():
    for i, j, k in ti.ndrange((0, nx), (0, ny), (0, nz)):
        if sigma[i, j, k] > 0.5:
            delta_T = T[i, j, k] - 20.0
            local_strain = alpha_T * delta_T
            strain[i, j, k] = local_strain
            # 1e6 لتحويل الباسكال إلى ميجاباسكال
            stress[i, j, k] = (E_young * local_strain) / 1e6

def main():
    print("="*60)
    print("بدء محاكاة المتانة الميكانيكية والحرارية (Thermo-Mechanical FTA)...")
    print("="*60)

    init_materials()
    print("[1] موازنة الجهد الكهربائي لاستخراج البؤرة الحرارية...")
    for _ in range(4000):
        solve_voltage()

    print("[2] تشغيل الترموديناميك لحساب التشتت الحراري الفعلي...")
    for _ in range(2000):
        update_thermal(0.01)

    print("[3] حساب الإجهادات والانفعالات الفيزيائية الناتجة...")
    compute_mechanics()

    print("[4] نقل المجسم لبيئة PyVista وعكس الإزاحة الفعلية (Displacement Warp)...")
    
    stress_np = stress.to_numpy()
    strain_np = strain.to_numpy()
    sigma_np = sigma.to_numpy()

    grid = pv.ImageData()
    grid.dimensions = np.array([nx, ny, nz])
    grid.origin = (0, 0, 0)
    grid.spacing = (1, 1, 1)

    grid.point_data["Conductivity"] = sigma_np.flatten(order='F')
    grid.point_data["Thermal_Stress_MPa"] = stress_np.flatten(order='F')
    
    x_pts, y_pts, z_pts = grid.points.T
    cx, cy, cz = nx/2.0, ny/2.0, nz/2.0
    
    # تحويل الانفعال (Strain) إلى تمدد قطري (Radial Expansion)
    strain_flat = strain_np.flatten(order='F')
    r_displ_x = strain_flat * (x_pts - cx)
    r_displ_y = strain_flat * (y_pts - cy)
    r_displ_z = strain_flat * (z_pts - cz) * 0.2  # تمدد أقل عمودياً
    
    grid.point_data["Radial_Expansion"] = np.column_stack((r_displ_x, r_displ_y, r_displ_z))

    conductor = grid.threshold([0.1, 1.0], scalars="Conductivity")
    
    # مضاعفة الازاحة هندسيا لرؤيتها
    warped_mesh = conductor.warp_by_vector(vectors="Radial_Expansion", factor=1500.0)

    plotter = pv.Plotter(title="Thermo-Mechanical Exaggerated Deformation (Stress Analysis)")
    
    # الهيكل الأصلي بشكل شبكي
    plotter.add_mesh(conductor, style="wireframe", color="white", opacity=0.08, label="Original Form (Zero Strain)")
    
    max_stress = np.percentile(stress_np, 99)
    print(f"أقصى إجهاد حراري تم رصده في المركز: {max_stress:.1f} MPa")
    plotter.add_mesh(warped_mesh, scalars="Thermal_Stress_MPa", cmap="jet", opacity=1.0, clim=[0, min(max_stress, 300)], label="Deformed Bulge (Stress MPa)")
    
    plotter.add_axes()
    print("=====================================================")
    print("شاهد بعينك (الانتفاخ الفيزيائي)! النافذة التفاعلية تفتح الآن...")
    print("=====================================================")
    plotter.show()

if __name__ == "__main__":
    main()
