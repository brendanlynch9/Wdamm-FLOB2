import numpy as np
from scipy.linalg import expm

def audit_isospectral_update():
    """
    Verifies that the Law 5 update rule H(t) = U H(0) U* preserves the spectrum (prevents catastrophic forgetting).
    """
    print("--- UFT-F LAW 5: UNITARY INVARIANCE AUDIT ---")
    
    # 1. Initialize a 16x16 Self-Adjoint Hamiltonian (Rank-16 Lock)
    dim = 16
    A_rand = np.random.randn(dim, dim) + 1j * np.random.randn(dim, dim)
    H_0 = (A_rand + A_rand.conj().T) / 2
    
    # 2. Generate an Anti-Hermitian Operator (The Generator A)
    G_rand = np.random.randn(dim, dim) + 1j * np.random.randn(dim, dim)
    A = (G_rand - G_rand.conj().T) / 2
    
    # 3. Compute Unitary Update U = exp(A * dt)
    dt = 0.01
    U = expm(A * dt)
    
    # 4. Apply Isospectral Flow: H_new = U @ H_0 @ U.H
    H_new = U @ H_0 @ U.conj().T
    
    # 5. Compare Spectra
    spec_0 = np.sort(np.linalg.eigvalsh(H_0))
    spec_new = np.sort(np.linalg.eigvalsh(H_new))
    
    drift = np.linalg.norm(spec_0 - spec_new)
    is_invariant = drift < 1e-12
    
    print(f"Original Spectrum (mean): {np.mean(spec_0):.6f}")
    print(f"Updated Spectrum (mean):  {np.mean(spec_new):.6f}")
    print(f"Spectral Drift:            {drift:.2e}")
    print(f"No-Forgetting Guarantee:   {is_invariant}")

if __name__ == "__main__":
    audit_isospectral_update()



#     (base) brendanlynch@Brendans-Laptop paper5IsospectralUpdate % python law5Update.py
# --- UFT-F LAW 5: UNITARY INVARIANCE AUDIT ---
# Original Spectrum (mean): 0.164620
# Updated Spectrum (mean):  0.164620
# Spectral Drift:            1.55e-14
# No-Forgetting Guarantee:   True
# (base) brendanlynch@Brendans-Laptop paper5IsospectralUpdate % 