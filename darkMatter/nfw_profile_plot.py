import numpy as np
import matplotlib.pyplot as plt

# The Navarro-Frenk-White (NFW) Dark Matter Density Profile
# The formula is: rho(r) = rho_s / ( (r/r_s) * (1 + r/r_s)^2 )
def nfw_density(r, rho_s, r_s):
    """
    Calculates the NFW dark matter density profile at a given radius r.

    Parameters:
    r (numpy.ndarray): Radial distance from the halo center.
    rho_s (float): Characteristic density (scale density).
    r_s (float): Characteristic scale radius.

    Returns:
    numpy.ndarray: Density at radius r.
    """
    x = r / r_s
    # Avoid division by zero at r=0 for log plot, though NFW diverges theoretically.
    # np.where is used to handle potential division by zero if r is exactly 0.
    # In this case, we use a small number for division if x is exactly 0.
    return np.where(x > 0, rho_s / (x * (1 + x)**2), np.inf)

# --- Simulation Parameters ---
# These are typical values for a small galaxy cluster or large galaxy halo.
RHO_S = 1.0e8    # Characteristic density in solar masses per cubic kiloparsec (M_sun / kpc^3)
R_S = 20.0       # Characteristic scale radius in kiloparsecs (kpc)

# Define the radial range for plotting (from 0.1 kpc to 1000 kpc)
# Logarithmic spacing is preferred for density profiles.
r_min = 0.1
r_max = 1000.0
R = np.logspace(np.log10(r_min), np.log10(r_max), 500) # 500 logarithmically spaced radii

# --- Calculate Density ---
Rho_NFW = nfw_density(R, RHO_S, R_S)

# --- Plotting ---
plt.figure(figsize=(10, 6))

# Use log-log plot, which is standard for density profiles
plt.loglog(R, Rho_NFW, color='#3498db', linewidth=3, label=f'NFW Profile (r_s = {R_S} kpc)')

# Add markers for the scale radius r_s
plt.axvline(x=R_S, color='red', linestyle='--', alpha=0.6, label='$r_s$ (Scale Radius)')
plt.text(R_S * 1.1, Rho_NFW.max() * 0.8, '$r_s$', color='red', fontsize=12)

# Styling and Labels
plt.title('Navarro-Frenk-White Dark Matter Density Profile', fontsize=16, fontweight='bold')
plt.xlabel('Radius $r$ (kpc)', fontsize=14)
plt.ylabel('Density $\\rho(r)$ ($M_{\\odot} / kpc^3$)', fontsize=14)
plt.grid(True, which="both", ls="--", alpha=0.5)
plt.legend(fontsize=12)
plt.style.use('seaborn-v0_8-darkgrid')
plt.tight_layout()

# Display the plot
plt.show()