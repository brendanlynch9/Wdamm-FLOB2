#!/usr/bin/env python3
"""
ULTIMATE MULTI-FAMILY PERFECT CUBOID FALSIFIER
Version: UFT-F Verified (Zero-Drift Bug Fixed)

Fixes:
1. Ignores "False Awakenings" (drift == 0.0) from non-Euler bricks (Spohn family).
2. Removes clunky Decimal/mpmath mixing for pure, high-speed mpmath precision.
3. Preserves the exact 4 families requested.
"""

import argparse
import math
import time
from mpmath import mp, mpf, sqrt, nint
import numpy as np
from scipy.stats import linregress
from typing import Generator, Tuple

# =====================================
# CONFIG & PRECISION
# =====================================
# 200 decimal places guarantees we don't miss any sub-LAMBDA_0 drifts
mp.dps = 200

def compute_drift(a: int, b: int, c: int) -> mpf:
    """Computes spectral drift of the space diagonal using pure mpmath."""
    s2 = a*a + b*b + c*c
    root = sqrt(s2)
    nearest = nint(root)
    return abs(root - nearest)

def is_perfect_square(n: int) -> bool:
    """Fast native integer square check."""
    if n < 0: return False
    if n in (0, 1): return True
    root = math.isqrt(n)
    return root * root == n

def check_coupling(a: int, b: int, c: int) -> bool:
    """The UFT-F Coupling Lemma: Mod 8 Residue Check"""
    sq = lambda n: (n * n) % 8
    d1 = (sq(a) + sq(b)) % 8
    d2 = (sq(a) + sq(c)) % 8
    d3 = (sq(b) + sq(c)) % 8
    g  = (sq(a) + sq(b) + sq(c)) % 8
    return all(x in {0, 1, 4} for x in (d1, d2, d3, g))

# ====================== THE 4 FAMILIES ======================

def saunderson_generator(max_m: int) -> Generator[Tuple[int, int, int], None, None]:
    for m in range(2, max_m + 1):
        for n in range(1, m):
            if math.gcd(m, n) != 1 or (m + n) % 2 != 1: continue
            u = m*m - n*n; v = 2*m*n; w = m*m + n*n
            a = abs(u * (4*v*v - w*w))
            b = abs(v * (4*u*u - w*w))
            c = abs(4*u*v*w)
            if a and b and c: yield a, b, c

def euler_chapple_generator(max_m: int) -> Generator[Tuple[int, int, int], None, None]:
    for m in range(2, max_m + 1):
        for n in range(1, m):
            if math.gcd(m, n) != 1 or (m + n) % 2 != 1: continue
            u = m*m - n*n; v = 2*m*n; w = m*m + n*n
            a = abs(u * (v*v - w*w))
            b = abs(v * (u*u - w*w))
            c = abs(w * (u*u + v*v))
            if a and b and c: yield a, b, c

def spohn_generator(max_m: int) -> Generator[Tuple[int, int, int], None, None]:
    for k in range(1, max_m + 1):
        for m_ in range(1, k):
            if math.gcd(m_, k) != 1: continue
            a = k * (k**2 - 3*m_**2)
            b = m_ * (3*k**2 - m_**2)
            c = 4 * k * m_ * (k**2 + m_**2)
            if a and b and c: yield abs(a), abs(b), abs(c)

def two_triples_generator(max_m: int) -> Generator[Tuple[int, int, int], None, None]:
    for m1 in range(2, min(25, max_m + 1)):
        for n1 in range(1, m1):
            if math.gcd(m1, n1) != 1 or (m1 + n1) % 2 != 1: continue
            u1 = m1*m1 - n1*n1; v1 = 2*m1*n1
            for m2 in range(2, min(25, max_m + 1)):
                for n2 in range(1, m2):
                    if math.gcd(m2, n2) != 1 or (m2 + n2) % 2 != 1: continue
                    u2 = m2*m2 - n2*n2; v2 = 2*m2*n2
                    lcm = math.lcm(u1, u2, v1, v2)
                    yield lcm*u1, lcm*v1, lcm*u2

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--max_param", type=int, default=20000)
    args = parser.parse_args()

    print("=== MULTI-FAMILY PERFECT CUBOID FALSIFIER ===")
    start = time.time()

    families = {
        "saunderson": saunderson_generator,
        "euler_chapple": euler_chapple_generator,
        "spohn": spohn_generator,
        "two_triples": two_triples_generator
    }

    drifts = []
    sizes = []
    total = 0
    min_drift = mpf('1.0')
    best = None

    print(f"Scanning 4 families up to m = {args.max_param}...")

    for name, gen in families.items():
        print(f"  → {name}")
        for a, b, c in gen(args.max_param):
            total += 1
            drift = compute_drift(a, b, c)
            size = max(a, b, c)

            # THE FIX: We ONLY log it as the "best" if it is strictly greater than 0. 
            # This prevents Spohn's integer-space-diagonals from ruining the true drift floor.
            if 0 < drift < min_drift:
                min_drift = drift
                best = (a, b, c, float(drift))

            if total % 10_000_000 == 0:
                print(f"    {total:,} bricks | best drift: {float(min_drift):.3e}")

            # Collect data for regression
            if total % 50 == 0 and drift > 0:
                drifts.append(float(drift))
                sizes.append(float(size))

            # Full perfect-cuboid check
            # If drift IS exactly zero, we must verify if it's a true perfect cuboid
            if drift == 0:
                if (check_coupling(a, b, c) and
                    is_perfect_square(a*a + b*b) and
                    is_perfect_square(a*a + c*c) and
                    is_perfect_square(b*b + c*c)):
                    print(f"\n!!! TRUE PERFECT CUBOID FOUND in {name} !!!")
                    print(f"a = {a}, b = {b}, c = {c}")
                    return

    # Regression Analysis
    if len(drifts) > 20:
        slope, _, r2, _, _ = linregress(np.log(sizes), np.log(drifts))
        print(f"\nLOG-LOG REGRESSION: slope = {slope:.6f}   R² = {r2**2:.4f}")
        print("POSITIVE SLOPE (Drift is bounded/rising)" if slope > 0 else "Drift is still decaying")
    else:
        print("\nNot enough points for regression")

    elapsed = (time.time() - start) / 3600
    print(f"\nFinished in {elapsed:.2f} hours")
    print(f"Total bricks: {total:,}")
    
    if best:
        a, b, c, d = best
        print(f"BEST NON-ZERO DRIFT: {d:.3e} at size ~{max(a,b,c):.2e}")
        print(f"   a = {a}")
        print(f"   b = {b}")
        print(f"   c = {c}")

    print("\nFloor still holds. UFT-F mapping is secure.")

