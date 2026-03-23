import numpy as np
from scipy.linalg import solve
import time
import sys

def solve_marchenko_schanuel(z_set, L=12.0, N=400):
    """
    Marchenko solver optimized for n-element Schanuel sets.
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
        exponent = -kappas[:, None, None] * t[None, :, :]
        return np.real(np.sum(alphas[:, None, None] * np.exp(exponent), axis=0))

    K_xx = np.zeros(N)
    for i in range(N):
        sub_grid = x_vals[i:]
        n_sub = len(sub_grid)
        if n_sub < 2: break
        
        x = x_vals[i]
        Y, Z = np.meshgrid(sub_grid, sub_grid)
        B_mat = B_func(Y + Z) * dx
        A = np.eye(n_sub) + B_mat
        
        t_rhs = x + sub_grid
        rhs_val = -np.real(np.sum(alphas[:, None] * np.exp(-kappas[:, None] * t_rhs[None, :]), axis=0))
        
        try:
            sol = solve(A, rhs_val, assume_a='pos')
            K_xx[i] = sol[0]
        except:
            K_xx[i] = 0.0

    V = -2 * np.gradient(K_xx, dx)
    mask = ~np.isnan(V)
    return np.trapz(np.abs(V[mask]), dx=dx) if np.any(mask) else 0

# --- n=5 Stress Test ---

n_samples = 15
test_cases = [
    ("Indep [1, e, π, √2, ln 3]", [1.0, np.e, np.pi, np.sqrt(2), np.log(3)]),
    ("Dep [ln 2, ln 3, ln 5, ln 6, ln 30]", [np.log(2), np.log(3), np.log(5), np.log(6), np.log(30)]), # ln 2+ln 3=ln 6; ln 5+ln 6=ln 30
    ("Powers [1, 2, 3, 4, 5]", [1.0, 2.0, 3.0, 4.0, 5.0]),
]

print(f"Starting n=5 Stress Test ({n_samples} baseline + {len(test_cases)} targets)...")
start_time = time.time()

baseline_norms = []
for i in range(n_samples):
    rand_set = np.random.uniform(0.5, 4.0, 5) # Random sets of 5
    norm = solve_marchenko_schanuel(rand_set)
    baseline_norms.append(norm)
    sys.stdout.write(f"\rBaseline Progress: {i+1}/{n_samples}")
    sys.stdout.flush()

mu = np.mean(baseline_norms)
sigma = np.std(baseline_norms)
print("\nBaseline Complete.")

print("\n" + "="*85)
print(f"{'Test Case (n=5)':<28} | {'L1 Norm':<15} | {'Z-Score':<10} | {'Status'}")
print("="*85)

for name, z_set in test_cases:
    norm = solve_marchenko_schanuel(z_set)
    z_score = (norm - mu) / sigma
    status = "INDEPENDENT" if z_score > -0.5 else "REDUNDANT (SCHANUEL COLLAPSE)"
    print(f"{name:<28} | {norm:<15.6f} | {z_score:<10.2f} | {status}")

print("="*85)
print(f"n=5 Baseline Mean (μ): {mu:.6f} | Std (σ): {sigma:.6f}")
print(f"Total Time: {time.time() - start_time:.2f} seconds")

# (base) brendanlynch@Brendans-Laptop schanuel % python schanuel3.py
# Starting n=5 Stress Test (15 baseline + 3 targets)...
# Baseline Progress: 15/15
# Baseline Complete.

# =====================================================================================
# Test Case (n=5)              | L1 Norm         | Z-Score    | Status
# =====================================================================================
# Indep [1, e, π, √2, ln 3]    | 0.723144        | -1.04      | REDUNDANT (SCHANUEL COLLAPSE)
# Dep [ln 2, ln 3, ln 5, ln 6, ln 30] | 0.715669        | -1.35      | REDUNDANT (SCHANUEL COLLAPSE)
# Powers [1, 2, 3, 4, 5]       | 0.806254        | 2.41       | INDEPENDENT
# =====================================================================================
# n=5 Baseline Mean (μ): 0.748199 | Std (σ): 0.024064
# Total Time: 20.35 seconds
# (base) brendanlynch@Brendans-Laptop schanuel % 