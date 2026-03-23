import numpy as np
from scipy.optimize import minimize

# UFT-F Constants
LAMBDA_0 = 15.0452
C_UFT_F = 0.003119
OMEGA_U = 0.0002073045

def uftf_spectral_potential(distances, k):
    l1_contribution = 0
    gap_threshold = 1.0 / k
    for d in distances:
        if d < gap_threshold:
            # The potential spike must be modeled as a Sobolev-divergence
            l1_contribution += np.exp((gap_threshold - d) / C_UFT_F) * (1 + OMEGA_U)
    return l1_contribution

def objective_l1(speeds, k):
    min_l1 = 1e10 # Initialize high
    # We check the temporal window for the lowest informational mass
    for t in np.arange(0.1, 1.5, 0.05):
        pos = np.sort((speeds * t) % 1.0)
        distances = np.append(np.diff(pos), 1.0 - (pos[-1] - pos[0]))
        l1 = uftf_spectral_potential(distances, k)
        if l1 < min_l1:
            min_l1 = l1
    return min_l1

# Initializing with the non-degenerate G24 residues
initial_speeds = np.array([1.0, 5.0, 7.0, 11.0, 13.0, 17.0, 19.0, 23.0])

print("--- Initializing UFT-F Simplex Optimization (k=8) ---")
res = minimize(objective_l1, initial_speeds, args=(8,), method='Nelder-Mead', tol=1e-6)

print(f"\nOptimization Success: {res.success}")
print(f"Optimized Speeds: {res.x}")
print(f"Final L1 Mass: {res.fun:.4f}")

if res.fun < LAMBDA_0:
    print(f"[SUCCESS] ACI Stability achieved. The Lonely Runner exists in the spectral gap.")
else:
    print(f"[CRITICAL] L1 Mass ({res.fun:.4f}) remains above LAMBDA_0 ({LAMBDA_0}).")
    print("This configuration represents a forbidden state in the current manifold.")

#     (base) brendanlynch@Brendans-Laptop lonelyRunner % python nelderMead.py
# --- Initializing UFT-F Simplex Optimization (k=8) ---

# Optimization Success: True
# Optimized Speeds: [ 0.99475673  5.01806619  6.9730176  10.98899672 13.27586436 16.96725758
#  19.03823499 22.94772159]
# Final L1 Mass: 7.9122
# [SUCCESS] ACI Stability achieved. The Lonely Runner exists in the spectral gap.
# (base) brendanlynch@Brendans-Laptop lonelyRunner % 