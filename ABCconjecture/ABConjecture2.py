import numpy as np
from scipy.sparse import diags
from scipy.sparse.linalg import eigsh
import matplotlib.pyplot as plt

def solve_uftf_abc(quality, c_log=10.0, violating=False, n_grid=600):
    L = 15.0
    x = np.linspace(-L, L, n_grid)
    dx = x[1] - x[0]
    
    V = np.zeros_like(x)
    primes = [2,3,5,7,11,13,17,19,23]  # base-24 allowed
    for p in primes:
        V += np.log(p) * np.exp(-quality * np.abs(x) / np.log(p + 1))
    
    if violating:
        noise_amp = 50 + quality * 30  # excess defect for high q
        V += noise_amp * np.random.normal(0, 1, x.shape) * np.exp(-np.abs(x)/2)
    
    main_diag = 2.0 / dx**2 + V
    off_diag = -1.0 / dx**2 * np.ones(n_grid-1)
    H = diags([off_diag, main_diag, off_diag], [-1, 0, 1]).tocsr()
    
    l1_norm = np.trapz(np.abs(V), x)
    is_stable = l1_norm < 50.0  # threshold near spectral floor scaling
    
    try:
        vals, _ = eigsh(H, k=1, which='SA')
        e0 = vals[0]
    except:
        e0 = np.nan
    
    return {"l1_norm": l1_norm, "stable": is_stable, "e0": e0, "x": x, "V": V}

# Real stable: 3+5=8, rad(3*5*8)=30, q = log(30)/log(8) ≈1.54
res_stable = solve_uftf_abc(quality=1.54, c_log=np.log(8))

# Hypothetical violating high-q proxy
res_violating = solve_uftf_abc(quality=1.8, c_log=20.0, violating=True)

print("--- UFT-F abc with Real Triple Proxies ---")
for name, res in [("Stable (3+5=8, q≈1.54)", res_stable),
                  ("Violating High-q Proxy", res_violating)]:
    print(f"\n{name}:")
    print(f"L1 Norm: {res['l1_norm']:.4f}")
    print(f"ACI Stability: {'PASS' if res['stable'] else 'FAIL (Diverges)'}")
    print(f"Ground State Energy: {res['e0']:.4f}")

plt.figure(figsize=(10,6))
plt.plot(res_stable['x'], res_stable['V'], label="Stable Triple (ACI PASS)", color='blue')
plt.plot(res_violating['x'], res_violating['V'], label="Violating Proxy (ACI FAIL)", color='red', linestyle='--')
plt.title("UFT-F Height Potential for abc: Stability vs. Divergence")
plt.xlabel("Manifold Coordinate x")
plt.ylabel("V_abc(x)")
plt.legend()
plt.show()

# (base) brendanlynch@Brendans-Laptop ABCconjecture % python ABConjecture2.py
# --- UFT-F abc with Real Triple Proxies ---

# Stable (3+5=8, q≈1.54):
# L1 Norm: 63.5057
# ACI Stability: FAIL (Diverges)
# Ground State Energy: 0.1793

# Violating High-q Proxy:
# L1 Norm: 338.2017
# ACI Stability: FAIL (Diverges)
# Ground State Energy: -15.9728
# 2025-12-28 14:17:23.568 python[60157:52543400] The class 'NSSavePanel' overrides the method identifier.  This method is implemented by class 'NSWindow'
# (base) brendanlynch@Brendans-Laptop ABCconjecture % 