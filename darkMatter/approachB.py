import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit

# NFW function (used as the fitting target function)
def nfw(r, rho_s, rs):
    # Use 1e-8 to prevent division by zero at r=0
    r_safe = r + 1e-8
    return rho_s / ((r_safe/rs) * (1 + r_safe/rs)**2)

# Spectral approximation (radial sum in 3D projection)
def spectral_rho(r, N=500, S_grav=0.04344799):
    rho = np.zeros_like(r)
    for n in range(1, N+1):
        theta = 2 * np.pi * n / 24
        denom = np.log(1 + np.cos(theta) + 1e-8)
        coeff = S_grav * np.cos(theta) / denom if denom > 0 else 0
        # CRUCIAL CHANGE: Exponents set to 1/(1+r)^2 to align with NFW
        rho += coeff / (r * (1 + r)**2)
    return np.abs(rho)

# Data for fitting
r = np.logspace(-1.5, 1.5, 200)
rho_nfw_true = nfw(r, rho_s=1, rs=1)

# Fit spectral to NFW
rho_spec_v2 = spectral_rho(r)
rho_spec_norm = rho_spec_v2 / np.max(rho_spec_v2) * np.max(rho_nfw_true)
popt, pcov = curve_fit(nfw, r, rho_spec_norm, p0=[1,1])
print(f"Fitted rs (Approach B): {popt[1]:.3f} (Target rs=1.0)")

# Plotting
plt.figure(figsize=(8, 6))
plt.loglog(r, rho_nfw_true, label='True NFW (rs=1.0)', linestyle='--')
plt.loglog(r, rho_spec_norm, label='Normalized Spectral Density (Approach B)', alpha=0.7)
plt.loglog(r, nfw(r, *popt), label=f'Fitted NFW (rs={popt[1]:.3f})', linestyle=':')
plt.xlabel('r (log scale)')
plt.ylabel(r'$\rho(r)$ (log scale)')
plt.title('Fit of Spectral Density (Approach B) to NFW Profile')
plt.legend()
plt.grid(True, which="both", ls="--")
plt.show()