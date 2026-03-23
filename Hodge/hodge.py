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

# ---------- 2. GLM reconstruction ----------
def glm_fast(x_grid, tol=1e-13, max_iter=1200):
    N = len(x_grid)
    dx = x_grid[1] - x_grid[0]
    i_idx, j_idx = np.ogrid[:N, :N]
    Fmat = np.frompyfunc(F, 1, 1)(x_grid[i_idx] + x_grid[j_idx]).astype(float)

    K = np.zeros((N, N))
    for it in range(max_iter):
        integ = np.zeros((N, N))
        for i in range(N):
            integ[i, i:] = np.cumsum(K[i, i:] * Fmat[i, i:][::-1])[::-1] * dx
        Knew = -(Fmat + integ)
        if np.max(np.abs(Knew - K)) < tol:
            K = Knew
            break
        K = Knew

    V = np.zeros(N)
    V[1:-1] = -(K[2:, 2:].diagonal() - K[:-2, :-2].diagonal()) / (2*dx)
    V[0] = V[1]; V[-1] = V[-2]
    return V

x_glm = np.linspace(0.01, 10.0, 4000)
V_alpha = glm_fast(x_glm)
V_interp = interp1d(x_glm, V_alpha, kind='cubic', fill_value=0.0, bounds_error=False)

print(f"GLM done. V(min) = {V_alpha.min():.2f}, V(end) = {V_alpha[-1]:.2e}")

# ---------- 3. Ground state: λ² = 0 ----------
def schrod(t, y):
    psi, dpsi = y
    return [dpsi, V_interp(t) * psi]

# UFT-F boundary: ψ(0)=0, ψ'(0)=1
sol = solve_ivp(
    schrod, [0.0, 12.0], [0.0, 1.0],
    method='RK45', rtol=1e-12, atol=1e-12, dense_output=True
)

x_eval = np.linspace(0.1, 8.0, 200000)
psi = sol.sol(x_eval)[0]

# ---------- 4. First zero ----------
zero_idx = np.where(np.diff(np.sign(psi)))[0]
if len(zero_idx) == 0:
    raise RuntimeError("No zero — check c < 0 and spectral data")
x_apex = x_eval[zero_idx[0]]

print(f"First zero at x_apex = {x_apex:.12f}")
print(f"QEC residual (x² - ½) = {x_apex**2 - 0.5:.2e}")

# ---------- 5. Plot ----------
plt.style.use('dark_background')
plt.figure(figsize=(10, 6))
plt.plot(x_eval, psi, label=r'$\psi_0(x)$ (ground state)', color='#00FFFF', lw=2.5)
plt.scatter([x_apex], [0], color='#FFD700', s=140, zorder=5,
            label=fr'$x_{{apex}} = {x_apex:.6f}$')
plt.axvline(np.sqrt(0.5), color='#FF00FF', ls='--', lw=2,
            label=r'$\sqrt{1/2}$')
plt.axhline(0, color='white', lw=0.8, alpha=0.5)
plt.xlabel(r'$x$', fontsize=14)
plt.ylabel(r'$\psi_0(x)$', fontsize=14)
plt.title(r'UFT-F Hodge QEC: Ground State Zero at $\sqrt{1/2}$', fontsize=16, color='w')
plt.legend(fontsize=12, fancybox=True, framealpha=0.9)
plt.grid(True, alpha=0.3)
plt.xlim(0, 3)
plt.ylim(-1.1, 1.1)
plt.tight_layout()
plt.savefig('hodge_qec_validation.png', dpi=300, facecolor='#000000')
plt.close()
print("Figure saved → hodge_qec_validation.png")