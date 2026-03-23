import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

# Constants
c_uft_f = 0.003119337
omega_u = 0.0002073045
N_base = 24
Re_c = 4914623.16  # Calculated in previous step

# Define the UFT-F Dissipation Limit (Spectral Floor Scale)
eta_min = c_uft_f

# Range of Reynolds numbers
re_range = np.logspace(4, 8, 500)

# Classical Kolmogorov Dissipation Scale (normalized by L=1)
C_norm = eta_min * (Re_c**0.75)
eta_classical = C_norm * (re_range**-0.75)

# UFT-F Regularized Dissipation Scale
eta_uft = np.maximum(eta_classical, eta_min)

# Visualization
plt.figure(figsize=(10, 6))

# Added 'r' before labels to treat backslashes as literal text for LaTeX
plt.loglog(re_range, eta_classical, '--', color='red', 
           label=r'Classical Kolmogorov Scale ($\eta \sim Re^{-3/4}$)')
plt.loglog(re_range, eta_uft, color='blue', linewidth=2, 
           label='UFT-F Regularized Scale (ACI Constrained)')

# Mark Re_c and eta_min using raw f-strings (fr'...')
plt.axvline(Re_c, color='gray', linestyle=':', 
            label=fr'$Re_c \approx 4.9 \times 10^6$')
plt.axhline(eta_min, color='green', linestyle='-.', 
            label=r'Spectral Floor $\eta_{min} = c_{UFT-F}$')

plt.title(r'Dissipation Scale $\eta$ vs. Reynolds Number: The ACI Cutoff')
plt.xlabel('Reynolds Number (Re)')
plt.ylabel(r'Normalized Dissipation Scale $\eta/L$')

plt.grid(True, which="both", alpha=0.3)
plt.legend()
plt.tight_layout()

# Save image and export results
plt.savefig('dissipation_scale_limit.png')

# Save data
df_dissipation = pd.DataFrame({
    'Re': re_range,
    'eta_classical': eta_classical,
    'eta_uft': eta_uft
})
df_dissipation.to_csv('dissipation_scale_data.csv', index=False)

print(f"Dissipation scale analysis complete.")
print(f"Re_c: {Re_c}")
print(f"Minimum scale (eta_min): {eta_min}")

# (base) brendanlynch@Brendans-Laptop reynolds % python dissipation.py
# Dissipation scale analysis complete.
# Re_c: 4914623.16
# Minimum scale (eta_min): 0.003119337
# (base) brendanlynch@Brendans-Laptop reynolds % 