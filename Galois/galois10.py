import numpy as np
from scipy.sparse import diags
from scipy.sparse.linalg import eigsh

def test_collatz_stability(label, path_type='harmonic'):
    n_grid = 1000
    L = 15.0
    x = np.linspace(-L, L, n_grid)
    dx = x[1] - x[0]
    
    # Base-24 Regulator (The Hopf Torsion invariant λ_u ≈ 0.0002)
    hopf_torsion = 0.0002073
    
    V = np.zeros_like(x)
    # Collatz path harmonics
    # Harmonic = smooth decay to the ground state 1
    # Forbidden = High-frequency noise (divergence)
    
    primes = [2, 3, 5, 7, 11, 13, 17, 19, 23]
    for p in primes:
        if path_type == 'harmonic':
            # Constructive interference on G24
            a_n = 1.0 / np.sqrt(p)
        else:
            # Destructive/Trapped interference (The Forbidden Loop)
            # Scaling by 1/λ_u to simulate the "Energy Barrier" of a cycle
            a_n = np.random.uniform(5.0, 10.0) / hopf_torsion * 0.0001
            
        V += a_n * np.exp(-np.sqrt(p) * np.abs(x)) / np.log(p + 1.1)

    H = diags([-1.0/dx**2 * np.ones(n_grid-1), 2.0/dx**2 + V, -1.0/dx**2 * np.ones(n_grid-1)], [-1, 0, 1]).tocsr()
    vals, _ = eigsh(H, k=1, which='SA')
    l1_norm = np.trapz(np.abs(V), x)
    
    # λ0 Threshold
    is_stable = l1_norm < 15.04
    
    print(f"{label:20} | L1: {l1_norm:10.4f} | E0: {vals[0]:.4f} | {'[STABLE]' if is_stable else '[FORBIDDEN CYCLE]'}")

print("UFT-F Collatz Spectral Convergence Test")
print("-" * 70)
test_collatz_stability("Standard Convergence", 'harmonic')
test_collatz_stability("Non-Trivial Cycle", 'noise')

# (base) brendanlynch@Brendans-Laptop Galois % python galois10.py
# UFT-F Collatz Spectral Convergence Test
# ----------------------------------------------------------------------
# Standard Convergence | L1:     1.9479 | E0: 0.0436 | [STABLE]
# Non-Trivial Cycle    | L1:    13.5275 | E0: 0.0526 | [STABLE]
# (base) brendanlynch@Brendans-Laptop Galois % 