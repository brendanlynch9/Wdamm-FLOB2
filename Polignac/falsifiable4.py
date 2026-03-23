import numpy as np
from scipy.fft import fft, ifft
from math import log, sqrt

def hl_constant(h):
    """Standard Hardy-Littlewood constant 2C_h for even gap h ≥ 2.
    Returns 0 for odd/negative h.
    """
    if h <= 0 or h % 2 != 0:
        return 0.0
    
    C2 = 0.660161815846869
    # Remove the single factor of 2 that every even h has
    n = h // 2
    
    # Collect **only odd prime factors** of the remaining n
    factors = set()
    d = 3
    while d * d <= n:
        if n % d == 0:
            factors.add(d)
            while n % d == 0:
                n //= d
        d += 2
    if n > 1:  # n itself could be an odd prime
        factors.add(n)
    
    # Product only over odd primes p|h of (p-1)/(p-2)
    if not factors:
        prod = 1.0
    else:
        prod = 1.0
        for p in factors:
            if p == 2:  # safety net — should never happen now
                continue
            prod *= (p - 1) / (p - 2)
    
    return 2 * C2 * prod

def run_diagnostic(N=10**7, gaps=[2,4,6,8,10,12,14,18,20,30,60]):
    print(f"--- Standard Prime-Pair Correlation Check (N={N:,}) ---")
    print("Method: von Mangoldt autocorrelation via Wiener-Khinchine")
    
    # Sieve
    is_prime = np.ones(N+1, dtype=bool)
    is_prime[0:2] = False
    for i in range(2, int(sqrt(N))+1):
        if is_prime[i]:
            is_prime[i*i::i] = False
    
    # Λ(n)
    Lambda = np.zeros(N)
    primes = np.nonzero(is_prime)[0]
    for p in primes:
        pk = p
        while pk < N:
            Lambda[pk] = log(p)
            pk *= p
    
    # FFT-based autocorrelation (padded)
    M = 1 << (2*N - 1).bit_length()
    padded = np.zeros(M, dtype=complex)
    padded[:N] = Lambda
    fft_vals = fft(padded)
    power = np.abs(fft_vals)**2 / N
    autocorr = ifft(power).real
    
    # Results
    print(f"{'h':>4} {'Theo 2C_h':>12} {'Obs R(h)':>12} {'Abs diff':>10} {'Rel err %':>10}")
    print("-"*52)
    for h in gaps:
        theo = hl_constant(h)
        obs = autocorr[h]
        diff = abs(obs - theo)
        rel = (diff / theo * 100) if theo > 0 else float('inf')
        print(f"{h:4} {theo:12.6f} {obs:12.6f} {diff:10.6f} {rel:10.3f}%")
    
    print("\nNote: Small rel errors support HL heuristic; does NOT prove infinitude.")

if __name__ == "__main__":
    run_diagnostic()

#     (base) brendanlynch@Brendans-Laptop Polignac % python falsifiable4.py
# --- Standard Prime-Pair Correlation Check (N=10,000,000) ---
# Method: von Mangoldt autocorrelation via Wiener-Khinchine
#    h    Theo 2C_h     Obs R(h)   Abs diff  Rel err %
# ----------------------------------------------------
#    2     1.320324     1.327167   0.006844      0.518%
#    4     1.320324     1.318593   0.001731      0.131%
#    6     2.640647     2.636198   0.004449      0.168%
#    8     1.980485     1.317300   0.663185     33.486%
#   10     1.760432     1.759259   0.001173      0.067%
#   12     1.650405     2.643799   0.993394     60.191%
#   14     1.584388     1.584624   0.000235      0.015%
#   18     2.640647     2.642526   0.001879      0.071%
#   20     1.485364     1.759091   0.273727     18.428%
#   30     3.520863     3.519399   0.001464      0.042%
#   60     2.970728     3.513858   0.543130     18.283%

# Note: Small rel errors support HL heuristic; does NOT prove infinitude.
# (base) brendanlynch@Brendans-Laptop Polignac % 