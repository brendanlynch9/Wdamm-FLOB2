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
    
    # Expand to all pairs (z, exp(z))
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

# --- Triplets Sweep ---

n_samples = 15
# We test sets of 3 numbers now
test_cases = [
    ("Indep Triplet [1, e, π]", [1.0, np.e, np.pi]),
    ("Dep Triplet [log 2, log 3, log 6]", [np.log(2), np.log(3), np.log(6)]), # log 2 + log 3 = log 6
    ("Powers [2, 4, 8]", [2.0, 4.0, 8.0]), # Algebraic dependence in exponents
    ("Mixed [1, π, 1+π]", [1.0, np.pi, 1.0 + np.pi]) # Linear dependence
]

print(f"Starting n=3 Robustness Sweep ({n_samples} baseline + {len(test_cases)} targets)...")
start_time = time.time()

baseline_norms = []
for i in range(n_samples):
    rand_set = np.random.uniform(0.5, 4.0, 3) # Random triplets
    norm = solve_marchenko_schanuel(rand_set)
    baseline_norms.append(norm)
    sys.stdout.write(f"\rBaseline Progress: {i+1}/{n_samples}")
    sys.stdout.flush()

mu = np.mean(baseline_norms)
sigma = np.std(baseline_norms)
print("\nBaseline Complete.")

print("\n" + "="*85)
print(f"{'Test Case (n=3)':<28} | {'L1 Norm':<15} | {'Z-Score':<10} | {'Status'}")
print("="*85)

for name, z_set in test_cases:
    norm = solve_marchenko_schanuel(z_set)
    z_score = (norm - mu) / sigma
    status = "INDEPENDENT" if z_score > -0.5 else "REDUNDANT (SCHANUEL VIOLATION)"
    print(f"{name:<28} | {norm:<15.6f} | {z_score:<10.2f} | {status}")

print("="*85)
print(f"n=3 Baseline Mean (μ): {mu:.6f} | Std (σ): {sigma:.6f}")

# (base) brendanlynch@Brendans-Laptop schanuel % python schanuel2.py
# Starting n=3 Robustness Sweep (15 baseline + 4 targets)...
# Baseline Progress: 15/15
# Baseline Complete.

# =====================================================================================
# Test Case (n=3)              | L1 Norm         | Z-Score    | Status
# =====================================================================================
# Indep Triplet [1, e, π]      | 0.714645        | 0.30       | INDEPENDENT
# Dep Triplet [log 2, log 3, log 6] | 0.648624        | -2.70      | REDUNDANT (SCHANUEL VIOLATION)
# Powers [2, 4, 8]             | 0.866519        | 7.19       | INDEPENDENT
# Mixed [1, π, 1+π]            | 0.747362        | 1.78       | INDEPENDENT
# =====================================================================================
# n=3 Baseline Mean (μ): 0.708082 | Std (σ): 0.022044
# (base) brendanlynch@Brendans-Laptop schanuel % 

