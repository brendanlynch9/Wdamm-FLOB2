import numpy as np

def discrete_laplacian(phi):
    # Simple 1D Laplacian extension to a vector
    lap = np.zeros_like(phi)
    for i in range(len(phi)):
        lap[i] = -2*phi[i] + phi[(i-1)%len(phi)] + phi[(i+1)%len(phi)]
    return lap

# Surrogate potential array in 24 dims
phi = np.random.rand(24)
lambda_e8 = 1.0  # toy eigenvalue
lap_phi = discrete_laplacian(phi)

# Solve lap_phi + lambda*Phi_SM = 0 => Phi_SM ≈ -lap_phi / lambda
phi_sm_estimates = -lap_phi / lambda_e8
print("Phi_SM estimates per dimension:", phi_sm_estimates)
print("Average Phi_SM estimate:", np.mean(phi_sm_estimates))


# (base) brendanlynch@Brendans-Laptop BellinsonConjecture % python generalizedSpectralFloor.py
# Phi_SM estimates per dimension: [ 0.1207109   0.06744075 -0.29861329  0.61272101 -0.47611908  0.55859092
#  -0.56715723  0.45343213 -0.8793612   0.48628714  0.48254335 -0.8347457
#   1.05699949 -0.81173387  0.54652966 -0.78106261  1.12847761 -1.01747079
#   0.15791777  0.14066958 -0.21489093  0.90521223 -0.67647597 -0.15990186]
# Average Phi_SM estimate: -1.3877787807814457e-17
# (base) brendanlynch@Brendans-Laptop BellinsonConjecture % 