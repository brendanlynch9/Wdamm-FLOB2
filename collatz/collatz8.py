import numpy as np
import matplotlib.pyplot as plt
from sympy import primerange
from scipy import signal

limit = 2000000
primes = list(primerange(3, limit))
r24_residues = {1,5,7,11,13,17,19,23}
r24_primes = [p for p in primes if p % 24 in r24_residues]

indicator = np.zeros(limit + 1)
for p in r24_primes:
    indicator[p] = 1

counts_raw = signal.fftconvolve(indicator, indicator)
evens = np.arange(4, limit + 1, 2)
raw_vals = counts_raw[evens].real

# p <= q correction
correction = np.zeros_like(evens, dtype=float)
for i, e in enumerate(evens):
    half = e // 2
    if half <= limit and indicator[half]:
        correction[i] = 1

pairs_counts = (raw_vals + correction) / 2

# Fit and detrend
mask = pairs_counts > 0
evens_fit = evens[mask]
counts_fit = pairs_counts[mask]

log_evens = np.log(evens_fit)
log_counts = np.log(counts_fit)
coeffs = np.polyfit(log_evens, log_counts, 1)

expected = np.exp(coeffs[1]) * evens_fit**coeffs[0]
residuals = counts_fit / expected

# FFT of residuals (detrended signal)
N = len(residuals)
detrended_centered = residuals - np.mean(residuals)
fft_vals = np.fft.rfft(detrended_centered)
power = np.abs(fft_vals)**2
freqs = np.fft.rfftfreq(N, d=np.diff(log_evens)[0])  # Approx spacing in ln(n)

# Plot power spectrum
plt.figure(figsize=(12,8))
plt.semilogy(freqs[1:], power[1:], label='Power Spectrum of Residuals')  # Skip DC
plt.xlabel('Frequency in ln(n) space')
plt.ylabel('Power')
plt.title('Fourier Analysis of Goldbach Detrended Residuals (Base-24 Harmonics)')
plt.axvline(1/np.log(24), color='red', linestyle='--', label=f'Expected: 1/ln(24) ≈ {1/np.log(24):.4f}')
plt.legend()
plt.grid(True, which='both')
plt.show()

# Peak detection
peak_idx = np.argmax(power[1:]) + 1
peak_freq = freqs[peak_idx]
print(f"Dominant frequency: {peak_freq:.4f} (expected 1/ln24 ≈ 0.3140)")
print(f"Ratio to expected: {peak_freq / (1/np.log(24)):.4f}")

# (base) brendanlynch@Brendans-Laptop collatz % python collatz8.py
# 2025-12-28 08:45:16.040 python[55642:51745595] The class 'NSSavePanel' overrides the method identifier.  This method is implemented by class 'NSWindow'
# Dominant frequency: 1.8283 (expected 1/ln24 ≈ 0.3140)
# Ratio to expected: 5.8103
# (base) brendanlynch@Brendans-Laptop collatz % 