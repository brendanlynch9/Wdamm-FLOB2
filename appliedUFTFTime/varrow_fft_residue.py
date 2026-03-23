#!/usr/bin/env python3
"""
varrow_fft_residue_fixed.py
Residue-grouped evaluator for Base-24 spectral potentials (BUGFIX).
This version computes both cosine- and sine-weighted k-sums per residue,
then applies the full trig identity:
  V_r(theta) = cos(rθ/24 + phi) * sum_k w_k cos(2π k θ)
             - sin(rθ/24 + phi) * sum_k w_k sin(2π k θ)
"""

import numpy as np
from math import pi
import time

def canonical_A_n(n_array, Sgrav=0.04344799, eps=1e-12):
    two_pi_over_24 = 2.0 * np.pi / 24.0
    cos_part = np.cos(two_pi_over_24 * n_array)
    A = Sgrav * cos_part / np.log(2.0 + cos_part + eps)
    A = A / np.log(n_array + 1.0)
    return A

def residue_grouped_V_fixed(N_max, theta, phi_u, sectors=24, Sgrav=0.04344799, chunk_k=1024):
    theta = np.asarray(theta, dtype=np.float64)
    R = sectors
    # allocate residue weight matrix: rows residues, columns k index (k = floor(n/R))
    max_k_len = (N_max // R) + 2
    residue_weights = np.zeros((R, max_k_len), dtype=np.float64)
    # Build coefficient vector and group by residue
    n = np.arange(1, N_max + 1, dtype=np.int64)
    A = canonical_A_n(n, Sgrav=Sgrav)
    for idx, nn in enumerate(n):
        r = int(nn % R)
        k = int(nn // R)
        residue_weights[r, k] += A[idx]
    # Prepare output V
    M = len(theta)
    V = np.zeros(M, dtype=np.float64)
    two_pi_over_24 = 2.0 * np.pi / 24.0
    # Precompute cos and sin factors for residue-phase term (without k)
    r_indices = np.arange(R)
    r_theta = two_pi_over_24 * (r_indices[:,None]) * theta[None,:]  # shape (R, M)
    cos_r_theta_phi = np.cos(r_theta + phi_u)  # shape (R, M)
    sin_r_theta_phi = np.sin(r_theta + phi_u)  # shape (R, M)
    j = np.arange(M)
    two_pi_over_M = 2.0 * np.pi / M
    # For each residue r, compute S_c = sum_k w_k cos(2π k theta_j) and
    # S_s = sum_k w_k sin(2π k theta_j), then add contribution:
    # V += S_c * cos_r_theta_phi[r,:] - S_s * sin_r_theta_phi[r,:]
    for r in range(R):
        w = residue_weights[r]
        nz = np.nonzero(w)[0]
        if nz.size == 0:
            continue
        maxk = nz[-1]
        ks = np.arange(0, maxk+1, dtype=np.int64)
        wk = w[:maxk+1]  # shape (K,)
        K = len(ks)
        S_c = np.zeros(M, dtype=np.float64)
        S_s = np.zeros(M, dtype=np.float64)
        # chunk over k to save memory
        for start in range(0, K, chunk_k):
            end = min(K, start + chunk_k)
            ks_chunk = ks[start:end]
            wk_chunk = wk[start:end]
            angle_chunk = np.outer(ks_chunk, j) * two_pi_over_M  # shape (K_chunk, M)
            cos_chunk = np.cos(angle_chunk)
            sin_chunk = np.sin(angle_chunk)
            S_c += (wk_chunk[:,None] * cos_chunk).sum(axis=0)
            S_s += (wk_chunk[:,None] * sin_chunk).sum(axis=0)
        V += S_c * cos_r_theta_phi[r,:] - S_s * sin_r_theta_phi[r,:]
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
    N_max = 100_000
    N_theta = 4096
    theta = np.linspace(0, 2*np.pi, N_theta, endpoint=False)
    omega_u = 0.0002073045
    phi_u = 2.0 * np.pi * omega_u
    t0 = time.time()
    V = residue_grouped_V_fixed(N_max, theta, phi_u, sectors=24, Sgrav=0.04344799, chunk_k=1024)
    t1 = time.time()
    conc, ints = sector_concentration(V, sectors=24)
    print(f"N_max={N_max:,}, N_theta={N_theta:,} -> top-2 concentration = {conc:.6f}% (elapsed {t1-t0:.3f}s)")
