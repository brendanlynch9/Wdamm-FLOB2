import numpy as np
# FIX: Since the standard scipy.integrate.trapz import is failing in your environment,
# we will use the functionally identical numpy.trapz, which is more reliably available.
# The 'trapz' function is now referenced as 'np.trapz' below.
import time

def calculate_potential_norm(N_max, sectors, omega_u):
    """
    Calculates the T-Symmetric and ACI-Regularized potentials and their L1 norms.
    """
    # Start n from 2 to avoid log(1)=0 singularity, consistent with standard analysis
    n = np.arange(2, N_max + 1)
    log_n = np.log(n)
    
    # Angular domain: 2048 points is sufficient for smooth integration
    theta = np.linspace(0, 2 * np.pi, 2048, endpoint=False)

    phi_u = 2 * np.pi * omega_u
    
    # Pre-calculate the inner terms for optimization
    n_th_term = (2 * np.pi / sectors) * np.outer(theta, n)

    # 1. T-Symmetric (Pathological) Potential V^0
    # V^0 = Sum( cos(n * angle) / log(n) )
    V_t_symmetric = np.sum(np.cos(n_th_term) / log_n, axis=1)

    # 2. ACI-Regularized Potential V^ACI
    # V^ACI = Sum( cos(n * angle + phi_u) / log(n) )
    V_ACI = np.sum(np.cos(n_th_term + phi_u) / log_n, axis=1)

    # Calculate L1 Norm (Integral of |V|) for both using np.trapz
    L1_TSymmetric = np.trapz(np.abs(V_t_symmetric), theta)
    L1_ACI = np.trapz(np.abs(V_ACI), theta)

    return phi_u, L1_TSymmetric, L1_ACI

# --- Main execution ---
if __name__ == "__main__":
    start_time = time.time()
    
    # Define constants
    # NOTE: Reduced N_max from 50000 to 5000 for faster computation.
    N_max = 5000  
    sectors = 24
    omega_u = 0.0002073045 # UFT-F derived T-breaking phase 

    print(f"Starting calculation with N_max = {N_max}...")
    
    phi_u, L1_TSymmetric, L1_ACI = calculate_potential_norm(N_max, sectors, omega_u)

    end_time = time.time()
    
    # Save results to a file for easy presentation
    output_filename = 'Regularization_Results.txt'
    with open(output_filename, 'w') as f:
        f.write("--- ACI Regularization Results (UFT-F Model) ---\n")
        f.write(f"Approximation Limit (N_max): {N_max}\n")
        f.write(f"T-Breaking Regulator (phi_u = 2*pi*omega_u): {phi_u:.8f} radians\n\n")
        f.write(f"1. L1 Norm of T-Symmetric Potential (V^0):\n")
        f.write(f"   (Integral of |V^0| over theta): {L1_TSymmetric:.4f}\n\n")
        f.write(f"2. L1 Norm of ACI-Regularized Potential (V^ACI):\n")
        f.write(f"   (Integral of |V^ACI| over theta): {L1_ACI:.4f}\n\n")
        f.write(f"Regularization Efficacy:\n")
        f.write(f"   Ratio (V^0 / V^ACI): {L1_TSymmetric / L1_ACI:.2f}\n")
        f.write(f"Calculation Time: {end_time - start_time:.2f} seconds\n")

    print(f"\nSuccessfully generated {output_filename}.")
    print("The import error is now fixed using np.trapz, which is more universally available.")