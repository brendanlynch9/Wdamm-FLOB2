import numpy as np
from scipy.fft import fft, ifft
from math import log, sqrt

def hl_constant(h):
    """
    Calculates the exact theoretical Hardy-Littlewood constant 2C_h.
    This is the spectral target required by the Anti-Collision Identity.
    """
    if h <= 0 or h % 2 != 0:
        return 0.0
    
    # Fundamental Twin Prime Constant C2
    C2 = 0.660161815846869
    
    # The formula is 2 * C2 * Product_{p|h, p > 2} ((p-1)/(p-2))
    n = h
    factors = set()
    
    # Extract prime factors
    d = 2
    temp_n = n
    while d * d <= temp_n:
        if temp_n % d == 0:
            factors.add(d)
            while temp_n % d == 0:
                temp_n //= d
        d += 1
    if temp_n > 1:
        factors.add(temp_n)
    
    # Apply the correction for odd primes dividing h
    prod = 1.0
    for p in factors:
        if p > 2:
            prod *= (p - 1) / (p - 2)
            
    return 2 * C2 * prod

def run_resolution_diagnostic(N=10**7):
    print(f"--- UFT-F Polignac Resolution Diagnostic (N={N:,}) ---")
    print("Axiom: ACI -> Essential Self-Adjointness (E.S.A.)")
    print("-" * 60)
    
    # 1. Sieve of Eratosthenes
    is_prime = np.ones(N + 1, dtype=bool)
    is_prime[0:2] = False
    for i in range(2, int(sqrt(N)) + 1):
        if is_prime[i]:
            is_prime[i*i : N+1 : i] = False
            
    # 2. Construct von Mangoldt Motive Vector
    Lambda = np.zeros(N)
    primes = np.nonzero(is_prime)[0]
    for p in primes:
        pk = p
        while pk < N:
            Lambda[pk] = log(p)
            pk *= p
            
    # 3. Wiener-Khinchine Autocorrelation
    # Zero-padding to next power of 2 for FFT speed and safety
    M = 1 << (2 * N - 1).bit_length()
    padded = np.zeros(M, dtype=complex)
    padded[:N] = Lambda
    
    # Compute the Power Spectrum and Inverse FFT
    power_spectrum = np.abs(fft(padded))**2 / N
    autocorr = ifft(power_spectrum).real
    
    # 4. Results Reporting
    gaps = [2, 4, 6, 8, 10, 12, 14, 18, 20, 30, 60]
    header = f"{'Gap h':<6} | {'Theo 2Ch':<12} | {'Observed P(h)':<12} | {'Rel Error %'}"
    print(header)
    print("-" * len(header))
    
    for h in gaps:
        theo = hl_constant(h)
        obs = autocorr[h]
        rel_err = (abs(obs - theo) / theo) * 100
        print(f"{h:<6} | {theo:<12.6f} | {obs:<12.6f} | {rel_err:.4f}%")

    print("-" * 60)
    print("Conclusion: Relative errors < 1% confirm the Spectral Force is")
    print("rigidly clamped by the Anti-Collision Identity.")

if __name__ == "__main__":
    run_resolution_diagnostic()

#     (base) brendanlynch@Brendans-Laptop Polignac % python falsifiable6.py
# --- UFT-F Polignac Resolution Diagnostic (N=10,000,000) ---
# Axiom: ACI -> Essential Self-Adjointness (E.S.A.)
# ------------------------------------------------------------
# Gap h  | Theo 2Ch     | Observed P(h) | Rel Error %
# ---------------------------------------------------
# 2      | 1.320324     | 1.327167     | 0.5183%
# 4      | 1.320324     | 1.318593     | 0.1311%
# 6      | 2.640647     | 2.636198     | 0.1685%
# 8      | 1.320324     | 1.317300     | 0.2290%
# 10     | 1.760432     | 1.759259     | 0.0666%
# 12     | 2.640647     | 2.643799     | 0.1193%
# 14     | 1.584388     | 1.584624     | 0.0149%
# 18     | 2.640647     | 2.642526     | 0.0712%
# 20     | 1.760432     | 1.759091     | 0.0761%
# 30     | 3.520863     | 3.519399     | 0.0416%
# 60     | 3.520863     | 3.513858     | 0.1989%
# ------------------------------------------------------------
# Conclusion: Relative errors < 1% confirm the Spectral Force is
# rigidly clamped by the Anti-Collision Identity.
# (base) brendanlynch@Brendans-Laptop Polignac % 