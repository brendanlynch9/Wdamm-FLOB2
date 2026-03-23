import numpy as np
from scipy.special import comb
import time

# ---------------------------
# 1. Cluster Statistic
# ---------------------------
def cluster_statistic(eigs, L):
    """Compute the multi-point cluster statistic for a sliding window of length L."""
    n_pairs = comb(L, 2)
    total = 0.0
    count = 0
    for i in range(len(eigs) - L):
        cluster = eigs[i:i+L]
        for a in range(L):
            for b in range(a+1, L):
                gap = abs(cluster[a] - cluster[b])
                total += 1.0 - np.sinc(gap)**2
        count += 1
    return total / (count * n_pairs) if count > 0 else np.nan

# ---------------------------
# 2. GUE Bulk Simulation
# ---------------------------
def generate_gue_bulk(N, bulk_fraction=0.4, seed=None):
    """Generate the unfolded bulk eigenvalues of a GUE matrix."""
    if seed is not None:
        np.random.seed(seed)
    M = (np.random.randn(N, N) + 1j*np.random.randn(N, N)) / np.sqrt(2*N)
    H = (M + M.conj().T) / 2
    eigs = np.linalg.eigvalsh(H)
    
    # Extract central bulk
    mid = len(eigs)//2
    w = int(len(eigs)*bulk_fraction/2)
    bulk = eigs[mid-w:mid+w]
    
    # Unfold: normalize mean spacing to 1
    return bulk / np.mean(np.diff(bulk))

# ---------------------------
# 3. Holographic Residue
# ---------------------------
def holographic_residue(K_gue):
    """Compute the E8 projected constant and residue."""
    V_e8 = 15.0453
    filter_factor = np.pi**2 + 2*np.pi
    K_derived = V_e8 / filter_factor
    residue = K_gue / K_derived
    return K_derived, residue

# ---------------------------
# 4. Rank Sweep Test
# ---------------------------
def rank_sweep(z, ranks=[2, 4, 8, 16]):
    """Compute raw cluster statistic and holographic residue for multiple ranks."""
    J_a = 1.1461
    W_g = 1.0268
    results = []
    for L in ranks:
        raw_val = cluster_statistic(z, L)
        dim_red = (L / 2.0)**0.125  # E8 dimensional reduction
        residue = raw_val * (J_a * W_g / dim_red) * (15.045 / 14.52)  # normalization
        results.append((L, raw_val, residue))
    return results

# ---------------------------
# 5. Main Execution
# ---------------------------
if __name__ == "__main__":
    print("\n--- UNIVERSALITY & HOLOGRAPHIC NULL TEST ---\n")
    
    Ns = [400, 800, 1600, 3200]
    bulk_fraction = 0.4
    L = 4  # Fixed cluster rank for null test
    raw_vals = []

    for N in Ns:
        start = time.time()
        z = generate_gue_bulk(N, bulk_fraction)
        val = cluster_statistic(z, L)
        raw_vals.append(val)
        runtime = time.time() - start
        print(f"N={N:<5}  GUE={val:.6f}   runtime={runtime:.2f}s")
    
    # Compute holographic residue for last N
    K_derived, residue = holographic_residue(raw_vals[-1])
    print("\n--- HOLOGRAPHIC CLOSURE ---")
    print(f"Measured GUE Constant:  {raw_vals[-1]:.6f}")
    print(f"Derived E8 Projection: {K_derived:.6f}")
    print(f"Holographic Residue:   {residue:.6f} (Target: 1.0)")
    print("-" * 34)
    print(f"Precision: {100 - abs(1-residue)*100:.4f}%")

    # Rank sweep
    print("\n--- RANK SWEEP TEST ---")
    z = generate_gue_bulk(Ns[-1], bulk_fraction)
    sweep_results = rank_sweep(z)
    print(f"{'Rank L':<8} {'Raw Mean':<12} {'UFT-F Residue':<14}")
    for L, raw_val, residue in sweep_results:
        print(f"{L:<8} {raw_val:<12.6f} {residue:<14.6f}")

# (base) brendanlynch@Brendans-Laptop MontgomeryPairCorrelation % python falsifiable2.py

# --- UNIVERSALITY & HOLOGRAPHIC NULL TEST ---

# N=400    GUE=0.929625   runtime=0.03s
# N=800    GUE=0.929828   runtime=0.11s
# N=1600   GUE=0.936211   runtime=0.55s
# N=3200   GUE=0.926442   runtime=3.35s

# --- HOLOGRAPHIC CLOSURE ---
# Measured GUE Constant:  0.926442
# Derived E8 Projection: 0.931437
# Holographic Residue:   0.994637 (Target: 1.0)
# ----------------------------------
# Precision: 99.4637%

# --- RANK SWEEP TEST ---
# Rank L   Raw Mean     UFT-F Residue 
# 2        0.868893     1.059498      
# 4        0.927835     1.037471      
# 8        0.961732     0.986121      
# 16       0.980113     0.921560      
# (base) brendanlynch@Brendans-Laptop MontgomeryPairCorrelation % 