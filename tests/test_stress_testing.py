import pytest
import numpy as np
from src.stress_testing import shock_market_regime, measure_survival_rate

def test_shock_market_regime():
    corr = np.array([
        [1.0, 0.2, 0.1],
        [0.2, 1.0, 0.4],
        [0.1, 0.4, 1.0]
    ])
    vol = np.array([0.15, 0.20, 0.25])
    
    # Extreme crash: full correlation, triple volatility
    shocked_corr, shocked_vol = shock_market_regime(
        corr, vol, corr_shock_factor=1.0, vol_shock_factor=3.0
    )
    
    assert np.allclose(shocked_corr, np.ones((3, 3)))
    assert np.allclose(shocked_vol, np.array([0.45, 0.60, 0.75]))
    
    # Normal regime: no shock
    no_shock_corr, no_shock_vol = shock_market_regime(
        corr, vol, corr_shock_factor=0.0, vol_shock_factor=1.0
    )
    
    assert np.allclose(no_shock_corr, corr)
    assert np.allclose(no_shock_vol, vol)
    
    # Mild shock
    mild_corr, mild_vol = shock_market_regime(
        corr, vol, corr_shock_factor=0.5, vol_shock_factor=1.5
    )
    
    expected_corr = 0.5 * corr + 0.5 * np.ones((3, 3))
    np.fill_diagonal(expected_corr, 1.0)
    
    assert np.allclose(mild_corr, expected_corr)
    assert np.allclose(mild_vol, vol * 1.5)

def test_measure_survival_rate():
    paths = np.array([
        [1.0, 0.8, 0.4, 0.5],
        [1.0, 0.9, 0.7, 0.6],
        [1.0, 0.5, 0.8, 0.9]
    ])
    
    rate = measure_survival_rate(paths, ruin_barrier=0.5)
    
    # 2 out of 3 paths survive (the first one breaches 0.5)
    assert np.isclose(rate, 2.0 / 3.0)

def test_measure_survival_rate_invalid_input():
    paths = np.array([1.0, 0.8, 0.4])
    with pytest.raises(ValueError):
        measure_survival_rate(paths, ruin_barrier=0.5)
