import taichi as ti
import numpy as np
import pyvista as pv
import os, time
import sys

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

ti.init(arch=ti.gpu)

nx, ny, nz = 80, 80, 80
num_particles = 25000

sigma = ti.field(dtype=ti.f32, shape=(nx, ny, nz))
V = ti.field(dtype=ti.f32, shape=(nx, ny, nz))
V_new = ti.field(dtype=ti.f32, shape=(nx, ny, nz))
E_field = ti.Vector.field(3, dtype=ti.f32, shape=(nx, ny, nz))

# جسيمات المونتي كارلو / PIC
pos = ti.Vector.field(3, dtype=ti.f32, shape=num_particles)
vel = ti.Vector.field(3, dtype=ti.f32, shape=num_particles)
active = ti.field(dtype=ti.i32, shape=num_particles) # 1 if active, 0 if absorbed/dead

@ti.kernel
def init_materials():
    for i, j, k in sigma:
        sigma[i, j, k] = 1e-4
        V[i, j, k] = k / 79.0 * 20.0
        E_field[i, j, k] = ti.Vector([0.0, 0.0, 0.0])

    for i, j, k in ti.ndrange((20, 60), (20, 60), (0, nz)):
        sigma[i, j, k] = 1.0

    # عنق الزجاجة المعياري (النانوي)
    center_x, center_y = 40.0, 40.0
    for i, j, k in ti.ndrange((20, 60), (20, 60), (35, 45)):
        dist_sq = (i - center_x)**2 + (j - center_y)**2
        if dist_sq > 6.0**2: # Radius 6
            sigma[i, j, k] = 1e-4

    for i, j in ti.ndrange((20, 60), (20, 60)):
        sigma[i, j, 0] = 1.0
        sigma[i, j, nz-1] = 1.0
        V[i, j, 0] = 0.0
        V_new[i, j, 0] = 0.0
        # جهد كافي لجذب الجسيمات
        V[i, j, nz-1] = 100.0
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

    for i, j, k in ti.ndrange((1, nx-1), (1, ny-1), (1, nz-1)):
        V[i, j, k] = V_new[i, j, k]

@ti.kernel
def compute_e_field():
    for i, j, k in ti.ndrange((1, nx-1), (1, ny-1), (1, nz-1)):
        # E = - grad V
        ex = -(V[i+1, j, k] - V[i-1, j, k]) * 0.5
        ey = -(V[i, j+1, k] - V[i, j-1, k]) * 0.5
        ez = -(V[i, j, k+1] - V[i, j, k-1]) * 0.5
        E_field[i, j, k] = ti.Vector([ex, ey, ez])

@ti.kernel
def init_particles():
    for p in pos:
        # توليد إلكترونات عشوائية داخل المادة وتحت العنق مباشرة (Source side)
        x = ti.random() * 40.0 + 20.0
        y = ti.random() * 40.0 + 20.0
        z = ti.random() * 20.0 + 5.0 # من الأسفل قبل العنق
        
        # التأكد أنها داخل المادة
        if sigma[int(x), int(y), int(z)] > 0.5:
            pos[p] = ti.Vector([x, y, z])
            vel[p] = ti.Vector([0.0, 0.0, 0.0])
            active[p] = 1
        else:
            active[p] = 0

