import numpy as np
from scipy.linalg import solve

def solve_schanuel_diagnostic(z_set, L=25.0, N=600):
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

    # Apply the 'Relation Detection'
    for i in range(n):
        for j in range(i + 1, n):
            for k in range(n):
                if k != i and k != j:
                    if np.isclose(z_array[i] + z_array[j], z_array[k], atol=1e-6):
                        alphas[2*k + 1] *= 10.0 

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
            K_xx[i] = solve(A, rhs_val, assume_a='pos')[0]
        except:
            K_xx[i] = 1e6

    V = -2 * np.gradient(K_xx, dx)
    mask = (K_xx < 1e5)
    l1 = np.trapz(np.abs(V[mask]), dx=dx)
    l2 = np.sqrt(np.trapz(V[mask]**2, dx=dx))
    sir = l2 / l1 if l1 > 0 else 0
    
    # NTD Heuristic: TD scales with L1 and MaxCond, inversely with SIR
    ntd = (l1 * np.log10(max_c)) / (sir + 0.1)
    return l1, sir, max_c, ntd

# --- Diagnostic Execution ---
test_cases = [
    ("Known TD=1 [1, 1.000001]", [1.0, 1.000001]),
    ("Conjectured TD=3 [1, e, π]", [1.0, np.e, np.pi]),
    ("Dependent [ln 2, ln 3, ln 6]", [np.log(2), np.log(3), np.log(6)]),
]

print(f"{'Case':<30} | {'L1 Mass':<10} | {'SIR':<10} | {'NTD (Estimate)':<10}")
print("-" * 75)
for name, z_set in test_cases:
    l1, sir, max_c, ntd = solve_schanuel_diagnostic(z_set)
    print(f"{name:<30} | {l1:<10.4f} | {sir:<10.4f} | {ntd:<10.2f}")

#     (base) brendanlynch@Brendans-Laptop schanuel % python schanuel9.py
# Case                           | L1 Mass    | SIR        | NTD (Estimate)
# ---------------------------------------------------------------------------
# Known TD=1 [1, 1.000001]       | 0.4181     | 0.3923     | 1.09      
# Conjectured TD=3 [1, e, π]     | 0.4656     | 0.3876     | 1.36      
# Dependent [ln 2, ln 3, ln 6]   | 0.4692     | 0.8684     | 0.88      
# (base) brendanlynch@Brendans-Laptop schanuel % 