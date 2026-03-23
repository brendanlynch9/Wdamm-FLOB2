"""
Unconditional Spectral Stability Test via Resonant Interaction Density
----------------------------------------------------------------------
Standard linear-algebraic probe of joint transcendental sets {z_j, exp(z_j)}.

Kernel T is weighted by the total inverse-gap interaction sum over all triples:
  ∑_{i<j,k≠i,j} 1 / |z_i + z_j - z_k + ε|

No per-case conditionals. No manual scaling. No framework-specific terms.
Instability emerges naturally when gaps approach zero (dependence).

Metrics:
- Condition number κ = σ_max / σ_min of A = I + dx T
- Smallest singular value σ_min

Run: python unconditional_spectral_resonance.py
"""

import numpy as np
from scipy.linalg import svdvals
import matplotlib.pyplot as plt

def resonant_spectral_test(z_set, name, L=25.0, N=500, eps=1e-10, plot_kernel=False):
    """
    Compute resonant interaction density → weighted kernel → SVD stability.
    """
    x = np.linspace(0.1, L, N)
    dx = x[1] - x[0]

    # Joint set
    freqs = np.concatenate([z_set, np.exp(z_set)])
    n_f = len(freqs)

    # 1. Total resonant interaction density (sum over all triples)
    # No if-statements — unconditional sum of inverse gaps
    interaction_density = 0.0
    for i in range(n_f):
        for j in range(i + 1, n_f):
            for k in range(n_f):
                if k == i or k == j:
                    continue
                gap = np.abs(freqs[i] + freqs[j] - freqs[k])
                interaction_density += 1.0 / (gap + eps)

    # Normalize by number of triples (prevents N-dependent blowup)
    n_triples = n_f * (n_f - 1) * (n_f - 2) / 2
    density_factor = interaction_density / n_triples if n_triples > 0 else 1.0

    # 2. Base decaying kernel
    t_grid = x[:, None] + x[None, :]
    T = np.exp(-0.1 * t_grid)  # standard Marchenko-like decay

    # 3. Resonant weighting (multiplies entire kernel)
    T *= density_factor

    # 4. Discretized operator
    A = np.eye(N) + T * dx

    # 5. Full SVD
    s = svdvals(A)
    cond = s[0] / s[-1] if s[-1] > 0 else np.inf
    s_min = s[-1]

    # Optional kernel visualization
    if plot_kernel:
        plt.figure(figsize=(8, 6))
        plt.imshow(np.log1p(np.abs(T)), cmap='viridis', origin='lower')
        plt.colorbar(label='log(1 + |T_ij|)')
        plt.title(f'Resonant Kernel |T| – {name}\nκ = {cond:.1e}')
        plt.xlabel('j')
        plt.ylabel('i')
        safe_name = name.replace(" ", "_").replace("{", "").replace("}", "").replace(",", "")
        plt.savefig(f'resonant_kernel_{safe_name}.png', dpi=150)
        plt.close()

    return cond, s_min

# ────────────────────────────────────────────────
# Test suite
# ────────────────────────────────────────────────
test_cases = [
    ("Independent {1, e, pi}", [1.0, np.e, np.pi]),
    ("Dependent {ln 2, ln 3, ln 6}", [np.log(2), np.log(3), np.log(6)]),
    ("Riemann Triple {g1, g2, g3}", [14.134725, 21.022040, 25.010858]),
    ("Additive {e, pi, e+pi}", [np.e, np.pi, np.e + np.pi]),
    ("Multiplicative {e, pi, e*pi}", [np.e, np.pi, np.e * np.pi]),
    ("Near collision {1, 1+1e-7}", [1.0, 1.0 + 1e-7]),
]

print(f"{'Case':<40} | {'Cond κ':<14} | {'Min σ':<12}")
print("-" * 70)
for name, z_set in test_cases:
    cond, s_min = resonant_spectral_test(z_set, name, plot_kernel=True)
    print(f"{name:<40} | {cond:<14.2e} | {s_min:<12.2e}")

print("\nNotes:")
print("- Density factor = (sum 1/|gap|) / #triples — emergent, no per-case if")
print("- If dependent sets show κ >> independent → natural resonance instability")
print("- If values are comparable → kernel insensitive to dependence")
print("- Kernel plots saved as resonant_kernel_*.png")

# (base) brendanlynch@Brendans-Laptop schanuel % python gap2.py
# Case                                     | Cond κ         | Min σ       
# ----------------------------------------------------------------------
# Independent {1, e, pi}                   | 1.98e+00       | 1.00e+00    
# Dependent {ln 2, ln 3, ln 6}             | 8.15e+08       | 1.00e+00    
# Riemann Triple {g1, g2, g3}              | 1.02e+00       | 1.00e+00    
# Additive {e, pi, e+pi}                   | 8.15e+08       | 1.00e+00    
# Multiplicative {e, pi, e*pi}             | 1.39e+00       | 1.00e+00    
# Near collision {1, 1+1e-7}               | 4.55e+00       | 1.00e+00    

# Notes:
# - Density factor = (sum 1/|gap|) / #triples — emergent, no per-case if
# - If dependent sets show κ >> independent → natural resonance instability
# - If values are comparable → kernel insensitive to dependence
# - Kernel plots saved as resonant_kernel_*.png
# (base) brendanlynch@Brendans-Laptop schanuel % 