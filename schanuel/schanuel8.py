import numpy as np
from scipy.linalg import solve
import time

def solve_marchenko_schanuel_heat(name, z_set, L=25.0, N=600):
    """
    Final 'Heat Death' solver to check for MaxCond explosion 
    under high-density dependency.
    """
    x_vals = np.linspace(0.01, L, N)
    dx = x_vals[1] - x_vals[0]
    
    z_array = np.array(z_set, dtype=complex)
    n = len(z_array)
    
    elements = []
    alphas = []
    for z in z_set:
        elements.extend([z, np.exp(z)])
        alphas.extend([1.0, 1.0])
    
    elements = np.array(elements, dtype=complex)
    alphas = np.array(alphas, dtype=complex)

    # High-Density Relation Check
    for i in range(n):
        for j in range(i + 1, n):
            for k in range(n):
                if k != i and k != j:
                    if np.isclose(z_array[i] + z_array[j], z_array[k], atol=1e-6):
                        alphas[2*k + 1] *= 10.0 # Aggressive Overload

    kappas = 0.10 + 0.01 * np.log(1 + np.abs(elements))

    def B_func(t):
        exponent = -kappas[:, None, None] * t[None, :, :]
        return np.real(np.sum(np.abs(alphas[:, None, None]) * np.exp(exponent), axis=0))

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
        
        rhs_val = -np.real(np.sum(np.abs(alphas[:, None]) * np.exp(-kappas[:, None] * (x_vals[i] + sub_grid)[None, :]), axis=0))
        
        try:
            # We use the standard solve to trigger error on singularity
            K_xx[i] = solve(A, rhs_val, assume_a='pos')[0]
        except:
            K_xx[i] = 1e6 # Singularity proxy

    V = -2 * np.gradient(K_xx, dx)
    mask = (K_xx < 1e5) # Mask out singularities
    l1 = np.trapz(np.abs(V[mask]), dx=dx) if np.any(mask) else 0
    l2 = np.sqrt(np.trapz(V[mask]**2, dx=dx)) if np.any(mask) else 0
    sir = l2 / l1 if l1 > 0 else 0
    
    return l1, sir, max_c

# --- The "Heat Death" Test ---
test_cases = [
    ("Independent [1..5]", [1.1, 2.2, 3.3, 4.4, 5.5]),
    ("Dependent [ln 2, 3, 5, 6, 30]", [np.log(2), np.log(3), np.log(5), np.log(6), np.log(30)]), # 2+3=6, 5+6=30
    ("Full Relation [1, 2, 3, 4, 7]", [1.0, 2.0, 3.0, 4.0, 7.0]) # 1+2=3, 3+4=7
]

print(f"{'Case':<30} | {'L1 Mass':<10} | {'SIR':<10} | {'MaxCond':<10}")
print("-" * 75)
for name, z_set in test_cases:
    l1, sir, cond = solve_marchenko_schanuel_heat(name, z_set)
    print(f"{name:<30} | {l1:<10.4f} | {sir:<10.4f} | {cond:<10.2e}")

#     (base) brendanlynch@Brendans-Laptop schanuel % python schanuel8.py
# Case                           | L1 Mass    | SIR        | MaxCond   
# ---------------------------------------------------------------------------
# Independent [1..5]             | 0.8083     | 0.9221     | 4.26e+02  
# Dependent [ln 2, 3, 5, 6, 30]  | 0.5538     | 1.0733     | 1.16e+02  
# Full Relation [1, 2, 3, 4, 7]  | 0.7669     | 0.5756     | 1.35e+02  
# (base) brendanlynch@Brendans-Laptop schanuel % 