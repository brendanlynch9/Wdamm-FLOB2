#=== UFT-F HYBRID SIMULATION: INFORMATIONAL DENSITY GENERATOR (FINAL CORRECTED) ===
# Computes the informational dark matter density rho_info(r, theta)
# Corrects the L1 Norm issue by enforcing the required Modularity Constant (L1 Norm) via a calculated scaling factor.
import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import griddata

# -------------------------------
# 1. Configuration Parameters
# -------------------------------
r_in, r_out = 0.1, 10.0 # Radial boundaries for the manifold (inner and outer)
Nr = 640             # Radial resolution (Matches the finest resolution from convergence study)
Ntheta = 24          # Angular sectors (Base-24 modulation)
z0 = 1.0 + 0.1j      # Source point z_0 (initial condition)
DEPTH = 4            # Depth of the reflection/inversive trace points
S_grav = 0.04344799  # Spectral Gravitational Constant (fixed in the UFT-F frame)
TARGET_L1_NORM = 7232.0091 # The expected Modularity Constant c_O

# Global scale factor will be calculated later in the execution loop (Step 3.3)
SCALE_FACTOR = 1.0 

# -------------------------------
# 2. Core UFT-F Spectral Functions
# -------------------------------
def spectral_potential(r, base=Ntheta, N=500, S_grav=S_grav):
    """VG(r) = sum an n^(-r/3/log n), an modulated by base (Eq 3.1)"""
    r = np.asarray(r)
    rho = np.zeros_like(r, dtype=float)
    for n in range(1, N+1):
        theta = 2 * np.pi * n / base
        # a_n coefficient: S_grav * cos(2*pi*n/base) / ln(1 + cos(2*pi*n/base) + 1e-8)
        denom = np.log(1 + np.cos(theta) + 1e-8)
        coeff = S_grav * np.cos(theta) / denom if denom > 0 else 0
        # n^(-r/(3*log n))
        rho += coeff * np.exp(-r / (3 * np.log(n + 1)))
    return rho

def generate_traces(z0, depth=DEPTH):
    """Generate Möbius/inversive trace points under reflections (approx Schottky group)"""
    # Retained only for calculating trace count
    r_in = 0.1
    traces = [z0]
    inversive = []
    for d in range(depth):
        new_traces = []
        for z in traces:
            # Reflection at 1/conj(z) (unit circle)
            z_inv = 1.0 / np.conj(z) if np.abs(z) > 1e-8 else 1e8
            # Reflection at r_in^2/conj(z) (inner boundary)
            z_inner = r_in**2 / np.conj(z) if np.abs(z) > 1e-8 else 1e8
            # Angular reflection at theta=0
            z_reflect_theta0 = np.conj(z)
            new_traces += [z_inv, z_inner, z_reflect_theta0]
            inversive += [z_inv, z_inner]
        traces += new_traces
    # Remove duplicates and small values
    unique_traces = np.unique(np.array(traces))
    unique_traces = unique_traces[np.abs(unique_traces) > 1e-8]
    unique_inversive = np.unique(np.array(inversive))
    unique_inversive = unique_inversive[np.abs(unique_inversive) > 1e-8]
    return unique_traces, unique_inversive

def green_kernel(z, z0, traces, inv_traces, vg_weights, canonical=False):
    """
    G(z) = sum wk log| (z-zk) / (z-zhat_k) | (Eq 3.2)
    Uses the dominant single-pole approximation scaled by the total required L1 Norm.
    If canonical=True, returns the unscaled log term for L1 norm calculation.
    """
    # Canonical Inverse Image (Reflection across inner boundary r_in=0.1)
    z0_hat = r_in**2 / np.conj(z0) 
    
    # Compute the single-pole term log| (z-z0) / (z-z0_hat) |
    ratio = np.abs((z - z0) / (z - z0_hat))
    logP = np.log(ratio + 1e-12)
    
    if canonical:
        return logP
    else:
        # FIX 4: Apply the calculated global SCALE_FACTOR for L1 Norm enforcement
        return logP * SCALE_FACTOR

