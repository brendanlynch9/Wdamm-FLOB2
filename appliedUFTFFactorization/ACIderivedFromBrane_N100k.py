import numpy as np
from scipy.integrate import trapezoid
import matplotlib.pyplot as plt

# ================================
# UFT-F Core Constants (December 2025)
# ================================
omega_u = 0.0002073045                    # Hopf torsion invariant
phi_u = 2 * np.pi * omega_u               # Minimal T-breaking phase
c_uft_f = 0.003119337523010599            # Modularity Constant (spectral floor)

# ================================
# Ultra-Fast Vectorized Potentials
# ================================
def compute_potential(theta_grid, N, phase_shift=0.0):
    """
    Returns V(θ) = sum_{n=2}^N n^{-1 + ω_u} cos(2π n θ / 24 + phase_shift)
    
    NOTE: This function is vectorized over theta_grid, but for large N, 
    the caller must pass a small theta_grid (a 'chunk') to manage memory.
    """
    n = np.arange(2, N + 1, dtype=np.float64)           # (N-1,)
    coeffs = n ** (-1.0 + omega_u)                      # (N-1,)

    # Broadcast: theta_grid[:, None] (G_chunk, 1) × n[None, :] (1, N-1)
    angles = 2 * np.pi * theta_grid[:, None] * n[None, :] / 24.0 + phase_shift
    cosines = np.cos(angles)                            # (G_chunk, N-1)
    terms = coeffs[None, :] * cosines                   # (G_chunk, N-1)
    
    # The large intermediate arrays (angles, cosines, terms) are freed 
    # after this function returns for each chunk.
    return np.sum(terms, axis=1)                        # (G_chunk,)

# ================================
# L1 Norm Calculation
# ================================
def l1_norm(V_abs, theta_grid):
    return trapezoid(V_abs, theta_grid)

# ================================
# Simulation Parameters
# ================================
N_target = 100_000          # <<< PUSH HERE (Max N for the sum)
grid_points = 50_000        # High resolution for accurate L1
theta_grid = np.linspace(0, 2*np.pi, grid_points, dtype=np.float64)

# --- CHUNKING PARAMETERS (Critical for Memory Management) ---
# Each chunk processes this many grid points. 
# 5,000 points * 100,000 N * 8 bytes/float64 ≈ 4 GB peak RAM per potential
chunk_size = 5_000 
num_chunks = grid_points // chunk_size

# Initialize full potential arrays
V_sym = np.zeros(grid_points, dtype=np.float64)
V_aci = np.zeros(grid_points, dtype=np.float64)

print(f"Running N = {N_target:,}  |  Grid points = {grid_points:,}")
print(f"Computing potentials in {num_chunks} chunks of size {chunk_size:,}...")

# ================================
# CHUNKED POTENTIAL COMPUTATION
# ================================
for i in range(num_chunks):
    start_index = i * chunk_size
    end_index = (i + 1) * chunk_size
    
    # Get the slice of the grid (the 'chunk')
    theta_chunk = theta_grid[start_index:end_index]

    # Compute potentials for the chunk and store in the full array
    # This keeps the peak memory low
    V_sym[start_index:end_index] = compute_potential(theta_chunk, N_target, phase_shift=0.0)
    V_aci[start_index:end_index] = compute_potential(theta_chunk, N_target, phase_shift=phi_u)
    
    # Optional: Display progress to user
    print(f"  Completed chunk {i + 1}/{num_chunks}...", end='\r')

print("\nPotentials computed successfully.")

# ================================
# L1 Norm Calculation (using the now-filled full arrays)
# ================================
L1_sym = l1_norm(np.abs(V_sym), theta_grid)
L1_aci = l1_norm(np.abs(V_aci), theta_grid)

# Peak at θ = 0 (Can use the original non-chunked method as it's only 1 point)
V_sym_0 = compute_potential(np.array([0.0]), N_target, 0.0)[0]
V_aci_0 = compute_potential(np.array([0.0]), N_target, phi_u)[0]

# ================================
# Results
# ================================
print("\n" + "="*60)
print(f"SYMMETRIC (Pre-Collision)   →  L¹ ≈ {L1_sym:.10f}")
print(f"ACI (Post-Collision)        →  L¹ ≈ {L1_aci:.10f}")
print(f"ΔL¹ (ACI stabilization)     =  {L1_sym - L1_aci:.10f}")
print()
print(f"V_sym(θ=0)  ≈ {V_sym_0:.10f}")
print(f"V_aci(θ=0)  ≈ {V_aci_0:.10f}")
print(f"ΔV(0) (peak shave)          =  {V_sym_0 - V_aci_0:.12f}")
print()
print(f"c_UFT-F (spectral floor)    =  {c_uft_f:.15f}")
print("="*60)

# ================================
# Optional Plot (N=200 for clarity)
# ================================
plot_N = 200
theta_plot = np.linspace(0, 2*np.pi, 20_000)
V_sym_plot = compute_potential(theta_plot, plot_N, 0.0)
V_aci_plot = compute_potential(theta_plot, plot_N, phi_u)

plt.figure(figsize=(12, 6))
plt.plot(theta_plot, V_sym_plot, color='red',   label='Symmetric (Pre-Collision)', lw=1.5)
plt.plot(theta_plot, V_aci_plot, color='blue',  label='ACI (Post-Collision)',      lw=1.5)
plt.title(f'Potential V(θ) Across [0, 2π] — N = {plot_N} (illustrative)')
plt.xlabel('θ (radians)')
plt.ylabel('V(θ)')
plt.legend()
plt.grid(alpha=0.3)
plt.tight_layout()
plt.savefig('brane_collision_N100k_proof.png', dpi=300)
plt.show()

print("\nFigure saved as 'brane_collision_N100k_proof.png'")

# the output was: 
# (base) brendanlynch@Mac appliedUFTFFactorization % python ACIderivedFromBrane_N100k.py
# Running N = 100,000  |  Grid points = 50,000
# Computing potentials in 10 chunks of size 5,000...
#   Completed chunk 10/10...
# Potentials computed successfully.

# ============================================================
# SYMMETRIC (Pre-Collision)   →  L¹ ≈ 3.3020278278
# ACI (Post-Collision)        →  L¹ ≈ 3.3010962391
# ΔL¹ (ACI stabilization)     =  0.0009315887

# V_sym(θ=0)  ≈ 11.1038808249
# V_aci(θ=0)  ≈ 11.1038714055
# ΔV(0) (peak shave)          =  0.000009419372

# c_UFT-F (spectral floor)    =  0.003119337523011
# ============================================================

# Figure saved as 'brane_collision_N100k_proof.png'
# (base) brendanlynch@Mac appliedUFTFFactorization % 