# === UFT-F CONTROL RUNS: Generate Base-12/24/48 PNGs ===
# Modifies sim1.py for variable base; outputs bar plots
import numpy as np
import matplotlib.pyplot as plt

# Modified Spectral Potential (from sim1.py, now with base param)
def spectral_potential(r, base=24, N=500, S_grav=0.04344799):
    """VG(r) = sum a_n * n^(-r/3 / log n), a_n modulated by base"""
    r = np.asarray(r)
    rho = np.zeros_like(r, dtype=float)
    for n in range(1, N+1):
        theta = 2 * np.pi * n / base
        denom = np.log(1 + np.cos(theta) + 1e-8)
        coeff = S_grav * np.cos(theta) / denom if denom > 0 else 0
        rho += coeff * np.exp(-r / (3 * np.log(n + 1)))  # log n → log(n+1) for n=1
    return rho

# Ring-Sector Grid (from sim1.py)
r_in, r_out = 0.1, 10.0
alpha = np.pi / 6
nr, ntheta = 80, 24  # Fixed 24 sectors for comparison
r = np.logspace(np.log10(r_in), np.log10(r_out), nr)
theta = np.linspace(0, alpha, ntheta, endpoint=False)
R, Theta = np.meshgrid(r, theta, indexing='ij')
X = R * np.cos(Theta)
Y = R * np.sin(Theta)
N_grid = nr * ntheta

# Traces (simplified from sim1.py for speed; full Schottky in production)
def generate_traces(z0, depth=4):
    traces = [z0]
    inversive = []
    for d in range(depth):
        new_traces = []
        for z in traces:
            z_inv = 1.0 / np.conj(z) if np.abs(z) > 1e-8 else 1e8
            z_inner = r_in**2 / np.conj(z) if np.abs(z) > 1e-8 else 1e8
            z_reflect_theta0 = np.conj(z)
            new_traces += [z_inv, z_inner, z_reflect_theta0]
            inversive += [z_inv, z_inner]
        traces += new_traces
    return np.array(traces), np.array(inversive)

z0 = 1.0 + 0.1j
traces, inv_traces = generate_traces(z0)
traces = traces[np.abs(traces) > 1e-8]
inv_traces = inv_traces[np.abs(inv_traces) > 1e-8]

# Green Kernel (from sim1.py, now with base)
def green_kernel(z, zeta, traces, inv_traces, vg_weights):
    logP = 0.0
    for i, (t, it) in enumerate(zip(traces, inv_traces)):
        num = z - t
        den = z - it
        ratio = np.abs(num / den) if den != 0 else 1e10
        weight = vg_weights[i % len(vg_weights)]
        logP += weight * np.log(ratio + 1e-12)
    return logP

# VG Weights (now base-dependent)
def get_vg_weights(base):
    vg_r = np.logspace(-1, 1, len(traces))
    vg_raw = spectral_potential(vg_r, base=base, N=base)  # N=base for truncation
    vg_weights = vg_raw / (np.max(np.abs(vg_raw)) + 1e-8)
    vg_weights = np.tile(vg_weights, (len(traces)//base + 1))[:len(traces)]
    return vg_weights

# Laplacian (from sim1.py, with r_safe regularization)
def laplacian_2d_polar(G, r, theta):
    dr = np.diff(r)
    dtheta = np.diff(theta)
    Lap = np.zeros_like(G)
    r_safe = r + 1e-3  # Regularization for stability
    for i in range(1, len(r)-1):
        for j in range(len(theta)):
            j_p = (j + 1) % len(theta)
            j_m = (j - 1) % len(theta)
            d2G_dr2 = (G[i+1,j] - 2*G[i,j] + G[i-1,j]) / dr[i-1]**2
            dG_dr = (G[i+1,j] - G[i-1,j]) / (2*dr[i-1])
            d2G_dtheta2 = (G[i,j_p] - 2*G[i,j] + G[i,j_m]) / dtheta[0]**2
            Lap[i,j] = d2G_dr2 + (1/r_safe[i])*dG_dr + (1/r_safe[i]**2)*d2G_dtheta2
    return Lap

# Compute for a given base
def run_simulation(base):
    vg_weights = get_vg_weights(base)
    Z = X + 1j*Y
    G = np.zeros_like(Z, dtype=float)
    for i in range(Z.shape[0]):
        for j in range(Z.shape[1]):
            G[i,j] = green_kernel(Z[i,j], z0, traces, inv_traces, vg_weights)
    LapG = laplacian_2d_polar(G, r, theta)
    rho_per_sector = np.zeros(ntheta)
    for j in range(ntheta):
        rho_per_sector[j] = np.mean(np.abs(LapG[:,j]))
    rho_per_sector /= np.max(np.abs(rho_per_sector))  # Normalize
    L1_norm = np.sum(np.abs(LapG)) * (r[-1]-r[0]) * alpha / N_grid
    return rho_per_sector, L1_norm

# Generate PNGs for bases 12, 24, 48
bases = [12, 24, 48]
for base in bases:
    rho_per_sector, L1 = run_simulation(base)
    plt.figure(figsize=(6,4))
    plt.bar(range(1,25), rho_per_sector)
    plt.title(f'Base-{base} Sector Density (L¹ = {L1:.1f})')
    plt.xlabel('Sector')
    plt.ylabel('Normalized ρ_info')
    plt.tight_layout()
    plt.savefig(f'base{base}.png', dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Generated base{base}.png: Max ρ in sectors 1/24 = {rho_per_sector[0]:.3f}/{rho_per_sector[-1]:.3f}, L¹={L1:.1f}")

print("\nAll PNGs ready! Drop them into your LaTeX figs dir.")