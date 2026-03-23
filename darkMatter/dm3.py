import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit

# NFW function
def nfw(r, rho_s, rs):
    # Fixed: Standard power-law notation is clear
    return rho_s / ((r/rs) * (1 + r/rs)**2)

# Spectral approximation (radial sum in 3D projection)
def spectral_rho(r, N=500, S_grav=0.04344799):
    # The output density must have the same shape as the input radius array
    rho = np.zeros_like(r) 
    
    # Pre-calculate the radial part, which is constant for all 'n'
    # Base-24 coefficients govern the overall form
    radial_part = 1 / (r**1.5 * (1 + r)**2.5) # This is the part that depends on 'r'

    # The sum is an approximation of the self-similar solution
    for n in range(1, N + 1):
        theta = 2 * np.pi * n / 24
        denom = np.log(1 + np.cos(theta) + 1e-8)
        
        # Check if denominator is non-zero before calculation
        if np.abs(denom) > 1e-10:
            coeff = S_grav * np.cos(theta) / denom
        else:
            coeff = 0

        # The overall density is the sum of the coefficient times the radial part.
        # This will broadcast 'coeff' (a scalar) across the 'radial_part' array
        rho += coeff * radial_part # Fixed: Added the missing '*' (multiplication) operator
        
    return np.abs(rho)

# Data for fitting
r = np.logspace(-1.5, 1.5, 200)
rho_nfw_true = nfw(r, rho_s=1, rs=1)

# Fit spectral to NFW
rho_spec = spectral_rho(r)
# Normalization step to ensure the fitting works well
rho_spec_norm = rho_spec / np.max(rho_spec) * np.max(rho_nfw_true) 
# p0 is the initial guess for [rho_s, rs]
popt, pcov = curve_fit(nfw, r, rho_spec_norm, p0=[1, 1]) 

print(f"Fitted rs: {popt[1]:.3f} (True rs=1.0)")

# Optional: Add a plot to visualize the fit
plt.figure(figsize=(8, 6))
plt.loglog(r, rho_nfw_true, label='True NFW (rho_s=1, rs=1)', linestyle='--')
plt.loglog(r, rho_spec_norm, label='Normalized Spectral Approx', alpha=0.7)
plt.loglog(r, nfw(r, *popt), label=f'Fitted NFW (rs={popt[1]:.3f})', linestyle='-')
plt.title('NFW Fit to Spectral Approximation')
plt.xlabel('Radius (r)')
plt.ylabel('Density (rho)')
plt.legend()
plt.grid(True, which="both", ls="--")
plt.show()