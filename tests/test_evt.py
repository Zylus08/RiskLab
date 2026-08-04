import pytest
import pandas as pd
import numpy as np
from src.evt import calculate_hill_estimator

def test_calculate_hill_estimator():
    # Create artificial heavy-tailed returns
    # Negative returns mean losses
    np.random.seed(42)
    # Generate Pareto distributed losses (tail index ~ alpha)
    # alpha = 2.0 -> gamma = 0.5
    losses = np.random.pareto(a=2.0, size=1000)
    returns = pd.Series(-losses)
    
    # Calculate Hill estimator for k=50
    gamma = calculate_hill_estimator(returns, k=50)
    
    # Should be close to 0.5
    assert 0.3 < gamma < 0.7

def test_calculate_hill_estimator_invalid_k():
    returns = pd.Series([-1.0, -2.0, -3.0])
    with pytest.raises(ValueError):
        calculate_hill_estimator(returns, k=0)

def test_calculate_hill_estimator_empty():
    returns = pd.Series(dtype=float)
    with pytest.raises(ValueError):
        calculate_hill_estimator(returns, k=10)
