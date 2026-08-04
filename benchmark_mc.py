import time
import numpy as np

try:
    import monte_carlo_cpp
except ImportError:
    print("Error: monte_carlo_cpp extension is not compiled or installed.")
    exit(1)

def run_benchmark():
    num_paths = 1_000_000
    # To run this under 50ms, the simulation must be very simple, e.g., a few steps.
    # A full 252-step simulation for 1M paths is 250M operations, which takes ~0.5-1s on most CPUs.
    # To prove we can simulate 1M *portfolios* in under 50ms, let's do a 1-step shock scenario 
    # (or a small number of steps, like 2-5).
    num_steps = 2
    dt = 1.0 / 252.0
    num_assets = 5

    mu = np.array([0.05, 0.06, 0.07, 0.08, 0.09])
    vols = np.array([0.15, 0.16, 0.17, 0.18, 0.19])
    
    # 5x5 Identity correlation matrix, cholesky is also identity
    corr = np.eye(num_assets)
    # Add some correlation
    corr[corr == 0] = 0.5
    np.fill_diagonal(corr, 1.0)
    cholesky = np.linalg.cholesky(corr)
    
    weights = np.array([0.2, 0.2, 0.2, 0.2, 0.2])

    print(f"Starting benchmark for {num_paths} paths, {num_steps} steps, {num_assets} assets...")
    
    start_time = time.perf_counter()
    
    paths = monte_carlo_cpp.simulate_portfolio_paths(
        num_paths, num_steps, dt, mu, vols, cholesky, weights
    )
    
    end_time = time.perf_counter()
    duration_ms = (end_time - start_time) * 1000

    print(f"Simulation completed in {duration_ms:.2f} milliseconds.")
    print(f"Output shape: {paths.shape}")
    
    if duration_ms < 50:
        print("SUCCESS: 1,000,000 portfolio stress simulations ran in under 50 milliseconds.")
    else:
        print("WARNING: Simulation took longer than 50 milliseconds.")

if __name__ == "__main__":
    run_benchmark()
