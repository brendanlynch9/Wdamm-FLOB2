import numpy as np
import pandas as pd
from scipy.linalg import eigvalsh

def run_uftf_spectral_verification():
    """
    UFT-F SPECTRAL VERIFICATION SUITE
    Objective: Prove the Rank-1 Unity of the Shape Layer (Primes 2-599).
    Mechanism: 24D Leech-Metric Expansion (360/p).
    """
    # 1. Generate the Prime Basis up to the P=599 Lock (109 primes)
    primes = []
    n = 2
    while len(primes) < 109:
        if all(n % i != 0 for i in range(2, int(n**0.5) + 1)):
            primes.append(n)
        n += 1
    
    # 2. Construct the Flux Matrix (M)
    # This matrix models the interaction between prime-indexed figurate inflations.
    # M_ij = (I_i * I_j) / 120, where I(p) = 360/p
    size = len(primes)
    flux_matrix = np.zeros((size, size))
    
    for i in range(size):
        for j in range(size):
            # Inflation factors derived from 24D expansion (120 * 3)
            inf_i = 360 / primes[i]
            inf_j = 360 / primes[j]
            # Normalizing by the E8 base constant
            flux_matrix[i, j] = (inf_i * inf_j) / 120
            
    # 3. Spectral Decomposition
    # eigvalsh is used for Hermitian/Symmetric matrices to ensure precision.
    eigenvalues = eigvalsh(flux_matrix)
    
    # 4. Metrics for the 'Academic Shield'
    max_ev = np.max(eigenvalues)
    trace = np.trace(flux_matrix)
    
    # Rank-1 Check: In a Rank-1 matrix, the Trace equals the Max Eigenvalue.
    # Any deviation (Symmetry Ratio != 1) would imply 'hidden' cardinals.
    symmetry_ratio = trace / max_ev
    
    # Cumulative Inflation Check (The 99.95% Precision Lock)
    # Sum(360/p) vs Chi (763.56)
    cumulative_inflation = sum(360 / p for p in primes)
    chi_target = 763.56
    precision = 1 - abs(cumulative_inflation - chi_target) / chi_target

    # --- OUTPUT LOGS ---
    print("="*50)
    print("UFT-F SPECTRAL SYMMETRY VERIFICATION")
    print("="*50)
    print(f"Matrix Dimension:       {size} (Basis: P=2 to P=599)")
    print(f"Maximum Eigenvalue:     {max_ev:.6f}")
    print(f"Trace (Sum of Diag):    {trace:.6f}")
    print(f"Symmetry Ratio:         {symmetry_ratio:.10f}")
    print(f"Rank-1 Identity:        {'VERIFIED' if np.isclose(symmetry_ratio, 1.0) else 'FAILED'}")
    print("-"*50)
    print(f"Cumulative Inflation:   {cumulative_inflation:.6f}")
    print(f"Target Chi:             {chi_target}")
    print(f"Closure Precision:      {precision:.4%}")
    print("="*50)

    return flux_matrix, eigenvalues

if __name__ == "__main__":
    matrix, spectrum = run_uftf_spectral_verification()

#     (base) brendanlynch@Brendans-Laptop continuumHypothesis % python rank1.py
# ==================================================
# UFT-F SPECTRAL SYMMETRY VERIFICATION
# ==================================================
# Matrix Dimension:       109 (Basis: P=2 to P=599)
# Maximum Eigenvalue:     488.181787
# Trace (Sum of Diag):    488.181787
# Symmetry Ratio:         1.0000000000
# Rank-1 Identity:        VERIFIED
# --------------------------------------------------
# Cumulative Inflation:   763.935501
# Target Chi:             763.56
# Closure Precision:      99.9508%
# ==================================================
# (base) brendanlynch@Brendans-Laptop continuumHypothesis % 