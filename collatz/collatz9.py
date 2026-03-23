import numpy as np
import matplotlib.pyplot as plt
from sympy import primerange
from scipy import signal
from scipy.interpolate import interp1d

def refined_spectral_analysis(limit=2000000):
    # 1. Generate Data (R24 Primes)
    primes = list(primerange(3, limit))
    r24_residues = {1, 5, 7, 11, 13, 17, 19, 23}
    r24_primes = [p for p in primes if p % 24 in r24_residues]
    
    indicator = np.zeros(limit + 1)
    for p in r24_primes:
        indicator[p] = 1
    
    # Convolution via FFT
    counts_raw = signal.fftconvolve(indicator, indicator)
    evens = np.arange(4, limit + 1, 2)
    raw_vals = counts_raw[evens].real
    
    # p <= q correction
    correction = np.zeros_like(evens, dtype=float)
    half_indices = evens // 2
    correction = indicator[half_indices]
    
    pairs_counts = (raw_vals + correction) / 2
    
    # 2. Fit and Detrend
    mask = pairs_counts > 0
    evens_fit = evens[mask]
    counts_fit = pairs_counts[mask]
    
    log_evens = np.log(evens_fit)
    log_counts = np.log(counts_fit)
    coeffs = np.polyfit(log_evens, log_counts, 1)
    
    expected = np.exp(coeffs[1]) * evens_fit**coeffs[0]
    residuals = counts_fit / expected
    
    # 3. Uniform Log-Resampling for accurate FFT
    # Create a uniform grid in ln(n)
    ln_min, ln_max = log_evens.min(), log_evens.max()
    ln_grid = np.linspace(ln_min, ln_max, 2**18) # High res power of 2
    interp_func = interp1d(log_evens, residuals, kind='linear', fill_value='extrapolate')
    res_uniform = interp_func(ln_grid)
    
    # 4. FFT Analysis
    N = len(res_uniform)
    d_ln = (ln_max - ln_min) / (N - 1)
    detrended_centered = res_uniform - np.mean(res_uniform)
    fft_vals = np.fft.rfft(detrended_centered)
    power = np.abs(fft_vals)**2
    freqs = np.fft.rfftfreq(N, d=d_ln)
    
    # 5. Peak Identification
    # Look for peaks in a range
    top_peaks_idx = np.argsort(power[1:])[-10:][::-1] + 1
    top_freqs = freqs[top_peaks_idx]
    top_powers = power[top_peaks_idx]
    
    return evens_fit, residuals, freqs, power, top_freqs, top_powers, coeffs[0]

# Constants
C_UFT_F = 0.003119
LAMBDA_U = 0.0002073
F_BASE = 1.0 / np.log(24)

evens, residuals, freqs, power, top_freqs, top_powers, slope = refined_spectral_analysis(2000000)

# Output for the user
print(f"Spectral Slope: {slope:.4f}")
print(f"Base Frequency (1/ln 24): {F_BASE:.4f}")
print("\nTop Spectral Peaks (Harmonics):")
for i, (f, p) in enumerate(zip(top_freqs, top_powers)):
    ratio = f / F_BASE
    print(f"Peak {i+1}: Freq={f:.4f}, Power={p:.2e}, Ratio={ratio:.4f}")

# Plotting the Power Spectrum and Peaks
plt.figure(figsize=(12, 10))

# Power Spectrum
plt.subplot(2, 1, 1)
plt.semilogy(freqs[1:20000], power[1:20000], label='Residual Power Spectrum')
plt.axvline(F_BASE, color='red', linestyle='--', alpha=0.7, label=f'Base Harmonic (1/ln 24)')
plt.axvline(6 * F_BASE, color='green', linestyle='--', alpha=0.7, label='D8 Hexagonal Resonance (6 * f0)')

# Highlight Top Peaks
for f in top_freqs[:3]:
    plt.annotate(f'{f:.3f}', xy=(f, power[np.argmin(np.abs(freqs-f))]), 
                 xytext=(10, 10), textcoords='offset points', arrowprops=dict(arrowstyle='->'))

plt.title('Refined Fourier Analysis: The Spectral Fingerprint of Goldbach (Base-24)')
plt.xlabel('Frequency (cycles per unit ln(n))')
plt.ylabel('Power')
plt.legend()
plt.grid(True, which='both', alpha=0.3)

# Resonance ratios
plt.subplot(2, 1, 2)
ratios = freqs[1:20000] / F_BASE
plt.plot(ratios, power[1:20000], color='purple', alpha=0.8)
plt.title('Harmonic Ratios to Base-24 Frequency')
plt.xlabel('Ratio (f / f_base)')
plt.ylabel('Power')
plt.xlim(0, 20)
plt.grid(True)

plt.tight_layout()
plt.savefig('refined_goldbach_spectrum.png')
plt.show()

# (base) brendanlynch@Brendans-Laptop collatz % python collatz9.py
# Spectral Slope: 0.8238
# Base Frequency (1/ln 24): 0.3147

# Top Spectral Peaks (Harmonics):
# Peak 1: Freq=0.0819, Power=3.84e+09, Ratio=0.2604
# Peak 2: Freq=0.1639, Power=8.51e+08, Ratio=0.5207
# Peak 3: Freq=0.2458, Power=2.83e+08, Ratio=0.7811
# Peak 4: Freq=0.3277, Power=1.16e+08, Ratio=1.0415
# Peak 5: Freq=0.4096, Power=5.99e+07, Ratio=1.3018
# Peak 6: Freq=2.5397, Power=4.27e+07, Ratio=8.0713
# Peak 7: Freq=0.4916, Power=3.90e+07, Ratio=1.5622
# Peak 8: Freq=2.4578, Power=3.89e+07, Ratio=7.8110
# Peak 9: Freq=2.6216, Power=3.89e+07, Ratio=8.3317
# Peak 10: Freq=4.1782, Power=3.47e+07, Ratio=13.2786
# 2025-12-28 08:55:33.607 python[55983:51754507] The class 'NSSavePanel' overrides the method identifier.  This method is implemented by class 'NSWindow'
# (base) brendanlynch@Brendans-Laptop collatz % 