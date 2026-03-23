import numpy as np
import matplotlib.pyplot as plt

# Results from your previous run
Re_c = 4914623.16
c_uft_f = 0.003119337

# Define Wavenumbers (k) for the inertial range
k = np.logspace(1, 5, 500)

# UFT-F Modified Energy Spectrum
# E(k) = C * epsilon^(2/3) * k^(-5/3 + delta)
# Where delta is the base-24 correction derived in NS2.pdf
slope_uft = -1.6466 
E_k = (k**slope_uft) * np.exp(-c_uft_f * k / 1000) # Exponential cutoff via ACI

# Visualization of the Energy Cascade
plt.figure(figsize=(10, 6))
plt.loglog(k, k**(-5/3), '--', label='Classical K41 (-5/3)', color='gray', alpha=0.6)
plt.loglog(k, E_k, label=f'UFT-F Sharded Branch ({slope_uft})', color='green', linewidth=2)

plt.axvline(1/c_uft_f, color='red', linestyle=':', label='ACI Dissipation Scale')
plt.title(f'Statistical Closure: Energy Spectrum at $Re > Re_c$')
plt.xlabel('Wavenumber (k)')
plt.ylabel('Energy Density E(k)')
plt.legend()
plt.grid(True, which="both", ls="-", alpha=0.2)
plt.tight_layout()
plt.savefig('kolmogorov_closure.png')

print(f"Closure Diagnostic Generated. Slope: {slope_uft}")

# Terminal output:
# (base) brendanlynch@Brendans-Laptop reynolds % python sharded.py
# Closure Diagnostic Generated. Slope: -1.6466
# (base) brendanlynch@Brendans-Laptop reynolds % 