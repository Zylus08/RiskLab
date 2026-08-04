import pytest
import numpy as np
from src.stress_testing import shock_correlation_matrix, measure_survival_rate

def test_shock_correlation_matrix():
    corr = np.array([
        [1.0, 0.2, 0.1],
        [0.2, 1.0, 0.4],
        [0.1, 0.4, 1.0]
    ])
    
    # Shock factor 1.0 means all elements become 1.0
    shocked = shock_correlation_matrix(corr, shock_factor=1.0)
    assert np.allclose(shocked, np.ones((3, 3)))
    
    # Shock factor 0.0 means no change
    no_shock = shock_correlation_matrix(corr, shock_factor=0.0)
    assert np.allclose(no_shock, corr)
    
    # Shock factor 0.5
    half_shock = shock_correlation_matrix(corr, shock_factor=0.5)
    expected = 0.5 * corr + 0.5 * np.ones((3, 3))
    np.fill_diagonal(expected, 1.0)
    assert np.allclose(half_shock, expected)

def test_measure_survival_rate():
    # 3 paths, 4 steps
    # Path 0: drops to 0.4 (breaches 0.5 barrier)
    # Path 1: drops to 0.6 (survives)
    # Path 2: drops to 0.5 (survives)
    paths = np.array([
        [1.0, 0.8, 0.4, 0.5],
        [1.0, 0.9, 0.7, 0.6],
        [1.0, 0.5, 0.8, 0.9]
    ])
    
    rate = measure_survival_rate(paths, ruin_barrier=0.5)
    
    # 2 out of 3 paths survive
    assert np.isclose(rate, 2.0 / 3.0)

def test_measure_survival_rate_invalid_input():
    paths = np.array([1.0, 0.8, 0.4])
    with pytest.raises(ValueError):
        measure_survival_rate(paths, ruin_barrier=0.5)
