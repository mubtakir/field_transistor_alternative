"""
3D Maxwell FDTD Solver (Taichi GPU).
Solves full Maxwell's equations for RF characterization.
"""

import numpy as np
from ..constants import mu_0, eps_0, c_0

try:
    import taichi as ti
    TAICHI_AVAILABLE = True
except ImportError:
    TAICHI_AVAILABLE = False

def run_fdtd_maxwell(nx=50, ny=50, nz=80, dx=1e-6, max_steps=10000, 
                     device_eps_r=4.0, device_sigma=200.0, neck_radius=5.0):
    """
    Run 3D FDTD Maxwell simulation.
    """
    if not TAICHI_AVAILABLE:
        raise ImportError("Taichi required for Maxwell FDTD.")
        
    ti.init(arch=ti.gpu, log_level=ti.ERROR)
    
    dt = 0.9 * dx / (c_0 * np.sqrt(3))
    
    # Fields
    Ex = ti.field(dtype=ti.f32, shape=(nx, ny, nz))
    Ey = ti.field(dtype=ti.f32, shape=(nx, ny, nz))
    Ez = ti.field(dtype=ti.f32, shape=(nx, ny, nz))
    Hx = ti.field(dtype=ti.f32, shape=(nx, ny, nz))
    Hy = ti.field(dtype=ti.f32, shape=(nx, ny, nz))
    Hz = ti.field(dtype=ti.f32, shape=(nx, ny, nz))
    
    Ceye = ti.field(dtype=ti.f32, shape=(nx, ny, nz))
    Cexh = ti.field(dtype=ti.f32, shape=(nx, ny, nz))
    
    v1_arr = ti.field(dtype=ti.f32, shape=max_steps)
    v2_arr = ti.field(dtype=ti.f32, shape=max_steps)
    
    @ti.kernel
    def init_materials():
        center_x, center_y = nx / 2, ny / 2
        for i, j, k in Ceye:
            # Vacuum default
            eps = eps_0
            sig = 0.0
            
            # Device region
            if 10 <= i < nx-10 and 10 <= j < ny-10 and 10 <= k < nz-10:
                is_gap = False
                if nz//2-5 <= k < nz//2+5:
                    dist_sq = (i - center_x)**2 + (j - center_y)**2
                    if dist_sq > neck_radius**2:
                        is_gap = True
                
                if not is_gap:
                    eps = device_eps_r * eps_0
                    sig = device_sigma
            
            den = 1.0 + (sig * dt) / (2.0 * eps)
            Ceye[i, j, k] = (1.0 - (sig * dt) / (2.0 * eps)) / den
            Cexh[i, j, k] = (dt / eps) / den / dx

    @ti.kernel
    def update_H():
        for i, j, k in ti.ndrange((0, nx-1), (0, ny-1), (0, nz-1)):
            Hx[i, j, k] -= (dt / mu_0 / dx) * ((Ez[i, j+1, k] - Ez[i, j, k]) - (Ey[i, j, k+1] - Ey[i, j, k]))
            Hy[i, j, k] -= (dt / mu_0 / dx) * ((Ex[i, j, k+1] - Ex[i, j, k]) - (Ez[i+1, j, k] - Ez[i, j, k]))
            Hz[i, j, k] -= (dt / mu0 / dx) * ((Ey[i+1, j, k] - Ey[i, j, k]) - (Ex[i, j+1, k] - Ex[i, j, k]))
            
    @ti.kernel
    def update_E():
        for i, j, k in ti.ndrange((1, nx), (1, ny), (1, nz)):
            Ex[i, j, k] = Ceye[i, j, k] * Ex[i, j, k] + Cexh[i, j, k] * ((Hz[i, j, k] - Hz[i, j-1, k]) - (Hy[i, j, k] - Hy[i, j, k-1]))
            Ey[i, j, k] = Ceye[i, j, k] * Ey[i, j, k] + Cexh[i, j, k] * ((Hx[i, j, k] - Hx[i, j, k-1]) - (Hz[i, j, k] - Hz[i-1, j, k]))
            Ez[i, j, k] = Ceye[i, j, k] * Ez[i, j, k] + Cexh[i, j, k] * ((Hy[i, j, k] - Hy[i-1, j, k]) - (Hx[i, j, k] - Hx[i, j-1, k]))

    @ti.kernel
    def add_source(step: ti.i32):
        t = float(step) * dt
        pulse = ti.exp(-((t - 100*dt)**2) / ((30*dt)**2))
        for i, j in ti.ndrange((nx//2-5, nx//2+5), (ny//2-5, ny//2+5)):
            Ez[i, j, 15] += pulse
            
    @ti.kernel
    def read_ports(step: ti.i32):
        v1, v2 = 0.0, 0.0
        for i, j in ti.ndrange((nx//2-5, nx//2+5), (ny//2-5, ny//2+5)):
            v1 += Ez[i, j, 15] * dx
            v2 += Ez[i, j, 65] * dx
        v1_arr[step] = v1
        v2_arr[step] = v2

    init_materials()
    for s in range(max_steps):
        update_H()
        update_E()
        add_source(s)
        read_ports(s)
        
    return {
        'v1': v1_arr.to_numpy(),
        'v2': v2_arr.to_numpy(),
        'dt': dt
    }
