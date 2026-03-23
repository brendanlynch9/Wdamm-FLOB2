# corrected_and_verified_safe.py
# Run this exact file — Memory-safe version for Apple Silicon Macs.
import numpy as np
import time

def calculate_potential_norm_safe(N_max, sectors, omega_u, N_theta):
    """
    Calculates the L1 norms using an iterative loop over theta to conserve memory.
    The integral is approximated as a Riemann sum: L1 = sum(|V(theta_i)| * d_theta)
    """
    start_time = time.time()
    
    phi_u = 2.0 * np.pi * omega_u
    
    # 1. Define vectors (n and coeff) only once - Small memory footprint (~16MB)
    n = np.arange(2, N_max + 1, dtype=np.float64)
    # Pathological decay: p = 1 - omega_u < 1 -> theoretically non-L1-integrable
    coeff = n ** (-1.0 + omega_u)
    
    # 2. Define angular domain
    N_theta = 1024 # Reduced angular points for memory safety
    theta = np.linspace(0, 2 * np.pi, N_theta, endpoint=False, dtype=np.float64)
    d_theta = theta[1] - theta[0] # Angular step size

    # Initialize L1 accumulators
    L1_sym_sum = 0.0
    L1_aci_sum = 0.0
    
    # Array to store V_aci for the concentration check
    V_aci_array = np.zeros(N_theta, dtype=np.float64)
    
    # 3. Iterate over each angular point (theta_i) to avoid massive M x N matrix
    for i in range(N_theta):
        # Calculate the series for this single theta point (vectorized over n)
        
        # Inner angular term (a vector of length N_max)
        inner_angles = (2.0 * np.pi / sectors) * theta[i] * n
        
        # T-symmetric potential V^0(theta_i)
        V_sym_i = np.sum(coeff * np.cos(inner_angles))
        
        # ACI-regularized potential V^ACI(theta_i)
        V_aci_i = np.sum(coeff * np.cos(inner_angles + phi_u))
        
        # Accumulate L1 integral sum
        L1_sym_sum += np.abs(V_sym_i) * d_theta
        L1_aci_sum += np.abs(V_aci_i) * d_theta
        
        # Store for concentration check
        V_aci_array[i] = V_aci_i

    L1_sym = L1_sym_sum
    L1_aci = L1_aci_sum
    
    # --- Concentration check for V_aci (using the stored array) ---
    top2_concentration = 0.0
    if sectors > 0:
        bounds = np.linspace(0, 2*np.pi, sectors+1)
        integrals = []
        for i in range(sectors):
            idx = (theta >= bounds[i]) & (theta < bounds[i+1])
            if np.any(idx):
                # Use trapz on the segment for a more accurate integral within the sector
                integral_segment = np.trapz(np.abs(V_aci_array[idx]), theta[idx])
                integrals.append(integral_segment)
        
        if integrals and sum(integrals) > 1e-12: # Avoid division by zero
            top2_concentration = sum(sorted(integrals, reverse=True)[:2]) / sum(integrals) * 100
    # --- End Concentration check ---

    end_time = time.time()
    
    # Prepare results string
    results = (
        f"N_max used (Series Truncation) : {N_max:,}\n"
        f"N_theta used (Integration Pts): {N_theta:,}\n"
        f"L1 symmetric (should blow up) : {L1_sym:,.2f}\n"
        f"L1 ACI-regularized          : {L1_aci:,.2f}\n"
        f"Regularization factor       : {L1_sym / L1_aci:,.1f}x\n"
        f"Time taken                  : {end_time - start_time:.1f} seconds\n"
        f"Top-2 sector concentration  : {top2_concentration:.4f}%"
    )
    
    return results

# --- Main execution ---
if __name__ == "__main__":
    
    # Define constants
    N_max = 2_000_000 
    N_theta = 1024
    sectors = 24
    omega_u = 0.0002073045 # UFT-F derived T-breaking phase 

    print("Running memory-safe, high-N calculation. This is slow but memory-safe (estimated 2-4 min)...\n")
    
    results = calculate_potential_norm_safe(N_max, sectors, omega_u, N_theta)

    print(results)

#     the output was: 
#     (base) brendanlynch@Mac appliedUFTFTime % python corrected.py
# Running memory-safe, high-N calculation. This is slow but memory-safe (estimated 2-4 min)...

# N_max used (Series Truncation) : 2,000,000
# N_theta used (Integration Pts): 1,024
# L1 symmetric (should blow up) : 3.37
# L1 ACI-regularized          : 3.36
# Regularization factor       : 1.0x
# Time taken                  : 20.4 seconds
# Top-2 sector concentration  : 32.2675%
# (base) brendanlynch@Mac appliedUFTFTime % 