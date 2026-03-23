import numpy as np
import math
from tqdm import tqdm
import cupy as cp

def get_base_primes(limit):
    """Primes up to sqrt(N) to seed segmented sieve."""
    sieve = np.ones(limit + 1, dtype=bool)
    sieve[:2] = False
    for p in range(2, int(math.sqrt(limit)) + 1):
        if sieve[p]:
            sieve[p*p : limit + 1 : p] = False
    return np.nonzero(sieve)[0]

def singular_series(h):
    """Hardy-Littlewood constant."""
    C2 = 0.660161815846869
    factors = set()
    n, d = h, 2
    while d*d <= n:
        if n % d == 0:
            if d > 2: factors.add(d)
            while n % d == 0: n //= d
        d += 1
    if n > 2: factors.add(n)
    prod = 1.0
    for p in factors: prod *= (p-1)/(p-2)
    return 2*C2*prod

def a100_polignac_run(N_target=10**10, gaps=[2,4,6,10,30]):
    print(f"Initializing A100 for N={N_target:e}...")
    
    base_limit = int(math.sqrt(N_target + max(gaps))) + 1
    base_primes = get_base_primes(base_limit)
    S_target = {h: singular_series(h) for h in gaps}
    S_total = {h: 0.0 for h in gaps}

    chunk_size = 5 * 10**7  # ~50 million numbers per chunk to fit GPU memory
    max_gap = max(gaps)

    for start in tqdm(range(1, N_target, chunk_size)):
        end = min(start + chunk_size, N_target)
        size = end - start

        ln_chunk = np.zeros(size + max_gap, dtype=np.float64)

        # Segmented sieve
        for p in base_primes:
            p_sq = p*p
            if p_sq > end + max_gap: break
            first = max(p_sq, ((start + p - 1)//p)*p)
            # fill multiples of p
            for multiple in range(first, end + max_gap, p):
                ln_chunk[multiple - start] = math.log(p)

        # Transfer to GPU
        ln_gpu = cp.array(ln_chunk)

        # Compute correlations
        for h in gaps:
            corr = cp.sum(ln_gpu[:size] * ln_gpu[h:h+size])
            S_total[h] += float(corr)

        # Quick stability print for B(2)
        if (start // chunk_size) % 2 == 0:
            B2 = S_total[2] / (S_target[2] * end)
            print(f"x={end:e}, B(2)={B2:.6f}")

    # Final B(h)
    print("\n--- Final Asymptotic Ratios ---")
    for h in gaps:
        B_final = S_total[h] / (S_target[h] * N_target)
        print(f"Gap {h}: B = {B_final:.8f}")

if __name__ == "__main__":
    a100_polignac_run(N_target=10**9)  # Start small to test speed

# root@9734f3dea6b5:/workspace# python computationalProof5.py
# Running Polignac Simulator up to N=1.000000e+09, chunk size=50000000
# 100%|██████████████████████████████████████████████████████████████████████████████| 20/20 [06:47<00:00, 20.35s/it]
# [INFO] CSV saved: polignac_B_values.csv
# [INFO] Plot saved: polignac_B_plot.png

# --- Final Asymptotic Ratios ---
# Gap 2: B = 2.11866171
# Gap 4: B = 2.11868156
# Gap 6: B = 1.27493661
# Gap 8: B = 2.11870868
# Gap 10: B = 1.64416308
# Gap 12: B = 1.27496408
# Gap 14: B = 1.78912466
# Gap 16: B = 2.11879452
# Gap 18: B = 1.27498139
# Gap 20: B = 1.64407444
# Gap 22: B = 1.91416424
# Gap 24: B = 1.27502388
# Gap 26: B = 1.94673620
# Gap 28: B = 1.78912242
# Gap 30: B = 1.01142263
# root@9734f3dea6b5:/workspace# 