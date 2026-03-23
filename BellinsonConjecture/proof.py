#!/usr/bin/env python3
"""
ROBUST UNIVERSAL RIGIDITY TEST
------------------------------

This script performs a falsifiable universality test on elliptic curves.

NO fitted constants.
NO reference conductor.
NO target spectral floor.

It computes the canonical BSD quantity:

    Xi(E) = L(E,1) / (Omega_E * Tamagawa_Product)

and tests whether it is universal across curves.

If variance is large -> universality falsified.
If variance collapses -> structural evidence.
"""

import mpmath as mp

mp.dps = 80


# ============================================================
# Canonical Approximate Functional Equation (Weight 2)
# ============================================================

def L_value_rank0(coeffs, conductor):
    """
    Computes L(E,1) using the approximate functional equation
    for weight 2 modular forms.
    """

    N = mp.mpf(conductor)
    total = mp.mpf(0)

    for n in range(1, len(coeffs)):
        x = 2 * mp.pi * n / mp.sqrt(N)
        total += coeffs[n] * mp.expint(1, x)

    return 2 * total


# ============================================================
# Curve Database (NO tuning)
# Insert verified LMFDB arithmetic data only
# ============================================================

curves = [

    {
        "name": "11a1",
        "rank": 0,
        "conductor": 11,
        "omega": mp.mpf("1.269209304"),
        "tamagawa": 5,
        "coeffs": [0,1,-1,-1,1,-1,1,1,-1,1,-1]  # truncated example
    },

    {
        "name": "37a1",
        "rank": 1,
        "conductor": 37,
        "omega": mp.mpf("2.993454416"),
        "tamagawa": 3,
        "coeffs": [
            0, 1, -2, -3, 2, -2, 6, -1, 0, 6, 4,
            -5, -6, 0, -2, 9, -7, 3, -8, -1
        ]
    },

]


# ============================================================
# Universality Test
# ============================================================

results = []

print("\nROBUST UNIVERSALITY TEST")
print("="*70)
print(f"{'Curve':<10} | {'Xi(E)':<25}")
print("-"*70)

for E in curves:

    if E["rank"] != 0:
        print(f"{E['name']}: Rank > 0 not handled in this strict test.")
        continue

    L1 = L_value_rank0(E["coeffs"], E["conductor"])

    Xi = L1 / (E["omega"] * E["tamagawa"])

    results.append(Xi)

    print(f"{E['name']:<10} | {mp.nstr(Xi, 25)}")


print("-"*70)

if len(results) > 1:
    mean_val = sum(results)/len(results)
    variance = sum((x-mean_val)**2 for x in results)/len(results)

    print(f"Mean Xi(E)      : {mp.nstr(mean_val, 20)}")
    print(f"Variance Xi(E)  : {mp.nstr(variance, 20)}")

    if variance < mp.mpf("1e-10"):
        print("\nRESULT: Strong universality evidence.")
    else:
        print("\nRESULT: Universality falsified (variance non-zero).")
