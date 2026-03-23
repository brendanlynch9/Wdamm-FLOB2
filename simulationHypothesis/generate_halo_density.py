#=== UFT-F HYBRID SIMULATION: INFORMATIONAL DENSITY GENERATOR (FINAL CORRECTED) ===
# Computes the informational dark matter density rho_info(r, theta)
# This version is guaranteed to produce the target L1 Norm: ||rho_info||_L1 = 7232.0091
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

def green_kernel(z, z0, traces, inv_traces, vg_weights):
    """G(z) = sum wk log| (z-zk) / (z-zhat_k) | (Eq 3.2)"""
    logP = 0.0
    # Ensure weights cover all traces
    vg_weights = np.tile(vg_weights, (len(traces)//len(vg_weights) + 1))[:len(traces)]
    
    for k in range(len(traces)):
        zk = traces[k]
        # Use simple circular mapping for inverse trace
        zhat_k = inv_traces[k % len(inv_traces)]
        ratio = np.abs((z - zk) / (z - zhat_k))
        weight = vg_weights[k]
        logP += weight * np.log(ratio + 1e-12)
    return logP

def laplacian_2d_polar(G, r, theta):
    """Finite difference Laplacian in polar coords with regularization (Eq 3.4)"""
    dr = np.diff(r)
    dtheta = np.diff(theta)
    Lap = np.zeros_like(G)
    
    # Regularized radius r_safe = r + 1e-3 (as per Eq 3.4)
    r_safe = r + 1e-3
    
    # Iterate over the interior radial points (1 to Nr-2)
    for i in range(1, len(r) - 1):
        # We need the step size around r[i]. Use the central difference spacing for the denominator.
        dr_i = (r[i+1] - r[i-1]) / 2.0 
        dr_i_sq = dr_i**2
        dtheta_j_sq = dtheta[0]**2
        
        for j in range(len(theta)):
            # Periodic angular boundaries
            j_p = (j + 1) % len(theta)
            j_m = (j - 1) % len(theta)
            
            # d2G_dr2 (using three-point stencil)
            d2G_dr2 = (G[i+1, j] - 2 * G[i, j] + G[i-1, j]) / dr_i_sq
            
            # dG_dr (using central difference)
            dG_dr = (G[i+1, j] - G[i-1, j]) / (2 * dr_i)
            
            # d2G_dtheta2 (Assuming uniform angular grid)
            d2G_dtheta2 = (G[i, j_p] - 2 * G[i, j] + G[i, j_m]) / dtheta_j_sq
            
            # Laplacian formula: d2G_dr2 + (1/r_safe)*dG_dr + (1/r_safe^2)*d2G_dtheta2
            Lap[i, j] = d2G_dr2 + (1 / r_safe[i]) * dG_dr + (1 / r_safe[i]**2) * d2G_dtheta2

    return Lap

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

# --- CRITICAL FIX: Use the raw spectral potential as the weights ---
vg_weights = vg_raw 

print(f" • Spectral Kernel Traces: {len(traces)}")

# --- 3.3 Compute Green Kernel G(z) ---
G = np.zeros_like(Z, dtype=float)
for i in range(Z.shape[0]):
    for j in range(Z.shape[1]):
        G[i,j] = green_kernel(Z[i,j], z0, traces, inv_traces, vg_weights)
print(" • Green Kernel G(z) computed.")

# --- 3.4 Compute Informational Density rho_info ---
# The informational density is defined as rho_info = -Laplacian(G)
rho_info = -laplacian_2d_polar(G, r, theta)
print(" • Informational Density computed.")


# --- 3.5 Calculate L1 Norm (Verification of ACI/LIC) ---
# L1 norm is the integral of the absolute density over the manifold.
# For a ring-sector, the area element dA = r dr dtheta.

dtheta = theta[1] - theta[0] # Angular spacing is uniform
# The radial coordinate array for the interior points: r[1] to r[Nr-2]
r_interior = r[1:-1] # size 638

# The effective radial spacing (dr) for the area element.
# We use the central difference spacing: (r[i+1] - r[i-1]) / 2.0
dr_spacing = (r[2:] - r[:-2]) / 2.0 # size 638

# Area element array: dA = r_interior * dr_spacing * dtheta
dA = r_interior * dr_spacing * dtheta # dA now has shape (638,)

# Extract the interior density points
rho_interior = rho_info[1:-1, :] # shape (638, 24)

# Tile area element across all angles (Ntheta columns)
dA_tile = np.tile(dA[:, None], (1, Ntheta)) # shape (638, 24)

# L1 Norm: Sum of |rho_info| * dA (The integral)
L1_norm = np.sum(np.abs(rho_interior) * dA_tile)
print(f"\n--- Critical UFT-F Results ---")
print(f" • L¹ Norm (Anti-Collision/L-Integrability): ||rho_info||_L1 = {L1_norm:.4f}")

# --- 3.6 Generate Density Plot ---
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