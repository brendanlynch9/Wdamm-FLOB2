import numpy as np

def hunt_the_outlier(k, resolution=50000):
    print(f"Hunting for a 'Never Lonely' Runner among k={k}...")
    
    # 1. Generate Prime Velocities (Orthogonal set)
    primes = []
    candidate = 1
    while len(primes) < k:
        candidate += 1
        if all(candidate % p != 0 for p in primes):
            primes.append(candidate)
    velocities = np.array(primes)
    
    t = np.linspace(0, 1, resolution, endpoint=False)
    
    # Track the 'Best Covered' runner
    best_min_depth = -1
    best_runner_idx = -1
    
    # Check every single runner
    for i in range(k):
        # Current runner is 'i', others are 'j'
        my_v = velocities[i]
        others_v = np.delete(velocities, i)
        
        # Calculate coverage for this specific runner
        # A point t is covered if |(v_j - v_i)t| <= 1/k for ANY j
        
        # We compute the combined mask of all slabs
        # Optimization: We sum the masks. If sum > 0 at all t, he is covered.
        depth_map = np.zeros(resolution)
        
        for other_v in others_v:
            diff = abs(other_v - my_v)
            phase = (diff * t) % 1.0
            # Slab condition
            mask = np.minimum(phase, 1.0 - phase) <= (1.0 / k)
            depth_map += mask.astype(int)
            
        min_d = np.min(depth_map)
        mean_d = np.mean(depth_map)
        
        if min_d > best_min_depth:
            best_min_depth = min_d
            best_runner_idx = i
            
        # Immediate Kill Condition
        if min_d > 0:
            print(f"\n!!! COUNTER-EXAMPLE FOUND !!!")
            print(f"Runner #{i} (Speed {my_v}) is NEVER LONELY.")
            print(f"Min Coverage Depth: {min_d}")
            return
            
        if i % 50 == 0:
            print(f"Checked {i}/{k} runners... Best Min Depth so far: {best_min_depth}")

    print(f"\nResult for k={k}:")
    print(f"Best Covered Runner: #{best_runner_idx} (Speed {velocities[best_runner_idx]})")
    print(f"His Min Depth: {best_min_depth} (If > 0, Conjecture is Dead)")
    print(f"His Mean Depth: {mean_d:.4f}")

if __name__ == "__main__":
    # The moment of truth. 
    # Warning: O(k^2) complexity. 321 is manageable (~10s).
    hunt_the_outlier(321)

#     (base) brendanlynch@Brendans-Laptop lonelyRunner % python oneRunner.py
# Hunting for a 'Never Lonely' Runner among k=321...
# Checked 0/321 runners... Best Min Depth so far: 0.0
# Checked 50/321 runners... Best Min Depth so far: 0.0
# Checked 100/321 runners... Best Min Depth so far: 0.0
# Checked 150/321 runners... Best Min Depth so far: 0.0
# Checked 200/321 runners... Best Min Depth so far: 0.0
# Checked 250/321 runners... Best Min Depth so far: 0.0
# Checked 300/321 runners... Best Min Depth so far: 0.0

# Result for k=321:
# Best Covered Runner: #0 (Speed 2)
# His Min Depth: 0.0 (If > 0, Conjecture is Dead)
# His Mean Depth: 2.0130
# (base) brendanlynch@Brendans-Laptop lonelyRunner % 
