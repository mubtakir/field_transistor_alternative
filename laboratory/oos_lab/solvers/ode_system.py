"""
Generic ODE System Solver wrapper around scipy.integrate.solve_ivp.
"""
import numpy as np
import scipy.integrate as spi


def solve_ode(system_fn, y0, t_span, t_eval=None, method='Radau',
              rtol=1e-8, atol=1e-10, max_step=np.inf):
    """
    Solve a system of ODEs using scipy's solve_ivp.
    
    Parameters
    ----------
    system_fn : callable
        Function f(t, y) -> dy/dt.
    y0 : array_like
        Initial state vector.
    t_span : tuple
        (t_start, t_end).
    t_eval : array_like, optional
        Times at which to store the solution.
    method : str
        Integration method ('Radau', 'RK45', 'BDF', etc.).
    rtol, atol : float
        Relative and absolute tolerances.
    max_step : float
        Maximum step size.
    
    Returns
    -------
    sol : OdeResult
        Solution object with .t and .y attributes.
    """
    sol = spi.solve_ivp(
        system_fn, t_span, y0,
        t_eval=t_eval, method=method,
        rtol=rtol, atol=atol, max_step=max_step
    )
    return sol
