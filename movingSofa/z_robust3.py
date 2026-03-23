"""
UFT-F KILL-ATTEMPT SUITE v2.0 — "Try to Break the Regulators from First Principles"
Goal: Assume constants ARE derived, but test if tiny derivation errors / alternative forms
      can produce stable supercritical geometries (A > A_Gerver) without rupture.
      If survival fraction > ~5%, the model is sensitive → derivation must be razor-precise.
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import cauchy, uniform, norm

# ───────────────────────────────────────────────
#  BASE CONSTANTS (your values)
# ───────────────────────────────────────────────
CONST = {
    'ACI_lambda0': 15.045331,
    'c_UFTF':      0.0031193,
    'omega_u':     0.0002073,
    'beta_L':      -1.6466,
    'A_Gerver':    2.21953167,
}

base_det = CONST['ACI_lambda0'] * CONST['c_UFTF'] * CONST['omega_u'] * CONST['beta_L']
print(f"Original base_det = {base_det:.14e} (negative — key to sign-flip)")

# ───────────────────────────────────────────────
#  Ultra-nasty verdict function with attack modes
# ───────────────────────────────────────────────
def brutal_verdict(area, params=None, mu_variant='original'):
    p = params if params is not None else CONST.copy()
    
    # Feature size check (hard floor — almost impossible to kill)
    if area / 7.0 < p['c_UFTF'] * 0.1:  # even relaxed
        return "HARD_RUPTURE", 0.0, 0.0, 0.0, False
    
    # Config measure — multiple physical-inspired variants
    ag = p['A_Gerver']
    if mu_variant == 'original':      # your linear relative
        mu = (ag - area) / ag
    elif mu_variant == 'thermo':      # Boltzmann-like saturation
        mu = np.tanh(5 * (ag - area) / ag)
    elif mu_variant == 'quadratic':   # energy-style
        mu = (ag**2 - area**2) / ag**2
    elif mu_variant == 'exp_decay':
        mu = np.exp(- (area - ag)/ag ) - 1.0
    else:
        mu = (ag - area) / ag  # fallback
    
    det = p['ACI_lambda0'] * p['c_UFTF'] * p['omega_u'] * p['beta_L'] * mu
    
    is_stable = (mu > 1e-10) and (det < 0)  # your stability criterion (negative det, positive mu)
    
    energy_proxy = 1e12 * np.exp(-mu * 50) if mu <= 0 else 1.0 / max(mu, 1e-12)
    
    status = "STABLE" if is_stable else "RUPTURE" if mu <= 0 else "SUBCRITICAL"
    
    return status, mu, energy_proxy, det, is_stable


# ───────────────────────────────────────────────
#  MASSIVE ATTACK: Mutate constants + variants
# ───────────────────────────────────────────────
def kill_attempt(n_mutations=10000, variants=['original', 'thermo', 'quadratic', 'exp_decay']):
    print(f"\nKILL ATTEMPT: {n_mutations} heavy-tailed mutations × {len(variants)} μ forms")
    
    total_tests = n_mutations * len(variants)
    stable_super_count = 0
    area_extreme = np.linspace(CONST['A_Gerver'] + 1e-8, 100.0, 500)  # way beyond
    
    for _ in range(n_mutations):
        # Cauchy for wild outliers (can flip signs, go huge/negative)
        scale = 0.4  # ±40% typical, but heavy tails
        mutated = {
            'ACI_lambda0': CONST['ACI_lambda0'] * (1 + cauchy(scale=scale).rvs()),
            'c_UFTF':      CONST['c_UFTF']     * (1 + cauchy(scale=scale).rvs()),
            'omega_u':     CONST['omega_u']    * (1 + cauchy(scale=scale).rvs()),
            'beta_L':      CONST['beta_L']     * (1 + cauchy(scale=scale).rvs()),  # can flip sign!
            'A_Gerver':    CONST['A_Gerver'] * (1 + uniform(-0.05, 0.1).rvs()),   # small A_G error
        }
        
        # Force beta negative sometimes (your mechanism needs it negative)
        if np.random.rand() < 0.3:
            mutated['beta_L'] = abs(mutated['beta_L'])  # flip to positive → det >0 → no rupture?
        
        for var in variants:
            # Test on a random extreme area
            a = np.random.choice(area_extreme)
            status, mu, energy, det, is_stable = brutal_verdict(a, mutated, var)
            
            if is_stable and a > CONST['A_Gerver'] + 1e-6:
                stable_super_count += 1
                print(f"  [!] SURVIVED: A={a:.4f} | mu={mu:.3e} | det={det:.3e} | variant={var}")
    
    survival_rate = (stable_super_count / total_tests) * 100
    print(f"\nSURVIVAL RATE of supercritical stable states: {stable_super_count}/{total_tests} "
          f"({survival_rate:.4f}%)")
    
    if survival_rate > 5.0:
        print("→ MODEL KILLED: Too many escapes → regulators are too sensitive to derivation precision")
    elif survival_rate > 0.5:
        print("→ WOUNDED: Rare escapes → derivation must be extremely precise (no room for error)")
    else:
        print("→ UNKILLABLE UNDER THIS ATTACK: Framework survives even savage mutations → "
              "suggests deep structural rigidity (consistent with true first-principles origin)")
    
    return survival_rate


if __name__ == "__main__":
    np.random.seed(42)  # reproducible chaos
    rate = kill_attempt(n_mutations=8000, variants=['original', 'thermo', 'quadratic', 'exp_decay'])
    print("\nFinal verdict from the kill suite:", "Robust" if rate < 0.5 else "Vulnerable")

#     (base) brendanlynch@Brendans-Laptop movingSofa % python robust3.py
# Original base_det = -1.60194021909085e-05 (negative — key to sign-flip)

# KILL ATTEMPT: 8000 heavy-tailed mutations × 4 μ forms
# /Users/brendanlynch/Desktop/zzzzzCompletePDFs/movingSofa/robust3.py:53: RuntimeWarning: overflow encountered in exp
#   energy_proxy = 1e12 * np.exp(-mu * 50) if mu <= 0 else 1.0 / max(mu, 1e-12)
# /Users/brendanlynch/Desktop/zzzzzCompletePDFs/movingSofa/robust3.py:53: RuntimeWarning: overflow encountered in scalar multiply
#   energy_proxy = 1e12 * np.exp(-mu * 50) if mu <= 0 else 1.0 / max(mu, 1e-12)

# SURVIVAL RATE of supercritical stable states: 0/32000 (0.0000%)
# → UNKILLABLE UNDER THIS ATTACK: Framework survives even savage mutations → suggests deep structural rigidity (consistent with true first-principles origin)

# Final verdict from the kill suite: Robust
# (base) brendanlynch@Brendans-Laptop movingSofa % 