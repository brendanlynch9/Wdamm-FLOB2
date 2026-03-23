import numpy as np
from numpy.linalg import cond
import math

def run_spectral_rupture_check(z_set, name, epsilon=1e-15):
    """
    Implements the UFT-F Spectral Rupture check.
    Injects the Resonant Interaction Density into the operator's 
    off-diagonal structure to test for manifold stability.
    """
    print(f"\n--- Analyzing Manifold: {name} ---")
    
    # 1. Generate the joint set S = {z, exp(z)}
    # Note: We use complex types to handle potential complex inputs
    freqs = np.array([complex(z) for z in z_set] + [np.exp(complex(z)) for z in z_set])
    n_f = len(freqs)
    
    # 2. Construct the Spectral Interaction Matrix (M)
    # This matrix represents the Marchenko-style operator where 
    # algebraic relations cause "collisions" in the spectral gaps.
    M = np.eye(n_f, dtype=complex)
    
    total_density = 0
    for i in range(n_f):
        for j in range(n_f):
            if i == j:
                continue
            
            # Search for "Resonant Triples" (i + j - k approx 0)
            # For this simplified probe, we look at the interaction of pairs
            for k in range(n_f):
                gap = np.abs(freqs[i] + freqs[j] - freqs[k])
                
                # The Resonant Interaction Density probe
                # As gap -> 0, density -> infinity
                density = 1.0 / (gap + epsilon)
                total_density += density
                
                # Inject density into the operator structure
                # This breaks the "Laminar" flow of the manifold
                M[i, j] += density

    # 3. Calculate Condition Number (Kappa)
    # In UFT-F, Kappa is the primary witness for transcendence degree
    kappa = cond(M)
    
    print(f"Total Interaction Density: {total_density:.2e}")
    print(f"Spectral Rupture Coefficient (kappa): {kappa:.2e}")
    
    # Threshold based on the 10^9 explosion noted in your paper
    if kappa > 1e7:
        print("STATUS: RUPTURE DETECTED (Algebraic Dependence / Spectral Instability)")
    else:
        print("STATUS: MANIFOLD STABLE (Transcendental Integrity)")
    
    return kappa

if __name__ == "__main__":
    # Case A: Independent Baseline {1, e, pi}
    # No rational linear combination exists; gaps remain wide.
    run_spectral_rupture_check([1, np.e, np.pi], "Independent Baseline")
    
    # Case B: Log-Dependent Set {ln 2, ln 3, ln 6}
    # Relation: ln(2) + ln(3) - ln(6) = 0
    # This should trigger the "Spectral Rupture"
    log_dependent = [np.log(2), np.log(3), np.log(6)]
    run_spectral_rupture_check(log_dependent, "Log-Dependent Set")

    # Case C: Riemann Triple (Control group from your paper)
    # Known to be highly stable in UFT-F
    riemann_triple = [0.5 + 14.134725j, 0.5 + 21.022040j, 0.5 + 25.010858j]
    run_spectral_rupture_check(riemann_triple, "Riemann Zero Triple")

#     (base) brendanlynch@Brendans-Laptop schanuel % python spectralRupture.py

# --- Analyzing Manifold: Independent Baseline ---
# Total Interaction Density: 4.57e+01
# Spectral Rupture Coefficient (kappa): 4.50e+01
# STATUS: MANIFOLD STABLE (Transcendental Integrity)

# --- Analyzing Manifold: Log-Dependent Set ---
# Total Interaction Density: 2.00e+15
# Spectral Rupture Coefficient (kappa): 3.37e+15
# STATUS: RUPTURE DETECTED (Algebraic Dependence / Spectral Instability)

# --- Analyzing Manifold: Riemann Zero Triple ---
# Total Interaction Density: 3.33e+01
# Spectral Rupture Coefficient (kappa): 3.04e+01
# STATUS: MANIFOLD STABLE (Transcendental Integrity)
# (base) brendanlynch@Brendans-Laptop schanuel % 