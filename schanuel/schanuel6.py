import numpy as np
from scipy.linalg import solve
import time

def solve_marchenko_schanuel_interference(name, z_set, L=25.0, N=600):
    """
    Advanced Marchenko solver with Relation-Aware Phase Interference.
    """
    x_vals = np.linspace(0.01, L, N)
    dx = x_vals[1] - x_vals[0]
    
    # 1. Detect Linear Relations (e.g., log a + log b = log c)
    # We apply a 'penalty phase' to terms that break linear independence.
    z_array = np.array(z_set, dtype=complex)
    n = len(z_array)
    relation_mask = np.ones(n, dtype=complex)
    
    for i in range(n):
        for j in range(i + 1, n):
            for k in range(n):
                if k != i and k != j:
                    # Check for z_i + z_j = z_k (Linear dependence)
                    if np.isclose(z_array[i] + z_array[j], z_array[k], atol=1e-8):
                        relation_mask[k] *= -1.5 # Destructive flip
    
    elements = []
    alphas = []
    for i, z in enumerate(z_set):
        # The value z and its exponential e^z
        elements.extend([z, np.exp(z)])
        # Apply the relation mask to the exponential term
        alphas.extend([1.0, 1.0 * relation_mask[i]])
    
    elements = np.array(elements, dtype=complex)
    alphas = np.array(alphas, dtype=complex)
    
    # Slower decay to allow long-range interaction
    kappas = 0.10 + 0.01 * np.log(1 + np.abs(elements))

    def B_func(t):
        # Interference kernel: Sum( alpha * exp(-kappa * t) )
        exponent = -kappas[:, None, None] * t[None, :, :]
        # We use the real part of the phased sum
        return np.real(np.sum(alphas[:, None, None] * np.exp(exponent), axis=0))

    K_xx = np.zeros(N)
    max_c = 0
    for i in range(N):
        sub_grid = x_vals[i:]
        n_sub = len(sub_grid)
        if n_sub < 2: break
        
        B_mat = B_func(sub_grid[:, None] + sub_grid[None, :]) * dx
        A = np.eye(n_sub) + B_mat
        
        c = np.linalg.cond(A)
        if c > max_c: max_c = c
        
        rhs_val = -np.real(np.sum(alphas[:, None] * np.exp(-kappas[:, None] * (x_vals[i] + sub_grid)[None, :]), axis=0))
        
        try:
            K_xx[i] = solve(A, rhs_val, assume_a='pos')[0]
        except:
            K_xx[i] = 0.0

    V = -2 * np.gradient(K_xx, dx)
    mask = ~np.isnan(V)
    l1 = np.trapz(np.abs(V[mask]), dx=dx)
    l2 = np.sqrt(np.trapz(V[mask]**2, dx=dx))
    sir = l2 / l1 if l1 > 0 else 0
    
    return l1, sir, max_c

# --- Execution ---
test_cases = [
    ("Independent [1, e, π]", [1.0, np.e, np.pi]),
    ("Dependent Log [ln 2, ln 3, ln 6]", [np.log(2), np.log(3), np.log(6)]),
    ("Euler Relation [π, iπ]", [np.pi, 1j*np.pi]),
    ("Collision [1, 1.000001]", [1.0, 1.000001])
]

print(f"{'Case':<30} | {'L1 Mass':<10} | {'SIR':<10} | {'MaxCond':<10}")
print("-" * 75)
for name, z_set in test_cases:
    l1, sir, cond = solve_marchenko_schanuel_interference(name, z_set)
    print(f"{name:<30} | {l1:<10.4f} | {sir:<10.4f} | {cond:<10.2e}")

#     (base) brendanlynch@Brendans-Laptop schanuel % python schanuel6.py
# Case                           | L1 Mass    | SIR        | MaxCond   
# ---------------------------------------------------------------------------
# Independent [1, e, π]          | 0.4656     | 0.3876     | 2.66e+01  
# Dependent Log [ln 2, ln 3, ln 6] | 0.3930     | 0.4259     | 1.77e+01  
# Euler Relation [π, iπ]         | 0.4491     | 0.3166     | 1.82e+01  
# Collision [1, 1.000001]        | 0.4181     | 0.3923     | 1.92e+01  
# (base) brendanlynch@Brendans-Laptop schanuel % 