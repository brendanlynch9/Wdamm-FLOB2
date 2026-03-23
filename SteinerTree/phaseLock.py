import numpy as np
from scipy.spatial.distance import pdist, squareform

def get_star_length(points, center):
    return np.sum(np.linalg.norm(points - center, axis=1))

# Configurations
n_rand = 100
configs = {
    "Equilateral": np.array([[0,0], [1,0], [0.5, np.sqrt(3)/2]]),
    "Adversarial Circle": np.column_stack([np.cos(np.linspace(0, 2*np.pi, 12)), np.sin(np.linspace(0, 2*np.pi, 12))]),
    "Random 100": np.random.RandomState(42).uniform(-5, 5, (n_rand, 2))
}

grid_steps = [12, 16, 20, 22, 23, 24, 25, 26, 30, 36, 48]

print(f"{'Config':<20} {'Grid':>5} {'Rel Err %':>15} {'Phase Lock Indicator'}")
print("-" * 60)

for name, pts in configs.items():
    med = np.mean(pts, axis=0) # Geometric Median approximation
    l_cont = get_star_length(pts, med)
    
    for g in grid_steps:
        step = 1.0 / g
        q_med = np.round(med / step) * step
        l_quant = get_star_length(pts, q_med)
        rel_err = 100 * (l_quant - l_cont) / l_cont
        
        # A simple 'Phase Lock' indicator: is the error significantly 
        # lower than the grid resolution (1/g)?
        lock = "LOCKED" if rel_err < (100.0/g**2) else "" 
        
        print(f"{name:<20} 1/{g:<3} {rel_err:15.8f}% {lock}")
    print("-" * 60)

#     (base) brendanlynch@Brendans-Laptop SteinerTree % python phaseLock.py
# Config                Grid       Rel Err % Phase Lock Indicator
# ------------------------------------------------------------
# Equilateral          1/12       0.11596571% LOCKED
# Equilateral          1/16       0.04169841% LOCKED
# Equilateral          1/20       0.00952485% LOCKED
# Equilateral          1/22       0.01933937% LOCKED
# Equilateral          1/23       0.05506635% LOCKED
# Equilateral          1/24       0.00066946% LOCKED
# Equilateral          1/25       0.03501404% LOCKED
# Equilateral          1/26       0.02667924% LOCKED
# Equilateral          1/30       0.00952485% LOCKED
# Equilateral          1/36       0.00899067% LOCKED
# Equilateral          1/48       0.00066946% LOCKED
# ------------------------------------------------------------
# Adversarial Circle   1/12       0.00000000% LOCKED
# Adversarial Circle   1/16       0.10449781% LOCKED
# Adversarial Circle   1/20      -0.06916152% LOCKED
# Adversarial Circle   1/22      -0.03302884% LOCKED
# Adversarial Circle   1/23      -0.01612730% LOCKED
# Adversarial Circle   1/24       0.00000000% LOCKED
# Adversarial Circle   1/25       0.01537277% LOCKED
# Adversarial Circle   1/26       0.03001856% LOCKED
# Adversarial Circle   1/30       0.08199522% LOCKED
# Adversarial Circle   1/36       0.00000000% LOCKED
# Adversarial Circle   1/48       0.00000000% LOCKED
# ------------------------------------------------------------
# Random 100           1/12      -0.03132551% LOCKED
# Random 100           1/16       0.00629386% LOCKED
# Random 100           1/20      -0.02264943% LOCKED
# Random 100           1/22      -0.00482512% LOCKED
# Random 100           1/23       0.00353071% LOCKED
# Random 100           1/24       0.00260050% LOCKED
# Random 100           1/25       0.00951381% LOCKED
# Random 100           1/26       0.01620511% LOCKED
# Random 100           1/30      -0.00524012% LOCKED
# Random 100           1/36      -0.01017445% LOCKED
# Random 100           1/48       0.00629386% LOCKED
# ------------------------------------------------------------
# (base) brendanlynch@Brendans-Laptop SteinerTree % 