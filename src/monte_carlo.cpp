#include <omp.h>
#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <vector>
#include <cmath>
#include <cstdint>
#include <random>

namespace py = pybind11;

// --- Xoshiro256** RNG ---
static inline uint64_t rotl(const uint64_t x, int k) {
	return (x << k) | (x >> (64 - k));
}

inline uint64_t next_xoshiro(uint64_t *s) {
	const uint64_t result = rotl(s[1] * 5, 7) * 9;
	const uint64_t t = s[1] << 17;

	s[2] ^= s[0];
	s[3] ^= s[1];
	s[1] ^= s[2];
	s[0] ^= s[3];
	s[2] ^= t;
	s[3] = rotl(s[3], 45);

	return result;
}

void jump_xoshiro(uint64_t *s) {
    static const uint64_t JUMP[] = { 0x180ec6d33cfd0aba, 0xd5a61266f0c9392c, 0xa9582618e03fc9aa, 0x39abdc4529b1661c };
    uint64_t s0 = 0, s1 = 0, s2 = 0, s3 = 0;
    for(int i = 0; i < 4; i++) {
        for(int b = 0; b < 64; b++) {
            if (JUMP[i] & (1ULL << b)) {
                s0 ^= s[0];
                s1 ^= s[1];
                s2 ^= s[2];
                s3 ^= s[3];
            }
            next_xoshiro(s);
        }
    }
    s[0] = s0;
    s[1] = s1;
    s[2] = s2;
    s[3] = s3;
}

// --- Ziggurat Algorithm for Normals ---
static uint32_t kn[128];
static float wn[128];
static float fn[128];
static bool ziggurat_initialized = false;

void setup_ziggurat() {
    if (ziggurat_initialized) return;
    
    #pragma omp critical
    {
        if (!ziggurat_initialized) {
            const double m1 = 2147483648.0; // 2^31
            double dn = 3.442619855899;
            double tn = dn;
            double vn = 9.91256303526217e-3;
            double q;
            
            q = vn / std::exp(-0.5 * dn * dn);
            kn[0] = (uint32_t)((dn / q) * m1);
            kn[1] = 0;
            
            wn[0] = (float)(q / m1);
            wn[127] = (float)(dn / m1);
            
            fn[0] = 1.0f;
            fn[127] = (float)(std::exp(-0.5 * dn * dn));
            
            for (int i = 126; i >= 1; i--) {
                dn = std::sqrt(-2.0 * std::log(vn / dn + std::exp(-0.5 * dn * dn)));
                kn[i + 1] = (uint32_t)((dn / tn) * m1);
                tn = dn;
                fn[i] = (float)(std::exp(-0.5 * dn * dn));
                wn[i] = (float)(dn / m1);
            }
            ziggurat_initialized = true;
        }
    }
}

// Convert 64-bit random int to double in [0, 1)
inline double to_double(uint64_t x) {
    return (x >> 11) * (1.0 / 9007199254740992.0); // 2^53
}

inline float rnor(uint64_t* state) {
    int hz = (int)next_xoshiro(state);
    uint32_t iz = hz & 127;
    
    if ((uint32_t)std::abs(hz) < kn[iz]) {
        return hz * wn[iz];
    }
    
    // Fallback: ~2% of the time
    const float r = 3.442619855899f;
    float x, y;
    for (;;) {
        if (iz == 0) {
            do {
                x = -std::log(to_double(next_xoshiro(state))) * 0.2904764f; // 1/r
                y = -std::log(to_double(next_xoshiro(state)));
            } while (y + y < x * x);
            return (hz > 0) ? r + x : -r - x;
        }
        
        x = hz * wn[iz];
        if (fn[iz] + to_double(next_xoshiro(state)) * (fn[iz - 1] - fn[iz]) < std::exp(-0.5f * x * x)) {
            return x;
        }
        
        hz = (int)next_xoshiro(state);
        iz = hz & 127;
        if ((uint32_t)std::abs(hz) < kn[iz]) {
            return hz * wn[iz];
        }
    }
}


