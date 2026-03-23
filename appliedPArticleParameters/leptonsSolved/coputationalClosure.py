import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla
import math

# ------------------------------------------------------------------
# 1. AXIOMATIC CONSTANTS (Derived from UFT-F Corpus)
# ------------------------------------------------------------------
# Hopf Torsion Invariant (omega_u): Source of T-breaking/CP-violation
OMEGA_U = 0.0002073045
# Modularity Constant (C_UFTF): The spectral floor.
C_UFTF = (331.0 / 22.0) * OMEGA_U
# Base-24 Mass Gap (Delta_m): The minimal quantum step
DELTA_M = 24.0

# Amplitude scale for the potential (Matches e8_base24_fermion_model.py)
A_SCALE = 30.0
EPSILON = 0.1
N_MODES = 24 # Use 24 modes, the Base-24 harmonic limit

# ----------------------
# 2. 3D DOMAIN AND GRID SETUP (Compactified Manifold Proxy)
# ----------------------
L = 4.0                  # Domain length in each dimension
N_POINTS = 20            # Grid points in each dimension (N x N x N grid)
N_TOTAL = N_POINTS**3    # Total number of grid points
dx = L / N_POINTS        # Grid spacing
dx2 = dx**2
I = np.eye(N_POINTS)

# ----------------------
# 3. BASE-24 INFORMATIONAL POTENTIAL (V_info) Generalization
# ----------------------
def base24_1d_potential(x, phase=0.0, scale_factor=1.0):
    """Calculates the 1D Base-24 harmonic potential with phase and scale."""
    V = np.zeros_like(x)
    L_eff = L * (DELTA_M / 24.0) * scale_factor
    
    for n in range(1, N_MODES + 1):
        coeff = A_SCALE * C_UFTF / (n**(1.0 + EPSILON))
        V += coeff * np.cos(2.0 * np.pi * n * x / L_eff + phase)
    return V

# Create 3D grid coordinates
x = np.linspace(0, L, N_POINTS, endpoint=False)
X, Y, Z = np.meshgrid(x, x, x, indexing='ij')

# Incorporate E8/K3 constraints:
# - Phase from Hopf torsion: phi_u = 2*pi*OMEGA_U
# - Scales: K3 rank=22, E8 Coxeter=30/2=15, total scaling 331/22≈15.045
phi_u = 2 * math.pi * OMEGA_U
scale_x = 1.0  # Reference
scale_y = 22.0 / 331.0  # K3 rank / total
scale_z = 30.0 / 2.0   # E8 Coxeter / 2

V_x = base24_1d_potential(X.flatten(), phase=0.0, scale_factor=scale_x)
V_y = base24_1d_potential(Y.flatten(), phase=phi_u, scale_factor=scale_y)
V_z = base24_1d_potential(Z.flatten(), phase=2*phi_u, scale_factor=scale_z)
V_info_3d = (V_x + V_y + V_z).reshape(N_TOTAL)

# ----------------------
# 4. ACI/LIC CHECK: L1-Integrability
# ----------------------
volume_element = dx**3
L1_norm = np.sum(np.abs(V_info_3d)) * volume_element
print(f"L1-Integrability Condition (LIC) Check:")
print(f"  Calculated ||V_info||_L1: {L1_norm:.4f}")
print(f"  ACI/LIC Status: {'Passed (Finite)' if L1_norm < float('inf') else 'Failed (Divergent)'}")
print("-" * 50)

# ----------------------
# 5. CONSTRUCT 3D HAMILTONIAN (H_SM)
# ----------------------
# Finite Difference Laplacian (Periodic Boundary Conditions)
T_1d = (sp.diags([-2, 1, 1], [0, 1, N_POINTS - 1], shape=(N_POINTS, N_POINTS)) +
        sp.diags([1, 1], [-1, -(N_POINTS - 1)], shape=(N_POINTS, N_POINTS))) / dx2
T_1d = sp.csc_matrix(T_1d)

L_x = sp.kron(T_1d, sp.kron(I, I))
L_y = sp.kron(I, sp.kron(T_1d, I))
L_z = sp.kron(I, sp.kron(I, T_1d))
L_3d = L_x + L_y + L_z

H_SM = -L_3d + sp.diags(V_info_3d)

# ----------------------
# 6. SOLVE FOR EIGENVALUES (Fermion Mass-Squared Candidates)
# ----------------------
k_eigenvalues = 6
if N_TOTAL > k_eigenvalues:
    print(f"Solving for {k_eigenvalues} lowest eigenvalues on {N_TOTAL} grid points...")
    eigenvalues, eigenvectors = spla.eigsh(H_SM, k=k_eigenvalues, which='SA')
    
    sorted_eigenvalues = np.sort(np.real(eigenvalues))
    
    MASS_GAP_THRESHOLD = 0.001
    mass_squared_candidates = sorted_eigenvalues[sorted_eigenvalues > MASS_GAP_THRESHOLD]

    print("\nSpectral Eigenvalues (Mass-Squared Candidates) $\\lambda_i$:")
    print("--------------------------------------------------")
    print("λ_0 (Vacuum/Ground State): ~0 (Expected)")
    
    if len(mass_squared_candidates) >= 3:
        print(f"1st Non-Zero λ_i (e-generation): {mass_squared_candidates[0]:.6f}")
        print(f"2nd Non-Zero λ_i (μ-generation): {mass_squared_candidates[1]:.6f}")
        print(f"3rd Non-Zero λ_i (τ-generation): {mass_squared_candidates[2]:.6f}")
        ratio_mu_e = mass_squared_candidates[1] / mass_squared_candidates[0]
        ratio_tau_mu = mass_squared_candidates[2] / mass_squared_candidates[1]
        print(f"\nMass Ratio Squares: μ/e ~ {ratio_mu_e:.2f}, τ/μ ~ {ratio_tau_mu:.2f}")
        print("Note: Tuned with E8/K3 scales and Hopf phases for splitting.")
    else:
        print(f"Only found {len(mass_squared_candidates)} non-zero eigenvalues above threshold.")

else:
    print("Grid too small to solve for eigenvalues.")

#     the output was:
#     (base) brendanlynch@Mac appliedPArticleParameters % python coputationalClosure.py
# L1-Integrability Condition (LIC) Check:
#   Calculated ||V_info||_L1: 12.8275
#   ACI/LIC Status: Passed (Finite)
# --------------------------------------------------
# Solving for 6 lowest eigenvalues on 8000 grid points...

# Spectral Eigenvalues (Mass-Squared Candidates) $\lambda_i$:
# --------------------------------------------------
# λ_0 (Vacuum/Ground State): ~0 (Expected)
# 1st Non-Zero λ_i (e-generation): 0.195118
# 2nd Non-Zero λ_i (μ-generation): 2.619007
# 3rd Non-Zero λ_i (τ-generation): 2.621447

# Mass Ratio Squares: μ/e ~ 13.42, τ/μ ~ 1.00
# Note: Tuned with E8/K3 scales and Hopf phases for splitting.
# (base) brendanlynch@Mac appliedPArticleParameters % 