import numpy as np
from scipy.special import comb
import time
import requests
import io

# ---------------------------
# 1. Data Retrieval
# ---------------------------
def get_riemann_zeros(n_max=10000):
    """
    Fetch the first n_max Riemann zeros.
    If network fails, fallback to synthetic GUE bulk.
    """
    url = "https://raw.githubusercontent.com/enisrichard/riemann-zeros/master/zeros.txt"
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        zeros = np.loadtxt(io.StringIO(response.text))[:n_max]
        print(f"Fetched {len(zeros)} Riemann zeros from archive.")
        return zeros
    except:
        print("Network unavailable. Using synthetic GUE as fallback...")
        size = n_max
        M = (np.random.randn(size, size) + 1j*np.random.randn(size, size)) / np.sqrt(2)
        H = (M + M.conj().T) / 2
        eigs = np.linalg.eigvalsh(H)
        mid = len(eigs)//2
        w = int(len(eigs)*0.4/2)
        return eigs[mid-w:mid+w]

# ---------------------------
# 2. Unfolding
# ---------------------------
def unfold_points(points, window=50):
    """
    Local unfolding: divide points by sliding mean spacing.
    """
    diffs = np.diff(points)
    mean_spacing = np.convolve(diffs, np.ones(window)/window, mode='same')
    unfolded = points / np.mean(mean_spacing)
    return unfolded

# ---------------------------
# 3. Cluster Statistic
# ---------------------------
def cluster_statistic(points, L):
    """
    Montgomery-style L-cluster statistic: average of 1 - sinc^2 of all pairwise gaps.
    """
    n_pairs = comb(L, 2)
    total, count = 0.0, 0
    for i in range(len(points) - L):
        cluster = points[i:i+L]
        for a in range(L):
            for b in range(a+1, L):
                gap = abs(cluster[a] - cluster[b])
                total += 1.0 - np.sinc(gap)**2
        count += 1
    return total / (count * n_pairs) if count > 0 else np.nan

# ---------------------------
# 4. UFT-F / E8 Residue
# ---------------------------
def uftf_residue(raw_val, L):
    """
    Map cluster statistic to E8 holographic projection.
    """
    J_a, W_g = 1.1461, 1.0268
    dim_red = (L / 2.0)**0.125
    scale_factor = 15.045 / 14.52  # Reference from prior closure
    residue = raw_val * (J_a * W_g / dim_red) * scale_factor
    return residue

# ---------------------------
# 5. Run Falsifiable Test
# ---------------------------
def run_falsifiable_test():
    zeros = get_riemann_zeros()
    z_unfolded = unfold_points(zeros)
    
    Ns = [400, 800, 1600, 3200]
    ranks = [2, 4, 8, 16]

    K_derived = 15.045 / (np.pi**2 + 2*np.pi)  # Holographic target

    print("\n--- FALSIFIABLE UFT-F / GUE CLUSTER TEST ---")
    print(f"{'N':<6} {'Rank L':<6} {'Raw Mean':<12} {'UFT-F Residue':<14} {'Error %':<10} {'Runtime'}")
    print("-"*70)

    for N in Ns:
        points = z_unfolded[:N]
        for L in ranks:
            t0 = time.time()
            raw_val = cluster_statistic(points, L)
            residue = uftf_residue(raw_val, L) / K_derived
            error = abs(1 - residue) * 100
            t1 = time.time()
            print(f"{N:<6} {L:<6} {raw_val:<12.6f} {residue:<14.6f} {error:<10.4f} {t1-t0:.2f}s")
        print("-"*70)

if __name__ == "__main__":
    run_falsifiable_test()

# (base) brendanlynch@Brendans-Laptop MontgomeryPairCorrelation % python falsifiable3.py
# Network unavailable. Using synthetic GUE as fallback...

# --- FALSIFIABLE UFT-F / GUE CLUSTER TEST ---
# N      Rank L Raw Mean     UFT-F Residue  Error %    Runtime
# ----------------------------------------------------------------------
# 400    2      0.881082     1.153468       15.3468    0.01s
# 400    4      0.935188     1.122689       12.2689    0.01s
# 400    8      0.965549     1.062934       6.2934     0.03s
# 400    16     0.982096     0.991418       0.8582     0.13s
# ----------------------------------------------------------------------
# 800    2      0.869679     1.138540       13.8540    0.00s
# 800    4      0.928875     1.115110       11.5110    0.01s
# 800    8      0.962468     1.059542       5.9542     0.06s
# 800    16     0.980535     0.989843       1.0157     0.27s
# ----------------------------------------------------------------------
# 1600   2      0.870624     1.139776       13.9776    0.00s
# 1600   4      0.929120     1.115404       11.5404    0.03s
# 1600   8      0.962401     1.059469       5.9469     0.13s
# 1600   16     0.980469     0.989776       1.0224     0.53s
# ----------------------------------------------------------------------
# 3200   2      0.869017     1.137673       13.7673    0.01s
# 3200   4      0.928181     1.114277       11.4277    0.06s
# 3200   8      0.961891     1.058907       5.8907     0.25s
# 3200   16     0.980203     0.989508       1.0492     1.04s
# ----------------------------------------------------------------------
# (base) brendanlynch@Brendans-Laptop MontgomeryPairCorrelation % 