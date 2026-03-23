import numpy as np
from scipy.sparse import diags
from scipy.sparse.linalg import eigsh
from sympy import factorint

def abc_galois_proxy_fixed(a, b, c, n_grid=500):
    # Corrected Rad(abc) using sympy for robust factorization
    factors = factorint(a * b * c)
    ps = sorted(factors.keys())
    rad_abc = np.prod(ps)
    
    order_proxy = rad_abc
    ratio = order_proxy / 22.0
    
    L = 10.0
    x = np.linspace(-L, L, n_grid)
    dx = x[1] - x[0]
    
    q = np.log(c) / np.log(rad_abc)
    
    # UFT-F Quality Threshold (q* = 1.18)
    proxy_type = 'noise' if q > 1.18 else 'stable'
    
    motive_coeffs = {}
    for p in ps:
        # Base-24 Harmonic Filtering
        if p % 24 not in {1, 5, 7, 11, 13, 17, 19, 23}: continue
        
        # Grok's scaling: a_n amplified by exponent multiplicity
        exponent = factors[p]
        if proxy_type == 'stable':
            val = (1 if p % 3 == 1 else -1)
        else:
            # Power-weighted density (Informational Mass)
            val = np.random.uniform(5.0, 10.0)
            
        motive_coeffs[p] = val * np.log(exponent + 1.1)

    V = np.zeros_like(x)
    for p, a_n in motive_coeffs.items():
        V += float(a_n) * np.exp(-np.sqrt(p) * np.abs(x)) / np.log(p + 1.5)
    
    # Hamiltonian
    main_diag = 2.0 / dx**2 + V
    off_diag = -1.0 / dx**2 * np.ones(n_grid - 1)
    H = diags([off_diag, main_diag, off_diag], [-1, 0, 1]).tocsr()
    
    vals, _ = eigsh(H, k=1, which='SA')
    l1_norm = np.trapz(np.abs(V), x)
    
    # λ0 Threshold (c_UFT-F)
    is_stable = l1_norm < 15.04
    
    return f"abc({a},{b},{c}): q={q:.4f}, L1={l1_norm:.4f}, E0={vals[0]:.4f}, {'[PASSED]' if is_stable else '[COLLAPSE]'}"

print("UFT-F Refined ABC Spectral Analysis (Exponent-Weighted)")
print("-" * 65)
print(abc_galois_proxy_fixed(2, 6436341, 6436343)) # Frey-Hellegouarch
print(abc_galois_proxy_fixed(1, 8, 9))             # Small stable

# (base) brendanlynch@Brendans-Laptop Galois % python galois7.py
# UFT-F Refined ABC Spectral Analysis (Exponent-Weighted)
# -----------------------------------------------------------------
# abc(2,6436341,6436343): q=1.6299, L1=1.4685, E0=0.0804, [PASSED]
# abc(1,8,9): q=1.2263, L1=0.0000, E0=0.0245, [PASSED]
# (base) brendanlynch@Brendans-Laptop Galois % 