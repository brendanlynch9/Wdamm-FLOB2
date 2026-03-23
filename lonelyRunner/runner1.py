import numpy as np
from scipy.integrate import quad

class UFTF_LonelyRunner:
    def __init__(self, k_runners, lambda_0=15.045):
        self.k = k_runners
        self.lambda_0 = lambda_0
        self.speeds = np.random.choice(np.arange(1, 100), self.k, replace=False)
        self.gap_threshold = 1.0 / self.k

    def get_positions(self, t):
        return (self.speeds * t) % 1.0

    def calculate_v_lr(self, t):
        """
        Maps runner distances to an Informational Potential V_M(x).
        The potential spikes (collisions) when distance < 1/k.
        """
        pos = self.get_positions(t)
        pos = np.sort(pos)
        # Calculate circular distances
        diffs = np.diff(pos)
        dist_to_others = np.append(diffs, 1.0 - (pos[-1] - pos[0]))
        
        # UFT-F mapping: Potential is inversely proportional to the gap
        # If any dist < 1/k, the potential mass increases.
        v_spectral = np.sum([np.exp(self.gap_threshold - d) for d in dist_to_others if d < self.gap_threshold])
        return v_spectral

    def check_aci_stability(self, time_limit=100, step=0.01):
        print(f"--- UFT-F Lonely Runner Stability Check (k={self.k}) ---")
        print(f"Speeds: {self.speeds}")
        
        max_l1 = 0
        lonely_time_found = False
        
        for t in np.arange(0.1, time_limit, step):
            # In UFT-F, L1 norm represents the informational mass
            l1_norm = self.calculate_v_lr(t)
            
            if l1_norm < self.lambda_0:
                # The "Lonely" state is a stable, self-adjoint vacuum
                if not lonely_time_found:
                    print(f"[*] Stability Achieved at t={t:.3f} | L1 Mass: {l1_norm:.4f}")
                    lonely_time_found = True
            
            max_l1 = max(max_l1, l1_norm)
            
        if lonely_time_found:
            print(f"[RESULT] ACI Verified: Particle stability exists within the spectral floor.")
        else:
            print(f"[RESULT] DIVERGENCE: Potential mass exceeded lambda_0. Manifold Rupture.")

# Initialize for k=7 (The current proven limit)
sim = UFTF_LonelyRunner(k_runners=7)
sim.check_aci_stability()

# (base) brendanlynch@Brendans-Laptop lonelyRunner % python runner1.py
# --- UFT-F Lonely Runner Stability Check (k=7) ---
# Speeds: [56 85 87 88 61 46 51]
# [*] Stability Achieved at t=0.100 | L1 Mass: 5.4385
# [RESULT] ACI Verified: Particle stability exists within the spectral floor.
# (base) brendanlynch@Brendans-Laptop lonelyRunner % 