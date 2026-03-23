import numpy as np

# UFT-F Constants from your 2025/2026 papers
LAMBDA_0 = 15.0452  # Modularity Constant
OMEGA_U = 0.0002073045  # Hopf Torsion (Time's Arrow)
C_UFT_F = 0.003119  # Spectral Floor

def uftf_spectral_potential(distances, k):
    """
    Calculates the Informational Mass of the runner configuration.
    Incorporates the Base-24 quantization and Hopf Torsion.
    """
    gap_threshold = 1.0 / k
    # L1 norm is the sum of potential spikes where distance < threshold
    # We add the Hopf Torsion as a 'stiffness' regulator
    l1_contribution = 0
    for d in distances:
        if d < gap_threshold:
            # Exponential spike as we approach 'collision'
            # Scaled by the spectral floor constant
            l1_contribution += np.exp((gap_threshold - d) / C_UFT_F) * (1 + OMEGA_U)
    
    return l1_contribution

def run_simulation_non_degenerate(k):
    # Enforce distinct residues (mod 24) to satisfy the ACI
    r24_residues = [1, 5, 7, 11, 13, 17, 19, 23] # The 8 fundamental residues
    # Each runner gets a unique residue to minimize L1 mass
    speeds = []
    for r in r24_residues[:k]:
        # Lift the residue into a higher prime frequency
        speeds.append(r + 24 * np.random.randint(1, 5))
    
    speeds = np.array(speeds)
    print(f"--- UFT-F Non-Degenerate Check (k={k}) ---")
    print(f"Distinct Residues: {speeds % 24}")

    # Use a wider temporal window to account for Hopf Torsion lag
    for t in np.arange(0.001, 5.0, 0.001):
        pos = np.sort((speeds * t) % 1.0)
        distances = np.append(np.diff(pos), 1.0 - (pos[-1] - pos[0]))
        
        l1_mass = uftf_spectral_potential(distances, k)
        
        if l1_mass < LAMBDA_0:
            print(f"[*] ACI Vacuum Found at t={t:.4f} | L1 Mass={l1_mass:.4f}")
            return True
    print("[!] MANIFOLD RUPTURE: No stable state found.")
    return False

run_simulation_non_degenerate(8)

# (base) brendanlynch@Brendans-Laptop lonelyRunner % python runnerTCBTest.py
# --- UFT-F Quantized Runner Check (k=8) ---
# Resonance Speeds (mod 24): [11 13 23 23 13  5 17 17]
# (base) brendanlynch@Brendans-Laptop lonelyRunner % 