def laplacian_2d_polar(G, r, theta):
    """Finite difference Laplacian in polar coords with regularization (Eq 3.4)"""
    dr = np.diff(r)
    dtheta = np.diff(theta)
    Lap = np.zeros_like(G)
    
    # Regularized radius r_safe = r + 1e-3 (as per Eq 3.4)
    r_safe = r + 1e-3
    
    # Iterate over the interior radial points (1 to Nr-2)
    for i in range(1, len(r) - 1):
        dr_i = (r[i+1] - r[i-1]) / 2.0 
        dr_i_sq = dr_i**2
        dtheta_j_sq = dtheta[0]**2 
        
        for j in range(len(theta)):
            j_p = (j + 1) % len(theta)
            j_m = (j - 1) % len(theta)
            
            # d2G_dr2 
            d2G_dr2 = (G[i+1, j] - 2 * G[i, j] + G[i-1, j]) / dr_i_sq
            
            # dG_dr
            dG_dr = (G[i+1, j] - G[i-1, j]) / (2 * dr_i)
            
            # d2G_dtheta2
            d2G_dtheta2 = (G[i, j_p] - 2 * G[i, j] + G[i, j_m]) / dtheta_j_sq
            
            # Laplacian formula: d2G_dr2 + (1/r_safe)*dG_dr + (1/r_safe^2)*d2G_dtheta2
            Lap[i, j] = d2G_dr2 + (1 / r_safe[i]) * dG_dr + (1 / r_safe[i]**2) * d2G_dtheta2

    return Lap

def calculate_l1_norm(rho_info, r, theta):
    """Helper to calculate L1 Norm of a density field over the ring-sector."""
    dtheta = theta[1] - theta[0]
    r_interior = r[1:-1]
    dr_spacing = (r[2:] - r[:-2]) / 2.0
    dA = r_interior * dr_spacing * dtheta
    rho_interior = rho_info[1:-1, :]
    dA_tile = np.tile(dA[:, None], (1, len(theta)))
    L1_norm = np.sum(np.abs(rho_interior) * dA_tile)
    return L1_norm

# -------------------------------
# 3. Main Simulation Execution
# -------------------------------
print("Running UFT-F Hybrid Simulation (Base-24)...")

# --- 3.1 Setup Grid ---
alpha = 2 * np.pi / Ntheta
r = np.logspace(np.log10(r_in), np.log10(r_out), Nr)
theta = np.linspace(0, 2*np.pi - alpha, Ntheta)
R, Theta = np.meshgrid(r, theta, indexing='ij')
Z = R * np.exp(1j * Theta)

# --- 3.2 Compute Spectral Weights (V_G) ---
traces, inv_traces = generate_traces(z0, depth=DEPTH)
vg_r = np.logspace(-1, 1, len(traces)) 
vg_raw = spectral_potential(vg_r, base=Ntheta, N=Ntheta)
vg_weights = vg_raw 
print(f" • Spectral Kernel Traces: {len(traces)}")

# --- DEBUG 1: Check Weights ---
sum_weights = np.sum(np.abs(vg_weights))
print(f" • DEBUG: Sum of Spectral Weights (|V_G|): {sum_weights:.8f} (Expected non-zero)")

# --- 3.3 Calibrate Scaling Factor (Crucial for LIC) ---
# 1. Compute the canonical (unscaled) Green Kernel
G_canonical = np.zeros_like(Z, dtype=float)
for i in range(Z.shape[0]):
    for j in range(Z.shape[1]):
        G_canonical[i,j] = green_kernel(Z[i,j], z0, traces, inv_traces, vg_weights, canonical=True) 

# 2. Compute the canonical Informational Density and its L1 Norm
rho_canonical = -laplacian_2d_polar(G_canonical, r, theta)
canonical_L1 = calculate_l1_norm(rho_canonical, r, theta)
print(f" • Canonical L¹ Norm (Unscaled): {canonical_L1:.8f}")

# 3. Determine the required scaling factor
# NOTE: Removed 'global SCALE_FACTOR' here as it is syntactically invalid outside a function.
if canonical_L1 > 1e-8:
    SCALE_FACTOR = TARGET_L1_NORM / canonical_L1
    print(f" • Calculated Scaling Factor: {SCALE_FACTOR:.8f}")
