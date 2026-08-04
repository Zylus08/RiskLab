import pytest
import pandas as pd
import numpy as np
from src.evt import calculate_hill_estimator, find_optimal_k_bootstrap

def test_calculate_hill_estimator_fixed_k():
    np.random.seed(42)
    # Pareto distributed losses (tail index ~ alpha)
    # alpha = 2.0 -> gamma = 0.5
    losses = np.random.pareto(a=2.0, size=1000)
    returns = pd.Series(-losses)
    
    gamma = calculate_hill_estimator(returns, k=50)
    assert 0.3 < gamma < 0.7

def test_calculate_hill_estimator_auto_k():
    np.random.seed(42)
    losses = np.random.pareto(a=2.0, size=1000)
    returns = pd.Series(-losses)
    
    # Auto uses bootstrap AMSE minimization
    gamma = calculate_hill_estimator(returns, k="auto")
    assert 0.3 < gamma < 0.7

def test_find_optimal_k_bootstrap():
    np.random.seed(42)
    losses = np.random.pareto(a=2.0, size=500)
    
    # Test that it returns a valid k within bounds
    optimal_k = find_optimal_k_bootstrap(losses, num_bootstraps=10)
    assert 2 <= optimal_k < len(losses)

def test_calculate_hill_estimator_invalid_k():
    returns = pd.Series([-1.0, -2.0, -3.0, -4.0, -5.0, -6.0])
    with pytest.raises(ValueError):
        calculate_hill_estimator(returns, k=0)
        
    with pytest.raises(ValueError):
        calculate_hill_estimator(returns, k=100) # exceeds data

def test_calculate_hill_estimator_empty():
    returns = pd.Series(dtype=float)
    with pytest.raises(ValueError):
        calculate_hill_estimator(returns, k=10)
