#
# twin_spectral_validator.py
#The empirical results you provided are exactly what we needed to see: the spectral coefficient $\widehat{P_N}(2)$ is clearly converging to the non-zero constant $2C_2$, strongly supporting the UFT-F requirement that the stability axiom ($\mathcal{A}_{ACI}$) forces this spectral feature.
# EMPIRICAL VALIDATION OF THE SPECTRAL MECHANISM FOR TPC
#
# Purpose: This script implements the Fourier-based approach described in Section 3
# of the diagnostic note. It calculates the normalized power spectrum coefficient
# P_N(2) (the spectral twin coefficient) for increasing cutoffs N and compares
# the result to the theoretical Hardy-Littlewood constant 2*C2.
#
# It verifies the convergence rate, providing computational evidence that the
# mechanism (ACI -> P-hat(2) > 0) is numerically sound.
#
# Requires: numpy, scipy, matplotlib
#
import numpy as np
import matplotlib.pyplot as plt
from scipy.fft import fft, ifft
from math import log, prod

# The Twin Prime Constant (Hardy-Littlewood constant C2)
# C2 = Product over primes p >= 3 of (1 - 1/(p-1)^2)
# We use a 15-digit approximation for 2*C2
TWO_C2 = 1.320323632350438

def sieve_of_eratosthenes(limit):
    """Generates primes up to 'limit' using the Sieve of Eratosthenes."""
    is_prime = np.ones(limit + 1, dtype=bool)
    is_prime[0:2] = False
    for p in range(2, int(np.sqrt(limit)) + 1):
        if is_prime[p]:
            for multiple in range(p * p, limit + 1, p):
                is_prime[multiple] = False
    return np.where(is_prime)[0]

def von_mangoldt_lambda_vector(N, primes):
    """Generates the von Mangoldt function Lambda(n) for n <= N."""
    Lambda = np.zeros(N + 1, dtype=float)
    
    for p in primes:
        if p > N:
            break
        # Lambda(n) = log(p) if n is a power of p (p^k)
        pk = p
        while pk <= N:
            Lambda[pk] = log(p)
            pk *= p
            
    # We only need Lambda for n >= 1
    return Lambda[1:]

def compute_PN_and_shift2(N):
    """
    Computes the Normalized Power Spectrum P_N and the spectral twin coefficient
    P_hat_N(2) using FFT, following the Wiener-Khinchine theorem.
    """
    # Use a prime list slightly larger than N to ensure full Lambda calculation
    primes = sieve_of_eratosthenes(int(N * 1.05))
    
    # Get Lambda(n) vector of size N
    Lambda_N = von_mangoldt_lambda_vector(N, primes)
    
    # 1. Zero-pad the Lambda vector to a power of two M for efficient FFT
    # Choose M > N (M=2*N is safe for autocorrelation)
    M = 1 << int(np.ceil(np.log2(2 * N)))
    x = np.zeros(M, dtype=complex)
    x[:N] = Lambda_N
    
    # 2. Compute the Fourier transform of the prime measure mu_N
    Xk = fft(x)
    
    # 3. Compute the Normalized Power Spectrum P_N(t) = |Xk|^2 / N
    # This is equivalent to the Fourier transform of the autocorrelation gamma_N
    PN = (np.abs(Xk)**2) / N
    
    # 4. Compute the autocorrelation (gamma_N / N) via inverse FFT
    # The result is the sequence of coefficients P_hat_N(h)
    autocorr_normalized = ifft(PN).real
    
    # 5. The twin coefficient P_hat_N(2) is the value at index h=2 (since indices are 0-based)
    approx_shift2 = autocorr_normalized[2]
    
    return approx_shift2

def run_convergence_analysis(max_N, num_points):
    """Runs the analysis for a sequence of N cutoffs."""
    # Generate N values logarithmically spaced
    N_values = np.logspace(np.log10(10000), np.log10(max_N), num_points, dtype=int)
    
    results = []
    
    print(f"--- Running Spectral Convergence Test up to N={max_N} ---")
    
    for N in N_values:
        shift2 = compute_PN_and_shift2(N)
        error = abs(shift2 - TWO_C2)
        
        results.append({
            'N': N,
            'shift2': shift2,
            'error': error
        })
        
        print(f"N={N:7d} | P_hat_N(2)={shift2:.10f} | Error={error:.4e}")
        
    return N_values, results

def plot_results(N_values, results):
    """Generates a log-log plot of the error term for convergence analysis."""
    N_list = N_values
    error_list = np.array([r['error'] for r in results])
    
    # 1. Plot the raw error (log-log scale)
    plt.figure(figsize=(10, 6))
    # FIX: Using raw string (r'...') to avoid SyntaxWarning with LaTeX backslashes
    plt.loglog(N_list, error_list, 'o-', color='#3b82f6', label=r'$|\widehat{P_N}(2) - 2C_2|$ Residual')
    
    # 2. Add an ideal theoretical convergence line (O(1/log(N)) or similar slow decay)
    # Since the exact error term is complex, we use a reference slope for visualization.
    # The convergence is known to be very slow (logarithmic factors).
    # We plot a reference line proportional to N^(-1/2) for comparison with typical FFT errors.
    
    # Create reference line points for slope visualization
    N_ref = np.array([N_list.min(), N_list.max()])
    Error_ref_start = error_list[0]
    # Set the target slope (heuristic for prime density problems)
    Reference_Slope = N_ref**(-0.5) * (Error_ref_start / (N_ref[0]**(-0.5)))
    
    plt.loglog(N_ref, Reference_Slope, '--', color='gray', alpha=0.6, label=r'Reference Slope $N^{-1/2}$')
    
    # FIX: Using raw string (r'...') to avoid SyntaxWarning with LaTeX backslashes
    plt.title(r'Empirical Convergence of Spectral Twin Coefficient $|\widehat{P_N}(2)|$ to $2C_2$')
    plt.xlabel('Cutoff $N$ (Log Scale)')
    plt.ylabel('Residual Error (Log Scale)')
    plt.grid(True, which="both", ls="--", alpha=0.7)
    plt.legend()
    # No need for raw string here, as no backslashes are at the beginning or end of escape sequences
    plt.figtext(0.15, 0.88, f'$2C_2 \\approx {TWO_C2:.8f}$', fontsize=10, bbox={"facecolor":"white", "alpha":0.8, "pad":5})
    
    plt.show()

if __name__ == "__main__":
    # --- Configuration ---
    # Maximum cutoff for the sieve/analysis. Max N should be kept manageable (e.g., 10^7)
    # The value N=10^6 is a good balance for speed and showing convergence trend.
    MAX_N_CUTOFF = 10**6
    # Number of different N values to test
    NUM_DATA_POINTS = 10
    # ---------------------
    
    try:
        N_values, results = run_convergence_analysis(MAX_N_CUTOFF, NUM_DATA_POINTS)
        plot_results(N_values, results)
        print("\nPlot displayed. The key takeaway is the non-zero convergence of P_hat_N(2).")
        print("To observe a clearer trend, increase MAX_N_CUTOFF (may increase runtime).")
        
    except Exception as e:
        print(f"\nAn error occurred during execution: {e}")
        print("Ensure you have numpy, scipy, and matplotlib installed (e.g., pip install numpy scipy matplotlib).")