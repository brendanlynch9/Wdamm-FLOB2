import numpy as np
import math

def von_mangoldt(N):
    """
    Generate von Mangoldt function Λ(n) for n=0..N
    Λ(n) = log(p) if n = p^k, else 0
    """
    ln = np.zeros(N+1, dtype=float)
    is_prime = np.ones(N+1, dtype=bool)
    is_prime[:2] = False
    for p in range(2, N+1):
        if is_prime[p]:
            logp = math.log(p)
            pk = p
            while pk <= N:
                ln[pk] = logp
                if pk > N // p: break
                pk *= p
            is_prime[p*p:N+1:p] = False
    return ln

def singular_series(h):
    """Hardy-Littlewood singular series for even gap h"""
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
    for p in factors:
        prod *= (p-1)/(p-2)
    return 2 * C2 * prod

def polignac_simulator(N_max=10_000_000, gaps=[2,4,6,8,10,12,30], chunk_size=5_000_000):
    """
    Simulate von Mangoldt correlation sums in chunks to avoid memory overflow
    Computes S_h(x), clustering ratio B(h,x), and flux for each gap
    """
    print(f"Running Polignac Simulator up to N={N_max} with chunk size={chunk_size}")
    max_h = max(gaps)
    S_cum = {h: 0.0 for h in gaps}
    B_dict = {h: [] for h in gaps}
    flux_dict = {h: [] for h in gaps}
    x_values = []

    # Process in chunks
    for chunk_start in range(1, N_max+1, chunk_size):
        chunk_end = min(chunk_start + chunk_size - 1, N_max)
        length = chunk_end - chunk_start + 1
        ln_block = von_mangoldt(chunk_end + max_h)  # include h-offset

        for h in gaps:
            # Compute correlation sum for this chunk
            terms = ln_block[chunk_start:chunk_end+1] * ln_block[chunk_start + h:chunk_end + h + 1]
            S_chunk = np.sum(terms)
            S_cum[h] += S_chunk

            # Correct n_count: total number of n summed so far
            n_count = chunk_end
            B = S_cum[h] / (singular_series(h) * n_count)
            flux = ((S_cum[h] - singular_series(h) * n_count)/n_count)**2
            B_dict[h].append(B)
            flux_dict[h].append(flux)

        x_values.append(chunk_end)

    # Print final results
    print("\n--- Final Clustering Ratios ---")
    for h in gaps:
        print(f"Gap h={h}: Final B={B_dict[h][-1]:.6f}, Final flux={flux_dict[h][-1]:.6e}")

    # Optional: plot convergence
    try:
        import matplotlib.pyplot as plt
        plt.figure(figsize=(12,6))
        for h in gaps:
            plt.plot(x_values, B_dict[h], marker='o', label=f'h={h}')
        plt.axhline(y=1.0, color='r', linestyle='--', alpha=0.5, label='HL Limit B=1')
        plt.xlabel("x")
        plt.ylabel("Clustering Ratio B(h,x)")
        plt.title(f"Polignac Clustering Ratio Convergence up to N={N_max}")
        plt.grid(True, linestyle='--', alpha=0.5)
        plt.legend()
        plt.show()
    except ImportError:
        pass

if __name__ == "__main__":
    polignac_simulator(N_max=100_000_000, gaps=[2,4,6,8,10,12,14,16,18,20,22,24,26,28,30], chunk_size=5_000_000)


# (base) brendanlynch@Brendans-Laptop Polignac % python computationalProof2.py
# Running Polignac Simulator up to N=100000000 with chunk size=5000000

# --- Final Clustering Ratios ---
# Gap h=2: Final B=1.000068, Final flux=7.951197e-09
# Gap h=4: Final B=1.000122, Final flux=2.579373e-08
# Gap h=6: Final B=0.999438, Final flux=2.200132e-06
# Gap h=8: Final B=0.999163, Final flux=1.221193e-06
# Gap h=10: Final B=0.999639, Final flux=4.047610e-07
# Gap h=12: Final B=0.999663, Final flux=7.916406e-07
# Gap h=14: Final B=0.999555, Final flux=4.974443e-07
# Gap h=16: Final B=1.001900, Final flux=6.293364e-06
# Gap h=18: Final B=0.999962, Final flux=1.026219e-08
# Gap h=20: Final B=0.998740, Final flux=4.918291e-06
# Gap h=22: Final B=0.999840, Final flux=5.496266e-08
# Gap h=24: Final B=1.000491, Final flux=1.680923e-06
# Gap h=26: Final B=1.000485, Final flux=4.876900e-07
# Gap h=28: Final B=1.000234, Final flux=1.371838e-07
# Gap h=30: Final B=0.999926, Final flux=6.871243e-08
# 2026-01-25 08:14:29.926 python[31535:31831872] The class 'NSSavePanel' overrides the method identifier.  This method is implemented by class 'NSWindow'
# (base) brendanlynch@Brendans-Laptop Polignac % 