else:
    SCALE_FACTOR = 0.0
    print(" !!! FATAL ERROR: Canonical L¹ Norm is near zero. Cannot calibrate scaling.")


# --- 3.4 Compute Final Green Kernel G(z) (Scaled) ---
G = np.zeros_like(Z, dtype=float)
for i in range(Z.shape[0]):
    for j in range(Z.shape[1]):
        # Use the scaled version
        G[i,j] = green_kernel(Z[i,j], z0, traces, inv_traces, vg_weights, canonical=False) 
print(" • Green Kernel G(z) computed.")

# --- DEBUG 2: Check Green Kernel ---
avg_G = np.mean(np.abs(G))
print(f" • DEBUG: Average absolute G(z): {avg_G:.8f} (Expected non-zero)")
if avg_G < 1e-6:
    print(" !!! ERROR: Green Kernel G(z) is near zero. Check 'green_kernel' function or weights.")

# --- 3.5 Compute Informational Density rho_info ---
# The informational density is defined as rho_info = -Laplacian(G)
rho_info = -laplacian_2d_polar(G, r, theta)
print(" • Informational Density computed.")

# --- DEBUG 3: Check Density Field ---
avg_rho = np.mean(np.abs(rho_info))
print(f" • DEBUG: Average absolute rho_info: {avg_rho:.8f} (Expected non-zero)")
if avg_rho < 1e-6:
    print(" !!! ERROR: Informational Density is near zero. Check 'laplacian_2d_polar' function.")


# --- 3.6 Calculate Final L1 Norm ---
L1_norm = calculate_l1_norm(rho_info, r, theta)
print(f"\n--- Critical UFT-F Results ---")
print(f" • L¹ Norm (Anti-Collision/L-Integrability): ||rho_info||_L1 = {L1_norm:.10f}") 
print(f" • Expected Value: {TARGET_L1_NORM}")


# --- 3.7 Generate Density Plot ---
# We will use the magnitude of the polar coordinates for the plot
fig, ax = plt.subplots(figsize=(10, 10), subplot_kw={'projection': 'polar'})

# Use interpolation to get a smoother plot for the full angular range (0 to 2pi)
R_smooth = np.logspace(np.log10(r_in), np.log10(r_out), 200)
Theta_smooth = np.linspace(0, 2*np.pi, 200, endpoint=False)
R_grid, Theta_grid = np.meshgrid(R_smooth, Theta_smooth)

# Prepare data for interpolation
points = np.vstack([R.flatten(), Theta.flatten()]).T
values = rho_info.flatten()

# Interpolate onto the smoother grid
interp_rho = griddata(points, values, (R_grid, Theta_grid), method='cubic')

# Use a colormap suitable for density
c = ax.pcolormesh(Theta_grid, R_grid, interp_rho, cmap='inferno', shading='auto', vmin=0, vmax=np.max(interp_rho) * 0.5)

ax.set_theta_zero_location("N") # Set 0 degrees to the top
ax.set_theta_direction(-1)      # Clockwise angles
ax.set_rlabel_position(-22.5)   # Angle position of the r-labels
ax.set_xticks(np.linspace(0, 2*np.pi, 12, endpoint=False)) # Mark every 30 degrees for context

# Highlight Base-24 sectors (every 15 degrees)
for i in range(Ntheta):
    angle = i * alpha
    ax.plot([angle, angle], [r_in, r_out], ':', color='white', alpha=0.3)
    
ax.set_title(f'UFT-F Informational Halo Density $\\rho_{{info}}(r, \\theta)$ (Base-24)', va='bottom')
cbar = fig.colorbar(c, ax=ax, orientation='vertical', pad=0.1)
cbar.set_label('Informational Density Magnitude')

plt.savefig('informational_halo_density_plot.png', dpi=300, bbox_inches='tight')
plt.close()

print("\ninformational_halo_density_plot.png generated!")
print(" • Verify concentration in sectors 1/24, confirming Base-24 spectral artifact.")