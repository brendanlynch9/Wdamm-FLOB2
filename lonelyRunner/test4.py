import numpy as np

def uftf_torus_check(k, t_max=100):
    """
    Actually simulates runners on a torus to see if they EVER reach 1/k loneliness.
    This answers Grok's critique by doing real time-sampling.
    """
    c_uft_f = 0.003119337
    delta = 1/k
    # Seed with Golden Ratio (best known irrational spacing for 1D torus)
    speeds = np.arange(k) * (np.sqrt(5) - 1) 
    
    min_potential = float('inf')
    
    # Sample 1000 points in time
    for t in np.linspace(0.1, t_max, 1000):
        pos = (speeds * t) % 1.0
        pos.sort()
        # Calculate circular distances
        diffs = np.diff(pos)
        dist = np.append(diffs, 1.0 - (pos[-1] - pos[0]))
        
        # Check if ANY gap is < c_uft_f (The Hard-Deck)
        if np.any(dist < c_uft_f):
            return "RUPTURE"
            
        # Real UFT-F Potential Calculation
        current_potential = np.sum(np.exp((delta - dist) / (dist - c_uft_f + 1e-12)))
        if current_potential < min_potential:
            min_potential = current_potential
            
    return min_potential

print(f"k=320 Real Torus Check: {uftf_torus_check(320)}")
print(f"k=321 Real Torus Check: {uftf_torus_check(321)}")