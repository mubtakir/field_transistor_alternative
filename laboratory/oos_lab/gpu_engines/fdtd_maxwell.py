"""
3D FDTD Maxwell Solver (Taichi GPU-Accelerated).
Solves full Maxwell's equations using Yee lattice to extract S-parameters.

Extracted from: first_principles_sim/taichi_fdtd_rf.py

Design Phase: RF/Microwave characterization — use AFTER device geometry is finalized.
"""
import numpy as np

try:
    import taichi as ti
    TAICHI_AVAILABLE = True
except ImportError:
    TAICHI_AVAILABLE = False


def check_taichi():
    if not TAICHI_AVAILABLE:
        raise ImportError(
            "Taichi is required for GPU engines. Install: pip install taichi"
        )


def run_fdtd_maxwell(nx=50, ny=50, nz=80, dx=1e-6,
                     max_steps=30000, device_geometry=None,
                     source_port_z=15, output_port_z=65,
                     device_eps_r=4.0, device_sigma=200.0,
                     neck_radius=5.0):
    """
    Run a 3D FDTD simulation of Maxwell's equations.
    
    Injects a Gaussian pulse and measures S-parameters.
    
    Parameters
    ----------
    nx, ny, nz : int
        Grid dimensions.
    dx : float
        Spatial resolution (meters). Default 1 um.
    max_steps : int
        Number of time steps.
    device_geometry : callable, optional
        Custom geometry function: f(i,j,k) -> (eps_r, sigma_e).
        If None, uses default FTA neck geometry.
    source_port_z : int
        Z-index of input port.
    output_port_z : int
        Z-index of output port.
    device_eps_r : float
        Relative permittivity of device material.
    device_sigma : float
        Conductivity of device material (S/m).
    neck_radius : float
        Radius of the bottleneck region.
    
    Returns
    -------
    results : dict
        'freqs_GHz': frequency array,
        'S21_dB': transmission coefficient,
        'Z_input': input impedance,
        'C_parasitic_pF': equivalent capacitance,
        'v1_time': input port voltage (time domain),
        'v2_time': output port voltage (time domain),
        'time_ps': time axis in picoseconds.
    """
    check_taichi()
    ti.init(arch=ti.gpu)
    
    eps0 = 8.854e-12
    mu0 = 4.0 * np.pi * 1e-7
    dt = 0.9 * dx / (3e8 * np.sqrt(3))
    
    # Fields
    Ex = ti.field(dtype=ti.f32, shape=(nx, ny, nz))
    Ey = ti.field(dtype=ti.f32, shape=(nx, ny, nz))
    Ez = ti.field(dtype=ti.f32, shape=(nx, ny, nz))
    Hx = ti.field(dtype=ti.f32, shape=(nx, ny, nz))
    Hy = ti.field(dtype=ti.f32, shape=(nx, ny, nz))
    Hz = ti.field(dtype=ti.f32, shape=(nx, ny, nz))
    
    eps_r_field = ti.field(dtype=ti.f32, shape=(nx, ny, nz))
    sigma_e = ti.field(dtype=ti.f32, shape=(nx, ny, nz))
    Ceye = ti.field(dtype=ti.f32, shape=(nx, ny, nz))
    Cexh = ti.field(dtype=ti.f32, shape=(nx, ny, nz))
    
    v1_arr = ti.field(dtype=ti.f32, shape=max_steps)
    i1_arr = ti.field(dtype=ti.f32, shape=max_steps)
    v2_arr = ti.field(dtype=ti.f32, shape=max_steps)
    i2_arr = ti.field(dtype=ti.f32, shape=max_steps)
    
    @ti.kernel
    def init_materials():
        center_x, center_y = nx / 2, ny / 2
        for i, j, k in eps_r_field:
            eps_r_field[i, j, k] = 1.0
            sigma_e[i, j, k] = 0.0
        
        for i, j, k in ti.ndrange((10, nx-10), (10, ny-10), (10, nz-10)):
            eps_r_field[i, j, k] = device_eps_r
            sigma_e[i, j, k] = device_sigma
        
        for i, j, k in ti.ndrange((10, nx-10), (10, ny-10), (nz//2-5, nz//2+5)):
            dist_sq = (i - center_x)**2 + (j - center_y)**2
            if dist_sq > neck_radius**2:
                eps_r_field[i, j, k] = 1.0
                sigma_e[i, j, k] = 0.0
        
        for i, j, k in eps_r_field:
            eps = eps_r_field[i, j, k] * eps0
            sig = sigma_e[i, j, k]
            den = 1.0 + (sig * dt) / (2.0 * eps)
            Ceye[i, j, k] = (1.0 - (sig * dt) / (2.0 * eps)) / den
            Cexh[i, j, k] = (dt / eps) / den / dx
    
    @ti.kernel
    def update_H():
        for i, j, k in ti.ndrange((0, nx-1), (0, ny-1), (0, nz-1)):
            Hx[i, j, k] -= (dt / mu0 / dx) * ((Ez[i, j+1, k] - Ez[i, j, k]) - (Ey[i, j, k+1] - Ey[i, j, k]))
            Hy[i, j, k] -= (dt / mu0 / dx) * ((Ex[i, j, k+1] - Ex[i, j, k]) - (Ez[i+1, j, k] - Ez[i, j, k]))
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
        t0 = 100.0 * dt
        spread = 30.0 * dt
        pulse = ti.exp(-((t - t0)**2) / (spread**2))
        port_s, port_e = nx // 2 - 5, nx // 2 + 5
        for i, j in ti.ndrange((port_s, port_e), (port_s, port_e)):
            Ez[i, j, source_port_z] += pulse
    
    @ti.kernel
    def read_ports(step: ti.i32):
        v1_sum, i1_sum = 0.0, 0.0
        v2_sum, i2_sum = 0.0, 0.0
        port_s, port_e = nx // 2 - 5, nx // 2 + 5
        for i, j in ti.ndrange((port_s, port_e), (port_s, port_e)):
            v1_sum += Ez[i, j, source_port_z] * dx
            i1_sum += (Hx[i, j+1, source_port_z] - Hx[i, j, source_port_z] - Hy[i+1, j, source_port_z] + Hy[i, j, source_port_z]) * dx
            v2_sum += Ez[i, j, output_port_z] * dx
            i2_sum += (Hx[i, j+1, output_port_z] - Hx[i, j, output_port_z] - Hy[i+1, j, output_port_z] + Hy[i, j, output_port_z]) * dx
        v1_arr[step] = v1_sum
        i1_arr[step] = i1_sum
        v2_arr[step] = v2_sum
        i2_arr[step] = i2_sum
    
    # Run
    init_materials()
    for step in range(max_steps):
        update_H()
        update_E()
        add_source(step)
        read_ports(step)
    
    # Post-process
    v1 = v1_arr.to_numpy()
    i1 = i1_arr.to_numpy()
    v2 = v2_arr.to_numpy()
    
    V1_f = np.fft.fft(v1)
    I1_f = np.fft.fft(i1)
    V2_f = np.fft.fft(v2)
    freqs = np.fft.fftfreq(max_steps, d=dt)
    
    valid = (freqs > 10e9) & (freqs < 1000e9)
    f_valid = freqs[valid]
    
    Z_in = V1_f[valid] / (I1_f[valid] + 1e-15)
    S21 = V2_f[valid] / (V1_f[valid] + 1e-15)
    S21_dB = 20 * np.log10(np.abs(S21) + 1e-15)
    
    omega = 2.0 * np.pi * f_valid
    Im_Y = np.imag(1.0 / Z_in)
    C_pF = (Im_Y / omega) * 1e12
    
    return {
        'freqs_GHz': f_valid / 1e9,
        'S21_dB': S21_dB,
        'Z_input': Z_in,
        'C_parasitic_pF': C_pF,
        'v1_time': v1,
        'v2_time': v2,
        'time_ps': np.arange(max_steps) * dt * 1e12,
    }
