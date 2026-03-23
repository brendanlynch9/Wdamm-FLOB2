"""
compare_varrow_methods.py
Compare direct, quick, and residue-grouped evaluations of V(theta).
"""

import numpy as np
import time
from varrow_fft_residue_fixed import residue_grouped_V_fixed, canonical_A_n

# --------------------------
# Direct method (naive)
# --------------------------
def direct_V(N_max, theta, phi_u, Sgrav=0.04344799):
    theta = np.asarray(theta)
    n = np.arange(1, N_max+1)
    A = canonical_A_n(n, Sgrav=Sgrav)
    angles = 2.0 * np.pi * n[:, None] * theta[None, :] / 24.0 + phi_u
    return np.dot(A, np.cos(angles))

# --------------------------
# Quick method (vectorized, similar to residue)
# --------------------------
def quick_V(N_max, theta, phi_u, Sgrav=0.04344799):
    # vectorized direct sum for speed
    theta = np.asarray(theta)
    n = np.arange(1, N_max+1)
    A = canonical_A_n(n, Sgrav=Sgrav)
    angles = 2.0 * np.pi * n[:, None] * theta[None, :] / 24.0 + phi_u
    return np.sum(A[:, None] * np.cos(angles), axis=0)

# --------------------------
# Sector concentration
# --------------------------
def sector_concentration(V, sectors=24):
    M = len(V)
    theta = np.linspace(0, 2*np.pi, M, endpoint=False)
    bounds = np.linspace(0, 2*np.pi, sectors+1)
    integrals = []
    for i in range(sectors):
        idx = (theta >= bounds[i]) & (theta < bounds[i+1])
        integrals.append(np.trapz(np.abs(V[idx]), theta[idx]))
    total = sum(integrals)
    top2 = sum(sorted(integrals, reverse=True)[:2])
    return top2 / total * 100.0, integrals

# --------------------------
# Main comparison
# --------------------------
if __name__ == "__main__":
    N_max = 100_000
    N_theta = 4096
    sectors = 24
    Sgrav = 0.04344799
    omega_u = 0.0002073045
    phi_u = 2.0 * np.pi * omega_u
    theta = np.linspace(0, 2*np.pi, N_theta, endpoint=False)

    methods = {
        'direct': lambda N_max, theta: direct_V(N_max, theta, phi_u, Sgrav),
        'quick': lambda N_max, theta: quick_V(N_max, theta, phi_u, Sgrav),
        'residue': lambda N_max, theta: residue_grouped_V_fixed(N_max, theta, omega_u, phi_u, sectors, Sgrav)
    }

    results = {}
    for name, func in methods.items():
        t0 = time.time()
        V = func(N_max, theta)
        t1 = time.time()
        conc, ints = sector_concentration(V, sectors)
        results[name] = (V, conc)
        print(f"{name}: top-2 concentration = {conc:.6f}%, elapsed {t1-t0:.3f}s")

    # Compute max absolute differences
    V_direct = results['direct'][0]
    for name in ['quick', 'residue']:
        V_method = results[name][0]
        max_diff = np.max(np.abs(V_direct - V_method))
        print(f"Max abs diff direct-{name}: {max_diff:.6e}")


# the output was:
# (base) brendanlynch@Mac appliedUFTFTime % python compare_varrow_methods.py

# direct: top-2 concentration = 36.356131%, elapsed 23.219s
# quick: top-2 concentration = 36.356131%, elapsed 42.183s
# residue: top-2 concentration = 36.356131%, elapsed 4.064s
# Max abs diff direct-quick: 4.882812e-04
# Max abs diff direct-residue: 2.005015e+01
# (base) brendanlynch@Mac appliedUFTFTime % 