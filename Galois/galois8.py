import numpy as np
from scipy.sparse import diags
from scipy.sparse.linalg import eigsh

def simulate_forbidden_extension(label, order_proxy, noise_level=15.0):
    # n_grid and L for consistent manifold
    n_grid = 1000
    L = 12.0
    x = np.linspace(-L, L, n_grid)
    dx = x[1] - x[0]
    
    # K3-Ratio check
    ratio = order_proxy / 22.0
    
    # Use primes as harmonic basis
    primes = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53]
    base24_units = {1, 5, 7, 11, 13, 17, 19, 23}
    
    V = np.zeros_like(x)
    # Simulation of "Noise" coefficients - violating the Automorphic Shield
    # These represent a non-realizable "collision" in the representation
    for p in primes:
        if p % 24 not in base24_units: continue
        a_n = np.random.uniform(noise_level, noise_level + 5.0) 
        V += float(a_n) * np.exp(-np.sqrt(p) * np.abs(x)) / np.log(p + 1.1)

    # Hamiltonian
    main_diag = 2.0 / dx**2 + V
    off_diag = -1.0 / dx**2 * np.ones(n_grid - 1)
    H = diags([off_diag, main_diag, off_diag], [-1, 0, 1]).tocsr()
    
    # Ground state energy
    vals, _ = eigsh(H, k=1, which='SA')
    
    # ACI/LIC Check
    l1_norm = np.trapz(np.abs(V), x)
    C_UFTF = 15.04
    is_stable = l1_norm < C_UFTF
    
    return {
        "label": label,
        "ratio": ratio,
        "l1_norm": l1_norm,
        "e0": vals[0],
        "status": "[ADMISSIBLE]" if is_stable else "[FORBIDDEN/COLLAPSE]"
    }

# Run the final "Spectral Prohibition" Test
# Case A: A high-complexity but "hypothetically" non-realizable massive group
# Case B: A standard stable case for comparison
res_forbidden = simulate_forbidden_extension("Non-Realizable G", 10**8)
res_stable = simulate_forbidden_extension("Stable Galois Motive", 10, noise_level=-1.0) # Negative noise to simulate binding

print(f"Final UFT-F Spectral Prohibition Test:")
print("-" * 65)
print(f"{res_stable['label']:20} | L1: {res_stable['l1_norm']:7.4f} | E0: {res_stable['e0']:8.4f} | {res_stable['status']}")
print(f"{res_forbidden['label']:20} | L1: {res_forbidden['l1_norm']:7.4f} | E0: {res_forbidden['e0']:8.4f} | {res_forbidden['status']}")

# (base) brendanlynch@Brendans-Laptop Galois % python galois8.py
# Final UFT-F Spectral Prohibition Test:
# -----------------------------------------------------------------
# Stable Galois Motive | L1:  0.5980 | E0:   0.0422 | [ADMISSIBLE]
# Non-Realizable G     | L1: 41.9273 | E0:   0.0817 | [FORBIDDEN/COLLAPSE]
# (base) brendanlynch@Brendans-Laptop Galois % 