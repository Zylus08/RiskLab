import numpy as np

def shock_market_regime(
    corr_matrix: np.ndarray,
    vol_vector: np.ndarray,
    corr_shock_factor: float = 0.5,
    vol_shock_factor: float = 2.0
) -> tuple[np.ndarray, np.ndarray]:
    """
    Simulate a market crash regime by jointly shocking correlations and volatilities.
    
    Parameters
    ----------
    corr_matrix : np.ndarray
        The original correlation matrix (N x N).
    vol_vector : np.ndarray
        The original annualized volatility vector (N,).
    corr_shock_factor : float
        A value between 0.0 and 1.0 representing how strongly correlations move towards 1.0.
    vol_shock_factor : float
        A multiplier for the volatilities (e.g., 2.0 means volatilities double).
        
    Returns
    -------
    tuple[np.ndarray, np.ndarray]
        (shocked_corr_matrix, shocked_vol_vector)
    """
    if corr_shock_factor < 0.0 or corr_shock_factor > 1.0:
        raise ValueError("corr_shock_factor must be between 0.0 and 1.0.")
    if vol_shock_factor < 0.0:
        raise ValueError("vol_shock_factor must be non-negative.")
        
    N = corr_matrix.shape[0]
    
    # 1. Shock correlations towards 1.0
    J = np.ones((N, N))
    shocked_corr = (1 - corr_shock_factor) * corr_matrix + corr_shock_factor * J
    np.fill_diagonal(shocked_corr, 1.0)
    
    # 2. Shock volatilities by the scalar
    shocked_vol = vol_vector * vol_shock_factor
    
    return shocked_corr, shocked_vol

def measure_survival_rate(
    simulated_paths: np.ndarray,
    ruin_barrier: float = 0.5
) -> float:
    """
    Measure the portfolio's survival rate given simulated wealth paths.
    
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
        
    min_wealth_per_path = np.min(simulated_paths, axis=1)
    survived_paths = np.sum(min_wealth_per_path >= ruin_barrier)
    survival_rate = survived_paths / simulated_paths.shape[0]
    
    return float(survival_rate)
