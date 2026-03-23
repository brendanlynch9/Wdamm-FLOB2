import numpy as np

def search_for_identity(target):
    # E8 Constants
    V_e8 = 15.0453 # Fundamental volume residue
    roots = 240
    dim = 8
    
    # Fundamental Constants
    pi = np.pi
    e = np.e
    gamma = 0.57721 # Euler-Mascheroni
    
    candidates = [
        ("V_e8 / (2 * pi * e)", V_e8 / (2 * pi * e)),
        ("V_e8 / (pi**2 + 2*pi)", V_e8 / (pi**2 + 2*pi)),
        ("(V_e8 * dim) / roots", (V_e8 * dim) / roots),
        ("V_e8 / (16 + gamma)", V_e8 / (16 + gamma)),
        ("sqrt(V_e8) / 4", np.sqrt(V_e8) / 4),
        ("V_e8 / (pi * 5)", V_e8 / (pi * 5))
    ]
    
    print(f"--- DECOMPOSING SPECTRAL CONSTANT: {target} ---")
    print(f"{'Formula':<25} | {'Value':<12} | {'Error %'}")
    print("-" * 55)
    
    for label, val in candidates:
        error = abs(val - target) / target * 100
        print(f"{label:<25} | {val:<12.6f} | {error:.4f}%")

if __name__ == "__main__":
    search_for_identity(0.928167)

#     (base) brendanlynch@Brendans-Laptop MontgomeryPairCorrelation % python constantDecomposition.py
# --- DECOMPOSING SPECTRAL CONSTANT: 0.928167 ---
# Formula                   | Value        | Error %
# -------------------------------------------------------
# V_e8 / (2 * pi * e)       | 0.880900     | 5.0925%
# V_e8 / (pi**2 + 2*pi)     | 0.931437     | 0.3523%
# (V_e8 * dim) / roots      | 0.501510     | 45.9677%
# V_e8 / (16 + gamma)       | 0.907589     | 2.2170%
# sqrt(V_e8) / 4            | 0.969707     | 4.4755%
# V_e8 / (pi * 5)           | 0.957814     | 3.1941%
# (base) brendanlynch@Brendans-Laptop MontgomeryPairCorrelation % 