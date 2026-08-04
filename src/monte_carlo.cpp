#include <omp.h>
#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <vector>
#include <cmath>
#include <cstdint>

namespace py = pybind11;

// Simulate portfolio paths assuming Geometric Brownian Motion
// Returns a 2D array of shape (num_paths, num_steps) containing the portfolio wealth at each step.
// Initial wealth is 1.0.
py::array_t<double> simulate_portfolio_paths(
    int num_paths,
    int num_steps,
    double dt,
    py::array_t<double> mu,       // Expected returns per year, shape (num_assets,)
    py::array_t<double> vols,     // Volatilities per year, shape (num_assets,)
    py::array_t<double> cholesky, // Cholesky factor of correlation matrix L, shape (num_assets, num_assets)
    py::array_t<double> weights   // Portfolio weights, shape (num_assets,)
) {
    py::buffer_info mu_buf = mu.request();
    py::buffer_info vols_buf = vols.request();
    py::buffer_info chol_buf = cholesky.request();
    py::buffer_info weights_buf = weights.request();

    int num_assets = mu_buf.shape[0];

    double* mu_ptr = static_cast<double*>(mu_buf.ptr);
    double* vols_ptr = static_cast<double*>(vols_buf.ptr);
    double* chol_ptr = static_cast<double*>(chol_buf.ptr);
    double* weights_ptr = static_cast<double*>(weights_buf.ptr);

    // Precompute drift terms
    std::vector<double> drift(num_assets);
    std::vector<double> vol_sqrt_dt(num_assets);
    for (int i = 0; i < num_assets; ++i) {
        drift[i] = (mu_ptr[i] - 0.5 * vols_ptr[i] * vols_ptr[i]) * dt;
        vol_sqrt_dt[i] = vols_ptr[i] * std::sqrt(dt);
    }

    auto result = py::array_t<double>({num_paths, num_steps});
    py::buffer_info result_buf = result.request();
    double* result_ptr = static_cast<double*>(result_buf.ptr);

    // To make it very fast, we avoid allocating inside the loop
    // and parallelize over paths
    #pragma omp parallel
    {
        // Thread-local random number generator and distributions
        // Seed differently for each thread
        // We use a small hack for openmp if available, or just standard thread local
        #ifdef _OPENMP
        int thread_id = omp_get_thread_num();
        #else
        int thread_id = 0;
        #endif
        uint32_t state = 42 + thread_id * 19937;
        auto next_float = [&]() -> float {
            state ^= state << 13;
            state ^= state >> 17;
            state ^= state << 5;
            return (state >> 8) * (1.0f / 16777216.0f);
        };
        auto next_normal = [&]() -> double {
            float u1 = next_float();
            float u2 = next_float();
            if (u1 < 1e-7f) u1 = 1e-7f;
            return std::sqrt(-2.0 * std::log(u1)) * std::cos(2.0 * 3.14159265358979323846 * u2);
        };

        std::vector<double> current_prices(num_assets);
        std::vector<double> indep_normals(num_assets);

        #pragma omp for schedule(static)
        for (int p = 0; p < num_paths; ++p) {
            // Reset prices to 1.0 at start of path
            for(int i=0; i<num_assets; ++i) current_prices[i] = 1.0;
            
            result_ptr[p * num_steps + 0] = 1.0; 
            
            for (int t = 1; t < num_steps; ++t) {
                // Generate independent normals
                for (int i = 0; i < num_assets; ++i) {
                    indep_normals[i] = next_normal();
                }
                
                double portfolio_value = 0.0;
                
                for (int i = 0; i < num_assets; ++i) {
                    double correlated_normal = 0.0;
                    for (int j = 0; j <= i; ++j) { // L is lower triangular
                        correlated_normal += chol_ptr[i * num_assets + j] * indep_normals[j];
                    }
                    
                    // Update asset price
                    current_prices[i] *= std::exp(drift[i] + vol_sqrt_dt[i] * correlated_normal);
                    
                    // Add to portfolio
                    portfolio_value += weights_ptr[i] * current_prices[i];
                }
                
                result_ptr[p * num_steps + t] = portfolio_value;
            }
        }
    }

    return result;
}

PYBIND11_MODULE(monte_carlo_cpp, m) {
    m.doc() = "C++ Monte Carlo Engine for RiskLab";
    m.def("simulate_portfolio_paths", &simulate_portfolio_paths, "Simulate multi-asset portfolio paths using GBM");
}
