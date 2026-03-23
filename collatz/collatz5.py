import numpy as np
from sympy import primerange

# Same T build as before (k=100)
odds = [1,3,5,7,9,11,13,15,17,19,21,23]
n_len = len(odds)
odd_idx = {odds[i]: i for i in range(n_len)}
T = np.zeros((n_len, n_len))

k_max = 100
for j_idx in range(n_len):
    j = odds[j_idx]
    for k in range(1, k_max + 1):
        temp = (1 << k) * j - 1
        if temp % 3 == 0:
            m = temp // 3
            if m % 2 == 1:
                m_mod = m % 24
                if m_mod in odd_idx:
                    T[j_idx, odd_idx[m_mod]] += 1.0 / m

# Torsion mod
omega_u = 0.0002073045
T_mod = T + omega_u * np.eye(n_len)

eig_orig = np.linalg.eigvals(T)
eig_mod = np.linalg.eigvals(T_mod)

print("Original PF approx:", max(eig_orig.real))
print("Modified PF:", max(eig_mod.real))
print("Smallest real (orig/mod):", min(eig_orig.real), "/", min(eig_mod.real))

# Goldbach proxy: primes in R24 up to limit, count even sums
limit = 1000000
primes = list(primerange(3, limit))
r24_primes = [p for p in primes if p % 24 in {1,5,7,11,13,17,19,23}]

pairs = set()
for i in range(len(r24_primes)):
    for j in range(i, len(r24_primes)):  # Allow same prime twice? No for >2
        s = r24_primes[i] + r24_primes[j]
        if s > 4 and s % 2 == 0:
            pairs.add(s)

max_covered = max(pairs) if pairs else 0
print(f"R24 primes: {len(r24_primes)}")
print(f"Unique even sums: {len(pairs)}, up to {max_covered}")

# (base) brendanlynch@Brendans-Laptop collatz % python collatz5.py
# Original PF approx: 1.0
# Modified PF: 1.0002073045
# Smallest real (orig/mod): -0.07243355444259611 / -0.07222624994259626
# R24 primes: 78496
# Unique even sums: 999898, up to 1999966
# (base) brendanlynch@Brendans-Laptop collatz % 