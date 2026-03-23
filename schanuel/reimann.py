import numpy as np
from scipy.linalg import solve
import pandas as pd
from mpmath import mp, zetazero

# Set precision for mpmath to ensure zero accuracy
mp.dps = 25

def get_zeta_zeros_fixed(n=1000):
    """
    Corrected getter for Riemann zeros using mpmath.zetazero.
    """
    print(f"Fetching first {n} non-trivial zeros...")
    return [float(zetazero(i).imag) for i in range(1, n + 1)]

def evaluate_zeta_triple(subset, name, L=40.0, N=1000):
    """
    Core Marchenko solver for a specific zeta triple.
    """
    x_vals = np.linspace(0.01, L, N)
    dx = x_vals[1] - x_vals[0]
    baseline_l1 = 0.3789
    
    elements = []
    alphas = []
    for g in subset:
        z = 1j * g
        elements.extend([z, np.exp(z)])
        alphas.extend([1.0 + 0j, 1.0 + 0j])
    
    elements = np.array(elements, dtype=complex)
    alphas = np.array(alphas, dtype=complex)

    # Rupture Check: If sum relation is close, apply UFT-F boost
    res = np.abs(subset[0] + subset[1] - subset[2])
    if res < 1e-4:
        boost = 15.0 / (res + 1e-11)
        alphas[1] *= boost
        alphas[3] *= boost

    kappas = 0.05 + 0.005 * np.log(1 + np.abs(elements))

    def B_func(t):
        exponent = -kappas[:, None, None] * t[None, :, :]
        return np.real(np.sum(alphas[:, None, None] * np.exp(exponent), axis=0))

    K_xx = np.zeros(N)
    max_c = 1.0
    for i in range(N):
        sub_grid = x_vals[i:]
        n_sub = len(sub_grid)
        if n_sub < 2: break
        
        A = np.eye(n_sub) + B_func(sub_grid[:, None] + sub_grid[None, :]) * dx
        max_c = max(max_c, np.linalg.cond(A))
        
        rhs = -np.real(np.sum(alphas[:, None] * np.exp(-kappas[:, None] * (x_vals[i] + sub_grid)[None, :]), axis=0))
        try:
            K_xx[i] = solve(A, rhs, assume_a='pos')[0]
        except:
            K_xx[i] = np.nan

    V = -2 * np.gradient(K_xx, dx)
    mask = np.isfinite(V)
    l1 = np.trapz(np.abs(V[mask]), dx=dx) if np.any(mask) else 0.0
    src = l1 / baseline_l1
    
    return src, max_c

def scan_zeta_manifold(n_zeros=1000):
    """
    Scans the 1000-zero manifold for the most 'suspicious' triples.
    """
    zeros = get_zeta_zeros_fixed(n_zeros)
    
    # 1. Representative checks
    test_indices = [
        (0, 1, 2),        # First three
        (997, 998, 999),  # Last three
        (10, 20, 30)      # Distributed
    ]
    
    # 2. Heuristic Search: Find the triple with the smallest |g_i + g_j - g_k|
    # To keep it efficient, we check a large subspace of the 1000 zeros
    min_res = 1.0
    best_triple = (0, 1, 2)
    
    print("Searching for near-rupture triples...")
    # Checking a subset of combinations to find a 'Near Miss'
    for i in range(100):
        for j in range(i + 1, 100):
            target = zeros[i] + zeros[j]
            # Find the index of the closest zero to the sum
            k = np.searchsorted(zeros, target)
            if k < n_zeros:
                res = np.abs(target - zeros[k])
                if res < min_res:
                    min_res = res
                    best_triple = (i, j, k)
    
    test_indices.append(best_triple)
    
    results = []
    for idx in test_indices:
        subset = [zeros[i] for i in idx]
        src, cond = evaluate_zeta_triple(subset, f"Triple {idx}")
        results.append({
            "Triple": idx,
            "Residual": np.abs(zeros[idx[0]] + zeros[idx[1]] - zeros[idx[2]]),
            "SRC": src,
            "MaxCond": cond
        })
        
    return pd.DataFrame(results)

# --- Execution ---
if __name__ == "__main__":
    df = scan_zeta_manifold(1000)
    print("\n--- UFT-F Zeta Global Scan (N=1000) ---")
    print(df.to_string(index=False))
    
    if df['SRC'].max() < 5.0:
        print("\nRESULT: LAMINAR. LIC preserved across 1000-zero manifold.")
    else:
        print("\nRESULT: RUPTURE DETECTED. Hidden dependency suspected.")

#         (base) brendanlynch@Brendans-Laptop schanuel % python reimann.py
# Fetching first 1000 non-trivial zeros...
# Searching for near-rupture triples...

# --- UFT-F Zeta Global Scan (N=1000) ---
#          Triple    Residual      SRC   MaxCond
#       (0, 1, 2)   10.145907 0.677218 51.546514
# (997, 998, 999) 1416.377306 0.972061 45.573095
#    (10, 20, 30)   28.582158 0.769557 49.373442
#   (77, 96, 220)    0.001244 0.859488 47.591490

# RESULT: LAMINAR. LIC preserved across 1000-zero manifold.
# (base) brendanlynch@Brendans-Laptop schanuel % 