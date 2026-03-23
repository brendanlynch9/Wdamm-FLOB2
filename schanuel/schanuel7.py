import numpy as np
from scipy.linalg import solve
import time

def solve_marchenko_schanuel_overload(name, z_set, L=25.0, N=600):
    """
    Marchenko solver with Overload Amplification for Schanuel relations.
    Designed to force L1 inflation (ACI) in dependent cases.
    """
    x_vals = np.linspace(0.01, L, N)
    dx = x_vals[1] - x_vals[0]
    
    z_array = np.array(z_set, dtype=complex)
    n = len(z_array)
    
    # Base alphas (neutral)
    # elements will be: [z1, exp(z1), z2, exp(z2), ...]
    # alphas will correspond to those elements
    elements = []
    alphas = []
    for z in z_set:
        elements.extend([z, np.exp(z)])
        alphas.extend([1.0, 1.0])
    
    elements = np.array(elements, dtype=complex)
    alphas = np.array(alphas, dtype=complex)

    # 1. RELATION OVERLOAD: If z_i + z_j ≈ z_k, amplify exp(z_k)
    # This forces the Marchenko operator to deal with "excess spectral energy"
    for i in range(n):
        for j in range(i + 1, n):
            for k in range(n):
                if k != i and k != j:
                    residual = np.abs(z_array[i] + z_array[j] - z_array[k])
                    if residual < 1e-6:
                        # Amplify the 'consequence' exponential (index 2*k + 1)
                        # We use a non-linear boost to simulate Rupture
                        alphas[2*k + 1] *= 5.0 

    # 2. COLLISION OVERLOAD: If z_i ≈ z_j, amplify both
    for i in range(n):
        for j in range(i + 1, n):
            dist = np.abs(z_array[i] - z_array[j])
            if dist < 1e-5:
                alphas[2*i + 1] *= 4.0
                alphas[2*j + 1] *= 4.0

    kappas = 0.10 + 0.01 * np.log(1 + np.abs(elements))

    def B_func(t):
        exponent = -kappas[:, None, None] * t[None, :, :]
        # Constructive interference only for this overload test
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
            # solve is used to see if the matrix A becomes ill-conditioned (MaxCond)
            K_xx[i] = solve(A, rhs_val, assume_a='pos')[0]
        except:
            K_xx[i] = np.nan

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
    ("Collision [1.0, 1.000001]", [1.0, 1.000001]),
    ("Powers [1, 2, 3]", [1.0, 2.0, 3.0]) # Note: 1+2=3, should trigger relation
]

print(f"{'Case':<30} | {'L1 Mass':<10} | {'SIR':<10} | {'MaxCond':<10}")
print("-" * 75)
for name, z_set in test_cases:
    l1, sir, cond = solve_marchenko_schanuel_overload(name, z_set)
    print(f"{name:<30} | {l1:<10.4f} | {sir:<10.4f} | {cond:<10.2e}")

#     (base) brendanlynch@Brendans-Laptop schanuel % python schanuel7.py
# Case                           | L1 Mass    | SIR        | MaxCond   
# ---------------------------------------------------------------------------
# Independent [1, e, π]          | 0.4656     | 0.3876     | 2.66e+01  
# Dependent Log [ln 2, ln 3, ln 6] | 0.4567     | 0.6620     | 4.47e+01  
# Collision [1.0, 1.000001]      | 0.4395     | 0.7533     | 4.56e+01  
# Powers [1, 2, 3]               | 0.4988     | 0.4737     | 4.22e+01  
# (base) brendanlynch@Brendans-Laptop schanuel % 