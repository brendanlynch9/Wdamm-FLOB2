import numpy as np
from scipy.linalg import eigh
from math import degrees, atan2, asin

def check_stability(j_params, perturbation=1e-5):
    def get_angles(p):
        # Construct the Jacobi Operator J
        J = np.array([
            [p[0], p[3], p[5]], 
            [p[3], p[1], p[4]], 
            [p[5], p[4], p[2]]
        ])
        
        # Eigendecomposition and sorting
        eigvals, eigvecs = eigh(J)
        idx = eigvals.argsort()
        U = eigvecs[:, idx]
        
        # Calculate CKM-like angles
        t12 = degrees(atan2(np.abs(U[0, 1]), np.abs(U[0, 0])))
        t23 = degrees(atan2(np.abs(U[1, 2]), np.abs(U[2, 2])))
        t13 = degrees(asin(np.abs(U[0, 2])))
        return np.array([t12, t23, t13])

    base_angles = get_angles(j_params)
    stiffness = []
    
    # Calculate the gradient across all 6 parameters
    for i in range(len(j_params)):
        p_up = np.array(j_params)
        p_up[i] += perturbation
        
        p_dn = np.array(j_params)
        p_dn[i] -= perturbation
        
        # Numerical gradient (Change in angles / Change in parameter)
        grad = (get_angles(p_up) - get_angles(p_dn)) / (2 * perturbation)
        stiffness.append(np.linalg.norm(grad))
        
    print(f"--- UFT-F STABILITY ANALYSIS ---")
    print(f"Mean Geometric Stiffness (S): {np.mean(stiffness):.4f}")
    
    # Validation against the Neutrino Paper (AAAANeutrinos.pdf)
    target_s = 8.91
    variance = abs(np.mean(stiffness) - target_s) / target_s
    print(f"Target Stiffness: {target_s}")
    print(f"Variance from Neutrino Sector: {variance:.2%}")

# Parameters from your Down-Quark Optimized Run
params = [2.43724348e-05, 5.01696885e-03, 2.30878263e+00, 1.28019732e-04, 9.62969066e-02, 8.98765247e-03]

if __name__ == "__main__":
    check_stability(params)

#     (base) brendanlynch@Brendans-Laptop Quarks % python quark_stability_gradient.py
# --- UFT-F STABILITY ANALYSIS ---
# Mean Geometric Stiffness (S): 11851.8648
# Target Stiffness: 8.91
# Variance from Neutrino Sector: 132917.56%
# (base) brendanlynch@Brendans-Laptop Quarks % 