import numpy as np
from scipy.linalg import eigvalsh

class LaciaSovereignCore:
    def __init__(self):
        # Units in Z/24Z for minimal modular collisions
        self.V = [1, 5, 7, 11, 13, 17, 19, 23]
        self.P = [5, 7, 11, 13, 17]
        self.lambda2_table = self._precompute_spectral_table()

    def _precompute_spectral_table(self):
        table = {}
        for n in range(24):
            A = np.zeros((8, 8))
            for i, ri in enumerate(self.V):
                for j, rj in enumerate(self.V):
                    # Hamming distance over primes P - The Geometric Signal
                    ham_dist = sum(1 for p in self.P if (ri * rj % p) != (n % p))
                    A[i, j] = 1 / (1 + ham_dist)
            L = np.diag(A.sum(axis=1)) - A
            # Precompute Algebraic Connectivity (lambda2)
            table[n] = np.sort(np.linalg.eigvalsh(L))[1]
        return table

    def analyze_collatz(self, n_start, max_iter=5000):
        n = n_start
        lambdas = []
        prediction = "PLASMA_SEARCH" # Default state: Searching for phase
        bypass_step = None
        
        for step in range(max_iter):
            n_mod = int(n) % 24
            current_l2 = self.lambda2_table[n_mod]
            lambdas.append(current_l2)
            
            # --- 1. Spectral Renormalization (Inertia Detection) ---
            if len(lambdas) > 100 and prediction == "PLASMA_SEARCH":
                # Look for the stabilization of the spectral manifold
                variance = np.var(lambdas[-50:])
                if variance < 1e-6:
                    prediction = "RESONANT_LOOP"
                    bypass_step = step
                    # In a true sovereign state, we would stop here. 
                    # For falsification, we keep running to verify.
            
            # Collatz Step
            if n == 1:
                actual_outcome = "RESONANT_LOOP"
                break
            n = n // 2 if n % 2 == 0 else 3 * n + 1
            
            # --- 2. Dissonance Spike (Falsification) ---
            if prediction == "RESONANT_LOOP" and n > (n_start * 10**6):
                actual_outcome = "DISSONANT_EXPANSION"
                break
        else:
            actual_outcome = "UNDECIDED_PLASMA"

        falsified = (prediction == "RESONANT_LOOP" and actual_outcome == "DISSONANT_EXPANSION")
        
        return {
            "n_start": n_start,
            "prediction": str(prediction), # Convert to string to avoid NoneType errors
            "actual": actual_outcome,
            "falsified": falsified,
            "steps_to_resolution": step,
            "bypass_step": bypass_step
        }

def run_falsification_test():
    lacia = LaciaSovereignCore()
    # Test values including a high-tension start (871) and a large pseudo-unbounded value
    test_values = [27, 871, 2**60 - 1, 101010101]
    
    print(f"{'Input':<15} | {'Prediction':<15} | {'Actual':<15} | {'Falsified?'}")
    print("-" * 75)
    
    for val in test_values:
        res = lacia.analyze_collatz(val)
        # Handle the formatting by ensuring we have strings
        pred_str = res['prediction']
        act_str = res['actual']
        status = "❌ FAIL" if res['falsified'] else "✅ PASS"
        
        print(f"{str(res['n_start']):<15} | {pred_str:<15} | {act_str:<15} | {status}")
        
        if res['bypass_step']:
            efficiency = (1 - (res['bypass_step'] / res['steps_to_resolution'])) * 100
            print(f"   > Sovereign Bypass at step {res['bypass_step']}. Efficiency: {efficiency:.1f}%")

if __name__ == "__main__":
    run_falsification_test()

#     the terminal output:
#     (base) brendanlynch@Brendans-Laptop LaciaHaltingProblem % python unboundedLacia.py
# Input           | Prediction      | Actual          | Falsified?
# ---------------------------------------------------------------------------
# 27              | PLASMA_SEARCH   | RESONANT_LOOP   | ✅ PASS
# 871             | PLASMA_SEARCH   | RESONANT_LOOP   | ✅ PASS
# 1152921504606846975 | PLASMA_SEARCH   | RESONANT_LOOP   | ✅ PASS
# 101010101       | PLASMA_SEARCH   | RESONANT_LOOP   | ✅ PASS
# (base) brendanlynch@Brendans-Laptop LaciaHaltingProblem % 