#!/usr/bin/env python3
"""
UFT-F FINAL ADMISSIBILITY: SPHERICAL NORMALIZATION
--------------------------------------------------
Refining the derivation of c to account for 3-sphere projection.
"""

import numpy as np

# 1. STRUCTURAL DATA
E8_ROOTS = 240.0
RESIDUE  = (E8_ROOTS - 1.0) / E8_ROOTS
R_ALPHA  = 1.0 + 1.0 / E8_ROOTS
PHI_SM   = 24.0 * R_ALPHA
OMEGA_U  = 0.0002073045
TARGETS  = {"C12": 1.034200, "O16": 0.998741, "37a1": 0.041010}

# 2. THE GEOMETRIC ADMISSIBILITY CHECK
def check_admissibility(dim, c):
    # The TCCH Mass Gap requirement: 1/24
    theoretical_gap = 1.0 / 24.0
    # Measured leakage: The flux through the 3D boundary
    measured_gap = (dim * c * np.pi) / (RESIDUE * (dim/3.0))
    
    # 3D is only admissible if the Gap is stable
    is_admissible = abs(measured_gap - theoretical_gap) < 0.001
    return is_admissible, abs(measured_gap - theoretical_gap)

# 3. SPHERICAL DERIVATION
def derive_c(dim):
    # Spherical Flux: V_24 / (Surface of 3-sphere * Renormalization)
    surface_3s = 2.0 * (np.pi**2)
    V_24 = 2.0
    # The flux is regulated by the dimension of the projection
    return (dim * V_24 * RESIDUE) / (surface_3s * PHI_SM)

print("\nUFT-F SPHERICAL ADMISSIBILITY COMPETITION")
print("=" * 75)
print(f"{'Structure':<15} | {'Fit Err':<10} | {'Gap Leak':<10} | {'Status'}")
print("-" * 75)

results = []
for d in [2.0, 3.0, 4.0]:
    c = derive_c(d)
    
    # Resolver Logic
    err_c12 = abs((R_ALPHA + c*24*0.4) - TARGETS["C12"]) / TARGETS["C12"]
    err_o16 = abs((R_ALPHA - 2.0*c*(1.0-1.5*OMEGA_U)) - TARGETS["O16"]) / TARGETS["O16"]
    err_37a = abs(((1.0/(24.0*R_ALPHA)) - c/(2.0*np.pi)) - TARGETS["37a1"]) / TARGETS["37a1"]
    fit_err = np.mean([err_c12, err_o16, err_37a])
    
    admissible, leak = check_admissibility(d, c)
    status = "ADMISSIBLE" if admissible else "LEAKY (INVALID)"
    
    results.append((d, fit_err, leak, status))
    print(f"D={int(d)} Spherical  | {fit_err*100:8.3f}% | {leak:10.5f} | {status}")

print("-" * 75)
valid = [r for r in results if r[3] == "ADMISSIBLE"]
if valid:
    best = min(valid, key=lambda x: x[1])
    print(f"CONCLUSION: D={int(best[0])} locks as the Optimal Admissible Structure.")
else:
    print("CONCLUSION: Structural Leaks detected. Adjusting Spherical Surface logic.")
print("=" * 75)