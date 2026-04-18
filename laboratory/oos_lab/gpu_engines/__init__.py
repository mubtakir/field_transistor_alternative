"""
OOS-Lab v1.1: GPU Engine Base Class
Provides unified interface for FDTD, PIC, and Thermal solvers.
"""

class GPUEngine:
    def __init__(self, nx: int, ny: int, nz: int, dx: float):
        self.nx, self.ny, self.nz = nx, ny, nz
        self.dx = dx
        self.results = {}

    def setup(self):
        """Initialize Taichi fields and materials."""
        pass

    def run(self, max_steps: int):
        """Execute the GPU simulation kernel."""
        raise NotImplementedError("Subclasses must implement run()")

    def calibrate_dt(self, material_params: dict):
        """Auto-calculate stable time step based on Courant condition."""
        pass

    def save_checkpoint(self, path: str):
        """Save intermediate state."""
        pass
