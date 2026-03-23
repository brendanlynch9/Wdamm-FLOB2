# NS.py (Final Cleaned Version)
import numpy as np
# Note: Using np.trapezoid to suppress deprecation warnings.

# 1. Gaussian Vortex Ring
def omega_theta(r, z, r0=1.0, sigma=0.3):
    # Simplified 2D slice
    R, Z = np.meshgrid(r, z, indexing='ij')
    return np.exp(-((R - r0)**2 + Z**2) / (2 * sigma**2))

# Grid
r = np.linspace(0.1, 3.0, 512)
z = np.linspace(-2.0, 2.0, 512)
omega = omega_theta(r, z)

# 2. Radial averaging: ∫ω dz / Δz
# Averaging over the z-dimension (axis=1 in the meshgrid)
bar_omega_r = np.trapezoid(omega, z, axis=1) / (z[-1] - z[0]) 

# 3. Encoding: α_n = ∫ bar_omega sin(κ_n r) dr
N = 200
kappa_n = np.pi * np.arange(1, N+1)
alpha_n = np.array([np.trapezoid(bar_omega_r * np.sin(k * r), r) for k in kappa_n])

# 4. Marchenko kernel B(t)
# Note: r is used as the t-variable for the kernel approximation
B_t = np.sum(alpha_n[:, None] * np.exp(-kappa_n[:, None] * r), axis=0)

# 5. GLM inversion: V = -2 dB/dr
dr = r[1] - r[0]
V = -2 * np.gradient(B_t, dr)

# 6. Reconstructed vorticity (Approximation of the potential V' ~ ω_L)
omega_L = np.gradient(V, dr)

# 7. Error
error = np.max(np.abs(np.abs(bar_omega_r) - np.abs(omega_L)))

print(f"Axisymmetric test: ||ω - ω_L||_∞ = {error:.3e}")
if error < 1e-3:
    print("PASS: (Q3) validated in axisymmetric case")
else:
    print("FAIL: error too high, requires full 3D inverse scattering theory.")