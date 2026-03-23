import numpy as np

class HofstadterAuditorFixed:
    def __init__(self):
        self.lambda_0 = 15.04545  # UFT-F Stability Ceiling (Truth Threshold)
        self.c_uft = 0.003119337  # Spectral Floor
        self.omega_u = 0.0002073  # Hopf Torsion

    def calculate_l1_norm(self, q):
        """
        Analytical solution for the L1 norm of 2*cos(2*pi*x/q) * exp(-c*|x|)
        Prevents numerical integration failure on high-frequency oscillations.
        """
        b = 2 * np.pi / q
        c = self.c_uft
        
        # Exact solution for the infinite integral of |2 cos(bx)| exp(-c|x|)
        term1 = 4 * c / (c**2 + b**2)
        term2 = 1.0 / np.tanh(c * np.pi / (2 * b))  # coth(c*pi/2b)
        return term1 * term2

    def verify_stability(self, q):
        l1_norm = self.calculate_l1_norm(q)
        
        # Stability is determined by the ACI (L1 < lambda_0)
        # Note: 1/q < c_uft is the geometric rupture point (q ~ 321)
        is_stable = l1_norm < self.lambda_0
        status = "ADMISSIBLE (TRUE)" if is_stable else "RUPTURE (SINGULAR)"
        
        return {
            "Bands (q)": q,
            "Flux (alpha)": round(1.0/q, 6),
            "L1_Norm": round(l1_norm, 4),
            "Status": status,
            "Spectral_Margin": round(self.lambda_0 - l1_norm, 4)
        }

# --- Verification ---
auditor = HofstadterAuditorFixed()

# 1. Base-24 Harmonic (Stable)
print(f"Base-24: {auditor.verify_stability(q=24)}")

# 2. Critical Point (Near lambda_0 ceiling)
print(f"Limit:   {auditor.verify_stability(q=37)}")

# 3. The Redundancy Cliff (q=321)
print(f"Rupture: {auditor.verify_stability(q=321)}")


# (base) brendanlynch@Brendans-Laptop hofstader % python numericalCheck.py
# Base-24: {'Bands (q)': 24, 'Flux (alpha)': 0.041667, 'L1_Norm': 9.7266, 'Status': 'ADMISSIBLE (TRUE)', 'Spectral_Margin': 5.3189}
# Limit:   {'Bands (q)': 37, 'Flux (alpha)': 0.027027, 'L1_Norm': 14.9946, 'Status': 'ADMISSIBLE (TRUE)', 'Spectral_Margin': 0.0508}
# Rupture: {'Bands (q)': 321, 'Flux (alpha)': 0.003115, 'L1_Norm': 129.5134, 'Status': 'RUPTURE (SINGULAR)', 'Spectral_Margin': -114.4679}
# (base) brendanlynch@Brendans-Laptop hofstader % 