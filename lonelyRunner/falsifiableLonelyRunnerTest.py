import numpy as np
from scipy.optimize import minimize, differential_evolution
import matplotlib.pyplot as plt
from tqdm import tqdm

# ================================================
#          CONFIGURATION
# ================================================

MAX_K = 60                     # How far to push (60 is already very hard)
TIME_SAMPLES = 5000            # Dense sampling per candidate
OPT_RESTARTS = 12              # How many independent optimization runs per k
GLOBAL_EFFORT = 80             # Differential evolution iterations

print(f"Starting pure Lonely Runner falsifiability test up to k={MAX_K}")

# ================================================
#          CORE LONELY RUNNER CHECK
# ================================================

def check_lonely_runner(speeds, k, n_samples=TIME_SAMPLES):
    """
    Returns (found, max_gap)
    found   : True if exists t with min-distance >= 1/k
    max_gap : the largest min-distance found (fraction of 1/k)
    """
    t_values = np.linspace(0, 1, n_samples)  # one period is enough due to periodicity
    best_min_dist = 0.0

    for t in t_values:
        positions = (speeds * t) % 1.0
        pos_sorted = np.sort(positions)
        diffs = np.diff(pos_sorted)
        circ_diff = 1.0 - (pos_sorted[-1] - pos_sorted[0])
        all_dists = np.append(diffs, circ_diff)
        min_dist = np.min(all_dists)
        best_min_dist = max(best_min_dist, min_dist)

    target = 1.0 / k
    return best_min_dist >= target, best_min_dist / target   # normalized to 1/k


# ================================================
#          OPTIMIZATION OBJECTIVE
# ================================================

def objective_to_maximize_gap(speeds, k):
    """Minimize the negative best gap (so we maximize it)"""
    _, norm_gap = check_lonely_runner(speeds, k, n_samples=800)
    return -norm_gap  # negative because minimize()


# ================================================
#          MAIN SEARCH FUNCTION
# ================================================

