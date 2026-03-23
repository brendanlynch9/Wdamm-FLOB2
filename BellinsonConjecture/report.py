#!/usr/bin/env python3
"""
UFT-F NEXT-GEN FALSIFIER SUITE
---------------------------------
- Scans derivations (linear, sqrt, inverse, log) across D = 2 → 4
- Computes numerical + topological + geometric penalties
- Identifies best structural fit
- Plots total cost vs D
- Checks ACI closure symbolically
"""

import numpy as np
import matplotlib.pyplot as plt
from sympy import S, N

# ----------------------------
# 1. LOCKED UFT-F BASES
# ----------------------------
E8_ROOT     = 1.0 / 240.0
PHI_SM      = 24 * (1 + E8_ROOT)
BASE_METRIC = 1.0 + E8_ROOT
OMEGA_U     = 0.0002073045
TARGETS = {"¹²C": 1.034200, "¹⁶O": 0.998741, "37a1": 0.041010}

# Topological / geometric penalties
S_TARGET       = 8.91
MAJ_PENALTY    = 50.0
DOF_SCALE      = 25.0
RAMA_SCALE     = 8.0

# ----------------------------
# 2. RESOLVER
# ----------------------------
def uft_f_resolver(system, c, phi=PHI_SM):
    base = BASE_METRIC
    if system == "¹²C":
        delta = phi * (2.0 / 5.0)
        return base + c * delta
    elif system == "¹⁶O":
        tension = 2.0 * c * (1.0 - 1.5 * OMEGA_U)
        return base - tension
    elif system == "37a1":
        return 1.0 / phi - c / (2 * np.pi)
    return np.nan

def numerical_error(c):
    return np.mean([abs(uft_f_resolver(k, c) - v) / v for k, v in TARGETS.items()])

# ----------------------------
# 3. PENALTIES
# ----------------------------
def stiffness_penalty(D): return (D - 3.0)**2 * (S_TARGET / 10.0)
def majorana_penalty(D): return MAJ_PENALTY if D % 2 == 0 else 0.0
def dof_penalty(D): return DOF_SCALE * (D - 3.0)**2
def ramachandran_penalty(D): return RAMA_SCALE * abs(D % 3)
def total_cost(c, D):
    return numerical_error(c) + stiffness_penalty(D) + majorana_penalty(D) + dof_penalty(D) + ramachandran_penalty(D)

# ----------------------------
# 4. DERIVATIONS
# ----------------------------
def derivations(D):
    residue = (240.0 - 1.0) / 240.0
    return {
        "linear_density":  (D * residue) / (240.0 * np.pi),
        "sqrt_density":    (D * residue) / (np.sqrt(240.0) * np.pi),
        "inverse_density": residue / (D * 240.0 * np.pi),
        "log_density":     (D * residue) / (np.log(240.0) * np.pi),
    }

# ----------------------------
# 5. SCAN D = 2 → 4
# ----------------------------
Ds = np.arange(2.0, 4.01, 0.05)
results = []

for D in Ds:
    for name, c in derivations(D).items():
        tot = total_cost(c, D)
        num_err = numerical_error(c)
        results.append((name, D, c, tot, num_err))

# Find best overall
best = min(results, key=lambda x: x[3])

# ----------------------------
# 6. PLOTTING TOTAL COST VS D
# ----------------------------
plt.figure(figsize=(10,6))
for name in ["linear_density","sqrt_density","inverse_density","log_density"]:
    costs = [total_cost(derivations(D)[name], D) for D in Ds]
    plt.plot(Ds, costs, label=name)
plt.axvline(best[1], color='k', linestyle='--', label=f'Best D={best[1]:.2f}')
plt.xlabel("Dimension D")
plt.ylabel("Total Structural Cost")
plt.title("UFT-F Total Structural Cost vs Dimension")
plt.legend()
plt.grid(True)
plt.show()

# ----------------------------
# 7. PRINT REPORT
# ----------------------------
print("\nUFT-F NEXT-GEN FALSIFIER REPORT")
print("="*80)
print(f"BEST OVERALL STRUCTURAL FIT:")
print(f"  Derivation : {best[0]}")
print(f"  Dimension  : {best[1]:.2f}")
print(f"  c          : {best[2]:.8f}")
print(f"  Total cost : {best[3]:.4f} (numerical only = {best[4]*100:.3f}%)")
print("-"*80)

# Main resolver validation with best c
print("\nMain resolver validation (best c):")
for sys, targ in TARGETS.items():
    pred = uft_f_resolver(sys, best[2])
    err = abs(pred - targ) / targ * 100
    print(f"{sys:6} | target {targ:10.6f} | predicted {pred:10.6f} | error {err:6.4f}%")

# ----------------------------
# 8. ACI SYMBOLIC CHECK
# ----------------------------
derived_c = S(best[2])
R_ALPHA = S(1 + 1/240)
potential_sum = N(1 - derived_c + 1/240, 12)
print("\nACI Symbolic Closure Check:")
print(f"  1 - c + residue = {potential_sum} ~ 1.0 ? {'PASS' if abs(potential_sum-1)<0.005 else 'FAIL'}")
print("="*80)

# (base) brendanlynch@Brendans-Laptop BellinsonConjecture % python report.py

# UFT-F NEXT-GEN FALSIFIER REPORT
# ================================================================================
# BEST OVERALL STRUCTURAL FIT:
#   Derivation : linear_density
#   Dimension  : 3.05
#   c          : 0.00402833
#   Total cost : 0.4697 (numerical only = 0.499%)
# --------------------------------------------------------------------------------

# Main resolver validation (best c):
# ¹²C    | target   1.034200 | predicted   1.043000 | error 0.8509%
# ¹⁶O    | target   0.998741 | predicted   0.996113 | error 0.2632%
# 37a1   | target   0.041010 | predicted   0.040853 | error 0.3837%

# ACI Symbolic Closure Check:
#   1 - c + residue = 1.00013833348 ~ 1.0 ? PASS
# ================================================================================
# (base) brendanlynch@Brendans-Laptop BellinsonConjecture % 

