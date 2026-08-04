import numpy as np
import pandas as pd
from typing import Union

def find_optimal_k_bootstrap(losses: np.ndarray, num_bootstraps: int = 100) -> int:
    """
    Find the optimal k for the Hill estimator using a bootstrap method
    to minimize Asymptotic Mean Squared Error (AMSE).
    
    Parameters
    ----------
    losses : np.ndarray
        Array of strictly positive extreme losses.
    num_bootstraps : int
        Number of bootstrap iterations.
        
    Returns
    -------
    int
        The optimal k.
    """
    n = len(losses)
    if n < 20:
        return max(2, n // 2)
        
    k_grid = np.arange(5, min(n - 1, int(n * 0.2)))
    if len(k_grid) == 0:
        return 2

    full_sorted = np.sort(losses)[::-1]
    
    # Pre-calculate full sample gammas to find a proxy for "true" gamma
    gammas_full = []
    for k in k_grid:
        if full_sorted[k] > 0:
            gammas_full.append(np.mean(np.log(full_sorted[:k] / full_sorted[k])))
        else:
            gammas_full.append(np.nan)
            
    # Use median of valid estimates as a robust proxy for the true tail index
    valid_gammas = [g for g in gammas_full if not np.isnan(g)]
    if not valid_gammas:
        return 2
        
    proxy_gamma = np.median(valid_gammas)
    
    mse = np.zeros(len(k_grid))
    
    for _ in range(num_bootstraps):
        # Draw bootstrap sample
        subsample = np.random.choice(losses, size=n, replace=True)
        sub_sorted = np.sort(subsample)[::-1]
        
        for i, k in enumerate(k_grid):
            if sub_sorted[k] > 0:
                gamma_est = np.mean(np.log(sub_sorted[:k] / sub_sorted[k]))
                mse[i] += (gamma_est - proxy_gamma) ** 2
            else:
                mse[i] += 1e6  # heavily penalize invalid k
                
    optimal_idx = np.argmin(mse)
    return int(k_grid[optimal_idx])

def calculate_hill_estimator(returns: pd.Series, k: Union[int, str] = "auto") -> float:
    """
    Calculate the Hill estimator for the tail index of asset returns.

    Parameters
    ----------
    returns : pd.Series
        Series of asset returns.
    k : int or str
        Number of upper order statistics to use. 
        If "auto", uses a bootstrap AMSE minimization to find optimal k.

    Returns
    -------
    float
        The estimated tail index (gamma).
    """
    if returns.empty:
        raise ValueError("Returns series cannot be empty.")
    
    losses = -returns.dropna()
    losses = losses[losses > 0].values
    
    if len(losses) < 5:
        raise ValueError("Not enough loss data points to compute Hill estimator.")

    if k == "auto":
        k_val = find_optimal_k_bootstrap(losses)
    elif isinstance(k, int):
        k_val = k
        if k_val <= 1:
            raise ValueError("k must be greater than 1.")
        if k_val >= len(losses):
            raise ValueError("k cannot exceed the number of positive losses.")
    else:
        raise ValueError("k must be an integer or 'auto'.")

    sorted_losses = np.sort(losses)[::-1]
    
    X_i = sorted_losses[:k_val]
    X_k_plus_1 = sorted_losses[k_val]
    
    if X_k_plus_1 <= 0:
        raise ValueError("The (k+1)-th order statistic must be strictly positive.")

    gamma = np.mean(np.log(X_i / X_k_plus_1))
    
    return gamma
