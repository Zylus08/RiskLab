import numpy as np
import pandas as pd

def calculate_hill_estimator(returns: pd.Series, k: int = 50) -> float:
    """
    Calculate the Hill estimator for the tail index of asset returns.

    The Hill estimator is used in Extreme Value Theory (EVT) to estimate the shape
    parameter (tail index) of the tail of a heavy-tailed distribution.
    A lower tail index indicates a heavier tail (i.e., more extreme events).

    Parameters
    ----------
    returns : pd.Series
        Series of asset returns.
    k : int
        Number of upper order statistics to use. Must be > 1.

    Returns
    -------
    float
        The estimated tail index (gamma).
    """
    if returns.empty:
        raise ValueError("Returns series cannot be empty.")
    if k <= 1:
        raise ValueError("k must be greater than 1.")
    
    # We are interested in the extreme negative returns (left tail)
    # Convert returns to losses (positive values for negative returns)
    losses = -returns.dropna()
    losses = losses[losses > 0]
    
    if len(losses) <= k:
        raise ValueError("Not enough loss data points to compute Hill estimator for the given k.")

    # Sort losses in descending order
    sorted_losses = np.sort(losses.values)[::-1]
    
    # The upper k order statistics
    X_i = sorted_losses[:k]
    # The (k+1)-th order statistic
    X_k_plus_1 = sorted_losses[k]
    
    if X_k_plus_1 <= 0:
        raise ValueError("The (k+1)-th order statistic must be strictly positive.")

    # Calculate Hill estimator: gamma = 1/k * sum_{i=1}^k ln(X_i / X_{k+1})
    gamma = np.mean(np.log(X_i / X_k_plus_1))
    
    return gamma
