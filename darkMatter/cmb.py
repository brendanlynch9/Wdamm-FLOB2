import numpy as np
import matplotlib.pyplot as plt

# Approximate acoustic peaks
def cl_standard(l):
    """
    Simplified function approximating the Lambda-CDM CMB angular power spectrum
    (C_l^{\Lambda CDM} baseline).
    """
    # This serves as the C_l^{\Lambda CDM} baseline
    return 1e5 * (1/l) * np.sin(np.pi * l / 220)**2 * (1 + 0.3 * np.exp(-(l-800)**2 / 1e5))

# Data setup
l = np.arange(2, 2500)
Cl = cl_standard(l)

# Base-24 Modulation Prediction
epsilon = 0.03  # Example amplitude (constrained by observational data <0.05)
Cl_mod = Cl * (1 + epsilon * np.cos(2 * np.pi * l / 24))

# Quantitative check for future missions (e.g., CMB-S4)
sensitivity_threshold = 0.005 # 0.5% sensitivity for CMB-S4
peak_modulation = np.max(np.abs(Cl_mod - Cl) / Cl)

if peak_modulation > sensitivity_threshold:
    print(f"Modulation peak amplitude ({epsilon:.3f}) is detectable by CMB-S4 (Max relative deviation: {peak_modulation:.3f}).")
else:
    print(f"Modulation peak amplitude ({epsilon:.3f}) is below CMB-S4 detectability threshold.")

# Plotting the result
plt.figure(figsize=(10, 6))
plt.plot(l, Cl, label=r'Standard $\Lambda$CDM', color='gray', linestyle='--')
plt.plot(l, Cl_mod, label=r'Base-24 Mod ($\epsilon=0.03$)', color='darkred', alpha=0.8)
plt.xscale('log')
plt.yscale('log')
plt.xlabel('Multipole $l$')
plt.ylabel(r'$C_l$ ($\mu K^2$) [Log Scale]')
plt.title(r'CMB Power Spectrum with Base-24 Modulation ($\Delta l=24$)')
plt.legend()
plt.grid(True, which="both", ls=":")
plt.tight_layout()
plt.show()