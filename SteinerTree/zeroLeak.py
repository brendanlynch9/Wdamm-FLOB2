import numpy as np

# FINAL ANALYTIC AUDIT: CROSS-GEOMETRY HARMONIC STABILITY
# This script evaluates if the 1/24 efficiency spike is universal across 
# different manifold types (Uniform, Corridor, Cluster).

def geometric_median(points, eps=1e-10, max_iter=500):
    y = np.mean(points, axis=0)
    for _ in range(max_iter):
        dists = np.linalg.norm(points - y, axis=1)
        dists = np.maximum(dists, 1e-12)
        weights = 1.0 / dists
        y_new = np.average(points, axis=0, weights=weights)
        if np.linalg.norm(y_new - y) < eps:
            break
        y = y_new
    return y

def star_length(points, pt):
    return np.sum(np.linalg.norm(points - pt, axis=1))

def get_points(mode):
    if mode == "uniform":
        return np.random.uniform(-5, 5, (50, 2))
    elif mode == "corridor":
        x = np.random.uniform(-10, 10, 100)
        y = np.random.normal(0, 0.01, 100)
        return np.column_stack((x, y))
    elif mode == "clusters":
        c1 = np.random.normal([-2, -2], 0.5, (25, 2))
        c2 = np.random.normal([2, 2], 0.5, (25, 2))
        return np.vstack((c1, c2))

def run_audit():
    modes = ["uniform", "corridor", "clusters"]
    grids = [23, 24, 25]
    results = {mode: {g: [] for g in grids} for mode in modes}
    
    n_trials = 1000
    print(f"Running Cross-Geometry Harmonic Audit ({n_trials} trials/mode)...")

    for mode in modes:
        for _ in range(n_trials):
            pts = get_points(mode)
            med = geometric_median(pts)
            l_cont = star_length(pts, med)
            
            for g in grids:
                step = 1.0 / g
                q_med = np.round(med / step) * step
                rel_err = (star_length(pts, q_med) - l_cont) / l_cont
                eff = 1.0 / ((rel_err + 1e-15) * g)
                results[mode][g].append(eff)

    print("\n--- FINAL AUDIT: Efficiency Comparison (1/24 vs Neighbors) ---")
    print(f"{'Geometry':<12} | {'1/23 Eff':<12} | {'1/24 Eff':<12} | {'1/25 Eff':<12} | {'24-Dominance'}")
    print("-" * 75)
    for mode in modes:
        e23 = np.mean(results[mode][23])
        e24 = np.mean(results[mode][24])
        e25 = np.mean(results[mode][25])
        dom = "YES" if (e24 > e23 and e24 > e25) else "NO"
        print(f"{mode:<12} | {e23:<12.0f} | {e24:<12.0f} | {e25:<12.0f} | {dom}")

if __name__ == "__main__":
    run_audit()

#     (base) brendanlynch@Brendans-Laptop SteinerTree % python zeroLEak.py
# Running Cross-Geometry Harmonic Audit (1000 trials/mode)...

# --- FINAL AUDIT: Efficiency Comparison (1/24 vs Neighbors) ---
# Geometry     | 1/23 Eff     | 1/24 Eff     | 1/25 Eff     | 24-Dominance
# ---------------------------------------------------------------------------
# uniform      | 59682        | 39344        | 31338        | NO
# corridor     | 351723       | 623188       | 60664        | YES
# clusters     | 263818       | 46226        | 58600        | NO
# (base) brendanlynch@Brendans-Laptop SteinerTree % 

