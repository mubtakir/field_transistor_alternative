"""
Laplace 2D FDM Solver - Foundational Physics Engine
---------------------------------------------------
Solves the Laplace equation on a 2D grid to extract the 6x6 Capacitance Matrix.
"""

import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla
from ..constants import eps_0

def solve_capacitance_matrix(nx=120, ny=100, plate_x_cells=[10,15,20,50,80,95], 
                             plate_y_range=(20, 80), eps_r=4.0, dx=1e-9, plate_depth=0.01):
    """
    Finite Difference Method (FDM) for Laplace equation.
    
    Args:
        nx, ny: Grid dimensions.
        plate_x_cells: X-coordinates of the U-plates.
        plate_y_range: (y_min, y_max) cells.
        eps_r: Dielectric constant.
        dx: Spatial resolution (meters).
        plate_depth: Z-dimension depth for capacitance scaling (meters).
        
    Returns:
        C: 6x6 Capacitance matrix (Farads).
        dist_matrix: Matrix of distances between plates.
    """
    N = nx * ny
    L_matrix = sp.lil_matrix((N, N))
    
    def idx(i, j): return i + j * nx

    # Standard 5-point Laplacian stencil
    for j in range(ny):
        for i in range(nx):
            k = idx(i, j)
            L_matrix[k, k] = 4
            if i > 0: L_matrix[k, idx(i-1, j)] = -1
            if i < nx-1: L_matrix[k, idx(i+1, j)] = -1
            if j > 0: L_matrix[k, idx(i, j-1)] = -1
            if j < ny-1: L_matrix[k, idx(i, j+1)] = -1
            
    L_matrix = L_matrix.tocsr()
    
    # Boundary nodes (plates + edges)
    plates = [[idx(x, j) for j in range(plate_y_range[0], plate_y_range[1])] for x in plate_x_cells]
    ap = set([n for p in plates for n in p])
    bn = set()
    for i in range(nx): bn.add(idx(i, 0)); bn.add(idx(i, ny-1))
    for j in range(ny): bn.add(idx(0, j)); bn.add(idx(nx-1, j))
    
    fixed_nodes = ap.union(bn)
    free_nodes = np.array([i for i in range(N) if i not in fixed_nodes])
    
    LF = L_matrix[free_nodes, :][:, free_nodes]
    C = np.zeros((len(plate_x_cells), len(plate_x_cells)))
    
    # Solve for each plate at 1.0V (Dirichlet)
    for j in range(len(plate_x_cells)):
        Vf = np.zeros(N)
        for n in plates[j]: Vf[n] = 1.0
        b = -(L_matrix * Vf)[free_nodes]
        VF = spla.spsolve(LF, b)
        
        V_complete = Vf.copy()
        V_complete[free_nodes] = VF
        
        # Charge Q = L * V
        Q_total = L_matrix * V_complete
        
        for i in range(len(plate_x_cells)):
            # C_ij = Q_i with V_j=1.0V
            C[i, j] = sum(Q_total[n] for n in plates[i]) * eps_0 * eps_r * plate_depth

    # Distance matrix for L-matrix calculations
    dist_matrix = np.zeros((len(plate_x_cells), len(plate_x_cells)))
    for i in range(len(plate_x_cells)):
        for j in range(len(plate_x_cells)):
            dist_matrix[i, j] = abs(plate_x_cells[i] - plate_x_cells[j]) * dx
            
    return C, dist_matrix
