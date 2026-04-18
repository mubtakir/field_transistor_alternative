"""
3D Electro-Thermal Simulator (Taichi GPU).
Couples Poisson voltage solver with Joule heating and thermal diffusion.

Extracted from: first_principles_sim/taichi_electro_thermal.py + taichi_3d_sim.py

Design Phase: Thermal validation — ensures device doesn't overheat under load.
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


def run_electro_thermal_3d(nx=80, ny=80, nz=80, V_supply=100.0,
                           neck_radius=8.0,
                           poisson_iters=3000, thermal_steps=2000,
                           thermal_dt=0.01, T_ambient=20.0):
    """
    Run a coupled electro-thermal simulation in 3D.
    
    1. Solve Poisson equation for voltage distribution
    2. Compute Joule heating Q = sigma * |grad(V)|^2
    3. Evolve thermal diffusion equation
    
    Parameters
    ----------
    nx, ny, nz : int
        Grid dimensions.
    V_supply : float
        Supply voltage (V).
    neck_radius : float
        Bottleneck radius (grid cells).
    poisson_iters : int
        Iterations for voltage convergence.
    thermal_steps : int
        Number of thermal time steps.
    thermal_dt : float
        Thermal time step.
    T_ambient : float
        Ambient temperature (C).
    
    Returns
    -------
    results : dict
        'V': 3D voltage field,
        'T': 3D temperature field,
        'sigma': 3D conductivity field,
        'T_max': peak temperature,
        'T_hotspot_location': (i,j,k) of hottest point.
    """
    check_taichi()
    ti.init(arch=ti.gpu)
    
    sigma = ti.field(dtype=ti.f32, shape=(nx, ny, nz))
    alpha_t = ti.field(dtype=ti.f32, shape=(nx, ny, nz))
    V = ti.field(dtype=ti.f32, shape=(nx, ny, nz))
    V_new = ti.field(dtype=ti.f32, shape=(nx, ny, nz))
    T = ti.field(dtype=ti.f32, shape=(nx, ny, nz))
    T_new = ti.field(dtype=ti.f32, shape=(nx, ny, nz))
    
    @ti.kernel
    def init_mat():
        for i, j, k in sigma:
            sigma[i, j, k] = 1e-4
            alpha_t[i, j, k] = 1e-4
            V[i, j, k] = 0.0
            T[i, j, k] = T_ambient
        for i, j, k in ti.ndrange((20, 60), (20, 60), (0, nz)):
            sigma[i, j, k] = 1.0
            alpha_t[i, j, k] = 1.0
        center_x, center_y = 40.0, 40.0
        for i, j, k in ti.ndrange((20, 60), (20, 60), (30, 50)):
            dist_sq = (i - center_x)**2 + (j - center_y)**2
            if dist_sq > neck_radius**2:
                sigma[i, j, k] = 1e-4
                alpha_t[i, j, k] = 1e-4
        for i, j in ti.ndrange((20, 60), (20, 60)):
            sigma[i, j, 0] = 1.0
            sigma[i, j, nz-1] = 1.0
    
    @ti.kernel
    def solve_V():
        for i, j, k in ti.ndrange((1, nx-1), (1, ny-1), (1, nz-1)):
            s_xp = 0.5 * (sigma[i, j, k] + sigma[i+1, j, k])
            s_xm = 0.5 * (sigma[i, j, k] + sigma[i-1, j, k])
            s_yp = 0.5 * (sigma[i, j, k] + sigma[i, j+1, k])
            s_ym = 0.5 * (sigma[i, j, k] + sigma[i, j-1, k])
            s_zp = 0.5 * (sigma[i, j, k] + sigma[i, j, k+1])
            s_zm = 0.5 * (sigma[i, j, k] + sigma[i, j, k-1])
            ss = s_xp + s_xm + s_yp + s_ym + s_zp + s_zm
            if ss > 0:
                V_new[i,j,k] = (s_xp*V[i+1,j,k]+s_xm*V[i-1,j,k]+s_yp*V[i,j+1,k]+s_ym*V[i,j-1,k]+s_zp*V[i,j,k+1]+s_zm*V[i,j,k-1]) / ss
            if k == 0: V_new[i,j,k] = 0.0
            if k == nz-1: V_new[i,j,k] = V_supply
        for i, j, k in ti.ndrange((1,nx-1),(1,ny-1),(1,nz-1)):
            V[i,j,k] = V_new[i,j,k]
    
    @ti.kernel
    def update_T(dt_val: ti.f32):
        for i, j, k in ti.ndrange((1,nx-1),(1,ny-1),(1,nz-1)):
            dv_dx = (V[i+1,j,k]-V[i-1,j,k])*0.5
            dv_dy = (V[i,j+1,k]-V[i,j-1,k])*0.5
            dv_dz = (V[i,j,k+1]-V[i,j,k-1])*0.5
            Q = sigma[i,j,k] * (dv_dx**2 + dv_dy**2 + dv_dz**2) * 8.0
            a_xp = 0.5*(alpha_t[i,j,k]+alpha_t[i+1,j,k])
            a_xm = 0.5*(alpha_t[i,j,k]+alpha_t[i-1,j,k])
            a_yp = 0.5*(alpha_t[i,j,k]+alpha_t[i,j+1,k])
            a_ym = 0.5*(alpha_t[i,j,k]+alpha_t[i,j-1,k])
            a_zp = 0.5*(alpha_t[i,j,k]+alpha_t[i,j,k+1])
            a_zm = 0.5*(alpha_t[i,j,k]+alpha_t[i,j,k-1])
            lap = (a_xp*(T[i+1,j,k]-T[i,j,k])-a_xm*(T[i,j,k]-T[i-1,j,k]) +
                   a_yp*(T[i,j+1,k]-T[i,j,k])-a_ym*(T[i,j,k]-T[i,j-1,k]) +
                   a_zp*(T[i,j,k+1]-T[i,j,k])-a_zm*(T[i,j,k]-T[i,j,k-1]))
            T_new[i,j,k] = T[i,j,k] + dt_val*lap + dt_val*Q
            if k == 0 or k == nz-1: T_new[i,j,k] = T_ambient
        for i,j,k in ti.ndrange((1,nx-1),(1,ny-1),(1,nz-1)):
            T[i,j,k] = T_new[i,j,k]
    
    # Run
    init_mat()
    for _ in range(poisson_iters):
        solve_V()
    for _ in range(thermal_steps):
        update_T(thermal_dt)
    
    T_np = T.to_numpy()
    hotspot = np.unravel_index(np.argmax(T_np), T_np.shape)
    
    return {
        'V': V.to_numpy(),
        'T': T_np,
        'sigma': sigma.to_numpy(),
        'T_max': float(np.max(T_np)),
        'T_hotspot_location': hotspot,
    }
