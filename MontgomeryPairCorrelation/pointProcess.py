import numpy as np
from scipy.special import comb
import time

# ---------- Observable ----------
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


# ---------- GUE generator ----------
def generate_gue_bulk(N, keep=0.4):
    M = (np.random.randn(N, N) + 1j*np.random.randn(N, N)) / np.sqrt(2*N)
    H = (M + M.conj().T) / 2
    eigs = np.linalg.eigvalsh(H)

    # take bulk window
    mid = len(eigs)//2
    w = int(len(eigs)*keep/2)
    eigs = eigs[mid-w:mid+w]

    # unfold by mean spacing
    eigs = eigs / np.mean(np.diff(eigs))
    return eigs


# ---------- Experiment ----------
def run_experiment():
    sizes = [400, 800, 1600, 3200]
    L = 4
    trials = 5

    print(f"\nCluster level L = {L}")
    print("N\tMean\t\tStdErr")

    for N in sizes:
        vals = []
        start = time.time()

        for _ in range(trials):
            z = generate_gue_bulk(N)
            vals.append(cluster_statistic(z, L))

        vals = np.array(vals)
        mean = vals.mean()
        stderr = vals.std(ddof=1)/np.sqrt(trials)

        print(f"{N}\t{mean:.6f}\t{stderr:.6f}")

        print(f"  runtime {time.time()-start:.1f}s")

run_experiment()


# (base) brendanlynch@Brendans-Laptop MontgomeryPairCorrelation % python pointProcess.py

# Cluster level L = 4
# N	Mean		StdErr
# 400	0.927808	0.002360
#   runtime 0.2s
# 800	0.927870	0.002337
#   runtime 0.5s
# 1600	0.928994	0.001671
#   runtime 2.6s
# 3200	0.928357	0.000705
#   runtime 16.0s
# (base) brendanlynch@Brendans-Laptop MontgomeryPairCorrelation % 