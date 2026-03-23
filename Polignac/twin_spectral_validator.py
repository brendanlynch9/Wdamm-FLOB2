import numpy as np
import matplotlib.pyplot as plt
from scipy.fft import fft, ifft
from math import log, prod

def get_polignac_constant(h):
    """
    Calculates the theoretical constant for a gap h.
    For h=2, this is 2 * C2.
    """
    # Standard Twin Prime Constant C2
    C2 = 0.660161815846869
    if h == 0: return 1.0
    
    # Extract unique prime factors of h/2
    def get_prime_factors(n):
        factors = set()
        d = 2
        temp = n
        while d * d <= temp:
            if temp % d == 0:
                factors.add(d)
                while temp % d == 0:
                    temp //= d
            d += 1
        if temp > 1:
            factors.add(temp)
        return factors

    factors = get_prime_factors(h)
    # The constant for gap h is 2 * C2 * Product((p-1)/(p-2)) for p|h, p > 2
    adjustment = 1.0
    for p in factors:
        if p > 2:
            adjustment *= (p - 1) / (p - 2)
    
    return 2 * C2 * adjustment

def sieve_of_eratosthenes(limit):
    is_prime = np.ones(limit + 1, dtype=bool)
    is_prime[0:2] = False
    for p in range(2, int(np.sqrt(limit)) + 1):
        if is_prime[p]:
            for multiple in range(p*p, limit+1, p):
                is_prime[multiple] = False
    return np.where(is_prime)[0]

def von_mangoldt_lambda_vector(N, primes):
    Lambda = np.zeros(N + 1, dtype=float)
    for p in primes:
        if p > N: break
        pk = p
        while pk <= N:
            Lambda[pk] = log(p)
            pk *= p
    return Lambda[1:]

def compute_polignac_shift(N, h):
    """
    Generalized version of compute_PN_and_shift2 for any shift h.
    Based on UFT-F Section 3.2 (Eq 3.3).
    """
    primes = sieve_of_eratosthenes(int(N * 1.1))
    Lambda_N = von_mangoldt_lambda_vector(N, primes)
    
    # Zero-pad to M > N + h
    M = 1 << int(np.ceil(np.log2(N + h + 1000)))
    x = np.zeros(M, dtype=complex)
    x[:N] = Lambda_N
    
    Xk = fft(x)
    PN = (np.abs(Xk)**2) / N
    autocorr_normalized = ifft(PN).real
    
    # The Polignac coefficient for gap h
    return autocorr_normalized[h]

def run_polignac_analysis(max_N, h_values):
    """
    Runs analysis across multiple gaps (h=2, 4, 6...) 
    to show universal ACI enforcement.
    """
    results = {}
    print(f"--- UFT-F Polignac Stability Test (N={max_N}) ---")
    for h in h_values:
        theoretical = get_polignac_constant(h)
        observed = compute_polignac_shift(max_N, h)
        error = abs(observed - theoretical)
        results[h] = {'obs': observed, 'theo': theoretical, 'err': error}
        print(f"Gap h={h:2d} | Observed={observed:.6f} | Expected={theoretical:.6f} | Error={error:.4e}")
    return results

if __name__ == "__main__":
    # Test for Twin (2), Cousin (4), and Sexy (6) primes
    GAPS_TO_TEST = [2, 4, 6, 8, 10, 12]
    N_CUTOFF = 10**6
    
    try:
        data = run_polignac_analysis(N_CUTOFF, GAPS_TO_TEST)
        
        # Plotting the 'Spectral Force' across gaps
        plt.figure(figsize=(10, 5))
        h_vals = list(data.keys())
        obs_vals = [data[h]['obs'] for h in h_vals]
        theo_vals = [data[h]['theo'] for h in h_vals]
        
        plt.bar(h_vals, obs_vals, alpha=0.6, label='Observed $\hat{P}_N(h)$', color='#3b82f6')
        plt.step(h_vals, theo_vals, where='mid', label='Theoretical $2C_h$', color='red', linestyle='--')
        
        plt.title(f'UFT-F Spectral Signature across Polignac Gaps (N={N_CUTOFF})')
        plt.xlabel('Gap $h$')
        plt.ylabel('Spectral Density')
        plt.legend()
        plt.grid(axis='y', alpha=0.3)
        plt.show()
        
    except Exception as e:
        print(f"Error: {e}")

#         (base) brendanlynch@Brendans-Laptop Polignac % python twin_spectral_validator.py 
# /Users/brendanlynch/Desktop/zzzzzCompletePDFs/Polignac/twin_spectral_validator.py:107: SyntaxWarning: invalid escape sequence '\h'
#   plt.bar(h_vals, obs_vals, alpha=0.6, label='Observed $\hat{P}_N(h)$', color='#3b82f6')
# --- UFT-F Polignac Stability Test (N=1000000) ---
# Gap h= 2 | Observed=1.312844 | Expected=1.320324 | Error=7.4793e-03
# Gap h= 4 | Observed=1.307979 | Expected=1.320324 | Error=1.2344e-02
# Gap h= 6 | Observed=2.631199 | Expected=2.640647 | Error=9.4485e-03
# Gap h= 8 | Observed=1.322643 | Expected=1.320324 | Error=2.3198e-03
# Gap h=10 | Observed=1.756383 | Expected=1.760432 | Error=4.0484e-03
# Gap h=12 | Observed=2.634022 | Expected=2.640647 | Error=6.6248e-03
# 2026-01-25 05:21:08.193 python[28980:31650440] The class 'NSSavePanel' overrides the method identifier.  This method is implemented by class 'NSWindow'
# (base) brendanlynch@Brendans-Laptop Polignac % 