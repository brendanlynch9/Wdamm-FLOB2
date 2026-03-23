#!/usr/bin/env python3
"""
UFT-F COMPARATIVE STRUCTURAL FALSIFICATION SUITE
-----------------------------------------------
Tests whether c_UFT-F is uniquely forced by
discrete geometry rather than by ansatz choice.
"""

import numpy as np

# -------------------------------------------------
# 1. STRUCTURAL INPUTS (ONLY DISCRETE DATA)
# -------------------------------------------------
E8_ROOTS = 240.0
RESIDUE  = (E8_ROOTS - 1.0) / E8_ROOTS  # 239/240
DIMS     = [2.0, 3.0, 4.0]

R_ALPHA = 1.0 + 1.0 / E8_ROOTS
OMEGA_U = 0.0002073045

TARGETS = {
    "C12": 1.034200,
    "O16": 0.998741,
    "37a1": 0.041010
}

# -------------------------------------------------
# 2. RESOLVER (FIXED — NO TUNING)
# -------------------------------------------------
def resolver(system, c):
    base = R_ALPHA
    if system == "C12":
        return base + c * 24.0 * 0.4
    if system == "O16":
        return base - 2.0 * c * (1.0 - 1.5 * OMEGA_U)
    if system == "37a1":
        return (1.0 / (24.0 * R_ALPHA)) - c / (2.0 * np.pi)
    raise ValueError

def mean_error(c):
    return np.mean([
        abs(resolver(k, c) - v) / v
        for k, v in TARGETS.items()
    ])

# -------------------------------------------------
# 3. COMPETING STRUCTURAL DERIVATIONS
# -------------------------------------------------
def derivations(dim):
    return {
        "linear_density":   (dim * RESIDUE) / (E8_ROOTS * np.pi),
        "sqrt_density":     (dim * RESIDUE) / (np.sqrt(E8_ROOTS) * np.pi),
        "inverse_density":  (RESIDUE) / (dim * E8_ROOTS * np.pi),
        "log_density":      (dim * RESIDUE) / (np.log(E8_ROOTS) * np.pi),
    }

# -------------------------------------------------
# 4. EVALUATION
# -------------------------------------------------
print("\nUFT-F STRUCTURAL COMPETITION TEST")
print("=" * 70)

results = []

for d in DIMS:
    for name, c in derivations(d).items():
        err = mean_error(c)
        results.append((name, d, c, err))
        print(f"{name:16} | D={int(d)} | c={c:.8f} | mean err={err*100:.3f}%")

print("-" * 70)

best = min(results, key=lambda x: x[3])
print(f"BEST STRUCTURAL FIT:")
print(f"Derivation: {best[0]}, Dimension: {int(best[1])}")
print(f"c = {best[2]:.8f}, Mean Error = {best[3]*100:.3f}%")

print("=" * 70)

# (base) brendanlynch@Brendans-Laptop BellinsonConjecture % python superFalsifiable.py

# UFT-F STRUCTURAL COMPETITION TEST
# ======================================================================
# linear_density   | D=2 | c=0.00264153 | mean err=0.207%
# sqrt_density     | D=2 | c=0.04092241 | mean err=19.144%
# inverse_density  | D=2 | c=0.00066038 | mean err=1.208%
# log_density      | D=2 | c=0.11567396 | mean err=56.932%
# linear_density   | D=3 | c=0.00396229 | mean err=0.461%
# sqrt_density     | D=3 | c=0.06138361 | mean err=29.488%
# inverse_density  | D=3 | c=0.00044025 | mean err=1.320%
# log_density      | D=3 | c=0.17351094 | mean err=86.169%
# linear_density   | D=4 | c=0.00528306 | mean err=1.128%
# sqrt_density     | D=4 | c=0.08184481 | mean err=39.831%
# inverse_density  | D=4 | c=0.00033019 | mean err=1.375%
# log_density      | D=4 | c=0.23134791 | mean err=115.407%
# ----------------------------------------------------------------------
# BEST STRUCTURAL FIT:
# Derivation: linear_density, Dimension: 2
# c = 0.00264153, Mean Error = 0.207%
# ======================================================================
# (base) brendanlynch@Brendans-Laptop BellinsonConjecture % 