def try_find_lonely_config(k):
    best_gap_norm = 0.0
    best_speeds = None

    # Seeding strategies
    seeds = []

    # 1. Golden ratio spacing (very good for uniform distribution)
    phi = (1 + np.sqrt(5)) / 2
    golden = np.arange(k) * (phi - 1) % 1
    seeds.append(golden)

    # 2. Base-24 lifted residues
    residues = np.array([1,5,7,11,13,17,19,23], dtype=float)
    n_res = min(k, len(residues))
    base24 = residues[:n_res]
    if n_res < k:
        base24 = np.concatenate([base24, np.random.uniform(24, 100, k - n_res)])
    seeds.append(base24)

    # 3. Several random starts
    for _ in range(OPT_RESTARTS // 2):
        seeds.append(np.random.uniform(0, 100, k))

    # Run optimization from each seed
    for idx, init in enumerate(seeds):
        print(f"k={k} | Seed {idx+1}/{len(seeds)} ... ", end="", flush=True)

        # Local optimization (maximize gap)
        res = minimize(
            objective_to_maximize_gap,
            init,
            args=(k,),
            method='Nelder-Mead',
            options={'maxiter': 1200, 'fatol': 1e-6, 'disp': False}
        )
        _, gap = check_lonely_runner(res.x, k)

        if gap > best_gap_norm:
            best_gap_norm = gap
            best_speeds = res.x.copy()
            print(f"new best: {gap:.4f} × (1/k)")
        else:
            print(f"{gap:.4f}")

    found, _ = check_lonely_runner(best_speeds, k)
    return found, best_gap_norm, best_speeds


# ================================================
#          EXECUTE THE TEST
# ================================================

results = []
best_gaps = []

for k in tqdm(range(2, MAX_K + 1), desc="Testing k"):
    found, gap_norm, _ = try_find_lonely_config(k)
    status = "FOUND ≥ 1/k" if found else "NOT FOUND (best: {:.4f} × 1/k)".format(gap_norm)
    print(f"k = {k:3d} → {status}")
    results.append((k, found, gap_norm))
    best_gaps.append(gap_norm)


# ================================================
#          SUMMARY & PLOT
# ================================================

print("\n" + "═"*70)
print("FINAL SUMMARY - PURE LONELY RUNNER TEST")
print("═"*70)
print(f"Tested up to k = {MAX_K}")
print(f"Found satisfying t (loneliness ≥ 1/k) for all k ≤ {MAX_K}? → {'YES' if all(r[1] for r in results) else 'NO'}")

# Plot best achieved gap (normalized to 1/k)
ks, _, gaps = zip(*results)
plt.figure(figsize=(12, 7))
plt.plot(ks, gaps, 'o-', color='blue', markersize=5, label='Best achieved gap / (1/k)')
plt.axhline(y=1.0, color='red', linestyle='--', label='Required: 1.0 × (1/k)')
plt.axvline(x=7, color='green', linestyle=':', label='Classically proven up to k=7')
plt.title('Pure Lonely Runner Search: Best Achieved Gap Ratio vs k\n(No custom potentials, no thresholds)')
plt.xlabel('Number of runners k')
plt.ylabel('Max min-distance found / (1/k)')
plt.ylim(0, 1.2)
plt.grid(True, alpha=0.3)
plt.legend()
plt.tight_layout()
plt.savefig("pure_lonely_runner_gap_ratio.png", dpi=300)
plt.show()

print("Plot saved: pure_lonely_runner_gap_ratio.png")
print("If gap stays ≥ 1.0 up to high k → conjecture supported")
print("If gap falls significantly below 1.0 → conjecture challenged")

# (base) brendanlynch@Brendans-Laptop lonelyRunner % python falsifiableLonelyRunnerTest.py 
# Starting pure Lonely Runner falsifiability test up to k=60
# Testing k:   0%|                                         | 0/59 [00:00<?, ?it/s]k=2 | Seed 1/8 ... new best: 1.0000 × (1/k)
# k=2 | Seed 2/8 ... 0.9998
# k=2 | Seed 3/8 ... 0.9999
# k=2 | Seed 4/8 ... 0.9999
# k=2 | Seed 5/8 ... new best: 1.0000 × (1/k)
# k=2 | Seed 6/8 ... 1.0000
# k=2 | Seed 7/8 ... 0.9998
# k=2 | Seed 8/8 ... 1.0000
# k =   2 → NOT FOUND (best: 1.0000 × 1/k)
# Testing k:   2%|▌                                | 1/59 [00:03<03:01,  3.13s/it]k=3 | Seed 1/8 ... new best: 0.9999 × (1/k)
# k=3 | Seed 2/8 ... 0.9993
# k=3 | Seed 3/8 ... 0.9965
# k=3 | Seed 4/8 ... 0.9988
# k=3 | Seed 5/8 ... 0.9877
# k=3 | Seed 6/8 ... 0.9946
# k=3 | Seed 7/8 ... 0.9976
# k=3 | Seed 8/8 ... 0.9970
# k =   3 → NOT FOUND (best: 0.9999 × 1/k)
# Testing k:   3%|█                                | 2/59 [00:08<04:18,  4.54s/it]k=4 | Seed 1/8 ... new best: 0.9998 × (1/k)
# k=4 | Seed 2/8 ... 0.9997
# k=4 | Seed 3/8 ... 0.9989
# k=4 | Seed 4/8 ... new best: 0.9999 × (1/k)
# k=4 | Seed 5/8 ... 0.9925
# k=4 | Seed 6/8 ... 0.9966
# k=4 | Seed 7/8 ... 0.9975
# k=4 | Seed 8/8 ... 0.9959
# k =   4 → NOT FOUND (best: 0.9999 × 1/k)
# Testing k:   5%|█▋                               | 3/59 [00:16<05:42,  6.12s/it]k=5 | Seed 1/8 ... new best: 0.9999 × (1/k)
# k=5 | Seed 2/8 ... 0.9987
# k=5 | Seed 3/8 ... 0.9889
# k=5 | Seed 4/8 ... 0.9734
# k=5 | Seed 5/8 ... 0.9984
# k=5 | Seed 6/8 ... 0.9873
# k=5 | Seed 7/8 ... 0.9878
# k=5 | Seed 8/8 ... 0.9950
# k =   5 → NOT FOUND (best: 0.9999 × 1/k)
# Testing k:   7%|██▏                              | 4/59 [00:30<08:30,  9.28s/it]k=6 | Seed 1/8 ... new best: 0.9111 × (1/k)
# k=6 | Seed 2/8 ... new best: 0.9980 × (1/k)
# k=6 | Seed 3/8 ... 0.9826
# k=6 | Seed 4/8 ... 0.9366
# k=6 | Seed 5/8 ... 0.9694
# k=6 | Seed 6/8 ... 0.9281
# k=6 | Seed 7/8 ... 0.8895
# k=6 | Seed 8/8 ... 0.9803
# k =   6 → NOT FOUND (best: 0.9980 × 1/k)
# Testing k:   8%|██▊                              | 5/59 [00:49<11:26, 12.72s/it]k=7 | Seed 1/8 ... new best: 0.9907 × (1/k)
# k=7 | Seed 2/8 ... 0.9439
# k=7 | Seed 3/8 ... 0.9802
# k=7 | Seed 4/8 ... 0.9767
# k=7 | Seed 5/8 ... 0.8941
# k=7 | Seed 6/8 ... 0.9384
# k=7 | Seed 7/8 ... new best: 0.9912 × (1/k)
# k=7 | Seed 8/8 ... 0.9739
# k =   7 → NOT FOUND (best: 0.9912 × 1/k)
# Testing k:  10%|███▎                             | 6/59 [01:15<15:05, 17.09s/it]k=8 | Seed 1/8 ... new best: 0.8975 × (1/k)
# k=8 | Seed 2/8 ... new best: 0.9850 × (1/k)
# k=8 | Seed 3/8 ... 0.9073
# k=8 | Seed 4/8 ... 0.9596
# k=8 | Seed 5/8 ... 0.9165
# k=8 | Seed 6/8 ... 0.9808
# k=8 | Seed 7/8 ... 0.9159
# k=8 | Seed 8/8 ... 0.9012
# k =   8 → NOT FOUND (best: 0.9850 × 1/k)
# Testing k:  12%|███▉                             | 7/59 [01:44<18:10, 20.98s/it]k=9 | Seed 1/8 ... new best: 0.9465 × (1/k)
# k=9 | Seed 2/8 ... 0.8968
# k=9 | Seed 3/8 ... new best: 0.9493 × (1/k)
# k=9 | Seed 4/8 ... 0.8393
# k=9 | Seed 5/8 ... 0.8232
# k=9 | Seed 6/8 ... 0.9049
# k=9 | Seed 7/8 ... 0.9061
# k=9 | Seed 8/8 ... 0.9099
# k =   9 → NOT FOUND (best: 0.9493 × 1/k)
# Testing k:  14%|████▍                            | 8/59 [02:20<21:55, 25.79s/it]k=10 | Seed 1/8 ... new best: 0.9487 × (1/k)
# k=10 | Seed 2/8 ... new best: 0.9527 × (1/k)
# k=10 | Seed 3/8 ... 0.8799
# k=10 | Seed 4/8 ... 0.8365
# k=10 | Seed 5/8 ... 0.8862
# k=10 | Seed 6/8 ... 0.8490
# k=10 | Seed 7/8 ... 0.8660
# k=10 | Seed 8/8 ... 0.8440
# k =  10 → NOT FOUND (best: 0.9527 × 1/k)
# Testing k:  15%|█████                            | 9/59 [03:02<25:54, 31.08s/it]k=11 | Seed 1/8 ... new best: 0.9253 × (1/k)
# k=11 | Seed 2/8 ... 0.8721
# k=11 | Seed 3/8 ... 0.8612
# k=11 | Seed 4/8 ... 0.8206
# k=11 | Seed 5/8 ... new best: 0.9513 × (1/k)
# k=11 | Seed 6/8 ... 0.8946
# k=11 | Seed 7/8 ... 0.8010
# k=11 | Seed 8/8 ... 0.9000
# k =  11 → NOT FOUND (best: 0.9513 × 1/k)
# Testing k:  17%|█████▍                          | 10/59 [03:53<30:13, 37.02s/it]k=12 | Seed 1/8 ... new best: 0.9510 × (1/k)
# k=12 | Seed 2/8 ... 0.8224
# k=12 | Seed 3/8 ... 0.8889
# k=12 | Seed 4/8 ... 0.7811
# k=12 | Seed 5/8 ... 0.8259
# k=12 | Seed 6/8 ... 0.7886
# k=12 | Seed 7/8 ... 0.8073
# k=12 | Seed 8/8 ... 0.8889
# k =  12 → NOT FOUND (best: 0.9510 × 1/k)
# Testing k:  19%|█████▉                          | 11/59 [04:47<33:50, 42.30s/it]k=13 | Seed 1/8 ... new best: 0.9722 × (1/k)
# k=13 | Seed 2/8 ... 0.8141
# k=13 | Seed 3/8 ... 0.8886
# k=13 | Seed 4/8 ... 0.6678
# k=13 | Seed 5/8 ... 0.8597
# k=13 | Seed 6/8 ... 0.8444
# k=13 | Seed 7/8 ... 0.8450
# k=13 | Seed 8/8 ... 0.8803
# k =  13 → NOT FOUND (best: 0.9722 × 1/k)
# Testing k:  20%|██████▌                         | 12/59 [05:41<35:53, 45.83s/it]k=14 | Seed 1/8 ... new best: 0.8378 × (1/k)
# k=14 | Seed 2/8 ... 0.7709
# k=14 | Seed 3/8 ... 0.7664
# k=14 | Seed 4/8 ... 0.7533
# k=14 | Seed 5/8 ... 0.7875
# k=14 | Seed 6/8 ... new best: 0.8914 × (1/k)
# k=14 | Seed 7/8 ... 0.6766
# k=14 | Seed 8/8 ... 0.8122
# k =  14 → NOT FOUND (best: 0.8914 × 1/k)
# Testing k:  22%|███████                         | 13/59 [06:45<39:24, 51.40s/it]k=15 | Seed 1/8 ... new best: 0.6535 × (1/k)
# k=15 | Seed 2/8 ... new best: 0.6968 × (1/k)
# k=15 | Seed 3/8 ... 0.6655
# k=15 | Seed 4/8 ... new best: 0.7273 × (1/k)
# k=15 | Seed 5/8 ... 0.6863
# k=15 | Seed 6/8 ... 0.7128
# k=15 | Seed 7/8 ... new best: 0.8182 × (1/k)
# k=15 | Seed 8/8 ... new best: 0.8429 × (1/k)
# k =  15 → NOT FOUND (best: 0.8429 × 1/k)
# Testing k:  24%|███████▌                        | 14/59 [07:53<42:10, 56.24s/it]k=16 | Seed 1/8 ... new best: 0.6968 × (1/k)
# k=16 | Seed 2/8 ... 0.6509
# k=16 | Seed 3/8 ... new best: 0.7488 × (1/k)
# k=16 | Seed 4/8 ... new best: 0.8522 × (1/k)
# k=16 | Seed 5/8 ... 0.6271
# k=16 | Seed 6/8 ... 0.7846
# k=16 | Seed 7/8 ... 0.6231
# k=16 | Seed 8/8 ... 0.7790
# k =  16 → NOT FOUND (best: 0.8522 × 1/k)
# Testing k:  25%|████████▏                       | 15/59 [09:01<43:59, 59.98s/it]k=17 | Seed 1/8 ... new best: 0.7996 × (1/k)
# k=17 | Seed 2/8 ... new best: 0.8146 × (1/k)
# k=17 | Seed 3/8 ... 0.7803
# k=17 | Seed 4/8 ... 0.7502
# k=17 | Seed 5/8 ... 0.7813
# k=17 | Seed 6/8 ... 0.6781
# k=17 | Seed 7/8 ... 0.8124
# k=17 | Seed 8/8 ... 0.7336
# k =  17 → NOT FOUND (best: 0.8146 × 1/k)
# Testing k:  27%|████████▋                       | 16/59 [10:06<43:55, 61.30s/it]k=18 | Seed 1/8 ... new best: 0.7958 × (1/k)
# k=18 | Seed 2/8 ... 0.6753
# k=18 | Seed 3/8 ... 0.7230
# k=18 | Seed 4/8 ... 0.5884
# k=18 | Seed 5/8 ... 0.7842
# k=18 | Seed 6/8 ... 0.7329
# k=18 | Seed 7/8 ... 0.6979
# k=18 | Seed 8/8 ... 0.7509
# k =  18 → NOT FOUND (best: 0.7958 × 1/k)
# Testing k:  29%|█████████▏                      | 17/59 [11:17<44:56, 64.20s/it]k=19 | Seed 1/8 ... new best: 0.8069 × (1/k)
# k=19 | Seed 2/8 ... 0.7158
# k=19 | Seed 3/8 ... 0.7420
# k=19 | Seed 4/8 ... 0.6994
# k=19 | Seed 5/8 ... 0.6852
# k=19 | Seed 6/8 ... 0.7180
# k=19 | Seed 7/8 ... new best: 0.8087 × (1/k)
# k=19 | Seed 8/8 ... 0.6594
# k =  19 → NOT FOUND (best: 0.8087 × 1/k)
# Testing k:  31%|█████████▊                      | 18/59 [12:26<45:01, 65.88s/it]k=20 | Seed 1/8 ... new best: 0.8507 × (1/k)
# k=20 | Seed 2/8 ... new best: 0.8509 × (1/k)
# k=20 | Seed 3/8 ... 0.6202
# k=20 | Seed 4/8 ... 0.4718
# k=20 | Seed 5/8 ... 0.6590
# k=20 | Seed 6/8 ... 0.5148
# k=20 | Seed 7/8 ... 0.7369
# k=20 | Seed 8/8 ... 0.7348
# k =  20 → NOT FOUND (best: 0.8509 × 1/k)
# Testing k:  32%|██████████▎                     | 19/59 [13:37<44:56, 67.40s/it]k=21 | Seed 1/8 ... new best: 0.8840 × (1/k)
# k=21 | Seed 2/8 ... 0.6931
# k=21 | Seed 3/8 ... 0.7168
# k=21 | Seed 4/8 ... 0.6357
# k=21 | Seed 5/8 ... 0.6296
# k=21 | Seed 6/8 ... 0.6465
# k=21 | Seed 7/8 ... 0.6124
# k=21 | Seed 8/8 ... 0.6362
# k =  21 → NOT FOUND (best: 0.8840 × 1/k)
# Testing k:  34%|██████████▊                     | 20/59 [14:47<44:11, 67.98s/it]k=22 | Seed 1/8 ... new best: 0.8468 × (1/k)
# k=22 | Seed 2/8 ... 0.6717
# k=22 | Seed 3/8 ... 0.6140
# k=22 | Seed 4/8 ... 0.6393
# k=22 | Seed 5/8 ... 0.5720
# k=22 | Seed 6/8 ... 0.7062
# k=22 | Seed 7/8 ... 0.6155
# k=22 | Seed 8/8 ... 0.5837
# k =  22 → NOT FOUND (best: 0.8468 × 1/k)
# Testing k:  36%|███████████▍                    | 21/59 [15:59<43:51, 69.26s/it]k=23 | Seed 1/8 ... new best: 0.9080 × (1/k)
# k=23 | Seed 2/8 ... 0.6020
# k=23 | Seed 3/8 ... 0.7040
# k=23 | Seed 4/8 ... 0.5731
# k=23 | Seed 5/8 ... 0.5985
# k=23 | Seed 6/8 ... 0.6626
# k=23 | Seed 7/8 ... 0.6052
# k=23 | Seed 8/8 ... 0.5853
# k =  23 → NOT FOUND (best: 0.9080 × 1/k)
# Testing k:  37%|███████████▉                    | 22/59 [17:13<43:32, 70.62s/it]k=24 | Seed 1/8 ... new best: 0.8661 × (1/k)
# k=24 | Seed 2/8 ... 0.5507
# k=24 | Seed 3/8 ... 0.4875
# k=24 | Seed 4/8 ... 0.5063
# k=24 | Seed 5/8 ... 0.5670
# k=24 | Seed 6/8 ... 0.5368
# k=24 | Seed 7/8 ... 0.6674
# k=24 | Seed 8/8 ... 0.6156
# k =  24 → NOT FOUND (best: 0.8661 × 1/k)
# Testing k:  39%|████████████▍                   | 23/59 [18:27<43:05, 71.82s/it]k=25 | Seed 1/8 ... new best: 0.8302 × (1/k)
# k=25 | Seed 2/8 ... 0.6143
# k=25 | Seed 3/8 ... 0.6972
# k=25 | Seed 4/8 ... 0.6608
# k=25 | Seed 5/8 ... 0.5659
# k=25 | Seed 6/8 ... 0.6991
# k=25 | Seed 7/8 ... 0.7401
# k=25 | Seed 8/8 ... 0.6512
# k =  25 → NOT FOUND (best: 0.8302 × 1/k)
# Testing k:  41%|█████████████                   | 24/59 [19:43<42:39, 73.14s/it]k=26 | Seed 1/8 ... new best: 0.8659 × (1/k)
# k=26 | Seed 2/8 ... 0.3779
# k=26 | Seed 3/8 ... 0.6304
# k=26 | Seed 4/8 ... 0.4243
# k=26 | Seed 5/8 ... 0.6184
# k=26 | Seed 6/8 ... 0.5936
# k=26 | Seed 7/8 ... 0.4235
# k=26 | Seed 8/8 ... 0.5355
# k =  26 → NOT FOUND (best: 0.8659 × 1/k)
# Testing k:  42%|█████████████▌                  | 25/59 [20:59<41:54, 73.96s/it]k=27 | Seed 1/8 ... new best: 0.8409 × (1/k)
# k=27 | Seed 2/8 ... 0.3501
# k=27 | Seed 3/8 ... 0.5358
# k=27 | Seed 4/8 ... 0.3658
# k=27 | Seed 5/8 ... 0.5302
# k=27 | Seed 6/8 ... 0.4333
# k=27 | Seed 7/8 ... 0.5211
# k=27 | Seed 8/8 ... 0.4647
# k =  27 → NOT FOUND (best: 0.8409 × 1/k)
# Testing k:  44%|██████████████                  | 26/59 [22:16<41:11, 74.91s/it]k=28 | Seed 1/8 ... new best: 0.8509 × (1/k)
# k=28 | Seed 2/8 ... 0.4190
# k=28 | Seed 3/8 ... 0.6722
# k=28 | Seed 4/8 ... 0.3888
# k=28 | Seed 5/8 ... 0.3241
# k=28 | Seed 6/8 ... 0.5307
# k=28 | Seed 7/8 ... 0.4156
# k=28 | Seed 8/8 ... 0.3674
# k =  28 → NOT FOUND (best: 0.8509 × 1/k)
# Testing k:  46%|██████████████▋                 | 27/59 [23:35<40:29, 75.93s/it]k=29 | Seed 1/8 ... new best: 0.8700 × (1/k)
# k=29 | Seed 2/8 ... 0.5660
# k=29 | Seed 3/8 ... 0.4732
# k=29 | Seed 4/8 ... 0.5170
# k=29 | Seed 5/8 ... 0.5914
# k=29 | Seed 6/8 ... 0.4929
# k=29 | Seed 7/8 ... 0.4401
# k=29 | Seed 8/8 ... 0.3926
# k =  29 → NOT FOUND (best: 0.8700 × 1/k)
# Testing k:  47%|███████████████▏                | 28/59 [24:53<39:36, 76.67s/it]k=30 | Seed 1/8 ... new best: 0.8694 × (1/k)
# k=30 | Seed 2/8 ... 0.5971
# k=30 | Seed 3/8 ... 0.4758
# k=30 | Seed 4/8 ... 0.5434
# k=30 | Seed 5/8 ... 0.4936
# k=30 | Seed 6/8 ... 0.4255
# k=30 | Seed 7/8 ... 0.6702
# k=30 | Seed 8/8 ... 0.3853
# k =  30 → NOT FOUND (best: 0.8694 × 1/k)
# Testing k:  49%|███████████████▋                | 29/59 [26:11<38:31, 77.05s/it]k=31 | Seed 1/8 ... new best: 0.8660 × (1/k)
# k=31 | Seed 2/8 ... 0.5055
# k=31 | Seed 3/8 ... 0.5151
# k=31 | Seed 4/8 ... 0.3768
# k=31 | Seed 5/8 ... 0.4483
# k=31 | Seed 6/8 ... 0.4423
# k=31 | Seed 7/8 ... 0.5832
# k=31 | Seed 8/8 ... 0.5095
# k =  31 → NOT FOUND (best: 0.8660 × 1/k)
# Testing k:  51%|████████████████▎               | 30/59 [27:29<37:18, 77.18s/it]k=32 | Seed 1/8 ... new best: 0.8936 × (1/k)
# k=32 | Seed 2/8 ... 0.5062
# k=32 | Seed 3/8 ... 0.6370
# k=32 | Seed 4/8 ... 0.3855
# k=32 | Seed 5/8 ... 0.2469
# k=32 | Seed 6/8 ... 0.4931
# k=32 | Seed 7/8 ... 0.5257
# k=32 | Seed 8/8 ... 0.3239
# k =  32 → NOT FOUND (best: 0.8936 × 1/k)
# Testing k:  53%|████████████████▊               | 31/59 [28:48<36:22, 77.93s/it]k=33 | Seed 1/8 ... new best: 0.8983 × (1/k)
# k=33 | Seed 2/8 ... 0.5242
# k=33 | Seed 3/8 ... 0.3356
# k=33 | Seed 4/8 ... 0.5868
# k=33 | Seed 5/8 ... 0.5824
# k=33 | Seed 6/8 ... 0.5135
# k=33 | Seed 7/8 ... 0.4746
# k=33 | Seed 8/8 ... 0.3116
# k =  33 → NOT FOUND (best: 0.8983 × 1/k)
# Testing k:  54%|█████████████████▎              | 32/59 [30:07<35:10, 78.16s/it]k=34 | Seed 1/8 ... new best: 0.9387 × (1/k)
# k=34 | Seed 2/8 ... 0.6262
# k=34 | Seed 3/8 ... 0.3982
# k=34 | Seed 4/8 ... 0.4457
# k=34 | Seed 5/8 ... 0.5831
# k=34 | Seed 6/8 ... 0.5121
# k=34 | Seed 7/8 ... 0.4027
# k=34 | Seed 8/8 ... 0.5084
# k =  34 → NOT FOUND (best: 0.9387 × 1/k)
# Testing k:  56%|█████████████████▉              | 33/59 [31:27<34:07, 78.74s/it]k=35 | Seed 1/8 ... new best: 0.6198 × (1/k)
# k=35 | Seed 2/8 ... 0.4339
# k=35 | Seed 3/8 ... 0.5555
# k=35 | Seed 4/8 ... 0.4767
# k=35 | Seed 5/8 ... 0.3414
# k=35 | Seed 6/8 ... 0.5652
# k=35 | Seed 7/8 ... 0.3947
# k=35 | Seed 8/8 ... 0.4896
# k =  35 → NOT FOUND (best: 0.6198 × 1/k)
# Testing k:  58%|██████████████████▍             | 34/59 [32:48<33:05, 79.42s/it]k=36 | Seed 1/8 ... new best: 0.5882 × (1/k)
# k=36 | Seed 2/8 ... 0.4630
# k=36 | Seed 3/8 ... 0.4960
# k=36 | Seed 4/8 ... new best: 0.6854 × (1/k)
# k=36 | Seed 5/8 ... 0.3950
# k=36 | Seed 6/8 ... 0.5672
# k=36 | Seed 7/8 ... 0.3881
# k=36 | Seed 8/8 ... 0.3429
# k =  36 → NOT FOUND (best: 0.6854 × 1/k)
# Testing k:  59%|██████████████████▉             | 35/59 [34:10<32:00, 80.03s/it]k=37 | Seed 1/8 ... new best: 0.5604 × (1/k)
# k=37 | Seed 2/8 ... new best: 0.5827 × (1/k)
# k=37 | Seed 3/8 ... 0.4639
# k=37 | Seed 4/8 ... 0.3404
# k=37 | Seed 5/8 ... new best: 0.6077 × (1/k)
# k=37 | Seed 6/8 ... 0.3040
# k=37 | Seed 7/8 ... 0.2309
# k=37 | Seed 8/8 ... 0.3805
# k =  37 → NOT FOUND (best: 0.6077 × 1/k)
# Testing k:  61%|███████████████████▌            | 36/59 [35:31<30:51, 80.51s/it]k=38 | Seed 1/8 ... new best: 0.6298 × (1/k)
# k=38 | Seed 2/8 ... 0.4500
# k=38 | Seed 3/8 ... 0.4450
# k=38 | Seed 4/8 ... 0.4253
# k=38 | Seed 5/8 ... 0.3695
# k=38 | Seed 6/8 ... 0.2677
# k=38 | Seed 7/8 ... 0.4301
# k=38 | Seed 8/8 ... 0.3697
# k =  38 → NOT FOUND (best: 0.6298 × 1/k)
# Testing k:  63%|████████████████████            | 37/59 [36:53<29:41, 80.96s/it]k=39 | Seed 1/8 ... new best: 0.5913 × (1/k)
# k=39 | Seed 2/8 ... 0.3450
# k=39 | Seed 3/8 ... 0.2267
# k=39 | Seed 4/8 ... 0.4371
# k=39 | Seed 5/8 ... 0.3574
# k=39 | Seed 6/8 ... 0.5366
# k=39 | Seed 7/8 ... 0.3885
# k=39 | Seed 8/8 ... 0.4921
# k =  39 → NOT FOUND (best: 0.5913 × 1/k)
# Testing k:  64%|████████████████████▌           | 38/59 [38:16<28:30, 81.43s/it]k=40 | Seed 1/8 ... new best: 0.6283 × (1/k)
# k=40 | Seed 2/8 ... 0.3972
# k=40 | Seed 3/8 ... 0.3632
# k=40 | Seed 4/8 ... 0.3029
# k=40 | Seed 5/8 ... 0.4054
# k=40 | Seed 6/8 ... 0.4415
# k=40 | Seed 7/8 ... 0.1898
# k=40 | Seed 8/8 ... 0.4064
# k =  40 → NOT FOUND (best: 0.6283 × 1/k)
# Testing k:  66%|█████████████████████▏          | 39/59 [39:40<27:26, 82.31s/it]k=41 | Seed 1/8 ... new best: 0.6218 × (1/k)
# k=41 | Seed 2/8 ... 0.4345
# k=41 | Seed 3/8 ... 0.4039
# k=41 | Seed 4/8 ... 0.2527
# k=41 | Seed 5/8 ... 0.2222
# k=41 | Seed 6/8 ... 0.3710
# k=41 | Seed 7/8 ... 0.2333
# k=41 | Seed 8/8 ... 0.3429
# k =  41 → NOT FOUND (best: 0.6218 × 1/k)
# Testing k:  68%|█████████████████████▋          | 40/59 [41:06<26:22, 83.31s/it]k=42 | Seed 1/8 ... new best: 0.6631 × (1/k)
# k=42 | Seed 2/8 ... 0.2168
# k=42 | Seed 3/8 ... 0.3832
# k=42 | Seed 4/8 ... 0.2753
# k=42 | Seed 5/8 ... 0.4118
# k=42 | Seed 6/8 ... 0.4040
# k=42 | Seed 7/8 ... 0.2967
# k=42 | Seed 8/8 ... 0.4383
# k =  42 → NOT FOUND (best: 0.6631 × 1/k)
# Testing k:  69%|██████████████████████▏         | 41/59 [42:23<24:28, 81.56s/it]k=43 | Seed 1/8 ... new best: 0.6484 × (1/k)
# k=43 | Seed 2/8 ... 0.5139
# k=43 | Seed 3/8 ... 0.4160
# k=43 | Seed 4/8 ... 0.2543
# k=43 | Seed 5/8 ... 0.3688
# k=43 | Seed 6/8 ... 0.2885
# k=43 | Seed 7/8 ... 0.2894
# k=43 | Seed 8/8 ... 0.3125
# k =  43 → NOT FOUND (best: 0.6484 × 1/k)
# Testing k:  71%|██████████████████████▊         | 42/59 [43:43<22:58, 81.11s/it]k=44 | Seed 1/8 ... new best: 0.6871 × (1/k)
# k=44 | Seed 2/8 ... 0.2981
# k=44 | Seed 3/8 ... 0.4211
# k=44 | Seed 4/8 ... 0.2053
# k=44 | Seed 5/8 ... 0.3429
# k=44 | Seed 6/8 ... 0.3010
# k=44 | Seed 7/8 ... 0.2204
# k=44 | Seed 8/8 ... 0.3637
# k =  44 → NOT FOUND (best: 0.6871 × 1/k)
# Testing k:  73%|███████████████████████▎        | 43/59 [45:02<21:24, 80.26s/it]k=45 | Seed 1/8 ... new best: 0.7092 × (1/k)
# k=45 | Seed 2/8 ... 0.2399
# k=45 | Seed 3/8 ... 0.1842
# k=45 | Seed 4/8 ... 0.4055
# k=45 | Seed 5/8 ... 0.2079
# k=45 | Seed 6/8 ... 0.3953
# k=45 | Seed 7/8 ... 0.1957
# k=45 | Seed 8/8 ... 0.4637
# k =  45 → NOT FOUND (best: 0.7092 × 1/k)
# Testing k:  75%|███████████████████████▊        | 44/59 [46:20<19:55, 79.68s/it]k=46 | Seed 1/8 ... new best: 0.6948 × (1/k)
# k=46 | Seed 2/8 ... 0.2655
# k=46 | Seed 3/8 ... 0.3860
# k=46 | Seed 4/8 ... 0.3241
# k=46 | Seed 5/8 ... 0.1780
# k=46 | Seed 6/8 ... 0.1826
# k=46 | Seed 7/8 ... 0.3698
# k=46 | Seed 8/8 ... 0.2223
# k =  46 → NOT FOUND (best: 0.6948 × 1/k)
# Testing k:  76%|████████████████████████▍       | 45/59 [47:42<18:44, 80.32s/it]k=47 | Seed 1/8 ... new best: 0.7052 × (1/k)
# k=47 | Seed 2/8 ... 0.4484
# k=47 | Seed 3/8 ... 0.4061
# k=47 | Seed 4/8 ... 0.2187
# k=47 | Seed 5/8 ... 0.2795
# k=47 | Seed 6/8 ... 0.3522
# k=47 | Seed 7/8 ... 0.1723
# k=47 | Seed 8/8 ... 0.1743
# k =  47 → NOT FOUND (best: 0.7052 × 1/k)
# Testing k:  78%|████████████████████████▉       | 46/59 [49:02<17:24, 80.35s/it]k=48 | Seed 1/8 ... new best: 0.7033 × (1/k)
# k=48 | Seed 2/8 ... 0.4707
# k=48 | Seed 3/8 ... 0.3496
# k=48 | Seed 4/8 ... 0.1907
# k=48 | Seed 5/8 ... 0.3682
# k=48 | Seed 6/8 ... 0.4909
# k=48 | Seed 7/8 ... 0.1579
# k=48 | Seed 8/8 ... 0.1653
# k =  48 → NOT FOUND (best: 0.7033 × 1/k)
# Testing k:  80%|█████████████████████████▍      | 47/59 [50:23<16:05, 80.46s/it]k=49 | Seed 1/8 ... new best: 0.7173 × (1/k)
# k=49 | Seed 2/8 ... 0.5377
# k=49 | Seed 3/8 ... 0.1625
# k=49 | Seed 4/8 ... 0.1405
# k=49 | Seed 5/8 ... 0.3575
# k=49 | Seed 6/8 ... 0.2086
# k=49 | Seed 7/8 ... 0.3252
# k=49 | Seed 8/8 ... 0.1764
# k =  49 → NOT FOUND (best: 0.7173 × 1/k)
# Testing k:  81%|██████████████████████████      | 48/59 [51:49<15:05, 82.28s/it]k=50 | Seed 1/8 ... new best: 0.7442 × (1/k)
# k=50 | Seed 2/8 ... 0.1824
# k=50 | Seed 3/8 ... 0.4216
# k=50 | Seed 4/8 ... 0.3810
# k=50 | Seed 5/8 ... 0.1448
# k=50 | Seed 6/8 ... 0.2190
# k=50 | Seed 7/8 ... 0.3105
# k=50 | Seed 8/8 ... 0.3637
# k =  50 → NOT FOUND (best: 0.7442 × 1/k)
# Testing k:  83%|██████████████████████████▌     | 49/59 [53:12<13:43, 82.33s/it]k=51 | Seed 1/8 ... new best: 0.7293 × (1/k)
# k=51 | Seed 2/8 ... 0.4238
# k=51 | Seed 3/8 ... 0.1934
# k=51 | Seed 4/8 ... 0.1663
# k=51 | Seed 5/8 ... 0.1421
# k=51 | Seed 6/8 ... 0.2357
# k=51 | Seed 7/8 ... 0.2048
# k=51 | Seed 8/8 ... 0.1668
# k =  51 → NOT FOUND (best: 0.7293 × 1/k)
# Testing k:  85%|███████████████████████████     | 50/59 [54:34<12:20, 82.31s/it]k=52 | Seed 1/8 ... new best: 0.7479 × (1/k)
# k=52 | Seed 2/8 ... 0.4011
# k=52 | Seed 3/8 ... 0.1624
# k=52 | Seed 4/8 ... 0.2927
# k=52 | Seed 5/8 ... 0.2424
# k=52 | Seed 6/8 ... 0.3814
# k=52 | Seed 7/8 ... 0.1714
# k=52 | Seed 8/8 ... 0.2510
# k =  52 → NOT FOUND (best: 0.7479 × 1/k)
# Testing k:  86%|███████████████████████████▋    | 51/59 [55:55<10:56, 82.02s/it]k=53 | Seed 1/8 ... new best: 0.7644 × (1/k)
# k=53 | Seed 2/8 ... 0.1990
# k=53 | Seed 3/8 ... 0.2368
# k=53 | Seed 4/8 ... 0.3675
# k=53 | Seed 5/8 ... 0.3786
# k=53 | Seed 6/8 ... 0.2647
# k=53 | Seed 7/8 ... 0.2436
# k=53 | Seed 8/8 ... 0.2498
# k =  53 → NOT FOUND (best: 0.7644 × 1/k)
# Testing k:  88%|████████████████████████████▏   | 52/59 [57:17<09:33, 81.97s/it]k=54 | Seed 1/8 ... new best: 0.7686 × (1/k)
# k=54 | Seed 2/8 ... 0.2498
# k=54 | Seed 3/8 ... 0.2467
# k=54 | Seed 4/8 ... 0.4208
# k=54 | Seed 5/8 ... 0.3000
# k=54 | Seed 6/8 ... 0.2973
# k=54 | Seed 7/8 ... 0.1888
# k=54 | Seed 8/8 ... 0.1564
# k =  54 → NOT FOUND (best: 0.7686 × 1/k)
# Testing k:  90%|████████████████████████████▋   | 53/59 [58:41<08:14, 82.46s/it]k=55 | Seed 1/8 ... new best: 0.7863 × (1/k)
# k=55 | Seed 2/8 ... 0.2321
# k=55 | Seed 3/8 ... 0.4758
# k=55 | Seed 4/8 ... 0.2900
# k=55 | Seed 5/8 ... 0.3081
# k=55 | Seed 6/8 ... 0.2794
# k=55 | Seed 7/8 ... 0.1447
# k=55 | Seed 8/8 ... 0.3400
# k =  55 → NOT FOUND (best: 0.7863 × 1/k)
# Testing k:  92%|███████████████████████████▍  | 54/59 [1:00:06<06:56, 83.30s/it]k=56 | Seed 1/8 ... new best: 0.7462 × (1/k)
# k=56 | Seed 2/8 ... 0.1710
# k=56 | Seed 3/8 ... 0.1230
# k=56 | Seed 4/8 ... 0.2848
# k=56 | Seed 5/8 ... 0.2478
# k=56 | Seed 6/8 ... 0.3257
# k=56 | Seed 7/8 ... 0.2077
# k=56 | Seed 8/8 ... 0.4169
# k =  56 → NOT FOUND (best: 0.7462 × 1/k)
# Testing k:  93%|███████████████████████████▉  | 55/59 [1:01:32<05:36, 84.14s/it]k=57 | Seed 1/8 ... new best: 0.7353 × (1/k)
# k=57 | Seed 2/8 ... 0.2501
# k=57 | Seed 3/8 ... 0.2615
# k=57 | Seed 4/8 ... 0.2488
# k=57 | Seed 5/8 ... 0.1582
# k=57 | Seed 6/8 ... 0.1947
# k=57 | Seed 7/8 ... 0.1359
# k=57 | Seed 8/8 ... 0.3217
# k =  57 → NOT FOUND (best: 0.7353 × 1/k)
# Testing k:  95%|████████████████████████████▍ | 56/59 [1:02:58<04:13, 84.63s/it]k=58 | Seed 1/8 ... new best: 0.7569 × (1/k)
# k=58 | Seed 2/8 ... 0.3509
# k=58 | Seed 3/8 ... 0.2059
# k=58 | Seed 4/8 ... 0.1422
# k=58 | Seed 5/8 ... 0.2214
# k=58 | Seed 6/8 ... 0.2103
# k=58 | Seed 7/8 ... 0.1685
# k=58 | Seed 8/8 ... 0.4567
# k =  58 → NOT FOUND (best: 0.7569 × 1/k)
# Testing k:  97%|████████████████████████████▉ | 57/59 [1:04:25<02:50, 85.37s/it]k=59 | Seed 1/8 ... new best: 0.7386 × (1/k)
# k=59 | Seed 2/8 ... 0.1497
# k=59 | Seed 3/8 ... 0.4511
# k=59 | Seed 4/8 ... 0.2863
# k=59 | Seed 5/8 ... 0.2686
# k=59 | Seed 6/8 ... 0.3112
# k=59 | Seed 7/8 ... 0.1945
# k=59 | Seed 8/8 ... 0.1693
# k =  59 → NOT FOUND (best: 0.7386 × 1/k)
# Testing k:  98%|█████████████████████████████▍| 58/59 [1:05:53<01:26, 86.03s/it]k=60 | Seed 1/8 ... new best: 0.6959 × (1/k)
# k=60 | Seed 2/8 ... 0.1300
# k=60 | Seed 3/8 ... 0.2552
# k=60 | Seed 4/8 ... 0.1859
# k=60 | Seed 5/8 ... 0.1800
# k=60 | Seed 6/8 ... 0.1408
# k=60 | Seed 7/8 ... 0.1556
# k=60 | Seed 8/8 ... 0.4265
# k =  60 → NOT FOUND (best: 0.6959 × 1/k)
# Testing k: 100%|██████████████████████████████| 59/59 [1:07:21<00:00, 68.50s/it]

# ══════════════════════════════════════════════════════════════════════
# FINAL SUMMARY - PURE LONELY RUNNER TEST
# ══════════════════════════════════════════════════════════════════════
# Tested up to k = 60
# Found satisfying t (loneliness ≥ 1/k) for all k ≤ 60? → NO
# 2026-01-16 05:46:22.880 python[66075:128922918] The class 'NSSavePanel' overrides the method identifier.  This method is implemented by class 'NSWindow'
# Plot saved: pure_lonely_runner_gap_ratio.png
# If gap stays ≥ 1.0 up to high k → conjecture supported
# If gap falls significantly below 1.0 → conjecture challenged
# (base) brendanlynch@Brendans-Laptop lonelyRunner % 
