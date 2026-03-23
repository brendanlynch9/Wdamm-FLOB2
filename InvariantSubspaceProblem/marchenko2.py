import numpy as np
import matplotlib.pyplot as plt
import time
import os

# ────────────────────────────────────────────────
# CONFIG
# ────────────────────────────────────────────────
N_zeros_target = 2000000       # full Odlyzko set — change to smaller for quick tests
dim_grid       = 128           # safe for laptop
r_max_grid     = 15.0
zeros_filename = "zero.txt"
OUTPUT_DIR     = "marchenko_laptop_safe"

os.makedirs(OUTPUT_DIR, exist_ok=True)

# Tail bound parameters (pessimistic subconvexity-style)
SIGMA_FIXED   = 0.51
C_EXP         = 0.165
LOG_POWER     = 4

# ────────────────────────────────────────────────
# Load zeros
# ────────────────────────────────────────────────
def load_zeros(filename=zeros_filename, max_n=N_zeros_target):
    print(f"Loading zeros from {filename} (up to {max_n})...")
    start = time.time()
    gammas = []
    with open(filename, 'r') as f:
        for line_num, line in enumerate(f, 1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                gamma = float(stripped)
                gammas.append(gamma)
                if len(gammas) >= max_n:
                    break
            except ValueError:
                print(f"Warning: skipped line {line_num}: {stripped}")
    elapsed = time.time() - start
    print(f"Loaded {len(gammas)} zeros in {elapsed:.2f} seconds")
    return gammas


# ────────────────────────────────────────────────
# Memory-safe kernel construction (lowest RAM possible)
# ────────────────────────────────────────────────
def build_kernel_memory_safe(gammas, dim=dim_grid, r_max=r_max_grid):
    print(f"Building {dim}x{dim} kernel via memory-safe summation...")
    start = time.time()

    grid = np.linspace(0, r_max, dim, dtype=np.float64)
    R = grid[:, None] + grid[None, :]               # (dim, dim)

    K = np.zeros((dim, dim), dtype=np.float64)
    gammas_np = np.array(gammas, dtype=np.float64)
    weights = 1.0 / (1.0 + gammas_np**2)

    for idx in range(len(gammas_np)):
        g = gammas_np[idx]
        w = weights[idx]
        K += w * np.cos(g * R)                      # in-place, no big temps

        if idx % 50000 == 0 and idx > 0:
            print(f"  Zeros processed: {idx}/{len(gammas_np)}...")

    elapsed = time.time() - start
    print(f"Kernel finished in {elapsed:.1f} seconds")
    return K, grid, gammas_np, weights


# ────────────────────────────────────────────────
# Schatten-1 norm + spectral decay plot
# ────────────────────────────────────────────────
def compute_spectral_analysis(K, n_zeros):
    print("Computing SVD / Schatten-1 norm...")
    s = np.linalg.svd(K, compute_uv=False)
    schatten1 = np.sum(s)

    print(f"\n--- RESULTS ---")
    print(f"N zeros used:     {n_zeros:,}")
    print(f"Schatten-1 norm:  {schatten1:.6f}")
    print(f"Largest SV:       {s[0]:.6f}")
    print(f"SV[32]:           {s[32] if len(s)>32 else 'N/A'}")
    print(f"SV[64]:           {s[64] if len(s)>64 else 'N/A'}")

    # Plot (one file only)
    plt.figure(figsize=(9, 5.5))
    plt.semilogy(s, 'r-', lw=1.2)
    plt.title("Spectral Decay (Trace-Class Verification)")
    plt.xlabel("Singular value index")
    plt.ylabel("Singular value")
    plt.grid(True, which="both", ls="--", alpha=0.6)
    plt.tight_layout()
    plot_path = os.path.join(OUTPUT_DIR, f"spectral_decay_N{n_zeros}.png")
    plt.savefig(plot_path)
    plt.close()
    print(f"Plot saved: {plot_path}")

    return s, schatten1


# ────────────────────────────────────────────────
# Rough tail bounds
# ────────────────────────────────────────────────
def print_tail_bounds(n_zeros):
    print("\nRough tail bounds (Paley-Wiener style):")
    for r in [5.0, 10.0, 15.0]:
        gamma_N_approx = 2 * np.pi * n_zeros / np.log(max(n_zeros, 100))
        tail_mass_approx = 1.0 / gamma_N_approx
        exp_growth = np.exp((SIGMA_FIXED - 0.5) * r)
        growth = (gamma_N_approx ** C_EXP) * (np.log(gamma_N_approx) ** LOG_POWER)
        bound = tail_mass_approx * exp_growth * growth
        print(f"  r = {r:4.1f} → tail bound ≈ {bound:.2e}")


# ────────────────────────────────────────────────
# Off-line blowup test (fixed & amplified versions)
# ────────────────────────────────────────────────
def off_line_demo(gammas_np, weights, r_test=10.0):
    print(f"\nOff-line blowup test at r = {r_test:.1f}")
    contrib_base = np.sum(weights * np.cos(gammas_np * r_test))
    print(f"  Baseline contribution at r={r_test:.1f}: {contrib_base:.6e}")

    # Real weight version (using strongest-weighted zero)
    idx_fake = np.argmax(weights)           # usually a small γ
    gamma_fake = gammas_np[idx_fake]
    w_fake = weights[idx_fake]
    print(f"  Using zero #{idx_fake+1} (γ ≈ {gamma_fake:.2f}, weight ≈ {w_fake:.2e})")

    for delta in [0.005, 0.010, 0.020, 0.050]:
        exp_factor = np.exp(delta * r_test)
        extra = w_fake * (exp_factor * np.cos(gamma_fake * r_test) - np.cos(gamma_fake * r_test))
        ratio = abs(extra) / abs(contrib_base) if contrib_base != 0 else float('inf')
        print(f"  Δσ = +{delta:.3f} → real-weight extra ≈ {ratio:9.2e}x")

    print("\nHypothetical full-weight blowup (normalized to weight=1):")
    for delta in [0.005, 0.010, 0.020, 0.050]:
        exp_factor = np.exp(delta * r_test)
        hypothetical_extra = (exp_factor - 1)   # pure exponential effect
        ratio_hyp = abs(hypothetical_extra) / abs(contrib_base)
        print(f"  Δσ = +{delta:.3f} → hypothetical blowup ≈ {ratio_hyp:9.2e}x")


# ────────────────────────────────────────────────
# MAIN
# ────────────────────────────────────────────────
if __name__ == "__main__":
    gammas = load_zeros()

    if len(gammas) < 1000:
        print("Too few zeros — check file.")
        exit(1)

    K, grid, gammas_np, weights = build_kernel_memory_safe(gammas)

    s, schatten1 = compute_spectral_analysis(K, len(gammas))

    print_tail_bounds(len(gammas))

    off_line_demo(gammas_np, weights, r_test=10.0)

    print("\nFinished. komis can watch all he wants — the numbers don't lie.")

#     (base) brendanlynch@Brendans-Laptop InvariantSubspaceProblem % python marchenko2.py
# Loading zeros from zero.txt (up to 2000000)...
# Loaded 2000000 zeros in 0.30 seconds
# Building 128x128 kernel via memory-safe summation...
#   Zeros processed: 50000/2000000...
#   Zeros processed: 100000/2000000...
#   Zeros processed: 150000/2000000...
#   Zeros processed: 200000/2000000...
#   Zeros processed: 250000/2000000...
#   Zeros processed: 300000/2000000...
#   Zeros processed: 350000/2000000...
#   Zeros processed: 400000/2000000...
#   Zeros processed: 450000/2000000...
#   Zeros processed: 500000/2000000...
#   Zeros processed: 550000/2000000...
#   Zeros processed: 600000/2000000...
#   Zeros processed: 650000/2000000...
#   Zeros processed: 700000/2000000...
#   Zeros processed: 750000/2000000...
#   Zeros processed: 800000/2000000...
#   Zeros processed: 850000/2000000...
#   Zeros processed: 900000/2000000...
#   Zeros processed: 950000/2000000...
#   Zeros processed: 1000000/2000000...
#   Zeros processed: 1050000/2000000...
#   Zeros processed: 1100000/2000000...
#   Zeros processed: 1150000/2000000...
#   Zeros processed: 1200000/2000000...
#   Zeros processed: 1250000/2000000...
#   Zeros processed: 1300000/2000000...
#   Zeros processed: 1350000/2000000...
#   Zeros processed: 1400000/2000000...
#   Zeros processed: 1450000/2000000...
#   Zeros processed: 1500000/2000000...
#   Zeros processed: 1550000/2000000...
#   Zeros processed: 1600000/2000000...
#   Zeros processed: 1650000/2000000...
#   Zeros processed: 1700000/2000000...
#   Zeros processed: 1750000/2000000...
#   Zeros processed: 1800000/2000000...
#   Zeros processed: 1850000/2000000...
#   Zeros processed: 1900000/2000000...
#   Zeros processed: 1950000/2000000...
# Kernel finished in 177.7 seconds
# Computing SVD / Schatten-1 norm...

# --- RESULTS ---
# N zeros used:     2,000,000
# Schatten-1 norm:  2.303557
# Largest SV:       0.312881
# SV[32]:           0.012443765728861142
# SV[64]:           0.004253484388950406
# Plot saved: marchenko_laptop_safe/spectral_decay_N2000000.png

# Rough tail bounds (Paley-Wiener style):
#   r =  5.0 → tail bound ≈ 4.05e-01
#   r = 10.0 → tail bound ≈ 4.25e-01
#   r = 15.0 → tail bound ≈ 4.47e-01

# Off-line blowup test at r = 10.0
#   Baseline contribution at r=10.0: -7.909828e-03
#   Using zero #1 (γ ≈ 14.13, weight ≈ 4.98e-03)
#   Δσ = +0.005 → real-weight extra ≈  3.23e-02x
#   Δσ = +0.010 → real-weight extra ≈  6.62e-02x
#   Δσ = +0.020 → real-weight extra ≈  1.39e-01x
#   Δσ = +0.050 → real-weight extra ≈  4.08e-01x

# Hypothetical full-weight blowup (normalized to weight=1):
#   Δσ = +0.005 → hypothetical blowup ≈  6.48e+00x
#   Δσ = +0.010 → hypothetical blowup ≈  1.33e+01x
#   Δσ = +0.020 → hypothetical blowup ≈  2.80e+01x
#   Δσ = +0.050 → hypothetical blowup ≈  8.20e+01x

# Finished. komis can watch all he wants — the numbers don't lie.
# (base) brendanlynch@Brendans-Laptop InvariantSubspaceProblem % 
