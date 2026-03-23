"""
varrow_fft_residue_fixed.py
Residue-grouped evaluator for Base-24 spectral potentials.
Fully corrected to reproduce canonical top-2 concentration.
"""

import numpy as np
from math import pi
import time

def canonical_A_n(n_array, Sgrav=0.04344799, eps=1e-12):
    """
    Canonical coefficient A_n as in the original method.
    """
    two_pi_over_24 = 2.0 * np.pi / 24.0
    cos_part = np.cos(two_pi_over_24 * n_array)
    A = Sgrav * cos_part / np.log(2.0 + cos_part + eps)
    A = A / np.log(n_array + 1.0)
    return A

def residue_grouped_V_fixed(N_max, theta, omega_u, phi_u, sectors=24, Sgrav=0.04344799):
    theta = np.asarray(theta, dtype=np.float64)
    R = sectors
    n = np.arange(1, N_max+1)
    A = canonical_A_n(n, Sgrav=Sgrav)

    # Group by residue
    residue_weights = [ [] for _ in range(R) ]
    for nn, an in zip(n, A):
        r = nn % R
        k = nn // R
        residue_weights[r].append((k, an))

    V = np.zeros_like(theta)
    for r in range(R):
        if not residue_weights[r]:
            continue
        ks, ws = zip(*residue_weights[r])
        ks = np.array(ks)
        ws = np.array(ws)
        r_theta_phi = 2*np.pi*r*theta/24.0 + phi_u
        cos_r = np.cos(r_theta_phi)
        sin_r = np.sin(r_theta_phi)
        # k-dependent factors
        angle_k = 2*np.pi*ks[:,None]*theta[None,:]  # shape K x M
        cos_k = np.cos(angle_k)
        sin_k = np.sin(angle_k)
        V += cos_r * np.sum(ws[:,None]*cos_k, axis=0) - sin_r * np.sum(ws[:,None]*sin_k, axis=0)
    return V


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

if __name__ == "__main__":
    # Demo run
    N_max = 100_000
    N_theta = 4096
    theta = np.linspace(0, 2*np.pi, N_theta, endpoint=False)
    omega_u = 0.0002073045
    phi_u = 2.0 * np.pi * omega_u
    t0 = time.time()
    V = residue_grouped_V_fixed(N_max, theta, omega_u, phi_u, sectors=24, Sgrav=0.04344799)
    t1 = time.time()
    conc, ints = sector_concentration(V, sectors=24)
    print(f"N_max={N_max:,}, N_theta={N_theta:,} -> top-2 concentration = {conc:.6f}% (elapsed {t1-t0:.3f}s)")

#     the output was: 
#     (base) brendanlynch@Mac appliedUFTFTime % python varrow_fft_residue_fixed.py
# N_max=100,000, N_theta=4,096 -> top-2 concentration = 36.356131% (elapsed 4.215s)
# (base) brendanlynch@Mac appliedUFTFTime % 
