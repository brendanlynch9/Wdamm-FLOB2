import numpy as np
from scipy.linalg import eigh

def run_unconditional_closure():
    print("--- UFT-F UNCONDITIONAL CLOSURE: LOGARITHMIC PROJECTION ---")
    
    # 1. Axiomatic Constants
    omega_u = 0.0002073045
    alpha_inv = 137.036
    N_base = 24
    S_stiff = 8.91
    # Lynch correction: The manifold depth is ln(alpha_inv) 
    # as per the 'Exponential Decoherence' proof in Zenodo [7]
    depth_correction = np.log(alpha_inv) / (alpha_inv / N_base) 
    
    # 2. Down-Quark Seed
    j_p = [2.43724348e-05, 5.01696885e-03, 2.30878263e+00, 1.28019732e-04, 9.62969066e-02, 8.98765247e-03]
    J_d = np.array([[j_p[0], j_p[3], j_p[5]], [j_p[3], j_p[1], j_p[4]], [j_p[5], j_p[4], j_p[2]]])
    eigvals_d, V_d = eigh(J_d)
    V_d = V_d[:, eigvals_d.argsort()]

    # 3. Sweep the Torsion Constant
    ks = np.linspace(0.9, 1.1, 500)
    volumes = []
    phases = []

    for k in ks:
        # The 'Perfect Wedge' Phase
        # Modulated by the Logarithmic Embedding Depth
        phi = k * (N_base / S_stiff) * omega_u * alpha_inv * depth_correction
        
        P = np.diag([np.exp(-1j * phi), np.exp(1j * phi), 1.0])
        CKM = V_d.T @ P @ V_d
        
        # Metric: Jarlskog Area
        j_cp = np.imag(CKM[0,0] * CKM[1,1] * np.conj(CKM[0,1]) * np.conj(CKM[1,0]))
        volumes.append(abs(j_cp))
        
        delta = -np.degrees(np.angle(CKM[0, 2]))
        if delta < 0: delta += 360
        phases.append(delta)

    # 4. Results
    max_idx = np.argmax(volumes)
    peak_phase = phases[max_idx]

    print(f"Final Analytical Peak: {peak_phase:.2f}°")
    print(f"Experimental Target: 69.31°")
    print(f"Final Falsification Delta: {abs(peak_phase - 69.31):.4f}°")

    if abs(peak_phase - 69.31) < 0.1:
        print(">>> RESULT: ABSOLUTE ANALYTICAL CLOSURE. The CKM phase is a geometric invariant.")
    else:
        print(">>> ANALYSIS: Check the Logarithmic manifold curvature.")

if __name__ == "__main__":
    run_unconditional_closure()

#     (base) brendanlynch@Brendans-Laptop Quarks % python Tviolation.py
# --- UFT-F UNCONDITIONAL CLOSURE: LOGARITHMIC PROJECTION ---
# Final Analytical Peak: 85.12°
# Experimental Target: 69.31°
# Final Falsification Delta: 15.8129°
# >>> ANALYSIS: Check the Logarithmic manifold curvature.
# (base) brendanlynch@Brendans-Laptop Quarks % 

