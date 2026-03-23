import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.optimize import minimize

# UFT-F Universal Constants
LAMBDA_0 = 15.045233122  # Modularity Constant (L1 threshold)
C_UFT_F = 0.003119337    # Spectral Hard-Deck / Kolmogorov Scale
OMEGA_U = 0.0002073045   # Hopf Torsion (Time's Arrow)
N_BASE = 24              # Harmonic Limit

def calculate_l1_mass(positions, k):
    """
    Calculates the Informational Mass (L1 norm) of a runner configuration.
    Incorporates the Hard-Deck (c_UFT_F) as a regularization floor.
    """
    # Sort and find circular distances
    pos = np.sort(positions % 1.0)
    diffs = np.diff(pos)
    distances = np.append(diffs, 1.0 - (pos[-1] - pos[0]))
    
    gap_threshold = 1.0 / k
    l1 = 0
    
    for d in distances:
        if d < gap_threshold:
            # UFT-F Potential Spike: Inverse-exponential divergence
            # If distance d approaches the Hard-Deck, the mass explodes.
            # We model this as the 'Informational Pressure'
            if d <= C_UFT_F:
                l1 += 1e6 # Manifold Rupture (Singularity)
            else:
                l1 += np.exp((gap_threshold - d) / (d - C_UFT_F + 1e-10)) * (1 + OMEGA_U)
                
    return l1

def find_min_l1(k, iterations=5):
    """
    Uses Nelder-Mead to find the most stable (loneliest) configuration for k runners.
    """
    def objective(speeds):
        # Sample over a temporal window to find the global minimum for this speed set
        min_l1_found = 1e9
        for t in np.linspace(0.1, 5.0, 50):
            mass = calculate_l1_mass(speeds * t, k)
            if mass < min_l1_found:
                min_l1_found = mass
        return min_l1_found

    # Start with distinct Base-24 residues
    initial_speeds = np.linspace(1, 23, k)
    res = minimize(objective, initial_speeds, method='Nelder-Mead', tol=1e-3)
    return res.fun, res.x

# 1. Sweep k to find the Redundancy Cliff
k_values = range(2, 26)
l1_results = []
stability_status = []

print("Sweeping runner count (k) to identify the Redundancy Cliff...")
for k in k_values:
    mass, _ = find_min_l1(k)
    l1_results.append(mass)
    status = "STABLE" if mass < LAMBDA_0 else "RUPTURE"
    stability_status.append(status)
    print(f"k={k:2} | Min L1: {mass:8.4f} | Status: {status}")

# 2. Map Standard Model States (k=3 Flavors)
# Neutrino Masses from AAAANeutrinos.pdf (scaled as speeds)
nu_speeds = np.array([0.01659, 0.02073, 0.05000]) * 1000 # scaling to visible frequencies
nu_mass = find_min_l1(3, iterations=1)[0]

# 3. Create DataFrame and Plot
df = pd.DataFrame({
    'k_runners': k_values,
    'L1_Informational_Mass': l1_results,
    'Stability': stability_status
})

df.to_csv('uftf_lonely_runner_analysis.csv', index=False)

plt.figure(figsize=(10, 6))
plt.plot(k_values, l1_results, 'o-', label='Runner Mass ($L^1$)', color='blue')
plt.axhline(y=LAMBDA_0, color='red', linestyle='--', label=f'Modularity Constant $\lambda_0$ ({LAMBDA_0:.3f})')
plt.axvline(x=24, color='green', linestyle=':', label='Base-24 Limit')

# Annotate critical points
plt.fill_between(k_values, 0, LAMBDA_0, color='green', alpha=0.1, label='Stable (Euclidean/Laminar)')
plt.fill_between(k_values, LAMBDA_0, max(l1_results)+5, color='red', alpha=0.1, label='Rupture (Non-Euclidean/Turbulent)')

plt.title('UFT-F Lonely Runner: Spectral Stability & Redundancy Cliff')
plt.xlabel('Number of Runners ($k$)')
plt.ylabel('Informational Mass ($L^1$)')
plt.legend()
plt.grid(True, which='both', linestyle='--', alpha=0.5)
plt.savefig('lonely_runner_stability_cliff.png')

print("\n--- RESULTS ---")
print(f"Redundancy Cliff identified at k={df[df['Stability'] == 'RUPTURE']['k_runners'].min()}")
print(f"Neutrino (k=3) Spectral Mass: {nu_mass:.4f} (Deeply Stable)")

# (base) brendanlynch@Brendans-Laptop lonelyRunner % python test1.py
# /Users/brendanlynch/Desktop/zzzzzCompletePDFs/lonelyRunner/test1.py:84: SyntaxWarning: invalid escape sequence '\l'
#   plt.axhline(y=LAMBDA_0, color='red', linestyle='--', label=f'Modularity Constant $\lambda_0$ ({LAMBDA_0:.3f})')
# Sweeping runner count (k) to identify the Redundancy Cliff...
# /Users/brendanlynch/Desktop/zzzzzCompletePDFs/lonelyRunner/test1.py:33: RuntimeWarning: overflow encountered in exp
#   l1 += np.exp((gap_threshold - d) / (d - C_UFT_F + 1e-10)) * (1 + OMEGA_U)
# k= 2 | Min L1:   1.0002 | Status: STABLE
# k= 3 | Min L1:   1.0002 | Status: STABLE
# k= 4 | Min L1:   1.0392 | Status: STABLE
# k= 5 | Min L1:   1.0002 | Status: STABLE
# k= 6 | Min L1:   1.1604 | Status: STABLE
# k= 7 | Min L1:   2.0593 | Status: STABLE
# k= 8 | Min L1:   1.6506 | Status: STABLE
# k= 9 | Min L1:   2.5998 | Status: STABLE
# k=10 | Min L1:   2.9188 | Status: STABLE
# k=11 | Min L1:   1.3950 | Status: STABLE
# k=12 | Min L1:   1.8687 | Status: STABLE
# k=13 | Min L1:   3.3344 | Status: STABLE
# k=14 | Min L1:   2.6384 | Status: STABLE
# k=15 | Min L1:   3.3273 | Status: STABLE
# k=16 | Min L1:   3.8528 | Status: STABLE
# k=17 | Min L1:   3.9358 | Status: STABLE
# k=18 | Min L1:   3.9610 | Status: STABLE
# k=19 | Min L1:   3.8814 | Status: STABLE
# k=20 | Min L1:   3.7686 | Status: STABLE
# k=21 | Min L1:   3.6210 | Status: STABLE
# k=22 | Min L1:   3.9824 | Status: STABLE
# k=23 | Min L1:   3.3200 | Status: STABLE
# k=24 | Min L1:   4.5416 | Status: STABLE
# k=25 | Min L1:   4.3298 | Status: STABLE

# --- RESULTS ---
# Redundancy Cliff identified at k=nan
# Neutrino (k=3) Spectral Mass: 1.0002 (Deeply Stable)
# (base) brendanlynch@Brendans-Laptop lonelyRunner % 