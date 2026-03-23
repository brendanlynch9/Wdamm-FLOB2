#!/usr/bin/env python3
import mpmath as mp

mp.dps = 50

# Rank r
r = 3

# Simplex volume in r dimensions
def simplex_volume(r):
    return mp.mpf(1) / mp.factorial(r)

vol = simplex_volume(r)
print("r-dimensional simplex volume:", vol)

# Truncated L-series surrogate
A_N = [0, 1, -2, -3, 2, -2, 6, -1]  # extend as necessary

def L_truncated(s):
    total = mp.mpf(0)
    for k in range(1, len(A_N)):
        total += A_N[k] / (mp.mpf(k) ** s)
    return total

# Estimate leading coefficient near s=1 using central difference
def eta_estimate(offset=1e-6):
    return (L_truncated(1 + offset) - L_truncated(1 - offset)) / (2 * offset)

eta_val = eta_estimate()
print("Estimated eta(X) near s=1:", eta_val)

# (base) brendanlynch@Brendans-Laptop BellinsonConjecture % python generalizedNodalIdentity.py
# r-dimensional simplex volume: 0.166666666666667
# Estimated eta(X) near s=1: 0.228615148492595
# (base) brendanlynch@Brendans-Laptop BellinsonConjecture % 