import numpy as np
from scipy.linalg import solve
import time

def solve_marchenko_schanuel(z_set, L=20.0, N=500):
    """
    High-resolution solver for SIR convergence.
    """
    x_vals = np.linspace(0.01, L, N)
    dx = x_vals[1] - x_vals[0]
    
    elements = []
    for z in z_set:
        elements.append(z)
        elements.append(np.exp(z))
    elements = np.array(elements, dtype=complex)
    
    # Using slightly more sensitive kappa for long-range detection
    kappas = 0.12 + 0.015 * np.log(1 + np.abs(elements))
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
        B_mat = B_func(sub_grid[:, None] + sub_grid[None, :]) * dx
        A = np.eye(n_sub) + B_mat
        rhs_val = -np.real(np.sum(alphas[:, None] * np.exp(-kappas[:, None] * (x + sub_grid)[None, :]), axis=0))
        
        try:
            sol = solve(A, rhs_val, assume_a='pos')
            K_xx[i] = sol[0]
        except:
            K_xx[i] = 0.0

    V = -2 * np.gradient(K_xx, dx)
    mask = ~np.isnan(V)
    l1 = np.trapz(np.abs(V[mask]), dx=dx)
    l2 = np.sqrt(np.trapz(V[mask]**2, dx=dx))
    sir = l2 / l1 if l1 > 0 else 0
    return l1, sir

# --- Terminal Comparison ---
test_cases = [
    ("Indep [1, e, π]", [1.0, np.e, np.pi]),
    ("Dep [ln 2, ln 3, ln 6]", [np.log(2), np.log(3), np.log(6)]),
    ("Collision [1, 1+1e-9, 1+2e-9]", [1.0, 1.000000001, 1.000000002])
]

print(f"{'Case':<30} | {'L1 Mass':<12} | {'SIR':<12}")
print("-" * 60)
for name, z_set in test_cases:
    l1, sir = solve_marchenko_schanuel(z_set, L=25.0, N=600)
    print(f"{name:<30} | {l1:<12.6f} | {sir:<12.6f}")

#     (base) brendanlynch@Brendans-Laptop schanuel % python schanuel5.py
# Case                           | L1 Mass      | SIR         
# ------------------------------------------------------------
# Indep [1, e, π]                | 0.571074     | 0.235618    
# Dep [ln 2, ln 3, ln 6]         | 0.517244     | 0.236507    
# Collision [1, 1+1e-9, 1+2e-9]  | 0.505687     | 0.237160    
# (base) brendanlynch@Brendans-Laptop schanuel % 