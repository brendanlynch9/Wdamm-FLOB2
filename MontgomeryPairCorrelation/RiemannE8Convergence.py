import numpy as np
from scipy.special import comb
import requests
import io
import time

# ---------------------------
# 1. Data Retrieval
# ---------------------------
def get_riemann_zeros(n_max=10000):
    """
    Fetch the first n_max Riemann zeros from a reliable online source.
    If network fails, generate synthetic GUE ensemble as fallback.
    """
    url = "https://raw.githubusercontent.com/enisrichard/riemann-zeros/master/zeros.txt"
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        zeros = np.loadtxt(io.StringIO(response.text))[:n_max]
        print(f"Fetched {len(zeros)} Riemann zeros from online archive.")
        return zeros
    except:
        print("Network unavailable. Using synthetic GUE as fallback...")
        size = n_max
        mat = (np.random.randn(size, size) + 1j*np.random.randn(size, size)) / np.sqrt(2)
        h_mat = (mat + mat.conj().T) / 2
        eigs = np.linalg.eigvalsh(h_mat)
        # Take central bulk 40%
        mid = len(eigs)//2
        w = int(len(eigs)*0.4/2)
        return eigs[mid-w:mid+w]

# ---------------------------
# 2. Cluster Statistic
# ---------------------------
def cluster_statistic(points, L):
    """
    Montgomery-style L-cluster statistic: average of 1 - sinc^2 of all pairwise gaps in sliding L-window.
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
# 3. Unfolding
# ---------------------------
def unfold_points(points, window=50):
    """
    Local unfolding using sliding window mean spacing.
    """
    diffs = np.diff(points)
    mean_spacing = np.convolve(diffs, np.ones(window)/window, mode='same')
    unfolded = points / np.mean(mean_spacing)
    return unfolded

# ---------------------------
# 4. E8 Holographic Residue
# ---------------------------
def e8_residue(raw_val, L):
    """
    Map cluster statistic to E8 holographic projection.
    """
    J_a, W_g = 1.1461, 1.0268
    dim_red = (L / 2.0)**0.125
    V_e8 = 15.045
    # Reference scale from prior closure
    scale_factor = 15.045 / 14.52
    residue = (raw_val * (J_a * W_g / dim_red) * scale_factor)
    return residue

# ---------------------------
# 5. Run Falsifiable Test
# ---------------------------
def run_test():
    zeros = get_riemann_zeros()
    z_unfolded = unfold_points(zeros)

    print("\n--- RIEMANN / GUE CLUSTER vs E8 HOLOGRAPHIC PROJECTION ---")
    print(f"{'N':<6} {'Rank L':<6} {'Raw Mean':<12} {'E8 Residue':<14} {'Error %'}")
    print("-"*60)

    Ns = [400, 800, 1600, 3200]
    ranks = [2, 4, 8, 16]

    K_derived = 15.045 / (np.pi**2 + 2*np.pi)  # Holographic target

    for N in Ns:
        points = z_unfolded[:N]
        for L in ranks:
            t0 = time.time()
            raw_val = cluster_statistic(points, L)
            residue = e8_residue(raw_val, L) / K_derived
            error = abs(1 - residue)*100
            t1 = time.time()
            print(f"{N:<6} {L:<6} {raw_val:<12.6f} {residue:<14.6f} {error:.4f}%   runtime={t1-t0:.2f}s")
        print("-"*60)

if __name__ == "__main__":
    run_test()

# (base) brendanlynch@Brendans-Laptop MontgomeryPairCorrelation % python RiemannE8Convergence.py
# Network unavailable. Using synthetic GUE as fallback...

# --- RIEMANN / GUE CLUSTER vs E8 HOLOGRAPHIC PROJECTION ---
# N      Rank L Raw Mean     E8 Residue     Error %
# ------------------------------------------------------------
# 400    2      0.875503     1.146164       14.6164%   runtime=0.00s
# 400    4      0.931554     1.118327       11.8327%   runtime=0.01s
# 400    8      0.963773     1.060978       6.0978%   runtime=0.03s
# 400    16     0.981205     0.990519       0.9481%   runtime=0.13s
# ------------------------------------------------------------
# 800    2      0.875320     1.145926       14.5926%   runtime=0.00s
# 800    4      0.931622     1.118408       11.8408%   runtime=0.01s
# 800    8      0.963682     1.060878       6.0878%   runtime=0.06s
# 800    16     0.981127     0.990441       0.9559%   runtime=0.27s
# ------------------------------------------------------------
# 1600   2      0.874181     1.144434       14.4434%   runtime=0.01s
# 1600   4      0.930822     1.117447       11.7447%   runtime=0.03s
# 1600   8      0.963227     1.060377       6.0377%   runtime=0.13s
# 1600   16     0.980863     0.990174       0.9826%   runtime=0.55s
# ------------------------------------------------------------
# 3200   2      0.869861     1.138779       13.8779%   runtime=0.01s
# 3200   4      0.928440     1.114588       11.4588%   runtime=0.06s
# 3200   8      0.961951     1.058972       5.8972%   runtime=0.25s
# 3200   16     0.980213     0.989517       1.0483%   runtime=1.07s
# ------------------------------------------------------------
# (base) brendanlynch@Brendans-Laptop MontgomeryPairCorrelation % 