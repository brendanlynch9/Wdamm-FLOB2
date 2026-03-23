import numpy as np
from scipy.linalg import solve
import matplotlib.pyplot as plt

def natural_marchenko_test(z_set, name, L=30.0, N=600, plot=False, verbose=False):
    x = np.linspace(0.01, L, N)
    dx = x[1] - x[0]

    # Build joint frequency set
    freqs = np.array([f for z in z_set for f in (z, np.exp(z))], dtype=float)

    kappas = 0.08 + 0.008 * np.log1p(np.abs(freqs))

    # Precompute kernel on needed range
    t_vals = np.linspace(0, 2*L, 2*N)
    B_table = np.sum(np.exp(-kappas[:, None] * t_vals[None, :]), axis=0)

    def B_lookup(t):
        idx = np.clip((t / (2*L) * (2*N-1)).astype(int), 0, 2*N-1)
        return B_table[idx]

    K_xx = np.zeros(N)
    max_cond_est = 1.0

    for i in range(N):
        sub_x = x[i:]
        n_sub = len(sub_x)
        if n_sub < 4:
            break

        t_grid = sub_x[:, None] + sub_x[None, :]
        B_mat = B_lookup(t_grid) * dx
        A = np.eye(n_sub) + B_mat

        # cheap condition estimate
        cond_est = np.linalg.norm(A, ord=np.inf) * np.linalg.norm(np.linalg.inv(A), ord=np.inf)
        max_cond_est = max(max_cond_est, cond_est)

        rhs = -B_lookup(x[i] + sub_x)

        try:
            sol = solve(A, rhs)   # no assume_a='pos'
            K_xx[i] = sol[0]
        except Exception as e:
            if verbose:
                print(f"Failure at i={i}: {e}")
            K_xx[i] = np.nan

    V = -2 * np.gradient(K_xx, dx)
    mask = np.isfinite(V)

    if not np.any(mask):
        return np.nan, np.nan, max_cond_est, np.nan

    l1 = np.trapz(np.abs(V[mask]), x[:len(V)][mask])
    l2 = np.sqrt(np.trapz(V[mask]**2, x[:len(V)][mask]))
    sir = l2 / l1 if l1 > 0 else 0.0

    if plot:
        plt.figure(figsize=(9, 5))
        plt.semilogy(x[:len(V)], np.abs(V))
        plt.title(f"{name}\nL¹={l1:.3f}, SIR={sir:.3f}, cond≈{max_cond_est:.1e}")
        plt.grid(True, which='both', ls='--')
        safe_name = name.replace(" ", "_").replace("{", "").replace("}", "")
        plt.savefig(f'natural_{safe_name}.png', dpi=150)
        plt.close()

    baseline = 0.379
    return l1, sir, max_cond_est, l1 / baseline


# TESTS
test_cases = [
    ("Independent {1, e, π}", [1.0, np.e, np.pi]),
    ("Additive {e, π, e+π}", [np.e, np.pi, np.e + np.pi]),
    ("Log-product {ln2, ln3, ln6}", [np.log(2), np.log(3), np.log(6)]),
    ("Multiplicative {e, π, e·π}", [np.e, np.pi, np.e * np.pi]),
    ("Near collision {1, 1+1e-7}", [1.0, 1.0 + 1e-7]),
    ("Riemann triple", [14.134725, 21.022040, 25.010858]),
]

print(f"{'Case':<40} | {'L¹':<10} | {'SIR':<8} | {'cond est':<10} | {'rel':<8}")
print("-"*80)

for name, z_set in test_cases:
    l1, sir, cond, rel = natural_marchenko_test(z_set, name, plot=True)
    print(f"{name:<40} | {l1:<10.3f} | {sir:<8.3f} | {cond:<10.1e} | {rel:<8.2f}")


# (base) brendanlynch@Brendans-Laptop schanuel % python schanuel_natural_spectral_test.py
# Case                                     | L¹         | SIR      | cond est   | rel     
# --------------------------------------------------------------------------------
# Independent {1, e, π}                    | 0.378      | 0.429    | 1.7e+02    | 1.00    
# Additive {e, π, e+π}                     | 0.424      | 0.307    | 1.6e+02    | 1.12    
# Log-product {ln2, ln3, ln6}              | 0.350      | 0.574    | 1.8e+02    | 0.92    
# Multiplicative {e, π, e·π}               | 0.467      | 0.279    | 1.5e+02    | 1.23    
# Near collision {1, 1+1e-7}               | 0.339      | 0.432    | 1.2e+02    | 0.89    
# Riemann triple                           | 0.879      | 0.255    | 1.0e+02    | 2.32    
# (base) brendanlynch@Brendans-Laptop schanuel % 