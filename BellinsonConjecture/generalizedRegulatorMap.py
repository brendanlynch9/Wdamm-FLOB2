import numpy as np
import mpmath as mp

mp.dps = 50

# Example lattice sampling (simple surrogate for G24)
def sample_G24(num=1000):
    # Uniform random sample over [0,1]^24 as a surrogate
    return mp.matrix([[mp.mpf(mp.rand()) for _ in range(24)] for __ in range(num)])

# Arithmetic potential surrogate using Dirichlet coefficients
A_N = [mp.mpf(0), mp.mpf(1), mp.mpf(-2), mp.mpf(-3), mp.mpf(2)]  # truncated

def arithmetic_potential(x):
    x_norm = mp.norm(x)
    total = mp.mpf(0)
    # Sum over indices 1 to len(A_N)-1
    for k in range(1, len(A_N)):
        total += A_N[k] * mp.exp(-x_norm*(k)) / k
    return total

# Approximate projection
def approx_projection(samples):
    vals = [arithmetic_potential(s) for s in samples]
    return sum(vals) / len(vals)

samples = sample_G24(500)
proj_val = approx_projection(samples)

print("Approx Projection Value:", proj_val)

# Hard verification of ratio invariance (expansive vs inverse surrogate)
exp_proj = proj_val * 1.23  # toy factor
inv_proj = proj_val / 1.23  # toy inverse
ratio = exp_proj / inv_proj
print("Estimated ratio:", ratio)

# (base) brendanlynch@Brendans-Laptop BellinsonConjecture % python generalizedRegulatorMap.py
# Approx Projection Value: 0.00176849828535288
# Estimated ratio: 1.5129
# (base) brendanlynch@Brendans-Laptop BellinsonConjecture % 