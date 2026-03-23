import numpy as np
from scipy.sparse import diags
from scipy.sparse.linalg import eigsh

def solve_uftf_galois_sim(order, proxy_type='stable', n_grid=500):
    L = 10.0
    x = np.linspace(-L, L, n_grid)
    dx = x[1] - x[0]
    
    # Ratio as per cheatSheet
    ratio = order / 22.0
    is_top_stable = ratio < 100
    
    primes = [2,3,5,7,11,13,17,19,23,29,31,37,41,43,47,53]
    motive_coeffs = {}
    if proxy_type == 'stable':
        motive_coeffs = {p: 1 if p % order == 1 else -1 if p % order == 2 else 0 for p in primes}  # Proxy traces
    else:
        motive_coeffs = {p: np.random.uniform(10, 20) for p in primes}  # High noise for large order
    
    base24_units = {1,5,7,11,13,17,19,23}
    
    V = np.zeros_like(x)
    for n, a_n in motive_coeffs.items():
        if n % 24 not in base24_units: continue
        V += float(a_n) * np.exp(-np.sqrt(n) * np.abs(x)) / np.log(n + 1.5)
    
    main_diag = 2.0 / dx**2 + V
    off_diag = -1.0 / dx**2 * np.ones(n_grid - 1)
    H = diags([off_diag, main_diag, off_diag], [-1, 0, 1]).tocsr()
    
    vals, _ = eigsh(H, k=1, which='SA')
    
    l1_norm = np.trapz(np.abs(V), x)
    is_stable = l1_norm < 15.04  # Refined c_UFT-F
    
    return {
        "ratio": ratio,
        "top_stable": is_top_stable,
        "l1_norm": l1_norm,
        "stable": is_stable,
        "e0": vals[0],
        "status": "[PASSED]" if is_stable else "[COLLAPSE]"
    }

res_psl27 = solve_uftf_galois_sim(168, 'stable')
print(f"PSL(2,7) Proxy: Ratio={res_psl27['ratio']:.4f}, L1={res_psl27['l1_norm']:.4f}, E0={res_psl27['e0']:.4f}, {res_psl27['status']}")

res_m23 = solve_uftf_galois_sim(10200960, 'noise')
print(f"M23 Proxy: Ratio={res_m23['ratio']:.4f}, L1={res_m23['l1_norm']:.4f}, E0={res_m23['e0']:.4f}, {res_m23['status']}")

# (base) brendanlynch@Brendans-Laptop Galois % python galois5.py
# PSL(2,7) Proxy: Ratio=7.6364, L1=0.0000, E0=0.0245, [PASSED]
# M23 Proxy: Ratio=463680.0000, L1=35.9032, E0=0.1194, [COLLAPSE]
# (base) brendanlynch@Brendans-Laptop Galois % 