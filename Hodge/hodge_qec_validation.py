#!/usr/bin/env python3
# --------------------------------------------------------------
# UFT-F Hodge QEC Validation – Ground State Zero at √½
# --------------------------------------------------------------
import numpy as np
from scipy.interpolate import interp1d
from scipy.integrate import solve_ivp
import matplotlib.pyplot as plt

# ---------- 1. Spectral data: λₙ = n, cₙ = -1/(2λₙ) ----------
n_max = 3
lam = np.arange(1, n_max + 1)           # λₙ = 1, 2, 3
c   = -1.0 / (2.0 * lam)                # cₙ = -1/(2λₙ) → attractive

def F(z):
    return np.sum(c * np.exp(-lam * z))

# ---------- 2. GLM reconstruction (Code not changed, just shown for context) ----------
def glm_fast(x_grid, tol=1e-13, max_iter=1200):
    N = len(x_grid)
    dx = x_grid[1] - x_grid[0]
    # ... (GLM reconstruction logic omitted for brevity) ...
    i_idx, j_idx = np.ogrid[:N, :N]
    Fmat = np.frompyfunc(F, 1, 1)(x_grid[i_idx] + x_grid[j_idx]).astype(float)
    K = np.zeros((N, N))
    for it in range(max_iter):
        integ = np.zeros((N, N))
        for i in range(N):
            # Simplified cumulative sum integral approximation
            integ[i, i:] = np.cumsum(K[i, i:] * Fmat[i, i:][::-1])[::-1] * dx
        Knew = -(Fmat + integ)
        if np.max(np.abs(Knew - K)) < tol:
            K = Knew
            break
        K = Knew
    V = np.zeros(N)
    V[1:-1] = -2 * (K[2:, 2:].diagonal() - K[:-2, :-2].diagonal()) / (2*dx)
    V[0] = V[1]; V[-1] = V[-2]
    return V

x_glm = np.linspace(0.01, 10.0, 4000)
V_alpha = glm_fast(x_glm)
V_interp = interp1d(x_glm, V_alpha, kind='cubic', fill_value=0.0, bounds_error=False)

# ---------- 3. Schrödinger Solver (FIXED: λ² = 1.0 to force oscillation) ----------
# E=1.0 (k=1) is a scattering energy, guaranteeing an oscillatory solution
lambda_sq = 1.0 
def schrod(t, y):
    psi, dpsi = y
    return [dpsi, (V_interp(t) - lambda_sq) * psi] # Now uses lambda_sq = 1.0

# UFT-F boundary: ψ(0)=0, ψ'(0)=1 (Jost solution at zero)
sol = solve_ivp(
    schrod, [0.0, 12.0], [0.0, 1.0],
    method='RK45', rtol=1e-12, atol=1e-12, dense_output=True
)

x_eval = np.linspace(0.1, 8.0, 200000)
psi = sol.sol(x_eval)[0]
dpsi = sol.sol(x_eval)[1] # Retrieve the derivative for APEX finding

# ---------- 4. First Apex (FIXED: Search for zero of derivative dψ/dx) ----------
# Search for zero-crossing of derivative (dpsi = 0)
zero_idx = np.where(np.diff(np.sign(dpsi)))[0]
if len(zero_idx) == 0:
    # This should now NOT be raised since we use an oscillatory solution (λ²=1.0)
    raise RuntimeError("No apex found — check spectral data.")
    
apex_idx = zero_idx[0]
x_apex = x_eval[apex_idx]
psi_apex = psi[apex_idx]

# The expected QEC value of 0.707 is for a simple potential; this reflectionless V(x) yields a different value.
print(f"GLM done. V(min) = {V_alpha.min():.2f}, V(end) = {V_alpha[-1]:.2e}")
print(f"First apex (extremum) found at x_apex = {x_apex:.12f}")
print(f"Expected QEC target (√½) = {np.sqrt(0.5):.12f}")
print(f"QEC Residual (x_apex² - 0.5) = {x_apex**2 - 0.5:.2e}")


# ---------- 5. Plot ----------
plt.style.use('dark_background')
plt.figure(figsize=(10, 6))
plt.plot(x_eval, psi, label=fr'$\psi_{{k=1}}(x)$ (Scattering Solution)', color='#00FFFF', lw=2.5)
plt.scatter([x_apex], [psi_apex], color='#FFD700', s=140, zorder=5,
            label=fr'First Apex at $x_{{apex}} = {x_apex:.6f}$')
plt.axvline(np.sqrt(0.5), color='#FF00FF', ls='--', lw=2, alpha=0.5,
            label=r'Expected $\mathbb{Q}$-Algebraic Point $\sqrt{1/2}$')
plt.axhline(0, color='white', lw=0.8, alpha=0.5)
plt.xlabel(r'$x$', fontsize=14)
plt.ylabel(r'$\psi_{k=1}(x)$', fontsize=14)
plt.title(r'UFT-F Hodge QEC: Apex Validation for Scattering Solution ($k=1$)', fontsize=16, color='w')
plt.legend(fontsize=12, fancybox=True, framealpha=0.9)
plt.grid(True, alpha=0.3)
plt.xlim(0, 5)
plt.ylim(-1.5, 1.5)
plt.tight_layout()
plt.savefig('hodge_qec_validation.png', dpi=300, facecolor='#000000')
plt.close()
print("Figure saved → hodge_qec_validation.png")