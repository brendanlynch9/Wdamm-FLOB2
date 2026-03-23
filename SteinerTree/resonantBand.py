import numpy as np

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

def run_resonant_band_scan():
    # Expanded grid to see the 'cliffs' on either side of the 23-25 band
    grids = [20, 21, 22, 23, 24, 25, 26, 27, 28]
    n_trials = 5000
    n_points = 50
    
    efficiency_totals = {g: 0.0 for g in grids}
    win_counts = {g: 0 for g in grids}
    ultra_precise_counts = {g: 0 for g in grids} # rel_err < 10^-6
    
    print(f"Executing Final Steiner Scan: {n_trials} trials...")

    for i in range(n_trials):
        # Generate random points + jiggle
        pts = np.random.uniform(-10, 10, (n_points, 2))
        shift = np.random.uniform(0.001, 0.010, size=2)
        pts += shift
        
        med = geometric_median(pts)
        l_cont = star_length(pts, med)
        
        trial_errors = {}
        for g in grids:
            step = 1.0 / g
            q_med = np.round(med / step) * step
            l_quant = star_length(pts, q_med)
            
            rel_err = (l_quant - l_cont) / l_cont
            trial_errors[g] = rel_err
            
            # 1. Efficiency
            eff = 1.0 / ((rel_err + 1e-15) * g)
            efficiency_totals[g] += eff
            
            # 2. Precision Count
            if rel_err < 1e-6:
                ultra_precise_counts[g] += 1
        
        # 3. Win Count
        winner = min(trial_errors, key=trial_errors.get)
        win_counts[winner] += 1
        
        if (i+1) % 1000 == 0:
            print(f"Progress: {i+1}/{n_trials} trials complete.")

    print("\n--- THE RESONANT BAND: Final Statistical Profile ---")
    print(f"{'Grid':<8} | {'Mean Efficiency':<15} | {'Win %':<8} | {'Precision %'}")
    print("-" * 55)
    for g in grids:
        avg_eff = efficiency_totals[g] / n_trials
        win_p = (win_counts[g] / n_trials) * 100
        prec_p = (ultra_precise_counts[g] / n_trials) * 100
        print(f"1/{g:<6} | {avg_eff:<15.2f} | {win_p:<8.1f} | {prec_p:.1f}%")

if __name__ == "__main__":
    run_resonant_band_scan()

#     (base) brendanlynch@Brendans-Laptop SteinerTree % python resonantBand.py
# Executing Final Steiner Scan: 5000 trials...
# Progress: 1000/5000 trials complete.
# Progress: 2000/5000 trials complete.
# Progress: 3000/5000 trials complete.
# Progress: 4000/5000 trials complete.
# Progress: 5000/5000 trials complete.

# --- THE RESONANT BAND: Final Statistical Profile ---
# Grid     | Mean Efficiency | Win %    | Precision %
# -------------------------------------------------------
# 1/20     | 119111.98       | 8.6      | 20.4%
# 1/21     | 121477.00       | 9.0      | 22.9%
# 1/22     | 130431.71       | 8.5      | 24.9%
# 1/23     | 139917.07       | 8.7      | 27.7%
# 1/24     | 262136.75       | 9.9      | 30.6%
# 1/25     | 168214.34       | 11.5     | 33.5%
# 1/26     | 117512.70       | 13.3     | 36.0%
# 1/27     | 249095.58       | 14.6     | 38.1%
# 1/28     | 193058.52       | 16.0     | 39.7%
# (base) brendanlynch@Brendans-Laptop SteinerTree % 

