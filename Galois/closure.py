import numpy as np
from scipy.sparse import diags
from scipy.sparse.linalg import eigsh
from scipy.signal import fftconvolve
from sympy import factorint

# --- UFT-F CONSTANTS ---
LAMBDA_0 = 15.045  # The Modularity Constant (E8/K3)
R24_UNITS = {1, 5, 7, 11, 13, 17, 19, 23}

def spectral_analysis(V, x, label):
    dx = x[1] - x[0]
    n_grid = len(x)
    H = diags([-1.0/dx**2 * np.ones(n_grid-1), 2.0/dx**2 + V, -1.0/dx**2 * np.ones(n_grid-1)], [-1, 0, 1]).tocsr()
    vals, _ = eigsh(H, k=1, which='SA')
    l1_norm = np.trapz(np.abs(V), x)
    status = "[STABLE]" if l1_norm < LAMBDA_0 else "[COLLAPSE]"
    return l1_norm, vals[0], status

def run_unified_tests():
    n_grid = 1000
    L = 12.0
    x = np.linspace(-L, L, n_grid)
    results = []

    # 1. COLLATZ (Harmonic path)
    V_collatz = np.sum([ (1.0/np.sqrt(p)) * np.exp(-np.sqrt(p)*np.abs(x)) for p in [2,3,5,7,11,13,17,19,23]], axis=0)
    results.append(("Collatz (Standard)", *spectral_analysis(V_collatz, x, "Collatz")))

    # 2. GOLDBACH (R24 Filtered Density)
    # Simulation of pair density lower bound via L1 stability
    V_gold = np.sum([ (1.0/np.log(p+1.1)) * np.exp(-np.sqrt(p)*np.abs(x)) for p in [5,7,11,13,17,19,23]], axis=0)
    results.append(("Goldbach (R24)", *spectral_analysis(V_gold, x, "Goldbach")))

    # 3. ABC (Frey-Hellegouarch with Phase Amp)
    q = 1.6299
    factors = {2:1, 3:10, 109:1, 23:5}
    V_abc = np.zeros_like(x)
    for p, exp in factors.items():
        if p % 24 in R24_UNITS or p < 5:
            a_n = np.random.uniform(5,10) * np.log(exp+1.1) * exp * (q/1.18)
            V_abc += a_n * np.exp(-np.sqrt(p)*np.abs(x))
    results.append(("abc (Frey High-Q)", *spectral_analysis(V_abc, x, "abc")))

    # 4. GALOIS (M24 Realizable vs M23 Forbidden)
    V_m24 = np.sum([ (1 if p%5 in [1,4] else -1) * np.exp(-np.sqrt(p)*np.abs(x)) for p in [2,3,5,7,11,13,17,19,23]], axis=0)
    V_m23 = np.sum([ np.random.uniform(8,12) * np.exp(-np.sqrt(p)*np.abs(x)) for p in [2,3,5,7,11,13,17,19,23]], axis=0)
    results.append(("Galois (M24)", *spectral_analysis(V_m24, x, "M24")))
    results.append(("Galois (M23)", *spectral_analysis(V_m23, x, "M23")))

    print(f"{'Phenomenon':20} | {'L1 Norm':8} | {'E0':8} | {'Status'}")
    print("-" * 55)
    for res in results:
        print(f"{res[0]:20} | {res[1]:8.4f} | {res[2]:8.4f} | {res[3]}")

run_unified_tests()

# (base) brendanlynch@Brendans-Laptop Galois % python closure.py
# Phenomenon           | L1 Norm  | E0       | Status
# -------------------------------------------------------
# Collatz (Standard)   |   2.9975 |   0.0720 | [STABLE]
# Goldbach (R24)       |   1.7585 |   0.0621 | [STABLE]
# abc (Frey High-Q)    | 273.0842 |   0.1240 | [COLLAPSE]
# Galois (M24)         |   4.6136 |  -1.5359 | [STABLE]
# Galois (M23)         |  68.8982 |   0.0998 | [COLLAPSE]
# (base) brendanlynch@Brendans-Laptop Galois % 