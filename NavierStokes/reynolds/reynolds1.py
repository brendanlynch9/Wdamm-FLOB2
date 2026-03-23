import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# Constants from the UFT-F framework
c_uft_f = 0.003119337
omega_u = 0.0002073045
N_base = 24

# Critical Reynolds Number formula based on UFT-F Spectral Overload
Re_c = np.log(N_base) / (c_uft_f * omega_u)

# Simulation range around Re_c
res = np.linspace(0.5 * Re_c, 1.5 * Re_c, 2000)

# Model 1: Eigenvalue Gap Closing
lambda_0 = c_uft_f * np.ones_like(res)
# Use np.clip to prevent tiny negative values due to float precision
diff = np.clip((Re_c - res) / Re_c, 0, None)
lambda_1 = lambda_0 + np.where(res < Re_c, 0.05 * np.sqrt(diff), 0)

# Model 2: L1 Norm behavior
eps = 1e-8
# Laminar branch: Grows logarithmically toward the collision and diverges beyond
l1_laminar = 1.0 + 0.15 * np.log(1 + res / Re_c) + 0.5 * np.log(1 / (np.abs((Re_c - res) / Re_c) + eps))

# Sharded branch: The system transitions to G24 at Re_c, regularizing the norm.
l1_sharded = np.copy(l1_laminar)
sharded_mask = res >= Re_c
# The ACI-regularized state holds the norm at the spectral floor limit
idx_at_c = np.argmin(np.abs(res - Re_c))
l1_sharded[sharded_mask] = l1_laminar[idx_at_c] * (1 + 0.01 * np.log(res[sharded_mask]/Re_c))

# Create DataFrame for export
df = pd.DataFrame({
    'Reynolds_Number': res,
    'Lambda_0': lambda_0,
    'Lambda_1': lambda_1,
    'L1_Norm_Laminar': l1_laminar,
    'L1_Norm_Sharded': l1_sharded,
    'Eigenvalue_Gap': lambda_1 - lambda_0
})

df.to_csv('rec_eigenvalue_collision_simulation.csv', index=False)

# Visualization
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 10), sharex=True)

# Plot 1: Eigenvalue Collision
# Fixed the LaTeX label formatting here
ax1.plot(res, lambda_1, label=r'$\lambda_1$ (Excited State Potential)', color='#ff7f0e', linewidth=2)
ax1.plot(res, lambda_0, label=r'$\lambda_0$ (Spectral Floor $c_{UFT-F}$)', color='#1f77b4', linestyle='--')
ax1.axvline(Re_c, color='red', linestyle=':', label=rf'Critical $Re_c \approx {Re_c/1e6:.2f} \times 10^6$')
ax1.fill_between(res, lambda_0, lambda_1, where=(res < Re_c), color='gray', alpha=0.2, label='Stability Gap')
ax1.set_ylabel('Eigenvalue Intensity')
ax1.set_title('UFT-F Eigenvalue Collision: The Transition Trigger')
ax1.legend(loc='upper right')
ax1.grid(True, alpha=0.3)

# Plot 2: L1 Norm Divergence vs. Sharded Regularization
ax2.plot(res, l1_laminar, label='Laminar Branch (Non-Sharded - ACI Violation)', color='red', linestyle='--')
ax2.plot(res, l1_sharded, label=r'Turbulent Branch ($G_{24}$ Sharded - ACI Compliant)', color='green', linewidth=2.5)
ax2.axvline(Re_c, color='red', linestyle=':')
ax2.set_yscale('log')
ax2.set_xlabel('Reynolds Number (Re)')
ax2.set_ylabel(r'$L^1$ Norm $||V||_{L^1}$ (Log Scale)')
ax2.set_title('Laminar $L^1$ Divergence vs. Turbulent ACI-Regularization')
ax2.legend()
ax2.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('rec_collision_simulation.png')

print(f"Simulation Complete. Re_c = {Re_c:,.2f}")