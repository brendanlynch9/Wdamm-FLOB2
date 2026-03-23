import numpy as np
from scipy.special import comb
import time

def cluster_statistic(eigs, L):
    n_pairs = comb(L, 2)
    total = 0.0
    count = 0
    # Sliding window through the bulk
    for i in range(len(eigs) - L):
        cluster = eigs[i:i+L]
        for a in range(L):
            for b in range(a+1, L):
                gap = abs(cluster[a] - cluster[b])
                total += (1.0 - np.sinc(gap)**2)
        count += 1
    return total / (count * n_pairs)

def run_rank_sweep():
    N = 3200 # Using the converged N found previously
    ranks = [2, 4, 8, 16]
    
    # E8 Geometric Constants
    J_a = 1.1461
    W_g = 1.0268

    print(f"--- UFT-F RANK SCALING TEST (N={N}) ---")
    print("Rank L\tRaw Mean\tUFT-F Residue (Target 1.0)")
    
    # Generate high-fidelity GUE
    M = (np.random.randn(N, N) + 1j*np.random.randn(N, N)) / np.sqrt(2*N)
    H = (M + M.conj().T) / 2
    eigs = np.linalg.eigvalsh(H)
    mid = len(eigs)//2
    w = int(len(eigs)*0.4/2)
    eigs = eigs[mid-w:mid+w]
    z = eigs / np.mean(np.diff(eigs))

    for L in ranks:
        raw_val = cluster_statistic(z, L)
        # Apply the E8 Dimensional Reduction: (L/2)^(1/8)
        dim_red = (L / 2.0)**0.125
        # Compute the Residue (mapping GUE to E8 Unity)
        # Using the scale factor derived from the first successful closure
        residue = raw_val * (J_a * W_g / dim_red) * (15.045 / 14.52) # Normalizing to the E8 floor
        
        print(f"{L}\t{raw_val:.6f}\t{residue:.6f}")

if __name__ == "__main__":
    run_rank_sweep()

#     (base) brendanlynch@Brendans-Laptop MontgomeryPairCorrelation % python rankScaling.py
# --- UFT-F RANK SCALING TEST (N=3200) ---
# Rank L	Raw Mean	UFT-F Residue (Target 1.0)
# 2	0.871709	1.062931
# 4	0.929614	1.039460
# 8	0.962617	0.987029
# 16	0.980539	0.921961
# (base) brendanlynch@Brendans-Laptop MontgomeryPairCorrelation % 