import numpy as np
from scipy.optimize import minimize
import matplotlib.pyplot as plt

def get_max_loneliness(speeds, k, samples=10000):
    """
    Pure mathematical check: finds the maximum loneliness gap achieved at any time t.
    No potentials, no constants, no penalties.
    """
    t_vals = np.linspace(0, 1, samples)
    best_min_dist = 0
    
    for t in t_vals:
        pos = (speeds * t) % 1.0
        pos = np.sort(pos)
        # Calculate all pairwise distances on the 1-torus
        dists = np.diff(pos)
        dists = np.append(dists, 1.0 - (pos[-1] - pos[0]))
        min_dist = np.min(dists)
        if min_dist > best_min_dist:
            best_min_dist = min_dist
            
    return best_min_dist

def objective(v, k):
    # We want to MAXIMIZE the best min distance found over all t
    # So we minimize the negative of it.
    return -get_max_loneliness(v, k)

def run_falsification_test(k_range):
    results = []
    required_gap = [1.0/k for k in k_range]
    achieved_gap = []

    for k in k_range:
        print(f"Testing k={k}...")
        # Start with random speeds, then optimize to find a 'Lonely' configuration
        v0 = np.random.uniform(1, 100, k)
        res = minimize(objective, v0, args=(k,), method='Nelder-Mead', tol=1e-6)
        
        max_gap = -res.fun
        achieved_gap.append(max_gap)
        success = max_gap >= (1.0/k)
        results.append(success)
        print(f"  Target: {1.0/k:.6f} | Achieved: {max_gap:.6f} | Success: {success}")

    return k_range, required_gap, achieved_gap

# Run it
ks, targets, achieved = run_falsification_test(range(2, 21))

# Visualization of the 'Cliff'
plt.figure(figsize=(10,6))
plt.plot(ks, targets, 'r--', label='LRC Required Gap (1/k)')
plt.plot(ks, achieved, 'bo-', label='Best Gap Found (Optimized)')
plt.title("Pure Search vs. Conjecture Requirement")
plt.xlabel("Number of Runners (k)")
plt.ylabel("Gap Distance")
plt.legend()
plt.show()


# (base) brendanlynch@Brendans-Laptop lonelyRunner %  python falsifiableLonelyRunnerTest2.py 
# Testing k=2...
#   Target: 0.500000 | Achieved: 0.500000 | Success: False
# Testing k=3...
#   Target: 0.333333 | Achieved: 0.333333 | Success: False
# Testing k=4...
#   Target: 0.250000 | Achieved: 0.250000 | Success: False
# Testing k=5...
#   Target: 0.200000 | Achieved: 0.200000 | Success: False
# Testing k=6...
#   Target: 0.166667 | Achieved: 0.166525 | Success: False
# Testing k=7...
#   Target: 0.142857 | Achieved: 0.142242 | Success: False
# Testing k=8...
#   Target: 0.125000 | Achieved: 0.121453 | Success: False
# Testing k=9...
#   Target: 0.111111 | Achieved: 0.109223 | Success: False
# Testing k=10...
#   Target: 0.100000 | Achieved: 0.094321 | Success: False
# Testing k=11...
#   Target: 0.090909 | Achieved: 0.078786 | Success: False
# Testing k=12...
#   Target: 0.083333 | Achieved: 0.070104 | Success: False
# Testing k=13...
#   Target: 0.076923 | Achieved: 0.072771 | Success: False
# Testing k=14...
#   Target: 0.071429 | Achieved: 0.062002 | Success: False
# Testing k=15...
#   Target: 0.066667 | Achieved: 0.053787 | Success: False
# Testing k=16...
#   Target: 0.062500 | Achieved: 0.049863 | Success: False
# Testing k=17...
#   Target: 0.058824 | Achieved: 0.047553 | Success: False
# Testing k=18...
#   Target: 0.055556 | Achieved: 0.041811 | Success: False
# Testing k=19...
#   Target: 0.052632 | Achieved: 0.039250 | Success: False
# Testing k=20...
#   Target: 0.050000 | Achieved: 0.038795 | Success: False
# 2026-01-16 05:20:47.502 python[66158:128928709] The class 'NSSavePanel' overrides the method identifier.  This method is implemented by class 'NSWindow'
# (base) brendanlynch@Brendans-Laptop lonelyRunner % 
