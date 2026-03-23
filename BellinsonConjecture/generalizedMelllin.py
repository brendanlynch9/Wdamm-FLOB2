import mpmath as mp
import itertools

mp.dps = 40

# Multi-dimensional integrand surrogate
def theta_X(*t):
    # Simple separable Gaussian surrogate
    prod = mp.mpf(1)
    for ti in t:
        prod *= mp.exp(-ti**2)
    return prod

def mellin_r(r, tmax=5, steps=40):
    # Create linspace for each dimension
    vals = [mp.linspace(0, tmax, steps) for _ in range(r)]
    total = mp.mpf(0)

    # Iterate over the full r-dimensional grid
    for pt in itertools.product(*vals):
        prod = mp.mpf(1)
        for ti in pt:
            prod *= 1/(ti + 1e-9)  # avoid zero
        total += theta_X(*pt) * prod

    # Normalize by total number of points
    return total / mp.mpf(steps**r)

for r in [1, 2, 3]:
    val = mellin_r(r)
    print(f"Mellin surrogate integral approximate for r={r}: {val}")

# (base) brendanlynch@Brendans-Laptop BellinsonConjecture % python generalizedMelllin.py
# Mellin surrogate integral approximate for r=1: 25000000.4571
# Mellin surrogate integral approximate for r=2: 625000022854998.0
# Mellin surrogate integral approximate for r=3: 1.56250008570624e+22
# (base) brendanlynch@Brendans-Laptop BellinsonConjecture % 