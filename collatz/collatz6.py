import numpy as np
import matplotlib.pyplot as plt
from sympy import primerange
from collections import Counter

limit = 2000000  # 2M as in run
primes = list(primerange(3, limit))
r24_residues = {1,5,7,11,13,17,19,23}
r24_primes = [p for p in primes if p % 24 in r24_residues]

# Goldbach sums (allow p+q with p<=q)
sums_counter = Counter()
for i in range(len(r24_primes)):
    for j in range(i, len(r24_primes)):
        s = r24_primes[i] + r24_primes[j]
        if s <= limit * 2:  # Cap
            sums_counter[s] += 1

evens = sorted(k for k in sums_counter if k % 2 == 0 and k > 2)
counts = [sums_counter[e] for e in evens]

print(f"Goldbach pairs for evens up to {max(evens)}: {len(evens)} unique evens covered")
print(f"Max pairs for single even: {max(counts)}")

# Plot density
plt.figure(figsize=(12,6))
plt.loglog(evens, counts, '.', alpha=0.6)
plt.xlabel('Even n')
plt.ylabel('Number of R24 prime pairs')
plt.title('Goldbach Pair Density from R24 Primes')

# Fit 1/log n decay
log_evens = np.log(evens)
log_counts = np.log(counts)
coeffs = np.polyfit(log_evens[np.array(counts)>1], log_counts[np.array(counts)>1], 1)
print(f"Log-log slope: {coeffs[0]:.4f} (expect ~ -1 for 1/log n)")

plt.plot(evens, np.exp(coeffs[1]) * np.array(evens)**coeffs[0], 'r--', label=f'Fit slope {coeffs[0]:.3f}')
plt.legend()
plt.show()

# Log-periodic check: detrend and FFT for period ln24
detrended = np.array(counts) / (np.array(evens) ** coeffs[0] * np.exp(-coeffs[1]))
plt.plot(np.log(evens), detrended, '.')
plt.title('Detrended (log-periodic residuals)')
plt.show()