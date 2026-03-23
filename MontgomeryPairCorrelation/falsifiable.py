import numpy as np
from scipy.special import comb

# -------- Observable --------
def cluster_statistic(eigs, L):
    n_pairs = comb(L, 2)
    total = 0.0
    count = 0
    for i in range(len(eigs) - L):
        cluster = eigs[i:i+L]
        for a in range(L):
            for b in range(a+1, L):
                gap = abs(cluster[a] - cluster[b])
                total += (1.0 - np.sinc(gap)**2)
        count += 1
    return total / (count * n_pairs)

# -------- Bulk extractor --------
def gue_bulk(N, bulk_fraction=0.2):
    M = (np.random.randn(N, N) + 1j*np.random.randn(N, N)) / np.sqrt(2*N)
    H = (M + M.conj().T)/2
    eigs = np.linalg.eigvalsh(H)

    mid = len(eigs)//2
    w = int(len(eigs)*bulk_fraction/2)
    eigs = eigs[mid-w:mid+w]

    # unfold
    eigs = eigs / np.mean(np.diff(eigs))
    return eigs

# -------- Experiment --------
def run_test():
    L = 4
    trials = 4

    print("\n--- UNIVERSALITY NULL TEST ---\n")

    # Sine-process proxy using huge N
    print("Computing sine-kernel limit proxy (large GUE)...")
    sine_vals = []
    for _ in range(trials):
        z = gue_bulk(12000, bulk_fraction=0.1)
        sine_vals.append(cluster_statistic(z, L))

    sine_mean = np.mean(sine_vals)
    sine_err = np.std(sine_vals, ddof=1)/np.sqrt(trials)

    print(f"Sine-limit proxy: {sine_mean:.6f} ± {sine_err:.6f}\n")

    # Finite-N GUE
    for N in [400, 800, 1600, 3200]:
        vals = []
        for _ in range(trials):
            z = gue_bulk(N)
            vals.append(cluster_statistic(z, L))

        mean = np.mean(vals)
        err = np.std(vals, ddof=1)/np.sqrt(trials)
        ratio = mean / sine_mean

        print(f"N={N:4d}  GUE={mean:.6f} ± {err:.6f}   Ratio={ratio:.6f}")

run_test()

# (base) brendanlynch@Brendans-Laptop MontgomeryPairCorrelation % python falsifiable.py

# --- UNIVERSALITY NULL TEST ---

# Computing sine-kernel limit proxy (large GUE)...
# Sine-limit proxy: 0.928167 ± 0.001128

# N= 400  GUE=0.931057 ± 0.005602   Ratio=1.003113
# N= 800  GUE=0.935679 ± 0.003559   Ratio=1.008093
# N=1600  GUE=0.930560 ± 0.002468   Ratio=1.002578
# N=3200  GUE=0.926593 ± 0.001005   Ratio=0.998304
# (base) brendanlynch@Brendans-Laptop MontgomeryPairCorrelation % 