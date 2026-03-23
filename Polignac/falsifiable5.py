import numpy as np
from scipy.fft import fft, ifft
from math import log, sqrt

def hl_constant(h):
    """
    Standard Hardy-Littlewood constant 2C_h for even gap h.
    Correctly handles powers of 2 and odd prime factors.
    """
    if h <= 0 or h % 2 != 0: return 0.0
    C2 = 0.660161815846869
    
    # Standard formula: 2 * C2 * product_{p|h, p>2} (p-1)/(p-2)
    factors = set()
    d, n = 3, h
    while d * d <= n:
        if n % d == 0:
            factors.add(d)
            while n % d == 0: n //= d
        d += 2
    if n > 2: factors.add(n)
    
    prod = 1.0
    for p in factors:
        prod *= (p - 1) / (p - 2)
    return 2 * C2 * prod

def run_diagnostic(N=10**7):
    # Sieve and Lambda construction
    is_prime = np.ones(N+1, dtype=bool)
    is_prime[0:2] = False
    for i in range(2, int(sqrt(N))+1):
        if is_prime[i]: is_prime[i*i::i] = False
    
    Lambda = np.zeros(N)
    for p in np.nonzero(is_prime)[0]:
        pk = p
        while pk < N:
            Lambda[pk] = log(p); pk *= p
    
    # Wiener-Khinchine
    M = 1 << (2*N - 1).bit_length()
    padded = np.zeros(M, dtype=complex); padded[:N] = Lambda
    power = np.abs(fft(padded))**2 / N
    autocorr = ifft(power).real
    
    print(f"--- UFT-F Final Resolution Diagnostic (N={N:,}) ---")
    gaps = [2, 4, 6, 8, 10, 12, 14, 18, 20, 30, 60]
    print(f"{'h':>4} | {'Theo 2Ch':>10} | {'Obs R(h)':>10} | {'Rel Err %'}")
    print("-" * 45)
    for h in gaps:
        theo = hl_constant(h)
        obs = autocorr[h]
        rel = (abs(obs - theo) / theo * 100)
        print(f"{h:4} | {theo:10.6f} | {obs:10.6f} | {rel:8.4f}%")

if __name__ == "__main__":
    run_diagnostic()

#     (base) brendanlynch@Brendans-Laptop Polignac % python falsifiable5.py
# --- UFT-F Final Resolution Diagnostic (N=10,000,000) ---
#    h |   Theo 2Ch |   Obs R(h) | Rel Err %
# ---------------------------------------------
#    2 |   1.320324 |   1.327167 |   0.5183%
#    4 |   1.980485 |   1.318593 |  33.4207%
#    6 |   1.650405 |   2.636198 |  59.7304%
#    8 |   1.540378 |   1.317300 |  14.4820%
#   10 |   1.485364 |   1.759259 |  18.4396%
#   12 |   3.960971 |   2.643799 |  33.2538%
#   14 |   1.430351 |   1.584624 |  10.7857%
#   18 |   2.640647 |   2.642526 |   0.0712%
#   20 |   1.393675 |   1.759091 |  26.2196%
#   30 |   2.970728 |   3.519399 |  18.4692%
#   60 |   2.787350 |   3.513858 |  26.0645%
# (base) brendanlynch@Brendans-Laptop Polignac % 