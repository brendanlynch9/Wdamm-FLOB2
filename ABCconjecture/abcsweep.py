import numpy as np
from scipy.sparse import diags
from scipy.sparse.linalg import eigsh
import matplotlib.pyplot as plt

np.random.seed(42)  # Reproducible noise

def solve_uftf_abc_height(quality, violating=False, n_grid=800):
    L = 15.0
    x = np.linspace(-L, L, n_grid)
    dx = x[1] - x[0]
    
    V = np.zeros_like(x)
    # Base-24 allowed primes contributing to rad
    primes = [2,3,5,7,11,13,17,19,23]
    for p in primes:
        V += np.log(p+1) * np.exp(-quality * np.abs(x) / np.log(p + 2))
    
    if violating:
        # Controlled excess defect for high-q proxy
        noise_amp = 40 + quality * 25
        V += noise_amp * np.random.normal(0, 1, x.shape) * np.exp(-np.abs(x)/3)
    
    # Hamiltonian
    main_diag = 2.0 / dx**2 + V
    off_diag = -1.0 / dx**2 * np.ones(n_grid-1)
    H = diags([off_diag, main_diag, off_diag], [-1, 0, 1]).tocsr()
    
    # L1 norm
    l1_norm = np.trapz(np.abs(V), x)
    
    # Ground state
    try:
        vals, _ = eigsh(H, k=1, which='SA')  # smallest algebraic
        e0 = vals[0]
    except:
        e0 = np.nan
    
    return {"l1_norm": l1_norm, "e0": e0, "x": x, "V": V}

# Sweep
qualities = [1.00, 1.10, 1.15, 1.20, 1.30, 1.80]
print("--- UFT-F abc Zero-Crossing Sweep ---")
print(f"{'q':>6} {'Stable E₀':>12} {'Violating E₀':>15}")
for q in qualities:
    stable = solve_uftf_abc_height(q, violating=False)
    violating = solve_uftf_abc_height(q, violating=True)
    print(f"{q:6.2f} {stable['e0']:12.4f} {violating['e0']:15.4f}")

# Plot the critical pair
q_crit = 1.18
stable_crit = solve_uftf_abc_height(q_crit, violating=False)
viol_crit = solve_uftf_abc_height(q_crit, violating=True)

plt.figure(figsize=(10,6))
plt.plot(stable_crit['x'], stable_crit['V'], label=f"Stable q={q_crit} (E₀ > 0)", color='blue')
plt.plot(viol_crit['x'], viol_crit['V'], label=f"Violating Proxy q={q_crit} (E₀ < 0)", color='red', linestyle='--')
plt.title("UFT-F abc Phase Transition at Critical Quality q* ≈1.18")
plt.xlabel("Manifold Coordinate x")
plt.ylabel("Height Potential V_abc(x)")
plt.legend()
plt.show()

# (base) brendanlynch@Brendans-Laptop ABCconjecture % python abcsweep.py
# --- UFT-F abc Zero-Crossing Sweep ---
#      q    Stable E₀    Violating E₀
#   1.00       0.4859         -0.1877
#   1.10       0.3893         -0.0186
#   1.15       0.3515         -5.0950
#   1.20       0.3193         -7.6904
#   1.30       0.2675         -1.4098
#   1.80       0.1421        -18.1652
# 2025-12-28 14:22:17.657 python[60184:52546421] The class 'NSSavePanel' overrides the method identifier.  This method is implemented by class 'NSWindow'
# (base) brendanlynch@Brendans-Laptop ABCconjecture % 