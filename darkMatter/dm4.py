import numpy as np
import matplotlib.pyplot as plt

# Approximate acoustic peaks
def cl_standard(l):
    # Simplified function approximating peaks and falloff
    # This serves as the C_l^{\Lambda CDM} baseline
    return 1e5 * (1/l) * np.sin(np.pi * l / 220)**2 * (1 + 0.3 * np.exp(-(l-800)**2 / 1e5))

l = np.arange(2, 2500)
Cl = cl_standard(l)
epsilon = 0.03 # Example value constrained by observational data (<0.05)

# Applying the Base-24 modulation
# This models a periodic oscillation in the power spectrum Cl
Cl_mod = Cl * (1 + epsilon * np.cos(2 * np.pi * l / 24))

# Quantitative check for future missions
sensitivity_threshold = 0.005 # 0.5% sensitivity for CMB-S4
# Calculate the maximum relative difference (percentage difference)
max_relative_diff = np.max(np.abs(Cl_mod - Cl) / Cl)

if max_relative_diff > sensitivity_threshold:
    print(f"Modulation peak amplitude ({epsilon:.3f}) is detectable by CMB-S4.")

# Plotting the CMB Angular Power Spectrum
plt.figure(figsize=(10, 6))
plt.plot(l, Cl, label=r'Standard $\Lambda$CDM', linestyle='--', color='gray')
plt.plot(l, Cl_mod, label=r'Base-24 Mod ($\epsilon=0.03$)', color='red')
plt.xscale('log')
plt.yscale('log')
plt.xlabel('Multipole $l$ (Angular Scale)')
# FIX: Correctly enclose the LaTeX y-label string in quotes
plt.ylabel(r'$C_l$ ($\mu K^2$)') 
plt.legend()
plt.title(r'Simulated CMB Angular Power Spectrum with Base-24 Modulation')
plt.grid(True, which="both", ls=":")
plt.tight_layout()
plt.show()