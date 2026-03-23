"""
Standard SVD-based Stability Test for Joint Transcendental Sets
----------------------------------------------------------------
Pure linear-algebraic analysis of the discretized Marchenko operator.

No relation detection. No manual scaling/amplification. No custom axioms.
Only sums of decaying exponentials + full SVD condition number.

Metrics:
- Condition number κ = σ_max / σ_min of A = I + dx T
- Smallest singular value σ_min (distance to singularity)

Run: python schanuel_svd_stability.py
"""

import numpy as np
from scipy.linalg import svdvals
import matplotlib.pyplot as plt

def svd_stability_test(z_set, name, L=20.0, N=600, plot_kernel=False):
    """
    Build kernel T_ij = sum exp(-κ (x_i + x_j)), form A = I + dx T,
    compute full SVD singular values, return cond and min singular value.
    """
    x = np.linspace(0.1, L, N)
    dx = x[1] - x[0]

    # Joint set: z and exp(z)
    freqs = []
    for z in z_set:
        freqs.extend([z, np.exp(z)])
    freqs = np.array(freqs, dtype=complex)

    # Decay rates (logarithmic proxy, no tuning)
    kappas = 0.1 + 0.01 * np.log(1 + np.abs(freqs))

    # Kernel matrix T_ij = sum_k Re[ exp(-κ_k (x_i + x_j)) ]
    t_grid = x[:, None] + x[None, :]
    T = np.zeros((N, N))
    for k in kappas:
        T += np.real(np.exp(-k * t_grid))

    # Discretized operator
    A = np.eye(N) + T * dx

    # Full SVD singular values (descending)
    s = svdvals(A)                  # most accurate & stable method

    cond = s[0] / s[-1] if s[-1] > 0 else np.inf
    s_min = s[-1]

    # Optional: plot the kernel T (for visual inspection)
    if plot_kernel:
        plt.figure(figsize=(8, 6))
        plt.imshow(np.log1p(np.abs(T)), cmap='viridis', origin='lower')
        plt.colorbar(label='log(1 + |T_ij|)')
        plt.title(f'Kernel |T| – {name}')
        plt.xlabel('j')
        plt.ylabel('i')
        safe_name = name.replace(" ", "_").replace("{", "").replace("}", "").replace(",", "")
        plt.savefig(f'svd_kernel_{safe_name}.png', dpi=150)
        plt.close()

    return cond, s_min

# ────────────────────────────────────────────────
# Test suite — same cases you used
# ────────────────────────────────────────────────
test_cases = [
    ("Independent {1, e, pi}", [1.0, np.e, np.pi]),
    ("Dependent {ln 2, ln 3, ln 6}", [np.log(2), np.log(3), np.log(6)]),
    ("Riemann Triple {g1, g2, g3}", [14.134725, 21.022040, 25.010858]),
    ("Additive {e, pi, e+pi}", [np.e, np.pi, np.e + np.pi]),
    ("Multiplicative {e, pi, e*pi}", [np.e, np.pi, np.e * np.pi]),
    ("Near collision {1, 1+1e-7}", [1.0, 1.0 + 1e-7]),
]

print(f"{'Case':<35} | {'Cond κ':<14} | {'Min singular value':<18}")
print("-" * 70)
for name, z_set in test_cases:
    cond, s_min = svd_stability_test(z_set, name, plot_kernel=True)
    print(f"{name:<35} | {cond:<14.2e} | {s_min:<18.2e}")

print("\nInterpretation guide:")
print("- If cond κ >> 10^4–10^6 or min singular value << 10^{-10} in dependent cases → natural instability")
print("- If all values remain similar (cond ~10^1–10^3, s_min ~1) → kernel is insensitive to dependence")
print("- Plots saved as svd_kernel_*.png — visually inspect for structure differences")

#  (base) brendanlynch@Brendans-Laptop schanuel % python standardMath3.py
# Case                                | Cond κ         | Min singular value
# ----------------------------------------------------------------------
# Independent {1, e, pi}              | 2.58e+01       | 1.00e+00          
# Dependent {ln 2, ln 3, ln 6}        | 2.72e+01       | 1.00e+00          
# Riemann Triple {g1, g2, g3}         | 1.66e+01       | 1.00e+00          
# Additive {e, pi, e+pi}              | 2.41e+01       | 1.00e+00          
# Multiplicative {e, pi, e*pi}        | 2.35e+01       | 1.00e+00          
# Near collision {1, 1+1e-7}          | 1.86e+01       | 1.00e+00          

# Interpretation guide:
# - If cond κ >> 10^4–10^6 or min singular value << 10^{-10} in dependent cases → natural instability
# - If all values remain similar (cond ~10^1–10^3, s_min ~1) → kernel is insensitive to dependence
# - Plots saved as svd_kernel_*.png — visually inspect for structure differences
# (base) brendanlynch@Brendans-Laptop schanuel % 