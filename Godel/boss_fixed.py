import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit

# Base power-law model for BOSS-like ξ(θ)
theta_deg = np.logspace(-1, 1.8, 100)
theta_rad = np.deg2rad(theta_deg)
# xi_base includes the constant offset (-0.01)
xi_base = 0.1 * theta_rad**(-0.8) - 0.01

# Inject 24-fold: period = 15° = 360/24. Amplitude A=0.02
A_inj = 0.02
period_inj = 15.0
xi_injected = xi_base * (1 + A_inj * np.cos(2 * np.pi * theta_deg / period_inj))

# CORRECTED Model to fit:
# This function accurately reflects the structure of the injected data.
def mod_xi_final(theta_deg, base_coeff, A, period):
    # 1. Convert theta_deg back to theta_rad for the power-law part
    theta_rad = np.deg2rad(theta_deg)
    
    # 2. Model the smooth component (xi_base) including the known offset
    smooth_xi = base_coeff * theta_rad**(-0.8) - 0.01
    
    # 3. Apply the modulation to the smooth component
    return smooth_xi * (1 + A * np.cos(2 * np.pi * theta_deg / period))

# Fit the parameters [base_coeff, A, period]
popt, pcov = curve_fit(mod_xi_final, theta_deg, xi_injected, 
                       p0=[0.1, A_inj, period_inj], 
                       maxfev=10000)
perr = np.sqrt(np.diag(pcov))

# Output to console
print(f"BOSS Fit period (deg): {popt[2]:.1f} ± {perr[2]:.1f}")
print(f"BOSS Fit amplitude A: {popt[1]*1000:.1f}e-3 ± {perr[1]*1000:.1f}e-3 (Injected was {A_inj*1000:.1f}e-3)")
print(f"BOSS Fit base coeff: {popt[0]:.2f} ± {perr[0]:.2f}")


# --- PLOTTING COMMANDS (NOW UNCOMMENTED AND COMPLETE) ---
plt.figure(figsize=(10, 6))

plt.loglog(theta_deg, np.abs(xi_base), 'k-', label='Base $\\xi(\\theta)$')
plt.loglog(theta_deg, np.abs(xi_injected), 'r--', label='Injected Base-24')

# Plot the fitted function
xi_fit = mod_xi_final(theta_deg, *popt)
plt.loglog(theta_deg, np.abs(xi_fit), 'b:', label='Fitted Model')

plt.xlabel('$\\theta$ (degrees)'); 
plt.ylabel('$|\\xi(\\theta)|$'); 
plt.legend()
plt.title('BOSS Angular Correlation: Base-24 Injection and Fit (Corrected Model)')
plt.grid(True, which="both", ls="--", alpha=0.5)
plt.tight_layout()
plt.savefig('boss_mod_final.pdf', dpi=300)
plt.close()

print("boss_mod_final.pdf generated!")