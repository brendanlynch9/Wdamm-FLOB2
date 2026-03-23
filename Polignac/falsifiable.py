import numpy as np
from scipy.fft import fft, ifft
import math

def hl_constant(h):
    """Hardy-Littlewood 2-tuple constant for gap h."""
    if h == 0: return 1.0
    c2 = 0.660161815846869
    factors = set()
    d, n = 2, h
    while d*d <= n:
        if n % d == 0:
            if d > 2: factors.add(d)
            while n % d == 0: n //= d
        d += 1
    if n > 2: factors.add(n)
    return 2 * c2 * np.prod([(p-1)/(p-2) for p in factors])

def run_falsifiable_proof(N=1000000):
    # Standard Sieve
    primes = np.ones(N + 1, dtype=bool)
    primes[:2] = False
    for p in range(2, int(N**0.5) + 1):
        if primes[p]: primes[p*p::p] = False
    
    # Lambda vector (Normal Math)
    L = np.zeros(N)
    for p in np.where(primes)[0]:
        pk = p
        while pk < N:
            L[pk] = math.log(p)
            pk *= p
            
    # Spectral Autocorrelation (Wiener-Khinchine)
    M = 1 << (N * 2 - 1).bit_length()
    S = fft(L, n=M)
    P = (np.abs(S)**2) / N
    R = ifft(P).real

    print(f"--- Falsifiable Spectral Diagnostic (N={N}) ---")
    print(f"{'Gap h':<6} | {'Theoretical':<15} | {'Observed':<15} | {'Residual'}")
    for h in [2, 4, 6, 10, 30]:
        theo = hl_constant(h)
        obs = R[h]
        print(f"{h:<6} | {theo:<15.8f} | {obs:<15.8f} | {abs(obs-theo):.4e}")

if __name__ == "__main__":
    run_falsifiable_proof()

#     (base) brendanlynch@Brendans-Laptop Polignac % python falsifiable.py
# --- Falsifiable Spectral Diagnostic (N=1000000) ---
# Gap h  | Theoretical     | Observed        | Residual
# 2      | 1.32032363      | 1.31284435      | 7.4793e-03
# 4      | 1.32032363      | 1.30797914      | 1.2344e-02
# 6      | 2.64064726      | 2.63119877      | 9.4485e-03
# 10     | 1.76043151      | 1.75638306      | 4.0484e-03
# 30     | 3.52086302      | 3.53012515      | 9.2621e-03
# (base) brendanlynch@Brendans-Laptop Polignac % 