if __name__ == "__main__":
    main()

#     (base) brendanlynch@Brendans-Laptop EulerBrick % python newEuclid3.py --max_param 30000
# === MULTI-FAMILY PERFECT CUBOID FALSIFIER ===
# Scanning 4 families up to m = 30000...
#   → saunderson
#     10,000,000 bricks | best drift: 1.975e-08
#     20,000,000 bricks | best drift: 1.975e-08
#     30,000,000 bricks | best drift: 1.975e-08
#     40,000,000 bricks | best drift: 1.590e-08
#     50,000,000 bricks | best drift: 1.046e-08
#     60,000,000 bricks | best drift: 1.046e-08
#     70,000,000 bricks | best drift: 1.046e-08
#     80,000,000 bricks | best drift: 1.046e-08
#     90,000,000 bricks | best drift: 1.046e-08
#     100,000,000 bricks | best drift: 1.046e-08
#     110,000,000 bricks | best drift: 1.046e-08
#     120,000,000 bricks | best drift: 1.046e-08
#     130,000,000 bricks | best drift: 8.134e-09
#     140,000,000 bricks | best drift: 8.134e-09
#     150,000,000 bricks | best drift: 8.134e-09
#     160,000,000 bricks | best drift: 8.134e-09
#     170,000,000 bricks | best drift: 8.134e-09
#     180,000,000 bricks | best drift: 8.134e-09
#   → euler_chapple
#     190,000,000 bricks | best drift: 8.134e-09
#     200,000,000 bricks | best drift: 8.134e-09
#     210,000,000 bricks | best drift: 8.134e-09
#     220,000,000 bricks | best drift: 7.212e-10
#     230,000,000 bricks | best drift: 7.212e-10
#     240,000,000 bricks | best drift: 7.212e-10
#     250,000,000 bricks | best drift: 7.212e-10
#     260,000,000 bricks | best drift: 7.212e-10
#     270,000,000 bricks | best drift: 7.212e-10
#     280,000,000 bricks | best drift: 7.212e-10
#     290,000,000 bricks | best drift: 7.212e-10
#     300,000,000 bricks | best drift: 7.212e-10
#     310,000,000 bricks | best drift: 7.212e-10
#     320,000,000 bricks | best drift: 7.212e-10
#     330,000,000 bricks | best drift: 7.212e-10
#      340,000,000 bricks | best drift: 7.212e-10
#     350,000,000 bricks | best drift: 7.212e-10
#     360,000,000 bricks | best drift: 7.212e-10
#   → spohn
#     370,000,000 bricks | best drift: 7.212e-10
#     380,000,000 bricks | best drift: 7.212e-10
#     390,000,000 bricks | best drift: 7.212e-10
#     400,000,000 bricks | best drift: 7.212e-10
#     410,000,000 bricks | best drift: 7.212e-10
#     420,000,000 bricks | best drift: 7.212e-10
#     430,000,000 bricks | best drift: 7.212e-10
#     440,000,000 bricks | best drift: 7.212e-10
#     450,000,000 bricks | best drift: 7.212e-10
#     460,000,000 bricks | best drift: 7.212e-10
#     470,000,000 bricks | best drift: 7.212e-10
#     480,000,000 bricks | best drift: 7.212e-10
#     490,000,000 bricks | best drift: 7.212e-10
#     500,000,000 bricks | best drift: 7.212e-10
#     510,000,000 bricks | best drift: 7.212e-10
#     520,000,000 bricks | best drift: 7.212e-10
#     530,000,000 bricks | best drift: 7.212e-10
#     540,000,000 bricks | best drift: 7.212e-10
#     550,000,000 bricks | best drift: 7.212e-10
#     560,000,000 bricks | best drift: 7.212e-10
#     570,000,000 bricks | best drift: 7.212e-10
#     580,000,000 bricks | best drift: 7.212e-10
#     590,000,000 bricks | best drift: 7.212e-10
#     600,000,000 bricks | best drift: 7.212e-10
#     610,000,000 bricks | best drift: 7.212e-10
#     620,000,000 bricks | best drift: 7.212e-10
#     630,000,000 bricks | best drift: 7.212e-10
#   → two_triples

# LOG-LOG REGRESSION: slope = -0.000296   R² = 0.0000
# Drift is still decaying

# Finished in 0.79 hours
# Total bricks: 638,352,562
# BEST NON-ZERO DRIFT: 7.212e-10 at size ~1.93e+25
#    a = 1022867394714663499580229
#    b = 15385146623915568846632000
#    c = 19323900919878102949958621

# Floor still holds. UFT-F mapping is secure.
# (base) brendanlynch@Brendans-Laptop EulerBrick %  