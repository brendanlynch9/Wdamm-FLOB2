import numpy as np
from scipy.linalg import eigh
from math import degrees, atan2, asin

def run_optimized():
    print("--- UFT-F Quark Sector: NELDER-MEAD OPTIMUM REACHED ---")
    
    # Optimized Parameters from the simplex search (Down Quarks)
    j11 = 2.43724348e-05  # Near-zero Down Anchor
    j22 = 5.01696885e-03  # Strange Anchor
    j33 = 2.30878263e+00  # Bottom Anchor
    j12 = 1.28019732e-04  # Cabibbo Torque
    j23 = 9.62969066e-02  # Atmospheric Torque
    j13 = 8.98765247e-03  # Small Residue

    # Construct the Jacobi Operator J
    J = np.array([
        [j11, j12, j13],
        [j12, j22, j23],
        [j13, j23, j33]
    ])

    # Eigendecomposition
    eigvals, eigvecs = eigh(J)
    idx = eigvals.argsort()
    m_sq = np.abs(eigvals[idx])
    U = eigvecs[:, idx]

    # Scale m3 to 4.196 GeV Physical Benchmark (Bottom Quark)
    scale = 4.196 / np.sqrt(m_sq[2])
    m_phys = np.sqrt(m_sq) * scale

    # CKM Angle Extraction
    theta12 = degrees(atan2(np.abs(U[0, 1]), np.abs(U[0, 0])))
    theta23 = degrees(atan2(np.abs(U[1, 2]), np.abs(U[2, 2])))
    theta13 = degrees(asin(np.abs(U[0, 2])))

    # Delta m_squared
    dm21 = m_phys[1]**2 - m_phys[0]**2
    dm31 = m_phys[2]**2 - m_phys[0]**2

    print(f"\nFinal Physical Hierarchy (Down Quarks):")
    print(f"m_d: {m_phys[0]:.4f} GeV | m_s: {m_phys[1]:.4f} GeV | m_b: {m_phys[2]:.4f} GeV")
    print(f"dm21: {dm21:.4e} GeV^2 | dm31: {dm31:.4e} GeV^2")
    
    print(f"\nFinal CKM Angles (Simplex Locked):")
    print(f"theta12: {theta12:.4f}° (Target 13.03°)")
    print(f"theta23: {theta23:.4f}° (Target 2.39°)")
    print(f"theta13: {theta13:.4f}° (Target 0.214°)")
    
    residual = (theta12-13.03)**2 + (theta23-2.39)**2 + (theta13-0.214)**2
    print(f"\nResidual Error (E): {residual:.2e}")

if __name__ == "__main__":
    run_optimized()

#     (base) brendanlynch@Brendans-Laptop Quarks % python quark_ckm_derivation_OPTIMIZED.py
# --- UFT-F Quark Sector: NELDER-MEAD OPTIMUM REACHED ---

# Final Physical Hierarchy (Down Quarks):
# m_d: 0.0227 GeV | m_s: 0.0897 GeV | m_b: 4.1960 GeV
# dm21: 7.5231e-03 GeV^2 | dm31: 1.7606e+01 GeV^2

# Final CKM Angles (Simplex Locked):
# theta12: 13.0299° (Target 13.03°)
# theta23: 2.3894° (Target 2.39°)
# theta13: 0.2226° (Target 0.214°)

# Residual Error (E): 7.42e-05
# (base) brendanlynch@Brendans-Laptop Quarks % 