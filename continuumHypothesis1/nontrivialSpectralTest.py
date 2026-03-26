import numpy as np
from scipy.linalg import eigvalsh

def uftf_nontrivial_test():
    """
    UFT-F Nontrivial Spectral Test: 
    Introducing Prime-Gap Interference to break separability.
    If the system remains 'Near-Rank-1', the Geometric Lock is verified.
    """
    primes = []
    n = 2
    while len(primes) < 109:
        if all(n % i != 0 for i in range(2, int(n**0.5) + 1)):
            primes.append(n)
        n += 1
    
    size = len(primes)
    M = np.zeros((size, size))
    
    for i in range(size):
        for j in range(size):
            inf_i = 360 / primes[i]
            inf_j = 360 / primes[j]
            
            # NON-SEPARABLE INTERACTION:
            # We add a phase interference term based on the gap between primes
            # This breaks the v*v^T property.
            gap = abs(primes[i] - primes[j])
            interference = np.exp(-gap / 599) # Scaled by the Lock Prime
            
            M[i, j] = ((inf_i * inf_j) / 120) * interference
            
    eigenvalues = eigvalsh(M)
    max_ev = np.max(eigenvalues)
    trace = np.trace(M)
    
    # Information Centrality: How much of the manifold is 'locked' in the first mode?
    centrality = max_ev / trace
    
    print(f"--- UFT-F NONTRIVIAL SPECTRAL TEST ---")
    print(f"Matrix Dimension: {size}")
    print(f"Symmetry Ratio (Max/Trace): {centrality:.6f}")
    print(f"Energy in Secondary Modes:  {trace - max_ev:.6f}")
    print(f"Lock Status: {'RIGID' if centrality > 0.99 else 'FLUID'}")

if __name__ == "__main__":
    uftf_nontrivial_test()

#     (base) brendanlynch@Brendans-Laptop continuumHypothesis % python nontrivialSpectralTest.py
# --- UFT-F NONTRIVIAL SPECTRAL TEST ---
# Matrix Dimension: 109
# Symmetry Ratio (Max/Trace): 0.993056
# Energy in Secondary Modes:  3.389992
# Lock Status: RIGID
# (base) brendanlynch@Brendans-Laptop continuumHypothesis % 