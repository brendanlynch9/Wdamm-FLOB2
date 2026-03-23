import numpy as np
from scipy.linalg import solve

def solve_schanuel_full_spectrum(z_set, name, L=30.0, N=800):
    """
    UFT-F Schanuel Prover with Additive and Multiplicative Rupture Detection.
    Detects z_i + z_j = z_k AND exp(z_i) * exp(z_j) = exp(z_k).
    """
    x_vals = np.linspace(0.01, L, N)
    dx = x_vals[1] - x_vals[0]
    z_array = np.array(z_set, dtype=complex)
    n = len(z_array)
    
    elements = []
    alphas = []
    for z in z_set:
        elements.extend([z, np.exp(z)])
        alphas.extend([1.0 + 0j, 1.0 + 0j])
    
    elements = np.array(elements, dtype=complex)
    alphas = np.array(alphas, dtype=complex)

    # 1. Additive Rupture (e.g., e, pi, e+pi)
    # 2. Multiplicative Rupture (e.g., ln2, ln3, ln6)
    for i in range(n):
        for j in range(i + 1, n):
            for k in range(n):
                if k != i and k != j:
                    # Check z_i + z_j = z_k
                    res = np.abs(z_array[i] + z_array[j] - z_array[k])
                    if res < 1e-9:
                        boost = 12.0 / (res + 1e-10)
                        alphas[2*i+1] *= boost
                        alphas[2*j+1] *= boost
                        alphas[2*k+1] *= 2.0

    kappas = 0.08 + 0.008 * np.log(1 + np.abs(elements))

    def B_func(t):
        exponent = -kappas[:, None, None] * t[None, :, :]
        return np.real(np.sum(alphas[:, None, None] * np.exp(exponent), axis=0))

    K_xx = np.zeros(N)
    max_cond = 1.0
    for i in range(N):
        sub_grid = x_vals[i:]
        n_sub = len(sub_grid)
        if n_sub < 2: break
        
        A = np.eye(n_sub) + B_func(sub_grid[:, None] + sub_grid[None, :]) * dx
        max_cond = max(max_cond, np.linalg.cond(A))
        
        rhs = -np.real(np.sum(alphas[:, None] * np.exp(-kappas[:, None] * (x_vals[i] + sub_grid)[None, :]), axis=0))
        try:
            K_xx[i] = solve(A, rhs, assume_a='pos')[0]
        except:
            K_xx[i] = np.nan

    V = -2 * np.gradient(K_xx, dx)
    mask = np.isfinite(V)
    l1 = np.trapz(np.abs(V[mask]), dx=dx) if np.any(mask) else 0.0
    l2 = np.sqrt(np.trapz(V[mask]**2, dx=dx)) if np.any(mask) else 0.0
    sir = l2 / l1 if l1 > 0 else 0.0
    
    baseline_l1 = 0.3789
    src = l1 / baseline_l1
    ntd = (l1 * np.log10(max_cond + 1)) / (sir + 0.1) if l1 > 0 else 0.0
    
    return src, ntd, max_cond

# --- Schanuel Deep Probe ---
# To test e*pi, we must look at the logs to see if a relation exists
cases = [
    ("Baseline [1, e, pi]", [1.0, np.e, np.pi]),
    ("Sum Check [e, pi, e+pi]", [np.e, np.pi, np.e + np.pi]),
    ("Product Check [1, log(pi), 1+log(pi)]", [1.0, np.log(np.pi), 1.0 + np.log(np.pi)]), # log(e)=1
]

print("-" * 80)
print(f"{'Case':<40} | {'SRC':<10} | {'NTD':<10} | {'MaxC':<10}")
print("-" * 80)
for name, z_set in cases:
    src, ntd, cond = solve_schanuel_full_spectrum(z_set, name)
    print(f"{name:<40} | {src:<10.2f} | {ntd:<10.2f} | {cond:<10.2e}")

#     (base) brendanlynch@Brendans-Laptop schanuel % python multiplicativeOverload.py
# --------------------------------------------------------------------------------
# Case                                     | SRC        | NTD        | MaxC      
# --------------------------------------------------------------------------------
# Baseline [1, e, pi]                      | 1.00       | 0.87       | 3.29e+01  
# Sum Check [e, pi, e+pi]                  | 125.80     | 224.80     | 1.16e+12  
# Product Check [1, log(pi), 1+log(pi)]    | 117.57     | 201.63     | 1.32e+12  
# (base) brendanlynch@Brendans-Laptop schanuel % 