// --- Main Simulation Routine ---
py::array_t<double> simulate_portfolio_paths(
    int num_paths,
    int num_steps,
    double dt,
    py::array_t<double> mu,       
    py::array_t<double> vols,     
    py::array_t<double> cholesky, 
    py::array_t<double> weights   
) {
    setup_ziggurat();

    py::buffer_info mu_buf = mu.request();
    py::buffer_info vols_buf = vols.request();
    py::buffer_info chol_buf = cholesky.request();
    py::buffer_info weights_buf = weights.request();

    int num_assets = mu_buf.shape[0];

    double* mu_ptr = static_cast<double*>(mu_buf.ptr);
    double* vols_ptr = static_cast<double*>(vols_buf.ptr);
    double* chol_ptr = static_cast<double*>(chol_buf.ptr);
    double* weights_ptr = static_cast<double*>(weights_buf.ptr);

    std::vector<double> drift(num_assets);
    std::vector<double> vol_sqrt_dt(num_assets);
    for (int i = 0; i < num_assets; ++i) {
        drift[i] = (mu_ptr[i] - 0.5 * vols_ptr[i] * vols_ptr[i]) * dt;
        vol_sqrt_dt[i] = vols_ptr[i] * std::sqrt(dt);
    }

    auto result = py::array_t<double>({num_paths, num_steps});
    py::buffer_info result_buf = result.request();
    double* result_ptr = static_cast<double*>(result_buf.ptr);

    // Initialize master seed from high-entropy source
    std::random_device rd;
    uint64_t master_state[4] = {
        ((uint64_t)rd() << 32) | rd(),
        ((uint64_t)rd() << 32) | rd(),
        ((uint64_t)rd() << 32) | rd(),
        ((uint64_t)rd() << 32) | rd()
    };
    // Ensure state is not fully zero
    if (master_state[0] == 0) master_state[0] = 1;

    #pragma omp parallel
    {
        #ifdef _OPENMP
        int thread_id = omp_get_thread_num();
        #else
        int thread_id = 0;
        #endif
        
        uint64_t local_state[4];
        // Safely copy master state
        for(int i=0; i<4; i++) local_state[i] = master_state[i];
        
        // Jump the state forward so threads do not overlap
        for(int i = 0; i < thread_id; ++i) {
            jump_xoshiro(local_state);
        }

        std::vector<double> current_prices(num_assets);
        std::vector<double> indep_normals(num_assets);

        #pragma omp for schedule(static)
        for (int p = 0; p < num_paths; ++p) {
            for(int i=0; i<num_assets; ++i) current_prices[i] = 1.0;
            
            result_ptr[p * num_steps + 0] = 1.0; 
            
            for (int t = 1; t < num_steps; ++t) {
                // Generate independent normals using Ziggurat
                for (int i = 0; i < num_assets; ++i) {
                    indep_normals[i] = (double)rnor(local_state);
                }
                
                double portfolio_value = 0.0;
                
                for (int i = 0; i < num_assets; ++i) {
                    double correlated_normal = 0.0;
                    for (int j = 0; j <= i; ++j) { 
                        correlated_normal += chol_ptr[i * num_assets + j] * indep_normals[j];
                    }
                    
                    current_prices[i] *= std::exp(drift[i] + vol_sqrt_dt[i] * correlated_normal);
                    portfolio_value += weights_ptr[i] * current_prices[i];
                }
                
                result_ptr[p * num_steps + t] = portfolio_value;
            }
        }
    }

    return result;
}

PYBIND11_MODULE(monte_carlo_cpp, m) {
    m.doc() = "Enterprise C++ Monte Carlo Engine for RiskLab (Xoshiro256** + Ziggurat)";
    m.def("simulate_portfolio_paths", &simulate_portfolio_paths, "Simulate multi-asset portfolio paths using GBM");
}
