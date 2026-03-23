import numpy as np
from scipy.fft import fft, ifft
from math import log

def get_theoretical_constant(h):
    """
    Standard Analytic Number Theory: Hardy-Littlewood k-tuple constant for h.
    Ref: Hardy & Littlewood (1923).
    """
    if h == 0: return 1.0
    C2 = 0.660161815846869
    factors = set()
    n = h
    for i in range(2, int(n**0.5) + 1):
        if n % i == 0:
            if i > 2: factors.add(i)
            while n % i == 0: n //= i
    if n > 2: factors.add(n)
    
    # 2 * C2 * Product((p-1)/(p-2)) for odd p | h
    adj = np.prod([(p - 1) / (p - 2) for p in factors]) if factors else 1.0
    return 2 * C2 * adj

def analyze_polignac_spectral_density(N, max_h):
    """
    Uses standard Signal Processing (Wiener-Khinchine) to derive 
    prime gap densities from the von Mangoldt function.
    """
    # 1. Sieve primes and calculate Lambda(n)
    is_prime = np.ones(N + 1, dtype=bool)
    is_prime[0:2] = False
    for p in range(2, int(N**0.5) + 1):
        if is_prime[p]:
            is_prime[p*p:N+1:p] = False
    
    lambda_vec = np.zeros(N, dtype=float)
    primes = np.where(is_prime)[0]
    for p in primes:
        pk = p
        while pk < N:
            lambda_vec[pk] = log(p)
            pk *= p
            
    # 2. Wiener-Khinchine: Correlation is the IFFT of the Power Spectrum
    # Pad to power of 2 for FFT efficiency
    M = 1 << int(np.ceil(np.log2(2 * N)))
    padded_lambda = np.zeros(M)
    padded_lambda[:N] = lambda_vec
    
    # Compute Power Spectrum P(w) = |FFT|^2 / N
    spectral_coeffs = fft(padded_lambda)
    power_spectrum = (np.abs(spectral_coeffs)**2) / N
    
    # Compute Autocorrelation (Inverse FFT of Power Spectrum)
    autocorr = ifft(power_spectrum).real
    
    # 3. Output Falsifiable Data
    print(f"{'Gap h':<6} | {'Theoretical':<15} | {'Observed':<15} | {'Residual'}")
    print("-" * 55)
    for h in range(2, max_h + 2, 2):
        theo = get_theoretical_constant(h)
        obs = autocorr[h]
        res = abs(obs - theo)
        print(f"{h:<6} | {theo:<15.8f} | {obs:<15.8f} | {res:.4e}")

if __name__ == "__main__":
    # N=10^6 is a sufficient sample for 2-digit precision
    analyze_polignac_spectral_density(N=1000000, max_h=20)

#     (base) brendanlynch@Brendans-Laptop Polignac % python weinerKhninchine.py
# Gap h  | Theoretical     | Observed        | Residual
# -------------------------------------------------------
# 2      | 1.32032363      | 1.31284435      | 7.4793e-03
# 4      | 1.32032363      | 1.30797914      | 1.2344e-02
# 6      | 2.64064726      | 2.63119877      | 9.4485e-03
# 8      | 1.32032363      | 1.32264344      | 2.3198e-03
# 10     | 1.76043151      | 1.75638306      | 4.0484e-03
# 12     | 2.64064726      | 2.63402246      | 6.6248e-03
# 14     | 1.58438836      | 1.58357349      | 8.1487e-04
# 16     | 1.32032363      | 1.31871939      | 1.6042e-03
# 18     | 2.64064726      | 2.64443169      | 3.7844e-03
# 20     | 1.76043151      | 1.76408552      | 3.6540e-03
# (base) brendanlynch@Brendans-Laptop Polignac % 