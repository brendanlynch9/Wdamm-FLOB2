import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# UFT-F Constants
LAMBDA_0 = 15.045233122
C_UFT_F = 0.003119337
OMEGA_U = 0.0002073045

def uftf_l1_potential(positions, k):
    pos = np.sort(positions % 1.0)
    distances = np.append(np.diff(pos), 1.0 - (pos[-1] - pos[0]))
    gap_threshold = 1.0 / k
    l1 = 0
    for d in distances:
        if d < gap_threshold:
            # Sobolev divergence proxy
            denom = max(d - C_UFT_F, 1e-12)
            l1 += np.exp((gap_threshold - d) / denom) * (1 + OMEGA_U)
    return l1

# 1. Test Standard Model Flavors (Fixed Speeds from User Papers)
# Neutrino speeds (eV)
nu_speeds = np.array([0.01659, 0.02073, 0.05000])
# Quark speeds (GeV)
up_quark_speeds = np.array([1.22, 4.44, 173.0])

def check_flavor_loneliness(speeds, name):
    min_l1 = 1e9
    best_t = 0
    for t in np.linspace(0.01, 1000.0, 10000):
        l1 = uftf_l1_potential(speeds * t, 3)
        if l1 < min_l1:
            min_l1 = l1
            best_t = t
    return min_l1, best_t

nu_l1, nu_t = check_flavor_loneliness(nu_speeds, "Neutrinos")
quark_l1, quark_t = check_flavor_loneliness(up_quark_speeds, "Quarks")

# 2. Large Scale Sweep for the Cliff (k up to 150)
cliff_results = []
k_test_range = range(2, 151, 5)

for k in k_test_range:
    # We estimate the minimum L1 by checking a large sample of random speeds
    # to find the "best case" for the manifold
    current_best_l1 = 1e9
    for _ in range(20): # Random sampling of speed sets
        speeds = np.random.uniform(1, 100, k)
        for t in np.linspace(0.1, 10.0, 50):
            l1 = uftf_l1_potential(speeds * t, k)
            if l1 < current_best_l1:
                current_best_l1 = l1
    cliff_results.append(current_best_l1)

# 3. Compile Data
df_cliff = pd.DataFrame({
    'k_runners': k_test_range,
    'L1_Mass': cliff_results
})
df_cliff['Status'] = df_cliff['L1_Mass'].apply(lambda x: 'STABLE' if x < LAMBDA_0 else 'RUPTURE')
df_cliff.to_csv('lonely_runner_cliff_analysis.csv', index=False)

# Plotting the Cliff
plt.figure(figsize=(10, 6))
plt.plot(df_cliff['k_runners'], df_cliff['L1_Mass'], 'r-', label='Minimal Spectral Mass')
plt.axhline(y=LAMBDA_0, color='black', linestyle='--', label='Modularity Constant ($\lambda_0$)')
plt.fill_between(df_cliff['k_runners'], 0, LAMBDA_0, color='blue', alpha=0.1, label='Stable Manifold')
plt.fill_between(df_cliff['k_runners'], LAMBDA_0, max(cliff_results), color='red', alpha=0.1, label='Spectral Sink')

# Marking Flavors
plt.scatter([3, 3], [nu_l1, quark_l1], color='gold', zorder=5, label='SM Flavors (k=3)')
plt.text(5, nu_l1, 'Neutrinos/Quarks', fontsize=9, fontweight='bold')

plt.title('UFT-F Falsifiable Bound: The Redundancy Cliff of the Lonely Runner')
plt.xlabel('Number of Runners ($k$)')
plt.ylabel('Informational Mass ($L^1$)')
plt.legend()
plt.grid(True, alpha=0.3)
plt.savefig('falsifiable_cliff.png')

print(f"Neutrino L1: {nu_l1:.4f}")
print(f"Quark L1: {quark_l1:.4f}")
print(f"Rupture detected at k={df_cliff[df_cliff['Status'] == 'RUPTURE']['k_runners'].min()}")

# (base) brendanlynch@Brendans-Laptop lonelyRunner % python test2.py
# /Users/brendanlynch/Desktop/zzzzzCompletePDFs/lonelyRunner/test2.py:68: SyntaxWarning: invalid escape sequence '\l'
#   plt.axhline(y=LAMBDA_0, color='black', linestyle='--', label='Modularity Constant ($\lambda_0$)')
# /Users/brendanlynch/Desktop/zzzzzCompletePDFs/lonelyRunner/test2.py:19: RuntimeWarning: overflow encountered in exp
#   l1 += np.exp((gap_threshold - d) / denom) * (1 + OMEGA_U)
# Neutrino L1: 1.0220
# Quark L1: 1.0133
# Rupture detected at k=12
# (base) brendanlynch@Brendans-Laptop lonelyRunner % 

