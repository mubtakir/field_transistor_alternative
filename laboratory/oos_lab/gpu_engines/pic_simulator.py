"""
Particle-In-Cell (PIC) Electron Transport Simulator (Taichi GPU).
Monte Carlo electron dynamics through nano-scale conductive channels.

Extracted from: first_principles_sim/taichi_pic_simulator.py

Design Phase: Post-geometry — validates current flow and bottleneck effects.
"""
import numpy as np

try:
    import taichi as ti
    TAICHI_AVAILABLE = True
except ImportError:
    TAICHI_AVAILABLE = False


def check_taichi():
    if not TAICHI_AVAILABLE:
        raise ImportError("Taichi required. Install: pip install taichi")


def run_pic_simulation(nx=80, ny=80, nz=80, num_particles=25000,
                       V_drain=100.0, neck_radius=6.0,
                       poisson_iters=5000, pic_steps=150,
                       pic_dt=0.1):
    """
    Simulate electron transport through a nano-channel using PIC method.
    
    Parameters
    ----------
    nx, ny, nz : int
        Grid dimensions.
    num_particles : int
        Number of electrons to simulate.
    V_drain : float
        Drain voltage (V).
    neck_radius : float
        Bottleneck radius (grid cells).
    poisson_iters : int
        Iterations for Poisson solver convergence.
    pic_steps : int
        Number of particle dynamics time steps.
    pic_dt : float
        Time step for particle updates.
    
    Returns
    -------
    results : dict
        'positions': (N,3) array of active electron positions,
        'n_active': number of surviving electrons,
        'n_total': total initial electrons,
        'transmission_ratio': fraction that passed the neck,
        'V_field': 3D voltage array,
        'sigma': 3D conductivity array.
    """
    check_taichi()
    ti.init(arch=ti.gpu)
    
    sigma = ti.field(dtype=ti.f32, shape=(nx, ny, nz))
    V = ti.field(dtype=ti.f32, shape=(nx, ny, nz))
    V_new = ti.field(dtype=ti.f32, shape=(nx, ny, nz))
    E_field = ti.Vector.field(3, dtype=ti.f32, shape=(nx, ny, nz))
    
    pos = ti.Vector.field(3, dtype=ti.f32, shape=num_particles)
    vel = ti.Vector.field(3, dtype=ti.f32, shape=num_particles)
    active = ti.field(dtype=ti.i32, shape=num_particles)
    
    @ti.kernel
    def init_materials():
        for i, j, k in sigma:
            sigma[i, j, k] = 1e-4
            V[i, j, k] = k / float(nz - 1) * V_drain
            E_field[i, j, k] = ti.Vector([0.0, 0.0, 0.0])
        
        for i, j, k in ti.ndrange((20, 60), (20, 60), (0, nz)):
            sigma[i, j, k] = 1.0
        
        center_x, center_y = 40.0, 40.0
        for i, j, k in ti.ndrange((20, 60), (20, 60), (35, 45)):
            dist_sq = (i - center_x)**2 + (j - center_y)**2
            if dist_sq > neck_radius**2:
                sigma[i, j, k] = 1e-4
        
        for i, j in ti.ndrange((20, 60), (20, 60)):
            sigma[i, j, 0] = 1.0
            sigma[i, j, nz - 1] = 1.0
            V[i, j, 0] = 0.0
            V_new[i, j, 0] = 0.0
            V[i, j, nz - 1] = V_drain
            V_new[i, j, nz - 1] = V_drain
    
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
        for i, j, k in ti.ndrange((1, nx-1), (1, ny-1), (1, nz-1)):
            V[i, j, k] = V_new[i, j, k]
    
    @ti.kernel
    def compute_e_field():
        for i, j, k in ti.ndrange((1, nx-1), (1, ny-1), (1, nz-1)):
            ex = -(V[i+1, j, k] - V[i-1, j, k]) * 0.5
            ey = -(V[i, j+1, k] - V[i, j-1, k]) * 0.5
            ez = -(V[i, j, k+1] - V[i, j, k-1]) * 0.5
            E_field[i, j, k] = ti.Vector([ex, ey, ez])
    
    @ti.kernel
    def init_particles():
        for p in pos:
            x = ti.random() * 40.0 + 20.0
            y = ti.random() * 40.0 + 20.0
            z = ti.random() * 20.0 + 5.0
            if sigma[int(x), int(y), int(z)] > 0.5:
                pos[p] = ti.Vector([x, y, z])
                vel[p] = ti.Vector([0.0, 0.0, 0.0])
                active[p] = 1
            else:
                active[p] = 0
    
    @ti.kernel
    def update_particles(dt_val: ti.f32):
        for p in pos:
            if active[p] == 1:
                p_pos = pos[p]
                ix, iy, iz = int(p_pos[0]), int(p_pos[1]), int(p_pos[2])
                if ix < 1 or ix >= nx-1 or iy < 1 or iy >= ny-1 or iz < 1 or iz >= nz-1:
                    active[p] = 0
                    continue
                E = E_field[ix, iy, iz]
                acceleration = E * -5.0
                jitter = ti.Vector([ti.random()-0.5, ti.random()-0.5, ti.random()-0.5]) * 10.0
                vel[p] = vel[p] * 0.85 + acceleration * dt_val + jitter * dt_val
                new_pos = pos[p] + vel[p] * dt_val
                nix, niy, niz = int(new_pos[0]), int(new_pos[1]), int(new_pos[2])
                if 0 < nix < nx and 0 < niy < ny and 0 < niz < nz:
                    if sigma[nix, niy, niz] < 0.5:
                        new_pos = pos[p]
                        vel[p] = vel[p] * -0.5
                else:
                    active[p] = 0
                pos[p] = new_pos
    
    # Run simulation
    init_materials()
    for _ in range(poisson_iters):
        solve_voltage()
    compute_e_field()
    init_particles()
    for _ in range(pic_steps):
        update_particles(pic_dt)
    
    # Collect results
    pos_np = pos.to_numpy()
    active_np = active.to_numpy()
    valid = pos_np[active_np == 1]
    
    # Count electrons that crossed the neck (z > 45)
    n_passed = np.sum(valid[:, 2] > 45) if len(valid) > 0 else 0
    
    return {
        'positions': valid,
        'n_active': len(valid),
        'n_total': num_particles,
        'n_passed_neck': n_passed,
        'transmission_ratio': n_passed / max(len(valid), 1),
        'V_field': V.to_numpy(),
        'sigma': sigma.to_numpy(),
    }
