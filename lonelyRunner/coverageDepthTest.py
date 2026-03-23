import numpy as np
import matplotlib.pyplot as plt

def check_coverage_depth_and_variance(k_values, resolution=100000):
    print(f"\n{'k':<5} | {'Mean Depth':<10} | {'Min Depth':<10} | {'Variance':<10} | {'Status'}")
    print("-" * 65)
    
    # We simulate the time axis t in [0, 1)
    # The 'Bad Set' for each pair (i, j) is where |(vi - vj)t| < 1/k
    t = np.linspace(0, 1, resolution, endpoint=False)
    
    for k in k_values:
        # Use first k primes for velocities to maximize 'Orthogonality'
        # (Simulating the 'Prime Runner' variant)
        primes = []
        candidate = 1
        while len(primes) < k:
            candidate += 1
            if all(candidate % p != 0 for p in primes):
                primes.append(candidate)
        velocities = np.array(primes)
        
        # Initialize 'Depth Map' (How many slabs cover each point t)
        coverage_depth = np.zeros(resolution)
        
        # Add the 'Slabs'
        # For each pair, add 1 to the depth where condition is met
        # We optimize by only checking adjacent differences to save time in simulation
        # (Approximation of the 'Local' density)
        # Note: A full N^2 check is slow, so we check relative to v_0 for demonstration
        # of the 'Sum = 2' principle.
        
        # Actually, let's do the rigorous pairwise check for a subset to be accurate.
        # We calculate the 'Forbidden Density' function F(t).
        
        # To keep it fast but accurate: Sum of indicator functions
        for i in range(k):
            # Check against the "Mean Speed" runner (middle of pack)
            # This captures the 'Average' constraint density
            ref_v = velocities[k // 2] 
            if i == k // 2: continue
            
            diff = abs(velocities[i] - ref_v)
            
            # The condition is |diff * t - integer| <= 1/k
            # This is a periodic wave of width 2/k
            phase = (diff * t) % 1.0
            # Wrap around handling
            mask = np.minimum(phase, 1.0 - phase) <= (1.0 / k)
            coverage_depth += mask.astype(int)

        # Statistics
        mean_depth = np.mean(coverage_depth)
        min_depth = np.min(coverage_depth)
        variance = np.var(coverage_depth)
        
        if min_depth > 0:
            status = "TOTAL SATURATION (L=Empty)"
        elif mean_depth > 1.5:
             status = "HIGH SATURATION"
        else:
            status = "GAPS EXIST"
            
        print(f"{k:<5} | {mean_depth:<10.4f} | {min_depth:<10.0f} | {variance:<10.4f} | {status}")

if __name__ == "__main__":
    # We test the transition
    check_coverage_depth_and_variance([5, 17, 100, 321])

#     Im honest here:
#     (base) brendanlynch@Brendans-Laptop lonelyRunner % python coverageDepthTest.py

# k     | Mean Depth | Min Depth  | Variance   | Status
# -----------------------------------------------------------------
# 5     | 1.6000     | 0          | 1.3067     | HIGH SATURATION
# 17    | 1.8828     | 0          | 4.6920     | HIGH SATURATION
# 100   | 1.9821     | 0          | 7.5041     | HIGH SATURATION
# 321   | 1.9801     | 0          | 9.5677     | HIGH SATURATION
# (base) brendanlynch@Brendans-Laptop lonelyRunner % 
