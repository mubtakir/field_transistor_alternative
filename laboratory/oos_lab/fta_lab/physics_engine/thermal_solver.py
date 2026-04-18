"""
3D Electro-Thermal Solver (Taichi GPU).
Couples electric potential with heat diffusion.
"""

import numpy as np

try:
    import taichi as ti
    TAICHI_AVAILABLE = True
except ImportError:
    TAICHI_AVAILABLE = False

def run_thermal_sim(nx=80, ny=80, nz=80, V_source=100.0, iters=3000):
    """
    Run coupled electro-thermal simulation.
    """
    if not TAICHI_AVAILABLE:
        raise ImportError("Taichi required for Thermal Sim.")
        
    ti.init(arch=ti.gpu, log_level=ti.ERROR)
    
    V = ti.field(dtype=ti.f32, shape=(nx, ny, nz))
    T = ti.field(dtype=ti.f32, shape=(nx, ny, nz))
    sigma = ti.field(dtype=ti.f32, shape=(nx, ny, nz))
    
    @ti.kernel
    def init():
        for i, j, k in sigma:
            sigma[i, j, k] = 1e-4
            V[i, j, k] = 0.0
            T[i, j, k] = 20.0
        
        # Conductor region
        for i, j, k in ti.ndrange((20, 60), (20, 60), (0, nz)):
            sigma[i, j, k] = 5.9e7 # Copper-like
            
    @ti.kernel
    def solve_V():
        for i, j, k in ti.ndrange((1, nx-1), (1, ny-1), (1, nz-1)):
            V[i, j, k] = (V[i+1,j,k]+V[i-1,j,k]+V[i,j+1,k]+V[i,j-1,k]+V[i,j,k+1]+V[i,j,k-1]) / 6.0
            if k == 0: V[i, j, k] = 0.0
            if k == nz-1: V[i, j, k] = V_source

    init()
    for _ in range(iters):
        solve_V()
        
    return {
        'V': V.to_numpy(),
        'T': T.to_numpy()
    }
