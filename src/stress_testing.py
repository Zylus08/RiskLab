import numpy as np
import pandas as pd

def shock_correlation_matrix(
    corr_matrix: np.ndarray,
    shock_factor: float = 0.5
) -> np.ndarray:
    """
    Artificially increase the correlations between assets to simulate a stress scenario.
    
    Parameters
    ----------
    corr_matrix : np.ndarray
        The original correlation matrix (N x N).
    shock_factor : float
        A value between 0.0 and 1.0. 
        0.0 means no shock.
        1.0 means perfect correlation (all off-diagonal elements become 1.0).
        
    Returns
    -------
    np.ndarray
        The shocked correlation matrix.
    """
    if shock_factor < 0.0 or shock_factor > 1.0:
        raise ValueError("shock_factor must be between 0.0 and 1.0.")
        
    N = corr_matrix.shape[0]
    # Create a matrix of ones
    J = np.ones((N, N))
    
    # Linearly interpolate between original correlation matrix and perfectly correlated matrix
    shocked_corr = (1 - shock_factor) * corr_matrix + shock_factor * J
    
    # Ensure diagonal is exactly 1.0
    np.fill_diagonal(shocked_corr, 1.0)
    
    return shocked_corr

def measure_survival_rate(
    simulated_paths: np.ndarray,
    ruin_barrier: float = 0.5
) -> float:
    """
    Measure the portfolio's survival rate given simulated wealth paths.
    
    Survival is defined as the portfolio value never dropping below a certain fraction
    (ruin_barrier) of its initial value (which is assumed to be 1.0 for normalized paths).
    
    Parameters
    ----------
    simulated_paths : np.ndarray
        Array of simulated portfolio wealth paths of shape (num_paths, num_steps).
    ruin_barrier : float
        The minimum allowable wealth relative to the initial wealth.
        
    Returns
    -------
    float
        The proportion of paths that survived (did not breach the ruin barrier).
    """
    if simulated_paths.ndim != 2:
        raise ValueError("simulated_paths must be a 2D array (num_paths, num_steps).")
        
    # Check if the minimum value in each path falls below the ruin barrier
    min_wealth_per_path = np.min(simulated_paths, axis=1)
    
    survived_paths = np.sum(min_wealth_per_path >= ruin_barrier)
    survival_rate = survived_paths / simulated_paths.shape[0]
    
    return float(survival_rate)
