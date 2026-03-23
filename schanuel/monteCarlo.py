import numpy as np
from scipy.linalg import solve
import time
import sys

def solve_marchenko_schanuel(z_set, L=12.0, N=400):
    """
    Core Marchenko solver optimized for speed and mass-deficit detection.
    """
    x_vals = np.linspace(0.01, L, N)
    dx = x_vals[1] - x_vals[0]
    
    elements = []
    for z in z_set:
        elements.append(z)
        elements.append(np.exp(z))
    elements = np.array(elements, dtype=complex)
    
    kappas = 0.15 + 0.02 * np.log(1 + np.abs(elements))
    alphas = elements / (1 + np.abs(elements)) 

    def B_func(t):
        # Optimized broadcasting
        exponent = -kappas[:, None, None] * t[None, :, :]
        return np.real(np.sum(alphas[:, None, None] * np.exp(exponent), axis=0))

    K_xx = np.zeros(N)
    
    # Pre-calculate components for RHS to save time in loop
    for i in range(N):
        sub_grid = x_vals[i:]
        n_sub = len(sub_grid)
        if n_sub < 2: break
        
        x = x_vals[i]
        # Build Kernel matrix
        Y, Z = np.meshgrid(sub_grid, sub_grid)
        B_mat = B_func(Y + Z) * dx
        A = np.eye(n_sub) + B_mat
        
        # RHS
        t_rhs = x + sub_grid
        rhs_val = -np.real(np.sum(alphas[:, None] * np.exp(-kappas[:, None] * t_rhs[None, :]), axis=0))
        
        try:
            # solve is faster than lstsq if matrix is well-behaved
            sol = solve(A, rhs_val, assume_a='pos')
            K_xx[i] = sol[0]
        except:
            K_xx[i] = 0.0

    V = -2 * np.gradient(K_xx, dx)
    mask = ~np.isnan(V)
    return np.trapz(np.abs(V[mask]), dx=dx) if np.any(mask) else 0

# --- Execution ---

n_samples = 15
test_cases = [
    ("Independent [1, π]", [1.0, np.pi]),
    ("Dependent [log 2, log 4]", [np.log(2), np.log(4)]),
    ("Euler Identity [π, iπ]", [np.pi, 1j*np.pi]),
    ("Near-Collision [1, 1+1e-9]", [1.0, 1.0 + 1e-9]),
]

print(f"Starting Robustness Sweep ({n_samples} baseline + {len(test_cases)} targets)...")
start_time = time.time()

baseline_norms = []
for i in range(n_samples):
    rand_set = np.random.uniform(0.5, 4.0, 2)
    norm = solve_marchenko_schanuel(rand_set)
    baseline_norms.append(norm)
    sys.stdout.write(f"\rBaseline Progress: {i+1}/{n_samples}")
    sys.stdout.flush()

mu = np.mean(baseline_norms)
sigma = np.std(baseline_norms)
print("\nBaseline Complete.")

print("\n" + "="*85)
print(f"{'Test Case':<28} | {'L1 Norm':<15} | {'Z-Score':<10} | {'Status'}")
print("="*85)

for name, z_set in test_cases:
    norm = solve_marchenko_schanuel(z_set)
    z_score = (norm - mu) / sigma
    status = "INDEPENDENT" if z_score > -0.2 else "DEPENDENT/REDUNDANT"
    print(f"{name:<28} | {norm:<15.6f} | {z_score:<10.2f} | {status}")

print("="*85)
total_time = time.time() - start_time
print(f"Total Execution Time: {total_time:.2f} seconds")
print(f"Baseline Mean (μ): {mu:.6f} | Std (σ): {sigma:.6f}")

# (base) brendanlynch@Brendans-Laptop schanuel % python monteCarlo.py
# Starting Robustness Sweep (15 baseline + 4 targets)...
# Baseline Progress: 15/15
# Baseline Complete.

# =====================================================================================
# Test Case                    | L1 Norm         | Z-Score    | Status
# =====================================================================================
# Independent [1, π]           | 0.674192        | -0.27      | DEPENDENT/REDUNDANT
# Dependent [log 2, log 4]     | 0.611179        | -1.90      | DEPENDENT/REDUNDANT
# Euler Identity [π, iπ]       | 0.627323        | -1.48      | DEPENDENT/REDUNDANT
# Near-Collision [1, 1+1e-9]   | 0.607778        | -1.99      | DEPENDENT/REDUNDANT
# =====================================================================================
# Total Execution Time: 10.32 seconds
# Baseline Mean (μ): 0.684694 | Std (σ): 0.038672
# (base) brendanlynch@Brendans-Laptop schanuel % 