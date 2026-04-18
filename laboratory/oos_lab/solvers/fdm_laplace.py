"""
FDM Laplace/Poisson Solver for multi-plate capacitor systems.
Extracted from FTA Phase 1-6 validated simulation scripts.
"""
import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla
from ..constants import eps_0


def solve_capacitance_matrix(nx=120, ny=100, plate_x_cells=None,
                             plate_y_range=(20, 80), eps_r=4.0,
                             plate_depth=0.01, dx=1e-9):
    """
    Solve 2D Laplace equation on a grid to extract the full
    capacitance matrix for a multi-plate system.
    
    Parameters
    ----------
    nx, ny : int
        Grid dimensions.
    plate_x_cells : list of int
        X-positions of each plate on the grid.
    plate_y_range : tuple
        (y_start, y_end) for plate extent in Y.
    eps_r : float
        Relative permittivity of dielectric.
    plate_depth : float
        Depth of plates (meters) for 3D capacitance.
    dx : float
        Grid spacing (meters).
    
    Returns
    -------
    C_matrix : ndarray (n_plates x n_plates)
        Capacitance matrix in Farads.
    dist_matrix : ndarray (n_plates x n_plates)
        Distance matrix between plates (meters).
    """
    if plate_x_cells is None:
        plate_x_cells = [10, 15, 20, 50, 80, 95]
    
    n_plates = len(plate_x_cells)
    N = nx * ny
    
    # Build Laplacian
    L = sp.lil_matrix((N, N))
    def idx(i, j):
        return i + j * nx
    
    for j in range(ny):
        for i in range(nx):
            k = idx(i, j)
            L[k, k] = 4
            if i > 0:    L[k, idx(i-1, j)] = -1
            if i < nx-1: L[k, idx(i+1, j)] = -1
            if j > 0:    L[k, idx(i, j-1)] = -1
            if j < ny-1: L[k, idx(i, j+1)] = -1
    L = L.tocsr()
    
    # Define plates
    y_s, y_e = plate_y_range
    plates = [[idx(x, j) for j in range(y_s, y_e)] for x in plate_x_cells]
    all_plate_nodes = set(n for p in plates for n in p)
    
    # Boundary nodes
    boundary = set()
    for i in range(nx):
        boundary.add(idx(i, 0)); boundary.add(idx(i, ny-1))
    for j in range(ny):
        boundary.add(idx(0, j)); boundary.add(idx(nx-1, j))
    
    fixed = all_plate_nodes.union(boundary)
    free = np.array([i for i in range(N) if i not in fixed])
    L_FF = L[free, :][:, free]
    
    # Solve for each plate at unit potential
    C_matrix = np.zeros((n_plates, n_plates))
    for j in range(n_plates):
        V_fixed = np.zeros(N)
        for n in plates[j]:
            V_fixed[n] = 1.0
        b = -(L * V_fixed)[free]
        V_F = spla.spsolve(L_FF, b)
        V_full = V_fixed.copy()
        V_full[free] = V_F
        Q_full = L * V_full
        for i in range(n_plates):
            C_matrix[i, j] = sum(Q_full[n] for n in plates[i]) * eps_0 * eps_r * plate_depth
    
    # Distance matrix
    dist_matrix = np.zeros((n_plates, n_plates))
    for i in range(n_plates):
        for j in range(n_plates):
            dist_matrix[i, j] = abs(plate_x_cells[i] - plate_x_cells[j]) * dx
    
    return C_matrix, dist_matrix


def compute_shielding_factor(V_full, plate_x_cells, dx, nx, ny):
    """
    Compute the Shielding Factor (S) as requested by the expert.
    S = E_at_collector_with_gate / E_at_collector_without_gate
    
    A value < 0.01 indicates > 99% shielding effectiveness.
    """
    # E_shielded: Gradient at collector x-position when gate is at fixed potential
    collector_x = plate_x_cells[-1]
    gate_x = plate_x_cells[1]
    
    def get_ex(x_idx):
        # Average Ex across the y-range of interest (plate height)
        y_mid = ny // 2
        # Simple finite difference
        return (V_full[x_idx + 1 + y_mid * nx] - V_full[x_idx - 1 + y_mid * nx]) / (2 * dx)

    E_shielded = abs(get_ex(collector_x))
    
    # E_unprotected: Simple linear field approximation (V_source / d_total)
    # in an open system with same geometry but no gate blocking.
    source_x = plate_x_cells[0]
    V_source = V_full[source_x + (ny // 2) * nx]
    d_total = (collector_x - source_x) * dx
    E_unprotected = V_source / d_total if d_total > 0 else 1e-6
    
    return E_shielded / max(1e-12, E_unprotected)