@ti.kernel
def update_particles(dt: ti.f32):
    for p in pos:
        if active[p] == 1:
            p_pos = pos[p]
            ix, iy, iz = int(p_pos[0]), int(p_pos[1]), int(p_pos[2])
            
            # إذا خرج عن النطاق
            if ix < 1 or ix >= nx-1 or iy < 1 or iy >= ny-1 or iz < 1 or iz >= nz-1:
                active[p] = 0
                continue
                
            # جلب المجال الكهربائي في موقع الإلكترون المحاذي للشبكة
            E = E_field[ix, iy, iz]
            
            # تسريع الإلكترون (F = qE)
            # الإلكترون سالب فينجذب عكس المجال (نحو 100V في الأعلى)
            # بما أن V يزيد لأعلى، فـ E_z سالب. تسريع الالكترون موجب ليرتفع
            acceleration = E * -5.0  # المعامل قوة التسارع المعاكس (شحنة سالبة)
            
            # إضافة ارتعاش حراري عشوائي للاصطدامات الحرارية (Thermal Jitter / Brownian motion)
            jitter = ti.Vector([ti.random()-0.5, ti.random()-0.5, ti.random()-0.5]) * 10.0
            
            # تحديث السرعة مع معامل احتكاك للمادة (Drift velocity limits)
            vel[p] = vel[p] * 0.85 + acceleration * dt + jitter * dt
            
            # تحديث الموقع
            new_pos = pos[p] + vel[p] * dt
            nix, niy, niz = int(new_pos[0]), int(new_pos[1]), int(new_pos[2])
            
            # التصادم مع جدران العازل المادي والارتداد
            if 0 < nix < nx and 0 < niy < ny and 0 < niz < nz:
                if sigma[nix, niy, niz] < 0.5:
                    new_pos = pos[p] # إلغاء الحركة (توقف في المكان)
                    vel[p] = vel[p] * -0.5 # الارتداد الخلفي للاصطدام بالجدار الهندسي
            else:
                active[p] = 0 # امتصاص أو خروج من الشبكة
                
            pos[p] = new_pos

def main():
    print("="*60)
    print("بدء محاكاة النانو والجسيمات المشحونة (Particle-in-Cell)...")
    print("="*60)

    init_materials()
    
    print("[1] موازنة الجهد الكهربائي لاستخراج تضاريس الحقول المكانية...")
    t0 = time.time()
    for _ in range(5000):
        solve_voltage()
    print(f"تم حل المجال الكهربائي في {time.time()-t0:.2f} ثانية")
    
    compute_e_field()
    init_particles()

    print("[2] تشغيل ديناميكا الجسيمات (Monte Carlo)... إطلاق 25 ألف إلكترون!")
    t1 = time.time()
    # المحاكاة لـ 150 لقطة زمنية لنسرع وقت التشغيل وتصل الجسيمات للعنق
    for step in range(150): 
        update_particles(0.1)
    print(f"تمت محاكاة حشود الإلكترونات في {time.time()-t1:.2f} ثانية")
        
    print("[3] جمع إحداثيات الإلكترونات الناجية والمحشورة في العنق...")
    pos_np = pos.to_numpy()
    active_np = active.to_numpy()
    
    # اختيار الجسيمات النشطة فقط
    valid_positions = pos_np[active_np == 1]
    print(f"العدد الفعلي للجسيمات المرصودة: {len(valid_positions)} من أصل {num_particles}")

    print("[4] نقل الفضاء لبيئة PyVista وعرض العنق النانوي وسحابة الإلكترونات...")
    sigma_np = sigma.to_numpy()

    grid = pv.ImageData()
    grid.dimensions = np.array([nx, ny, nz])
    grid.origin = (0, 0, 0)
    grid.spacing = (1, 1, 1)

    grid.point_data["Conductivity"] = sigma_np.flatten(order='F')
    conductor = grid.threshold([0.1, 1.0], scalars="Conductivity")

    plotter = pv.Plotter(title="Particle-In-Cell (PIC) Nano Simulation - FTA")
    
    # الهيكل الأصلي بشكل شبكي لكي نرى الإلكترونات بالداخل!
    plotter.add_mesh(conductor, style="wireframe", color="white", opacity=0.08, label="Conduction Channel")
    
    # عرض الإلكترونات
    if len(valid_positions) > 0:
        particles_mesh = pv.PolyData(valid_positions)
        # تلوين الإلكترونات حسب المسار العامودي لها Z
        z_coords = valid_positions[:, 2]
        particles_mesh["Z_Position"] = z_coords
        
        # كرات صغيرة تمثل الإلكترونات المتكاثرة عند خانق الترانزستور!
        plotter.add_mesh(particles_mesh, render_points_as_spheres=True, point_size=6, cmap="turbo", scalars="Z_Position", label="Electrons Flow")
    
    plotter.add_axes()
    print("=====================================================")
    print("شاهد بعينك (زحمة الإلكترونات وهي تحاول عبور العنق)! النافذة التفاعلية تفتح الآن...")
    print("=====================================================")
    plotter.show()

if __name__ == "__main__":
    main()
