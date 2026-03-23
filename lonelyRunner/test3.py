import numpy as np
from scipy.optimize import minimize
import time
import csv
import os

# ─── UFT-F SACRED CONSTANTS ────────────────────────────────────────────────
LAMBDA_0 = 15.045233122          # Modularity Constant
C_UFT_F  = 0.003119337           # Spectral Hard-Deck / Kolmogorov grain
OMEGA_U  = 0.0002073045          # Hopf Torsion (time's arrow)
BASE_24_RESIDUES = np.array([1, 5, 7, 11, 13, 17, 19, 23], dtype=float)

# ─── HYPERPARAMETERS ────────────────────────────────────────────────────────
MAX_K_TO_TRY         = 320       # Theoretical target
OPTIMIZATION_EFFORT  = 4
TIME_SAMPLES_PER_EVAL = 250
RANDOM_RESTARTS_BASE = 8

CSV_FILE = "lonely_runner_uftf_results.csv"

# Initialize CSV if it doesn't exist
if not os.path.exists(CSV_FILE):
    with open(CSV_FILE, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["k", "min_L1_mass", "status", "success", "grain_margin"])

print("="*90)
print("UFT-F LONELY RUNNER MAXIMUM STRESS PROTOCOL - TARGET k=320 WITH CSV LOGGING")
print("Results saved to:", CSV_FILE)
print("="*90)

def uftf_informational_mass(positions, k):
    pos = np.sort(positions % 1.0)
    diffs = np.diff(pos)
    distances = np.append(diffs, 1.0 - (pos[-1] - pos[0]))

    gap_threshold = 1.0 / k
    mass = 0.0

    for d in distances:
        if d < gap_threshold:
            diff_to_grain = d - C_UFT_F
            if diff_to_grain <= 1e-9:
                return 1e18
            exponent = np.clip((gap_threshold - d) / diff_to_grain, -700, 700)
            mass += np.exp(exponent) * (1 + OMEGA_U)

    return mass


def objective(speeds, k):
    min_mass = 1e20
    for t in np.linspace(0.001, 30.0, TIME_SAMPLES_PER_EVAL):
        mass = uftf_informational_mass(speeds * t, k)
        min_mass = min(min_mass, mass)
    return min_mass


def find_best_configuration(k):
    best_mass = 1e20
    restarts = RANDOM_RESTARTS_BASE + max(0, (k - 20) // 10)

    n_res = min(k, len(BASE_24_RESIDUES))
    initial = BASE_24_RESIDUES[:n_res].copy()
    if n_res < k:
        extra = np.random.uniform(24, 120, k - n_res)
        initial = np.concatenate([initial, extra])
    initial += np.random.normal(0, 0.4, k)

    if k > 17:
        print(f"  → Redundancy cliff zone (k > 17)")
    if k > 100:
        print(f"  → High k regime (k > 100) — grain proximity warning")

    for r in range(restarts):
        print(f"  Restart {r+1}/{restarts} ... ", end="", flush=True)
        res = minimize(
            objective, initial, args=(k,),
            method='Nelder-Mead',
            options={'maxiter': 1500 * min(k, 40), 'fatol': 1e-6, 'disp': False}
        )
        candidate_mass = res.fun
        if candidate_mass < best_mass:
            best_mass = candidate_mass
            print(f"new best: {best_mass:12.4f}")
        else:
            print(f"{candidate_mass:12.4f}")
        initial = res.x + np.random.normal(0, 1.0, k)

    return best_mass < LAMBDA_0, best_mass, res.x


def quick_high_k_verify(k):
    print(f"\nQuick quasi-uniform verifier: k={k}")
    phi = (1 + np.sqrt(5)) / 2
    speeds = np.arange(k) * (phi - 1)

    min_mass = 1e20
    for t in np.linspace(0.001, 60.0, 600):
        mass = uftf_informational_mass(speeds * t, k)
        min_mass = min(min_mass, mass)

    print(f"  Best L¹ (quasi-uniform): {min_mass:12.4e}")
    return min_mass


# ─── MAIN PROTOCOL ──────────────────────────────────────────────────────────
start_time = time.time()

print(f"Theoretical Lynch Limit: k_max ≈ {1/C_UFT_F:.2f} → termination at k≥321\n")

for k in range(2, MAX_K_TO_TRY + 1):
    print(f"\n┌── k = {k:3d} " + "─"*70)
    
    if k <= 50:
        success, min_mass, _ = find_best_configuration(k)
    else:
        print("  → Switching to quasi-uniform verifier (full search intractable)")
        min_mass = quick_high_k_verify(k)
        success = min_mass < LAMBDA_0

    margin = (1.0 / k) - C_UFT_F
    status = "STABLE" if success else "DANGER ZONE"
    if min_mass > 1e15 or margin <= 0:
        status = "MANIFOLD RUPTURE"

    print(f"│   Minimal L¹ mass: {min_mass:12.4e}")
    print(f"│   Status: {status}")
    print(f"│   Grain margin: {margin:.9f}")
    print(f"└{'─'*80}")

    # Save to CSV
    with open(CSV_FILE, 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([k, f"{min_mass:.4e}", status, int(success), f"{margin:.9f}"])

    if min_mass > LAMBDA_0 * 50 and k > 30:
        print("\n!!! PRACTICAL RUPTURE THRESHOLD REACHED !!!")
        break

# Final summary
print("\n" + "═"*90)
print("FINAL SUMMARY & TERMINATION STATEMENT")
print("═"*90)
print(f"Last tested k: {k}")
print(f"Last mass: {min_mass:.4e}")
print(f"\nAt k=321: δ = 1/321 ≈ {1/321:.7f} < c_UFT-F = {C_UFT_F:.7f}")
print("→ Required gap falls below spectral grain → inevitable manifold rupture")
print("Lonely Runner Conjecture topologically terminated at k ≥ 321 in UFT-F framework")
print(f"\nResults saved to: {CSV_FILE}")
print(f"Total runtime: {(time.time() - start_time)/60:.1f} minutes")

# (base) brendanlynch@Brendans-Laptop lonelyRunner % python test3.py
# ==========================================================================================
# UFT-F LONELY RUNNER MAXIMUM STRESS PROTOCOL - TARGET k=320 WITH CSV LOGGING
# Results saved to: lonely_runner_uftf_results.csv
# ==========================================================================================
# Theoretical Lynch Limit: k_max ≈ 320.58 → termination at k≥321


# ┌── k =   2 ──────────────────────────────────────────────────────────────────────
#   Restart 1/8 ... new best:       1.0002
#   Restart 2/8 ...       1.0002
#   Restart 3/8 ...       1.0002
#   Restart 4/8 ... new best:       1.0002
#   Restart 5/8 ...       1.0002
#   Restart 6/8 ...       1.0002
#   Restart 7/8 ...       1.0002
#   Restart 8/8 ...       1.0002
# │   Minimal L¹ mass:   1.0002e+00
# │   Status: STABLE
# │   Grain margin: 0.496880663
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k =   3 ──────────────────────────────────────────────────────────────────────
#   Restart 1/8 ... new best:       1.0002
#   Restart 2/8 ... new best:       1.0002
#   Restart 3/8 ...       1.0002
#   Restart 4/8 ...       1.0002
#   Restart 5/8 ...       1.0002
#   Restart 6/8 ... new best:       1.0002
#   Restart 7/8 ...       1.0002
#   Restart 8/8 ...       1.0002
# │   Minimal L¹ mass:   1.0002e+00
# │   Status: STABLE
# │   Grain margin: 0.330213996
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k =   4 ──────────────────────────────────────────────────────────────────────
#   Restart 1/8 ... new best:       1.0007
#   Restart 2/8 ...       1.0035
#   Restart 3/8 ... new best:       1.0002
#   Restart 4/8 ...       1.0002
#   Restart 5/8 ...       1.0002
#   Restart 6/8 ...       1.0002
#   Restart 7/8 ...       1.0003
#   Restart 8/8 ... new best:       1.0002
# │   Minimal L¹ mass:   1.0002e+00
# │   Status: STABLE
# │   Grain margin: 0.246880663
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k =   5 ──────────────────────────────────────────────────────────────────────
#   Restart 1/8 ... new best:       1.0266
#   Restart 2/8 ...       1.0332
#   Restart 3/8 ... new best:       1.0055
#   Restart 4/8 ...       1.0876
#   Restart 5/8 ...       1.1258
#   Restart 6/8 ...       1.0611
#   Restart 7/8 ...       1.0829
#   Restart 8/8 ...       1.0064
# │   Minimal L¹ mass:   1.0055e+00
# │   Status: STABLE
# │   Grain margin: 0.196880663
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k =   6 ──────────────────────────────────────────────────────────────────────
#   Restart 1/8 ... new best:       1.1143
#   Restart 2/8 ... new best:       1.0315
#   Restart 3/8 ...       1.1178
#   Restart 4/8 ...       1.1013
#   Restart 5/8 ...       1.1181
#   Restart 6/8 ...       1.1411
#   Restart 7/8 ...       1.4625
#   Restart 8/8 ...       1.0652
# │   Minimal L¹ mass:   1.0315e+00
# │   Status: STABLE
# │   Grain margin: 0.163547330
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k =   7 ──────────────────────────────────────────────────────────────────────
#   Restart 1/8 ... new best:       1.0352
#   Restart 2/8 ...       2.2848
#   Restart 3/8 ...       1.0943
#   Restart 4/8 ...       2.1627
#   Restart 5/8 ...       1.2578
#   Restart 6/8 ...       2.2843
#   Restart 7/8 ...       2.0385
#   Restart 8/8 ...       1.1579
# │   Minimal L¹ mass:   1.0352e+00
# │   Status: STABLE
# │   Grain margin: 0.139737806
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k =   8 ──────────────────────────────────────────────────────────────────────
#   Restart 1/8 ... new best:       1.6388
#   Restart 2/8 ... new best:       1.0535
#   Restart 3/8 ...       2.7413
#   Restart 4/8 ...       1.4378
#   Restart 5/8 ...       2.4185
#   Restart 6/8 ...       2.9139
#   Restart 7/8 ...       1.2822
#   Restart 8/8 ...       2.1738
# │   Minimal L¹ mass:   1.0535e+00
# │   Status: STABLE
# │   Grain margin: 0.121880663
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k =   9 ──────────────────────────────────────────────────────────────────────
#   Restart 1/8 ... new best:       1.3256
#   Restart 2/8 ...       2.1926
#   Restart 3/8 ... new best:       1.1499
#   Restart 4/8 ...       2.8636
#   Restart 5/8 ...       3.0806
#   Restart 6/8 ...       2.3135
#   Restart 7/8 ...       1.3515
#   Restart 8/8 ...       2.4110
# │   Minimal L¹ mass:   1.1499e+00
# │   Status: STABLE
# │   Grain margin: 0.107991774
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k =  10 ──────────────────────────────────────────────────────────────────────
#   Restart 1/8 ... new best:       2.5258
#   Restart 2/8 ...       4.1144
#   Restart 3/8 ...       2.7270
#   Restart 4/8 ...       2.9413
#   Restart 5/8 ...       5.9416
#   Restart 6/8 ...       3.6526
#   Restart 7/8 ...       6.1133
#   Restart 8/8 ...       2.7787
# │   Minimal L¹ mass:   2.5258e+00
# │   Status: STABLE
# │   Grain margin: 0.096880663
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k =  11 ──────────────────────────────────────────────────────────────────────
#   Restart 1/8 ... new best:       3.9171
#   Restart 2/8 ... new best:       3.2335
#   Restart 3/8 ...       5.1106
#   Restart 4/8 ...       6.7009
#   Restart 5/8 ... new best:       2.5633
#   Restart 6/8 ...       4.8101
#   Restart 7/8 ...       2.6570
#   Restart 8/8 ...       2.5873
# │   Minimal L¹ mass:   2.5633e+00
# │   Status: STABLE
# │   Grain margin: 0.087789754
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k =  12 ──────────────────────────────────────────────────────────────────────
#   Restart 1/8 ... new best:       5.5353
#   Restart 2/8 ... new best:       3.6639
#   Restart 3/8 ...       5.5264
#   Restart 4/8 ...       7.3985
#   Restart 5/8 ...       4.9020
#   Restart 6/8 ...       6.7288
#   Restart 7/8 ...       6.9232
#   Restart 8/8 ...       4.9235
# │   Minimal L¹ mass:   3.6639e+00
# │   Status: STABLE
# │   Grain margin: 0.080213996
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k =  13 ──────────────────────────────────────────────────────────────────────
#   Restart 1/8 ... new best:       6.1932
#   Restart 2/8 ...       6.9033
#   Restart 3/8 ...       7.0720
#   Restart 4/8 ... new best:       5.5448
#   Restart 5/8 ... new best:       5.1422
#   Restart 6/8 ...       5.9409
#   Restart 7/8 ...       6.1927
#   Restart 8/8 ...       6.5335
# │   Minimal L¹ mass:   5.1422e+00
# │   Status: STABLE
# │   Grain margin: 0.073803740
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k =  14 ──────────────────────────────────────────────────────────────────────
#   Restart 1/8 ... new best:       7.1799
#   Restart 2/8 ...      10.2797
#   Restart 3/8 ... new best:       5.6216
#   Restart 4/8 ... new best:       5.1843
#   Restart 5/8 ...       7.1714
#   Restart 6/8 ...       9.8876
#   Restart 7/8 ...       7.3496
#   Restart 8/8 ...       6.6299
# │   Minimal L¹ mass:   5.1843e+00
# │   Status: STABLE
# │   Grain margin: 0.068309234
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k =  15 ──────────────────────────────────────────────────────────────────────
#   Restart 1/8 ... new best:      10.4163
#   Restart 2/8 ... new best:       6.4375
#   Restart 3/8 ...       8.5705
#   Restart 4/8 ...       8.7533
#   Restart 5/8 ...       7.6153
#   Restart 6/8 ...       6.5171
#   Restart 7/8 ... new best:       5.7236
#   Restart 8/8 ...       7.7002
# │   Minimal L¹ mass:   5.7236e+00
# │   Status: STABLE
# │   Grain margin: 0.063547330
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k =  16 ──────────────────────────────────────────────────────────────────────
#   Restart 1/8 ... new best:       8.0242
#   Restart 2/8 ...       8.5375
#   Restart 3/8 ...       8.1076
#   Restart 4/8 ...      10.8039
#   Restart 5/8 ... new best:       6.7312
#   Restart 6/8 ...       9.4106
#   Restart 7/8 ...       8.4806
#   Restart 8/8 ...       7.5596
# │   Minimal L¹ mass:   6.7312e+00
# │   Status: STABLE
# │   Grain margin: 0.059380663
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k =  17 ──────────────────────────────────────────────────────────────────────
#   Restart 1/8 ... new best:       9.5993
#   Restart 2/8 ...      10.0819
#   Restart 3/8 ... new best:       9.2421
#   Restart 4/8 ... new best:       6.5475
#   Restart 5/8 ...       7.9900
#   Restart 6/8 ...       6.5993
#   Restart 7/8 ...       9.7822
#   Restart 8/8 ...      11.1725
# │   Minimal L¹ mass:   6.5475e+00
# │   Status: STABLE
# │   Grain margin: 0.055704192
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k =  18 ──────────────────────────────────────────────────────────────────────
#   → Redundancy cliff zone (k > 17)
#   Restart 1/8 ... new best:      13.5615
#   Restart 2/8 ... new best:       9.3107
#   Restart 3/8 ...      14.2705
#   Restart 4/8 ...      13.9197
#   Restart 5/8 ...      13.8965
#   Restart 6/8 ...      10.0307
#   Restart 7/8 ... new best:       8.9291
#   Restart 8/8 ...      10.9292
# │   Minimal L¹ mass:   8.9291e+00
# │   Status: STABLE
# │   Grain margin: 0.052436219
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k =  19 ──────────────────────────────────────────────────────────────────────
#   → Redundancy cliff zone (k > 17)
#   Restart 1/8 ... new best:      14.3915
#   Restart 2/8 ... new best:       8.5726
#   Restart 3/8 ... new best:       8.3542
#   Restart 4/8 ...      14.3376
#   Restart 5/8 ...      12.2257
#   Restart 6/8 ...      12.6363
#   Restart 7/8 ...      10.3769
#   Restart 8/8 ...      11.2639
# │   Minimal L¹ mass:   8.3542e+00
# │   Status: STABLE
# │   Grain margin: 0.049512242
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k =  20 ──────────────────────────────────────────────────────────────────────
#   → Redundancy cliff zone (k > 17)
#   Restart 1/8 ... new best:      14.6853
#   Restart 2/8 ...      19.2074
#   Restart 3/8 ... new best:      12.3829
#   Restart 4/8 ... new best:       7.3048
#   Restart 5/8 ...      18.1474
#   Restart 6/8 ...      12.1340
#   Restart 7/8 ...      16.6127
#   Restart 8/8 ...      13.1036
# │   Minimal L¹ mass:   7.3048e+00
# │   Status: STABLE
# │   Grain margin: 0.046880663
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k =  21 ──────────────────────────────────────────────────────────────────────
#   → Redundancy cliff zone (k > 17)
#   Restart 1/8 ... new best:      13.8019
#   Restart 2/8 ...      14.6485
#   Restart 3/8 ... new best:      11.4129
#   Restart 4/8 ...      17.4840
#   Restart 5/8 ... new best:      10.4185
#   Restart 6/8 ...      10.7986
#   Restart 7/8 ...      14.6608
#   Restart 8/8 ...      13.3374
# │   Minimal L¹ mass:   1.0419e+01
# │   Status: STABLE
# │   Grain margin: 0.044499711
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k =  22 ──────────────────────────────────────────────────────────────────────
#   → Redundancy cliff zone (k > 17)
#   Restart 1/8 ... new best:      12.8906
#   Restart 2/8 ...      13.7838
#   Restart 3/8 ...      13.4968
#   Restart 4/8 ...      16.5205
#   Restart 5/8 ...      13.6027
#   Restart 6/8 ...      16.7840
#   Restart 7/8 ...      15.6278
#   Restart 8/8 ...      13.5253
# │   Minimal L¹ mass:   1.2891e+01
# │   Status: STABLE
# │   Grain margin: 0.042335208
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k =  23 ──────────────────────────────────────────────────────────────────────
#   → Redundancy cliff zone (k > 17)
#   Restart 1/8 ... new best:      17.6767
#   Restart 2/8 ... new best:      13.8028
#   Restart 3/8 ...      15.2203
#   Restart 4/8 ... new best:      10.5041
#   Restart 5/8 ...      12.7423
#   Restart 6/8 ...      16.2335
#   Restart 7/8 ...      15.4234
#   Restart 8/8 ...      18.3355
# │   Minimal L¹ mass:   1.0504e+01
# │   Status: STABLE
# │   Grain margin: 0.040358924
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k =  24 ──────────────────────────────────────────────────────────────────────
#   → Redundancy cliff zone (k > 17)
#   Restart 1/8 ... new best:      17.0445
#   Restart 2/8 ...      19.2942
#   Restart 3/8 ...      21.2072
#   Restart 4/8 ...      19.9273
#   Restart 5/8 ...      24.3074
#   Restart 6/8 ...      18.5472
#   Restart 7/8 ... new best:      13.1787
#   Restart 8/8 ... new best:      11.4774
# │   Minimal L¹ mass:   1.1477e+01
# │   Status: STABLE
# │   Grain margin: 0.038547330
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k =  25 ──────────────────────────────────────────────────────────────────────
#   → Redundancy cliff zone (k > 17)
#   Restart 1/8 ... new best:      20.5053
#   Restart 2/8 ...      22.0879
#   Restart 3/8 ...      21.2280
#   Restart 4/8 ... new best:      20.1114
#   Restart 5/8 ...      23.8152
#   Restart 6/8 ... new best:      20.0821
#   Restart 7/8 ... new best:      16.9931
#   Restart 8/8 ...      19.2892
# │   Minimal L¹ mass:   1.6993e+01
# │   Status: DANGER ZONE
# │   Grain margin: 0.036880663
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k =  26 ──────────────────────────────────────────────────────────────────────
#   → Redundancy cliff zone (k > 17)
#   Restart 1/8 ... new best:      22.1616
#   Restart 2/8 ... new best:      17.1163
#   Restart 3/8 ...      17.5477
#   Restart 4/8 ...      19.5369
#   Restart 5/8 ...      21.1881
#   Restart 6/8 ... new best:      14.3712
#   Restart 7/8 ...      18.4927
#   Restart 8/8 ...      26.6903
# │   Minimal L¹ mass:   1.4371e+01
# │   Status: STABLE
# │   Grain margin: 0.035342201
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k =  27 ──────────────────────────────────────────────────────────────────────
#   → Redundancy cliff zone (k > 17)
#   Restart 1/8 ... new best:      19.6975
#   Restart 2/8 ...      25.2683
#   Restart 3/8 ... new best:      19.3485
#   Restart 4/8 ... new best:      17.4924
#   Restart 5/8 ...      25.1779
#   Restart 6/8 ...      22.9482
#   Restart 7/8 ...      26.5166
#   Restart 8/8 ... new best:      16.1586
# │   Minimal L¹ mass:   1.6159e+01
# │   Status: DANGER ZONE
# │   Grain margin: 0.033917700
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k =  28 ──────────────────────────────────────────────────────────────────────
#   → Redundancy cliff zone (k > 17)
#   Restart 1/8 ... new best:      23.9075
#   Restart 2/8 ... new best:      22.7245
#   Restart 3/8 ...      23.1796
#   Restart 4/8 ... new best:      21.1124
#   Restart 5/8 ...      25.9151
#   Restart 6/8 ... new best:      19.6356
#   Restart 7/8 ...      22.3647
#   Restart 8/8 ...      21.1913
# │   Minimal L¹ mass:   1.9636e+01
# │   Status: DANGER ZONE
# │   Grain margin: 0.032594949
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k =  29 ──────────────────────────────────────────────────────────────────────
#   → Redundancy cliff zone (k > 17)
#   Restart 1/8 ... new best:      24.4867
#   Restart 2/8 ...      27.3447
#   Restart 3/8 ... new best:      21.7610
#   Restart 4/8 ...      27.8138
#   Restart 5/8 ...      24.3867
#   Restart 6/8 ... new best:      20.0757
#   Restart 7/8 ...      21.8951
#   Restart 8/8 ...      26.9881
# │   Minimal L¹ mass:   2.0076e+01
# │   Status: DANGER ZONE
# │   Grain margin: 0.031363422
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k =  30 ──────────────────────────────────────────────────────────────────────
#   → Redundancy cliff zone (k > 17)
#   Restart 1/9 ... new best:      24.1560
#   Restart 2/9 ... new best:      22.2146
#   Restart 3/9 ...      25.5743
#   Restart 4/9 ... new best:      20.3771
#   Restart 5/9 ...      20.9058
#   Restart 6/9 ...      34.4457
#   Restart 7/9 ...      26.9997
#   Restart 8/9 ...      22.5407
#   Restart 9/9 ...      20.7501
# │   Minimal L¹ mass:   2.0377e+01
# │   Status: DANGER ZONE
# │   Grain margin: 0.030213996
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k =  31 ──────────────────────────────────────────────────────────────────────
#   → Redundancy cliff zone (k > 17)
#   Restart 1/9 ... new best:      29.6009
#   Restart 2/9 ... new best:      19.4490
#   Restart 3/9 ...      28.9315
#   Restart 4/9 ...      19.8129
#   Restart 5/9 ...      30.9561
#   Restart 6/9 ...      35.3002
#   Restart 7/9 ...      23.8006
#   Restart 8/9 ...      29.1817
#   Restart 9/9 ...      31.7807
# │   Minimal L¹ mass:   1.9449e+01
# │   Status: DANGER ZONE
# │   Grain margin: 0.029138728
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k =  32 ──────────────────────────────────────────────────────────────────────
#   → Redundancy cliff zone (k > 17)
#   Restart 1/9 ... new best:      23.0279
#   Restart 2/9 ...      30.9692
#   Restart 3/9 ...      37.6339
#   Restart 4/9 ... new best:      19.9443
#   Restart 5/9 ...      48.9409
#   Restart 6/9 ...      31.7874
#   Restart 7/9 ...      22.3133
#   Restart 8/9 ...      24.8642
#   Restart 9/9 ...      26.8687
# │   Minimal L¹ mass:   1.9944e+01
# │   Status: DANGER ZONE
# │   Grain margin: 0.028130663
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k =  33 ──────────────────────────────────────────────────────────────────────
#   → Redundancy cliff zone (k > 17)
#   Restart 1/9 ... new best:      33.8143
#   Restart 2/9 ... new best:      23.7476
#   Restart 3/9 ...      28.2882
#   Restart 4/9 ...      31.5815
#   Restart 5/9 ...      37.1470
#   Restart 6/9 ...      40.8867
#   Restart 7/9 ...      29.2535
#   Restart 8/9 ...      31.1345
#   Restart 9/9 ...      25.6912
# │   Minimal L¹ mass:   2.3748e+01
# │   Status: DANGER ZONE
# │   Grain margin: 0.027183693
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k =  34 ──────────────────────────────────────────────────────────────────────
#   → Redundancy cliff zone (k > 17)
#   Restart 1/9 ... new best:      24.6918
#   Restart 2/9 ...      27.7982
#   Restart 3/9 ...      29.5621
#   Restart 4/9 ...      25.4055
#   Restart 5/9 ... new best:      23.9410
#   Restart 6/9 ...      28.6842
#   Restart 7/9 ...      40.1079
#   Restart 8/9 ... new best:      20.1620
#   Restart 9/9 ...      39.4431
# │   Minimal L¹ mass:   2.0162e+01
# │   Status: DANGER ZONE
# │   Grain margin: 0.026292428
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k =  35 ──────────────────────────────────────────────────────────────────────
#   → Redundancy cliff zone (k > 17)
#   Restart 1/9 ... new best:      41.5731
#   Restart 2/9 ... new best:      37.6658
#   Restart 3/9 ... new best:      28.5148
#   Restart 4/9 ...      28.9763
#   Restart 5/9 ... new best:      27.7906
#   Restart 6/9 ...      33.3016
#   Restart 7/9 ...      48.0019
#   Restart 8/9 ... new best:      27.7782
#   Restart 9/9 ... new best:      21.7846
# │   Minimal L¹ mass:   2.1785e+01
# │   Status: DANGER ZONE
# │   Grain margin: 0.025452092
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k =  36 ──────────────────────────────────────────────────────────────────────
#   → Redundancy cliff zone (k > 17)
#   Restart 1/9 ... new best:      28.6166
#   Restart 2/9 ...      33.1270
#   Restart 3/9 ...      38.0747
#   Restart 4/9 ... new best:      28.1868
#   Restart 5/9 ... new best:      27.0099
#   Restart 6/9 ...      30.0428
#   Restart 7/9 ...      32.1316
#   Restart 8/9 ...      27.3538
#   Restart 9/9 ...      28.3137
# │   Minimal L¹ mass:   2.7010e+01
# │   Status: DANGER ZONE
# │   Grain margin: 0.024658441
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k =  37 ──────────────────────────────────────────────────────────────────────
#   → Redundancy cliff zone (k > 17)
#   Restart 1/9 ... new best:      47.4934
#   Restart 2/9 ... new best:      27.1501
#   Restart 3/9 ...      39.0693
#   Restart 4/9 ...      42.7878
#   Restart 5/9 ...      29.8462
#   Restart 6/9 ...      48.8409
#   Restart 7/9 ...      38.7161
#   Restart 8/9 ...      31.4261
#   Restart 9/9 ...      34.1769
# │   Minimal L¹ mass:   2.7150e+01
# │   Status: DANGER ZONE
# │   Grain margin: 0.023907690
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k =  38 ──────────────────────────────────────────────────────────────────────
#   → Redundancy cliff zone (k > 17)
#   Restart 1/9 ... new best:      29.8978
#   Restart 2/9 ...      35.0349
#   Restart 3/9 ...      31.2139
#   Restart 4/9 ...      37.8083
#   Restart 5/9 ...      36.0013
#   Restart 6/9 ...      34.3289
#   Restart 7/9 ...      44.3316
#   Restart 8/9 ...      41.0846
#   Restart 9/9 ...      39.5813
# │   Minimal L¹ mass:   2.9898e+01
# │   Status: DANGER ZONE
# │   Grain margin: 0.023196452
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k =  39 ──────────────────────────────────────────────────────────────────────
#   → Redundancy cliff zone (k > 17)
#   Restart 1/9 ... new best:      37.5701
#   Restart 2/9 ...      43.3136
#   Restart 3/9 ... new best:      30.8282
#   Restart 4/9 ...      32.8792
#   Restart 5/9 ...      46.6724
#   Restart 6/9 ...      32.4441
#   Restart 7/9 ... new best:      30.0099
#   Restart 8/9 ...      49.4772
#   Restart 9/9 ...      52.6918
# │   Minimal L¹ mass:   3.0010e+01
# │   Status: DANGER ZONE
# │   Grain margin: 0.022521689
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k =  40 ──────────────────────────────────────────────────────────────────────
#   → Redundancy cliff zone (k > 17)
#   Restart 1/10 ... new best:      39.5003
#   Restart 2/10 ... new best:      28.3929
#   Restart 3/10 ...      33.4454
#   Restart 4/10 ...      40.7986
#   Restart 5/10 ...      51.4446
#   Restart 6/10 ...      34.1325
#   Restart 7/10 ...      47.9163
#   Restart 8/10 ...      38.5946
#   Restart 9/10 ...      42.1201
#   Restart 10/10 ...      33.7614
# │   Minimal L¹ mass:   2.8393e+01
# │   Status: DANGER ZONE
# │   Grain margin: 0.021880663
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k =  41 ──────────────────────────────────────────────────────────────────────
#   → Redundancy cliff zone (k > 17)
#   Restart 1/10 ... new best:      41.7656
#   Restart 2/10 ... new best:      34.2852
#   Restart 3/10 ...      43.9488
#   Restart 4/10 ...      49.0691
#   Restart 5/10 ... new best:      33.0282
#   Restart 6/10 ...      33.5604
#   Restart 7/10 ...      47.4811
#   Restart 8/10 ...      40.6343
#   Restart 9/10 ...      41.2925
#   Restart 10/10 ...      47.6639
# │   Minimal L¹ mass:   3.3028e+01
# │   Status: DANGER ZONE
# │   Grain margin: 0.021270907
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k =  42 ──────────────────────────────────────────────────────────────────────
#   → Redundancy cliff zone (k > 17)
#   Restart 1/10 ... new best:      38.7830
#   Restart 2/10 ... new best:      29.0449
#   Restart 3/10 ...      51.1496
#   Restart 4/10 ...      41.0915
#   Restart 5/10 ...      33.7522
#   Restart 6/10 ...      58.1035
#   Restart 7/10 ...      39.7375
#   Restart 8/10 ...      50.6657
#   Restart 9/10 ...      47.7166
#   Restart 10/10 ...      44.7460
# │   Minimal L¹ mass:   2.9045e+01
# │   Status: DANGER ZONE
# │   Grain margin: 0.020690187
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k =  43 ──────────────────────────────────────────────────────────────────────
#   → Redundancy cliff zone (k > 17)
#   Restart 1/10 ... new best:      44.8596
#   Restart 2/10 ... new best:      31.2116
#   Restart 3/10 ...      56.2505
#   Restart 4/10 ...      49.8825
#   Restart 5/10 ...      34.2400
#   Restart 6/10 ...      53.0363
#   Restart 7/10 ...      38.7021
#   Restart 8/10 ...      40.1212
#   Restart 9/10 ...      45.5395
#   Restart 10/10 ...      59.4854
# │   Minimal L¹ mass:   3.1212e+01
# │   Status: DANGER ZONE
# │   Grain margin: 0.020136477
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k =  44 ──────────────────────────────────────────────────────────────────────
#   → Redundancy cliff zone (k > 17)
#   Restart 1/10 ... new best:      33.6907
#   Restart 2/10 ...      48.3918
#   Restart 3/10 ...      50.6442
#   Restart 4/10 ...      37.6496
#   Restart 5/10 ...      39.0848
#   Restart 6/10 ...      53.6107
#   Restart 7/10 ...      39.3717
#   Restart 8/10 ...      35.9211
#   Restart 9/10 ...      49.4844
#   Restart 10/10 ...      48.3533
# │   Minimal L¹ mass:   3.3691e+01
# │   Status: DANGER ZONE
# │   Grain margin: 0.019607936
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k =  45 ──────────────────────────────────────────────────────────────────────
#   → Redundancy cliff zone (k > 17)
#   Restart 1/10 ... new best:      44.3571
#   Restart 2/10 ... new best:      37.4812
#   Restart 3/10 ... new best:      32.2493
#   Restart 4/10 ...      47.7468
#   Restart 5/10 ...      51.3364
#   Restart 6/10 ...      48.1620
#   Restart 7/10 ... 1000000000000000000.0000
#   Restart 8/10 ...      40.5350
#   Restart 9/10 ...      47.3003
#   Restart 10/10 ...      38.1541
# │   Minimal L¹ mass:   3.2249e+01
# │   Status: DANGER ZONE
# │   Grain margin: 0.019102885
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k =  46 ──────────────────────────────────────────────────────────────────────
#   → Redundancy cliff zone (k > 17)
#   Restart 1/10 ... new best:      46.7290
#   Restart 2/10 ...      50.2698
#   Restart 3/10 ... new best:      37.8290
#   Restart 4/10 ...      52.8905
#   Restart 5/10 ...      51.6021
#   Restart 6/10 ...      48.2317
#   Restart 7/10 ...      53.5291
#   Restart 8/10 ...      44.4529
#   Restart 9/10 ...      44.5735
#   Restart 10/10 ...      50.3285
# │   Minimal L¹ mass:   3.7829e+01
# │   Status: DANGER ZONE
# │   Grain margin: 0.018619793
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k =  47 ──────────────────────────────────────────────────────────────────────
#   → Redundancy cliff zone (k > 17)
#   Restart 1/10 ... new best: 1000000000000000000.0000
#   Restart 2/10 ... new best:      41.8465
#   Restart 3/10 ...      53.9542
#   Restart 4/10 ... 1000000000000000000.0000
#   Restart 5/10 ...      51.6776
#   Restart 6/10 ...      58.4375
#   Restart 7/10 ...      54.1702
#   Restart 8/10 ...      49.9132
#   Restart 9/10 ...      44.4971
#   Restart 10/10 ...      50.5260
# │   Minimal L¹ mass:   4.1847e+01
# │   Status: DANGER ZONE
# │   Grain margin: 0.018157259
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k =  48 ──────────────────────────────────────────────────────────────────────
#   → Redundancy cliff zone (k > 17)
#   Restart 1/10 ... new best:      64.9727
#   Restart 2/10 ... 1000000000000000000.0000
#   Restart 3/10 ... new best:      46.9772
#   Restart 4/10 ... new best:      44.9547
#   Restart 5/10 ... 1000000000000000000.0000
#   Restart 6/10 ... new best:      39.7856
#   Restart 7/10 ...      70.7885
#   Restart 8/10 ... 1000000000000000000.0000
#   Restart 9/10 ... 1000000000000000000.0000
#   Restart 10/10 ...      55.3193
# │   Minimal L¹ mass:   3.9786e+01
# │   Status: DANGER ZONE
# │   Grain margin: 0.017713996
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k =  49 ──────────────────────────────────────────────────────────────────────
#   → Redundancy cliff zone (k > 17)
#   Restart 1/10 ... new best:      44.1638
#   Restart 2/10 ...      55.3020
#   Restart 3/10 ...      58.7104
#   Restart 4/10 ... 1000000000000000000.0000
#   Restart 5/10 ...      78.1831
#   Restart 6/10 ... 1000000000000000000.0000
#   Restart 7/10 ... 1000000000000000000.0000
#   Restart 8/10 ... 1000000000000000000.0000
#   Restart 9/10 ...      53.5768
#   Restart 10/10 ... 1000000000000000000.0000
# │   Minimal L¹ mass:   4.4164e+01
# │   Status: DANGER ZONE
# │   Grain margin: 0.017288826
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k =  50 ──────────────────────────────────────────────────────────────────────
#   → Redundancy cliff zone (k > 17)
#   Restart 1/11 ... new best: 1000000000000000000.0000
#   Restart 2/11 ... 1000000000000000000.0000
#   Restart 3/11 ... new best:      52.3426
#   Restart 4/11 ... 1000000000000000000.0000
#   Restart 5/11 ...      54.7662
#   Restart 6/11 ... 1000000000000000000.0000
#   Restart 7/11 ...     122.7022
#   Restart 8/11 ... 1000000000000000000.0000
#   Restart 9/11 ... 1000000000000000000.0000
#   Restart 10/11 ... new best:      49.1627
#   Restart 11/11 ... 1000000000000000000.0000
# │   Minimal L¹ mass:   4.9163e+01
# │   Status: DANGER ZONE
# │   Grain margin: 0.016880663
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k =  51 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=51
#   Best L¹ (quasi-uniform):   4.4230e+00
# │   Minimal L¹ mass:   4.4230e+00
# │   Status: STABLE
# │   Grain margin: 0.016488506
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k =  52 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=52
#   Best L¹ (quasi-uniform):   5.1856e+00
# │   Minimal L¹ mass:   5.1856e+00
# │   Status: STABLE
# │   Grain margin: 0.016111432
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k =  53 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=53
#   Best L¹ (quasi-uniform):   6.1179e+00
# │   Minimal L¹ mass:   6.1179e+00
# │   Status: STABLE
# │   Grain margin: 0.015748588
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k =  54 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=54
#   Best L¹ (quasi-uniform):   7.4094e+00
# │   Minimal L¹ mass:   7.4094e+00
# │   Status: STABLE
# │   Grain margin: 0.015399182
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k =  55 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=55
#   Best L¹ (quasi-uniform):   1.3029e+00
# │   Minimal L¹ mass:   1.3029e+00
# │   Status: STABLE
# │   Grain margin: 0.015062481
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k =  56 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=56
#   Best L¹ (quasi-uniform):   1.8040e+01
# │   Minimal L¹ mass:   1.8040e+01
# │   Status: DANGER ZONE
# │   Grain margin: 0.014737806
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k =  57 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=57
#   Best L¹ (quasi-uniform):   2.3838e+00
# │   Minimal L¹ mass:   2.3838e+00
# │   Status: STABLE
# │   Grain margin: 0.014424523
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k =  58 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=58
#   Best L¹ (quasi-uniform):   1.2334e+01
# │   Minimal L¹ mass:   1.2334e+01
# │   Status: STABLE
# │   Grain margin: 0.014122042
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k =  59 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=59
#   Best L¹ (quasi-uniform):   2.0670e+00
# │   Minimal L¹ mass:   2.0670e+00
# │   Status: STABLE
# │   Grain margin: 0.013829816
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k =  60 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=60
#   Best L¹ (quasi-uniform):   4.5718e+00
# │   Minimal L¹ mass:   4.5718e+00
# │   Status: STABLE
# │   Grain margin: 0.013547330
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k =  61 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=61
#   Best L¹ (quasi-uniform):   6.6097e+00
# │   Minimal L¹ mass:   6.6097e+00
# │   Status: STABLE
# │   Grain margin: 0.013274106
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k =  62 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=62
#   Best L¹ (quasi-uniform):   1.4261e+01
# │   Minimal L¹ mass:   1.4261e+01
# │   Status: STABLE
# │   Grain margin: 0.013009695
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k =  63 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=63
#   Best L¹ (quasi-uniform):   2.2338e+01
# │   Minimal L¹ mass:   2.2338e+01
# │   Status: DANGER ZONE
# │   Grain margin: 0.012753679
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k =  64 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=64
#   Best L¹ (quasi-uniform):   9.5879e+00
# │   Minimal L¹ mass:   9.5879e+00
# │   Status: STABLE
# │   Grain margin: 0.012505663
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k =  65 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=65
#   Best L¹ (quasi-uniform):   1.0684e+01
# │   Minimal L¹ mass:   1.0684e+01
# │   Status: STABLE
# │   Grain margin: 0.012265278
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k =  66 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=66
#   Best L¹ (quasi-uniform):   1.5244e+01
# │   Minimal L¹ mass:   1.5244e+01
# │   Status: DANGER ZONE
# │   Grain margin: 0.012032178
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k =  67 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=67
#   Best L¹ (quasi-uniform):   1.3566e+00
# │   Minimal L¹ mass:   1.3566e+00
# │   Status: STABLE
# │   Grain margin: 0.011806036
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k =  68 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=68
#   Best L¹ (quasi-uniform):   1.4736e+01
# │   Minimal L¹ mass:   1.4736e+01
# │   Status: STABLE
# │   Grain margin: 0.011586545
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k =  69 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=69
#   Best L¹ (quasi-uniform):   1.6309e+01
# │   Minimal L¹ mass:   1.6309e+01
# │   Status: DANGER ZONE
# │   Grain margin: 0.011373417
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k =  70 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=70
#   Best L¹ (quasi-uniform):   3.1733e+01
# │   Minimal L¹ mass:   3.1733e+01
# │   Status: DANGER ZONE
# │   Grain margin: 0.011166377
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k =  71 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=71
#   Best L¹ (quasi-uniform):   2.6265e+01
# │   Minimal L¹ mass:   2.6265e+01
# │   Status: DANGER ZONE
# │   Grain margin: 0.010965170
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k =  72 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=72
#   Best L¹ (quasi-uniform):   1.5864e+01
# │   Minimal L¹ mass:   1.5864e+01
# │   Status: DANGER ZONE
# │   Grain margin: 0.010769552
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k =  73 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=73
#   Best L¹ (quasi-uniform):   1.5547e+01
# │   Minimal L¹ mass:   1.5547e+01
# │   Status: DANGER ZONE
# │   Grain margin: 0.010579293
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k =  74 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=74
#   Best L¹ (quasi-uniform):   1.8156e+00
# │   Minimal L¹ mass:   1.8156e+00
# │   Status: STABLE
# │   Grain margin: 0.010394177
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k =  75 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=75
#   Best L¹ (quasi-uniform):   2.7155e+00
# │   Minimal L¹ mass:   2.7155e+00
# │   Status: STABLE
# │   Grain margin: 0.010213996
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k =  76 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=76
#   Best L¹ (quasi-uniform):   4.4223e+00
# │   Minimal L¹ mass:   4.4223e+00
# │   Status: STABLE
# │   Grain margin: 0.010038558
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k =  77 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=77
#   Best L¹ (quasi-uniform):   1.5582e+01
# │   Minimal L¹ mass:   1.5582e+01
# │   Status: DANGER ZONE
# │   Grain margin: 0.009867676
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k =  78 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=78
#   Best L¹ (quasi-uniform):   1.5220e+01
# │   Minimal L¹ mass:   1.5220e+01
# │   Status: DANGER ZONE
# │   Grain margin: 0.009701176
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k =  79 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=79
#   Best L¹ (quasi-uniform):   1.4770e+01
# │   Minimal L¹ mass:   1.4770e+01
# │   Status: STABLE
# │   Grain margin: 0.009538891
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k =  80 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=80
#   Best L¹ (quasi-uniform):   1.5604e+01
# │   Minimal L¹ mass:   1.5604e+01
# │   Status: DANGER ZONE
# │   Grain margin: 0.009380663
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k =  81 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=81
#   Best L¹ (quasi-uniform):   1.4687e+01
# │   Minimal L¹ mass:   1.4687e+01
# │   Status: STABLE
# │   Grain margin: 0.009226342
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k =  82 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=82
#   Best L¹ (quasi-uniform):   1.2706e+01
# │   Minimal L¹ mass:   1.2706e+01
# │   Status: STABLE
# │   Grain margin: 0.009075785
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k =  83 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=83
#   Best L¹ (quasi-uniform):   1.6167e+01
# │   Minimal L¹ mass:   1.6167e+01
# │   Status: DANGER ZONE
# │   Grain margin: 0.008928856
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k =  84 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=84
#   Best L¹ (quasi-uniform):   3.0409e+01
# │   Minimal L¹ mass:   3.0409e+01
# │   Status: DANGER ZONE
# │   Grain margin: 0.008785425
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k =  85 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=85
#   Best L¹ (quasi-uniform):   1.5440e+01
# │   Minimal L¹ mass:   1.5440e+01
# │   Status: DANGER ZONE
# │   Grain margin: 0.008645369
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k =  86 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=86
#   Best L¹ (quasi-uniform):   1.6398e+01
# │   Minimal L¹ mass:   1.6398e+01
# │   Status: DANGER ZONE
# │   Grain margin: 0.008508570
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k =  87 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=87
#   Best L¹ (quasi-uniform):   5.5771e+00
# │   Minimal L¹ mass:   5.5771e+00
# │   Status: STABLE
# │   Grain margin: 0.008374916
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k =  88 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=88
#   Best L¹ (quasi-uniform):   8.1055e+00
# │   Minimal L¹ mass:   8.1055e+00
# │   Status: STABLE
# │   Grain margin: 0.008244299
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k =  89 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=89
#   Best L¹ (quasi-uniform):   5.5757e+00
# │   Minimal L¹ mass:   5.5757e+00
# │   Status: STABLE
# │   Grain margin: 0.008116618
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k =  90 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=90
#   Best L¹ (quasi-uniform):   2.6325e+01
# │   Minimal L¹ mass:   2.6325e+01
# │   Status: DANGER ZONE
# │   Grain margin: 0.007991774
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k =  91 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=91
#   Best L¹ (quasi-uniform):   5.2827e+00
# │   Minimal L¹ mass:   5.2827e+00
# │   Status: STABLE
# │   Grain margin: 0.007869674
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k =  92 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=92
#   Best L¹ (quasi-uniform):   2.8849e+01
# │   Minimal L¹ mass:   2.8849e+01
# │   Status: DANGER ZONE
# │   Grain margin: 0.007750228
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k =  93 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=93
#   Best L¹ (quasi-uniform):   2.1341e+01
# │   Minimal L¹ mass:   2.1341e+01
# │   Status: DANGER ZONE
# │   Grain margin: 0.007633351
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k =  94 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=94
#   Best L¹ (quasi-uniform):   2.2865e+01
# │   Minimal L¹ mass:   2.2865e+01
# │   Status: DANGER ZONE
# │   Grain margin: 0.007518961
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k =  95 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=95
#   Best L¹ (quasi-uniform):   2.4309e+01
# │   Minimal L¹ mass:   2.4309e+01
# │   Status: DANGER ZONE
# │   Grain margin: 0.007406979
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k =  96 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=96
#   Best L¹ (quasi-uniform):   3.2268e+00
# │   Minimal L¹ mass:   3.2268e+00
# │   Status: STABLE
# │   Grain margin: 0.007297330
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k =  97 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=97
#   Best L¹ (quasi-uniform):   2.6977e+01
# │   Minimal L¹ mass:   2.6977e+01
# │   Status: DANGER ZONE
# │   Grain margin: 0.007189941
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k =  98 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=98
#   Best L¹ (quasi-uniform):   2.7714e+01
# │   Minimal L¹ mass:   2.7714e+01
# │   Status: DANGER ZONE
# │   Grain margin: 0.007084745
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k =  99 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=99
#   Best L¹ (quasi-uniform):   2.5775e+01
# │   Minimal L¹ mass:   2.5775e+01
# │   Status: DANGER ZONE
# │   Grain margin: 0.006981673
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 100 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=100
#   Best L¹ (quasi-uniform):   2.6577e+01
# │   Minimal L¹ mass:   2.6577e+01
# │   Status: DANGER ZONE
# │   Grain margin: 0.006880663
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 101 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=101
#   Best L¹ (quasi-uniform):   1.0924e+01
# │   Minimal L¹ mass:   1.0924e+01
# │   Status: STABLE
# │   Grain margin: 0.006781653
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 102 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=102
#   Best L¹ (quasi-uniform):   2.8102e+01
# │   Minimal L¹ mass:   2.8102e+01
# │   Status: DANGER ZONE
# │   Grain margin: 0.006684585
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 103 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=103
#   Best L¹ (quasi-uniform):   3.8373e+01
# │   Minimal L¹ mass:   3.8373e+01
# │   Status: DANGER ZONE
# │   Grain margin: 0.006589401
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 104 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=104
#   Best L¹ (quasi-uniform):   3.9360e+01
# │   Minimal L¹ mass:   3.9360e+01
# │   Status: DANGER ZONE
# │   Grain margin: 0.006496048
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 105 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=105
#   Best L¹ (quasi-uniform):   2.6745e+01
# │   Minimal L¹ mass:   2.6745e+01
# │   Status: DANGER ZONE
# │   Grain margin: 0.006404473
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 106 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=106
#   Best L¹ (quasi-uniform):   2.8414e+01
# │   Minimal L¹ mass:   2.8414e+01
# │   Status: DANGER ZONE
# │   Grain margin: 0.006314625
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 107 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=107
#   Best L¹ (quasi-uniform):   2.9992e+01
# │   Minimal L¹ mass:   2.9992e+01
# │   Status: DANGER ZONE
# │   Grain margin: 0.006226457
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 108 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=108
#   Best L¹ (quasi-uniform):   2.2842e+01
# │   Minimal L¹ mass:   2.2842e+01
# │   Status: DANGER ZONE
# │   Grain margin: 0.006139922
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 109 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=109
#   Best L¹ (quasi-uniform):   1.9148e+01
# │   Minimal L¹ mass:   1.9148e+01
# │   Status: DANGER ZONE
# │   Grain margin: 0.006054975
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 110 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=110
#   Best L¹ (quasi-uniform):   2.0017e+01
# │   Minimal L¹ mass:   2.0017e+01
# │   Status: DANGER ZONE
# │   Grain margin: 0.005971572
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 111 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=111
#   Best L¹ (quasi-uniform):   1.9939e+01
# │   Minimal L¹ mass:   1.9939e+01
# │   Status: DANGER ZONE
# │   Grain margin: 0.005889672
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 112 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=112
#   Best L¹ (quasi-uniform):   4.2012e+01
# │   Minimal L¹ mass:   4.2012e+01
# │   Status: DANGER ZONE
# │   Grain margin: 0.005809234
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 113 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=113
#   Best L¹ (quasi-uniform):   4.2464e+01
# │   Minimal L¹ mass:   4.2464e+01
# │   Status: DANGER ZONE
# │   Grain margin: 0.005730221
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 114 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=114
#   Best L¹ (quasi-uniform):   4.5926e+01
# │   Minimal L¹ mass:   4.5926e+01
# │   Status: DANGER ZONE
# │   Grain margin: 0.005652593
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 115 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=115
#   Best L¹ (quasi-uniform):   8.2810e+00
# │   Minimal L¹ mass:   8.2810e+00
# │   Status: STABLE
# │   Grain margin: 0.005576315
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 116 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=116
#   Best L¹ (quasi-uniform):   4.6570e+01
# │   Minimal L¹ mass:   4.6570e+01
# │   Status: DANGER ZONE
# │   Grain margin: 0.005501353
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 117 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=117
#   Best L¹ (quasi-uniform):   1.8136e+00
# │   Minimal L¹ mass:   1.8136e+00
# │   Status: STABLE
# │   Grain margin: 0.005427672
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 118 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=118
#   Best L¹ (quasi-uniform):   4.7618e+01
# │   Minimal L¹ mass:   4.7618e+01
# │   Status: DANGER ZONE
# │   Grain margin: 0.005355239
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 119 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=119
#   Best L¹ (quasi-uniform):   4.8115e+01
# │   Minimal L¹ mass:   4.8115e+01
# │   Status: DANGER ZONE
# │   Grain margin: 0.005284024
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 120 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=120
#   Best L¹ (quasi-uniform):   2.6182e+01
# │   Minimal L¹ mass:   2.6182e+01
# │   Status: DANGER ZONE
# │   Grain margin: 0.005213996
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 121 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=121
#   Best L¹ (quasi-uniform):   2.3057e+00
# │   Minimal L¹ mass:   2.3057e+00
# │   Status: STABLE
# │   Grain margin: 0.005145126
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 122 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=122
#   Best L¹ (quasi-uniform):   2.7954e+01
# │   Minimal L¹ mass:   2.7954e+01
# │   Status: DANGER ZONE
# │   Grain margin: 0.005077384
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 123 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=123
#   Best L¹ (quasi-uniform):   2.8795e+01
# │   Minimal L¹ mass:   2.8795e+01
# │   Status: DANGER ZONE
# │   Grain margin: 0.005010744
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 124 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=124
#   Best L¹ (quasi-uniform):   4.3181e+01
# │   Minimal L¹ mass:   4.3181e+01
# │   Status: DANGER ZONE
# │   Grain margin: 0.004945179
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 125 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=125
#   Best L¹ (quasi-uniform):   4.4110e+01
# │   Minimal L¹ mass:   4.4110e+01
# │   Status: DANGER ZONE
# │   Grain margin: 0.004880663
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 126 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=126
#   Best L¹ (quasi-uniform):   1.7026e+01
# │   Minimal L¹ mass:   1.7026e+01
# │   Status: DANGER ZONE
# │   Grain margin: 0.004817171
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 127 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=127
#   Best L¹ (quasi-uniform):   1.8231e+01
# │   Minimal L¹ mass:   1.8231e+01
# │   Status: DANGER ZONE
# │   Grain margin: 0.004754679
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 128 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=128
#   Best L¹ (quasi-uniform):   1.9391e+01
# │   Minimal L¹ mass:   1.9391e+01
# │   Status: DANGER ZONE
# │   Grain margin: 0.004693163
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 129 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=129
#   Best L¹ (quasi-uniform):   5.0599e+01
# │   Minimal L¹ mass:   5.0599e+01
# │   Status: DANGER ZONE
# │   Grain margin: 0.004632601
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 130 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=130
#   Best L¹ (quasi-uniform):   5.1078e+01
# │   Minimal L¹ mass:   5.1078e+01
# │   Status: DANGER ZONE
# │   Grain margin: 0.004572971
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 131 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=131
#   Best L¹ (quasi-uniform):   5.1541e+01
# │   Minimal L¹ mass:   5.1541e+01
# │   Status: DANGER ZONE
# │   Grain margin: 0.004514251
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 132 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=132
#   Best L¹ (quasi-uniform):   4.6467e+01
# │   Minimal L¹ mass:   4.6467e+01
# │   Status: DANGER ZONE
# │   Grain margin: 0.004456421
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 133 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=133
#   Best L¹ (quasi-uniform):   2.9018e+01
# │   Minimal L¹ mass:   2.9018e+01
# │   Status: DANGER ZONE
# │   Grain margin: 0.004399460
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 134 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=134
#   Best L¹ (quasi-uniform):   4.7388e+01
# │   Minimal L¹ mass:   4.7388e+01
# │   Status: DANGER ZONE
# │   Grain margin: 0.004343350
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 135 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=135
#   Best L¹ (quasi-uniform):   1.2703e+01
# │   Minimal L¹ mass:   1.2703e+01
# │   Status: STABLE
# │   Grain margin: 0.004288070
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 136 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=136
#   Best L¹ (quasi-uniform):   1.4494e+01
# │   Minimal L¹ mass:   1.4494e+01
# │   Status: STABLE
# │   Grain margin: 0.004233604
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 137 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=137
#   Best L¹ (quasi-uniform):   1.7983e+01
# │   Minimal L¹ mass:   1.7983e+01
# │   Status: DANGER ZONE
# │   Grain margin: 0.004179933
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 138 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=138
#   Best L¹ (quasi-uniform):   1.9773e+01
# │   Minimal L¹ mass:   1.9773e+01
# │   Status: DANGER ZONE
# │   Grain margin: 0.004127040
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 139 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=139
#   Best L¹ (quasi-uniform):   2.1480e+01
# │   Minimal L¹ mass:   2.1480e+01
# │   Status: DANGER ZONE
# │   Grain margin: 0.004074908
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 140 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=140
#   Best L¹ (quasi-uniform):   7.0530e+01
# │   Minimal L¹ mass:   7.0530e+01
# │   Status: DANGER ZONE
# │   Grain margin: 0.004023520
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 141 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=141
#   Best L¹ (quasi-uniform):   7.1360e+01
# │   Minimal L¹ mass:   7.1360e+01
# │   Status: DANGER ZONE
# │   Grain margin: 0.003972862
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 142 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=142
#   Best L¹ (quasi-uniform):   1.1519e+01
# │   Minimal L¹ mass:   1.1519e+01
# │   Status: STABLE
# │   Grain margin: 0.003922917
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 143 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=143
#   Best L¹ (quasi-uniform):   6.9387e+01
# │   Minimal L¹ mass:   6.9387e+01
# │   Status: DANGER ZONE
# │   Grain margin: 0.003873670
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 144 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=144
#   Best L¹ (quasi-uniform):   7.4780e+00
# │   Minimal L¹ mass:   7.4780e+00
# │   Status: STABLE
# │   Grain margin: 0.003825107
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 145 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=145
#   Best L¹ (quasi-uniform):   3.6097e+01
# │   Minimal L¹ mass:   3.6097e+01
# │   Status: DANGER ZONE
# │   Grain margin: 0.003777215
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 146 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=146
#   Best L¹ (quasi-uniform):   1.5752e+01
# │   Minimal L¹ mass:   1.5752e+01
# │   Status: DANGER ZONE
# │   Grain margin: 0.003729978
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 147 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=147
#   Best L¹ (quasi-uniform):   1.1226e+01
# │   Minimal L¹ mass:   1.1226e+01
# │   Status: STABLE
# │   Grain margin: 0.003683384
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 148 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=148
#   Best L¹ (quasi-uniform):   8.9324e+00
# │   Minimal L¹ mass:   8.9324e+00
# │   Status: STABLE
# │   Grain margin: 0.003637420
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 149 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=149
#   Best L¹ (quasi-uniform):   3.1032e+01
# │   Minimal L¹ mass:   3.1032e+01
# │   Status: DANGER ZONE
# │   Grain margin: 0.003592072
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 150 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=150
#   Best L¹ (quasi-uniform):   1.1841e+01
# │   Minimal L¹ mass:   1.1841e+01
# │   Status: STABLE
# │   Grain margin: 0.003547330
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 151 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=151
#   Best L¹ (quasi-uniform):   1.2950e+01
# │   Minimal L¹ mass:   1.2950e+01
# │   Status: STABLE
# │   Grain margin: 0.003503180
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 152 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=152
#   Best L¹ (quasi-uniform):   4.3197e+01
# │   Minimal L¹ mass:   4.3197e+01
# │   Status: DANGER ZONE
# │   Grain margin: 0.003459610
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 153 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=153
#   Best L¹ (quasi-uniform):   8.3972e+01
# │   Minimal L¹ mass:   8.3972e+01
# │   Status: DANGER ZONE
# │   Grain margin: 0.003416611
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 154 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=154
#   Best L¹ (quasi-uniform):   5.9642e+01
# │   Minimal L¹ mass:   5.9642e+01
# │   Status: DANGER ZONE
# │   Grain margin: 0.003374169
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 155 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=155
#   Best L¹ (quasi-uniform):   5.9906e+01
# │   Minimal L¹ mass:   5.9906e+01
# │   Status: DANGER ZONE
# │   Grain margin: 0.003332276
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 156 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=156
#   Best L¹ (quasi-uniform):   8.7189e+01
# │   Minimal L¹ mass:   8.7189e+01
# │   Status: DANGER ZONE
# │   Grain margin: 0.003290919
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 157 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=157
#   Best L¹ (quasi-uniform):   4.7274e+00
# │   Minimal L¹ mass:   4.7274e+00
# │   Status: STABLE
# │   Grain margin: 0.003250090
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 158 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=158
#   Best L¹ (quasi-uniform):   6.1606e+01
# │   Minimal L¹ mass:   6.1606e+01
# │   Status: DANGER ZONE
# │   Grain margin: 0.003209777
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 159 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=159
#   Best L¹ (quasi-uniform):   6.1866e+01
# │   Minimal L¹ mass:   6.1866e+01
# │   Status: DANGER ZONE
# │   Grain margin: 0.003169971
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 160 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=160
#   Best L¹ (quasi-uniform):   6.0243e+01
# │   Minimal L¹ mass:   6.0243e+01
# │   Status: DANGER ZONE
# │   Grain margin: 0.003130663
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 161 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=161
#   Best L¹ (quasi-uniform):   6.0498e+01
# │   Minimal L¹ mass:   6.0498e+01
# │   Status: DANGER ZONE
# │   Grain margin: 0.003091843
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 162 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=162
#   Best L¹ (quasi-uniform):   9.8880e+01
# │   Minimal L¹ mass:   9.8880e+01
# │   Status: DANGER ZONE
# │   Grain margin: 0.003053503
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 163 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=163
#   Best L¹ (quasi-uniform):   5.4755e+01
# │   Minimal L¹ mass:   5.4755e+01
# │   Status: DANGER ZONE
# │   Grain margin: 0.003015632
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 164 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=164
#   Best L¹ (quasi-uniform):   3.1599e+01
# │   Minimal L¹ mass:   3.1599e+01
# │   Status: DANGER ZONE
# │   Grain margin: 0.002978224
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 165 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=165
#   Best L¹ (quasi-uniform):   3.2481e+01
# │   Minimal L¹ mass:   3.2481e+01
# │   Status: DANGER ZONE
# │   Grain margin: 0.002941269
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 166 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=166
#   Best L¹ (quasi-uniform):   3.3333e+01
# │   Minimal L¹ mass:   3.3333e+01
# │   Status: DANGER ZONE
# │   Grain margin: 0.002904759
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 167 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=167
#   Best L¹ (quasi-uniform):   3.4153e+01
# │   Minimal L¹ mass:   3.4153e+01
# │   Status: DANGER ZONE
# │   Grain margin: 0.002868687
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 168 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=168
#   Best L¹ (quasi-uniform):   4.7748e+01
# │   Minimal L¹ mass:   4.7748e+01
# │   Status: DANGER ZONE
# │   Grain margin: 0.002833044
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 169 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=169
#   Best L¹ (quasi-uniform):   4.8246e+01
# │   Minimal L¹ mass:   4.8246e+01
# │   Status: DANGER ZONE
# │   Grain margin: 0.002797823
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 170 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=170
#   Best L¹ (quasi-uniform):   4.8727e+01
# │   Minimal L¹ mass:   4.8727e+01
# │   Status: DANGER ZONE
# │   Grain margin: 0.002763016
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 171 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=171
#   Best L¹ (quasi-uniform):   4.7595e+01
# │   Minimal L¹ mass:   4.7595e+01
# │   Status: DANGER ZONE
# │   Grain margin: 0.002728616
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 172 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=172
#   Best L¹ (quasi-uniform):   4.3326e+01
# │   Minimal L¹ mass:   4.3326e+01
# │   Status: DANGER ZONE
# │   Grain margin: 0.002694616
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 173 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=173
#   Best L¹ (quasi-uniform):   1.4717e+00
# │   Minimal L¹ mass:   1.4717e+00
# │   Status: STABLE
# │   Grain margin: 0.002661010
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 174 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=174
#   Best L¹ (quasi-uniform):   4.1954e+01
# │   Minimal L¹ mass:   4.1954e+01
# │   Status: DANGER ZONE
# │   Grain margin: 0.002627789
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 175 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=175
#   Best L¹ (quasi-uniform):   4.2608e+01
# │   Minimal L¹ mass:   4.2608e+01
# │   Status: DANGER ZONE
# │   Grain margin: 0.002594949
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 176 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=176
#   Best L¹ (quasi-uniform):   4.3238e+01
# │   Minimal L¹ mass:   4.3238e+01
# │   Status: DANGER ZONE
# │   Grain margin: 0.002562481
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 177 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=177
#   Best L¹ (quasi-uniform):   4.3845e+01
# │   Minimal L¹ mass:   4.3845e+01
# │   Status: DANGER ZONE
# │   Grain margin: 0.002530381
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 178 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=178
#   Best L¹ (quasi-uniform):   1.2136e+00
# │   Minimal L¹ mass:   1.2136e+00
# │   Status: STABLE
# │   Grain margin: 0.002498641
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 179 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=179
#   Best L¹ (quasi-uniform):   8.6893e+01
# │   Minimal L¹ mass:   8.6893e+01
# │   Status: DANGER ZONE
# │   Grain margin: 0.002467255
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 180 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=180
#   Best L¹ (quasi-uniform):   8.6806e+01
# │   Minimal L¹ mass:   8.6806e+01
# │   Status: DANGER ZONE
# │   Grain margin: 0.002436219
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 181 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=181
#   Best L¹ (quasi-uniform):   1.2472e+02
# │   Minimal L¹ mass:   1.2472e+02
# │   Status: DANGER ZONE
# │   Grain margin: 0.002405525
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 182 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=182
#   Best L¹ (quasi-uniform):   1.2400e+02
# │   Minimal L¹ mass:   1.2400e+02
# │   Status: DANGER ZONE
# │   Grain margin: 0.002375168
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 183 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=183
#   Best L¹ (quasi-uniform):   9.9369e+01
# │   Minimal L¹ mass:   9.9369e+01
# │   Status: DANGER ZONE
# │   Grain margin: 0.002345144
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 184 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=184
#   Best L¹ (quasi-uniform):   9.9076e+01
# │   Minimal L¹ mass:   9.9076e+01
# │   Status: DANGER ZONE
# │   Grain margin: 0.002315446
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 185 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=185
#   Best L¹ (quasi-uniform):   9.8786e+01
# │   Minimal L¹ mass:   9.8786e+01
# │   Status: DANGER ZONE
# │   Grain margin: 0.002286068
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 186 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=186
#   Best L¹ (quasi-uniform):   5.4772e+01
# │   Minimal L¹ mass:   5.4772e+01
# │   Status: DANGER ZONE
# │   Grain margin: 0.002257007
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 187 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=187
#   Best L¹ (quasi-uniform):   6.4014e+01
# │   Minimal L¹ mass:   6.4014e+01
# │   Status: DANGER ZONE
# │   Grain margin: 0.002228257
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 188 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=188
#   Best L¹ (quasi-uniform):   6.4216e+01
# │   Minimal L¹ mass:   6.4216e+01
# │   Status: DANGER ZONE
# │   Grain margin: 0.002199812
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 189 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=189
#   Best L¹ (quasi-uniform):   3.1950e+01
# │   Minimal L¹ mass:   3.1950e+01
# │   Status: DANGER ZONE
# │   Grain margin: 0.002171668
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 190 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=190
#   Best L¹ (quasi-uniform):   3.2702e+01
# │   Minimal L¹ mass:   3.2702e+01
# │   Status: DANGER ZONE
# │   Grain margin: 0.002143821
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 191 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=191
#   Best L¹ (quasi-uniform):   3.3427e+01
# │   Minimal L¹ mass:   3.3427e+01
# │   Status: DANGER ZONE
# │   Grain margin: 0.002116265
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 192 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=192
#   Best L¹ (quasi-uniform):   9.8834e+01
# │   Minimal L¹ mass:   9.8834e+01
# │   Status: DANGER ZONE
# │   Grain margin: 0.002088996
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 193 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=193
#   Best L¹ (quasi-uniform):   9.8521e+01
# │   Minimal L¹ mass:   9.8521e+01
# │   Status: DANGER ZONE
# │   Grain margin: 0.002062010
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 194 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=194
#   Best L¹ (quasi-uniform):   9.8211e+01
# │   Minimal L¹ mass:   9.8211e+01
# │   Status: DANGER ZONE
# │   Grain margin: 0.002035302
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 195 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=195
#   Best L¹ (quasi-uniform):   5.7628e+01
# │   Minimal L¹ mass:   5.7628e+01
# │   Status: DANGER ZONE
# │   Grain margin: 0.002008868
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 196 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=196
#   Best L¹ (quasi-uniform):   5.8909e+01
# │   Minimal L¹ mass:   5.8909e+01
# │   Status: DANGER ZONE
# │   Grain margin: 0.001982704
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 197 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=197
#   Best L¹ (quasi-uniform):   5.6746e+01
# │   Minimal L¹ mass:   5.6746e+01
# │   Status: DANGER ZONE
# │   Grain margin: 0.001956805
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 198 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=198
#   Best L¹ (quasi-uniform):   5.7831e+01
# │   Minimal L¹ mass:   5.7831e+01
# │   Status: DANGER ZONE
# │   Grain margin: 0.001931168
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 199 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=199
#   Best L¹ (quasi-uniform):   5.8841e+01
# │   Minimal L¹ mass:   5.8841e+01
# │   Status: DANGER ZONE
# │   Grain margin: 0.001905789
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 200 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=200
#   Best L¹ (quasi-uniform):   5.9779e+01
# │   Minimal L¹ mass:   5.9779e+01
# │   Status: DANGER ZONE
# │   Grain margin: 0.001880663
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 201 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=201
#   Best L¹ (quasi-uniform):   6.0650e+01
# │   Minimal L¹ mass:   6.0650e+01
# │   Status: DANGER ZONE
# │   Grain margin: 0.001855787
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 202 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=202
#   Best L¹ (quasi-uniform):   1.3538e+02
# │   Minimal L¹ mass:   1.3538e+02
# │   Status: DANGER ZONE
# │   Grain margin: 0.001831158
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 203 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=203
#   Best L¹ (quasi-uniform):   1.3433e+02
# │   Minimal L¹ mass:   1.3433e+02
# │   Status: DANGER ZONE
# │   Grain margin: 0.001806771
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 204 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=204
#   Best L¹ (quasi-uniform):   6.8727e+01
# │   Minimal L¹ mass:   6.8727e+01
# │   Status: DANGER ZONE
# │   Grain margin: 0.001782624
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 205 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=205
#   Best L¹ (quasi-uniform):   3.7652e+01
# │   Minimal L¹ mass:   3.7652e+01
# │   Status: DANGER ZONE
# │   Grain margin: 0.001758712
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 206 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=206
#   Best L¹ (quasi-uniform):   6.9082e+01
# │   Minimal L¹ mass:   6.9082e+01
# │   Status: DANGER ZONE
# │   Grain margin: 0.001735032
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 207 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=207
#   Best L¹ (quasi-uniform):   1.8074e+01
# │   Minimal L¹ mass:   1.8074e+01
# │   Status: DANGER ZONE
# │   Grain margin: 0.001711581
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 208 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=208
#   Best L¹ (quasi-uniform):   8.9813e+00
# │   Minimal L¹ mass:   8.9813e+00
# │   Status: STABLE
# │   Grain margin: 0.001688355
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 209 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=209
#   Best L¹ (quasi-uniform):   4.3362e+01
# │   Minimal L¹ mass:   4.3362e+01
# │   Status: DANGER ZONE
# │   Grain margin: 0.001665352
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 210 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=210
#   Best L¹ (quasi-uniform):   4.3977e+01
# │   Minimal L¹ mass:   4.3977e+01
# │   Status: DANGER ZONE
# │   Grain margin: 0.001642568
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 211 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=211
#   Best L¹ (quasi-uniform):   2.2667e+01
# │   Minimal L¹ mass:   2.2667e+01
# │   Status: DANGER ZONE
# │   Grain margin: 0.001619999
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 212 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=212
#   Best L¹ (quasi-uniform):   3.7456e+01
# │   Minimal L¹ mass:   3.7456e+01
# │   Status: DANGER ZONE
# │   Grain margin: 0.001597644
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 213 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=213
#   Best L¹ (quasi-uniform):   3.8906e+01
# │   Minimal L¹ mass:   3.8906e+01
# │   Status: DANGER ZONE
# │   Grain margin: 0.001575499
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 214 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=214
#   Best L¹ (quasi-uniform):   4.0265e+01
# │   Minimal L¹ mass:   4.0265e+01
# │   Status: DANGER ZONE
# │   Grain margin: 0.001553560
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 215 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=215
#   Best L¹ (quasi-uniform):   1.8230e+02
# │   Minimal L¹ mass:   1.8230e+02
# │   Status: DANGER ZONE
# │   Grain margin: 0.001531826
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 216 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=216
#   Best L¹ (quasi-uniform):   1.8017e+02
# │   Minimal L¹ mass:   1.8017e+02
# │   Status: DANGER ZONE
# │   Grain margin: 0.001510293
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 217 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=217
#   Best L¹ (quasi-uniform):   1.7808e+02
# │   Minimal L¹ mass:   1.7808e+02
# │   Status: DANGER ZONE
# │   Grain margin: 0.001488958
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 218 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=218
#   Best L¹ (quasi-uniform):   5.2658e+01
# │   Minimal L¹ mass:   5.2658e+01
# │   Status: DANGER ZONE
# │   Grain margin: 0.001467819
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 219 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=219
#   Best L¹ (quasi-uniform):   5.3284e+01
# │   Minimal L¹ mass:   5.3284e+01
# │   Status: DANGER ZONE
# │   Grain margin: 0.001446873
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 220 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=220
#   Best L¹ (quasi-uniform):   5.3864e+01
# │   Minimal L¹ mass:   5.3864e+01
# │   Status: DANGER ZONE
# │   Grain margin: 0.001426118
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 221 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=221
#   Best L¹ (quasi-uniform):   5.4402e+01
# │   Minimal L¹ mass:   5.4402e+01
# │   Status: DANGER ZONE
# │   Grain margin: 0.001405550
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 222 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=222
#   Best L¹ (quasi-uniform):   9.0459e+01
# │   Minimal L¹ mass:   9.0459e+01
# │   Status: DANGER ZONE
# │   Grain margin: 0.001385168
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 223 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=223
#   Best L¹ (quasi-uniform):   9.0239e+01
# │   Minimal L¹ mass:   9.0239e+01
# │   Status: DANGER ZONE
# │   Grain margin: 0.001364968
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 224 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=224
#   Best L¹ (quasi-uniform):   8.9994e+01
# │   Minimal L¹ mass:   8.9994e+01
# │   Status: DANGER ZONE
# │   Grain margin: 0.001344949
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 225 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=225
#   Best L¹ (quasi-uniform):   8.9725e+01
# │   Minimal L¹ mass:   8.9725e+01
# │   Status: DANGER ZONE
# │   Grain margin: 0.001325107
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 226 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=226
#   Best L¹ (quasi-uniform):   8.9434e+01
# │   Minimal L¹ mass:   8.9434e+01
# │   Status: DANGER ZONE
# │   Grain margin: 0.001305442
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 227 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=227
#   Best L¹ (quasi-uniform):   1.0150e+02
# │   Minimal L¹ mass:   1.0150e+02
# │   Status: DANGER ZONE
# │   Grain margin: 0.001285949
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 228 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=228
#   Best L¹ (quasi-uniform):   1.7723e+02
# │   Minimal L¹ mass:   1.7723e+02
# │   Status: DANGER ZONE
# │   Grain margin: 0.001266628
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 229 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=229
#   Best L¹ (quasi-uniform):   1.7500e+02
# │   Minimal L¹ mass:   1.7500e+02
# │   Status: DANGER ZONE
# │   Grain margin: 0.001247475
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 230 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=230
#   Best L¹ (quasi-uniform):   1.7282e+02
# │   Minimal L¹ mass:   1.7282e+02
# │   Status: DANGER ZONE
# │   Grain margin: 0.001228489
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 231 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=231
#   Best L¹ (quasi-uniform):   1.7069e+02
# │   Minimal L¹ mass:   1.7069e+02
# │   Status: DANGER ZONE
# │   Grain margin: 0.001209667
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 232 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=232
#   Best L¹ (quasi-uniform):   1.6860e+02
# │   Minimal L¹ mass:   1.6860e+02
# │   Status: DANGER ZONE
# │   Grain margin: 0.001191008
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 233 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=233
#   Best L¹ (quasi-uniform):   1.6655e+02
# │   Minimal L¹ mass:   1.6655e+02
# │   Status: DANGER ZONE
# │   Grain margin: 0.001172508
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 234 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=234
#   Best L¹ (quasi-uniform):   2.5895e+01
# │   Minimal L¹ mass:   2.5895e+01
# │   Status: DANGER ZONE
# │   Grain margin: 0.001154167
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 235 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=235
#   Best L¹ (quasi-uniform):   2.6879e+01
# │   Minimal L¹ mass:   2.6879e+01
# │   Status: DANGER ZONE
# │   Grain margin: 0.001135982
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 236 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=236
#   Best L¹ (quasi-uniform):   1.3054e+02
# │   Minimal L¹ mass:   1.3054e+02
# │   Status: DANGER ZONE
# │   Grain margin: 0.001117951
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 237 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=237
#   Best L¹ (quasi-uniform):   1.2939e+02
# │   Minimal L¹ mass:   1.2939e+02
# │   Status: DANGER ZONE
# │   Grain margin: 0.001100072
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 238 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=238
#   Best L¹ (quasi-uniform):   1.5694e+02
# │   Minimal L¹ mass:   1.5694e+02
# │   Status: DANGER ZONE
# │   Grain margin: 0.001082344
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 239 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=239
#   Best L¹ (quasi-uniform):   2.0130e+02
# │   Minimal L¹ mass:   2.0130e+02
# │   Status: DANGER ZONE
# │   Grain margin: 0.001064763
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 240 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=240
#   Best L¹ (quasi-uniform):   1.9830e+02
# │   Minimal L¹ mass:   1.9830e+02
# │   Status: DANGER ZONE
# │   Grain margin: 0.001047330
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 241 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=241
#   Best L¹ (quasi-uniform):   8.8498e+01
# │   Minimal L¹ mass:   8.8498e+01
# │   Status: DANGER ZONE
# │   Grain margin: 0.001030041
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 242 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=242
#   Best L¹ (quasi-uniform):   8.8060e+01
# │   Minimal L¹ mass:   8.8060e+01
# │   Status: DANGER ZONE
# │   Grain margin: 0.001012894
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 243 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=243
#   Best L¹ (quasi-uniform):   8.7591e+01
# │   Minimal L¹ mass:   8.7591e+01
# │   Status: DANGER ZONE
# │   Grain margin: 0.000995889
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 244 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=244
#   Best L¹ (quasi-uniform):   8.7094e+01
# │   Minimal L¹ mass:   8.7094e+01
# │   Status: DANGER ZONE
# │   Grain margin: 0.000979024
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 245 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=245
#   Best L¹ (quasi-uniform):   8.6572e+01
# │   Minimal L¹ mass:   8.6572e+01
# │   Status: DANGER ZONE
# │   Grain margin: 0.000962296
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 246 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=246
#   Best L¹ (quasi-uniform):   2.2833e+02
# │   Minimal L¹ mass:   2.2833e+02
# │   Status: DANGER ZONE
# │   Grain margin: 0.000945704
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 247 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=247
#   Best L¹ (quasi-uniform):   2.2491e+02
# │   Minimal L¹ mass:   2.2491e+02
# │   Status: DANGER ZONE
# │   Grain margin: 0.000929246
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 248 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=248
#   Best L¹ (quasi-uniform):   2.2157e+02
# │   Minimal L¹ mass:   2.2157e+02
# │   Status: DANGER ZONE
# │   Grain margin: 0.000912921
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 249 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=249
#   Best L¹ (quasi-uniform):   1.1150e+02
# │   Minimal L¹ mass:   1.1150e+02
# │   Status: DANGER ZONE
# │   Grain margin: 0.000896727
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 250 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=250
#   Best L¹ (quasi-uniform):   1.1012e+02
# │   Minimal L¹ mass:   1.1012e+02
# │   Status: DANGER ZONE
# │   Grain margin: 0.000880663
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 251 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=251
#   Best L¹ (quasi-uniform):   1.0874e+02
# │   Minimal L¹ mass:   1.0874e+02
# │   Status: DANGER ZONE
# │   Grain margin: 0.000864727
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 252 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=252
#   Best L¹ (quasi-uniform):   1.0736e+02
# │   Minimal L¹ mass:   1.0736e+02
# │   Status: DANGER ZONE
# │   Grain margin: 0.000848917
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 253 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=253
#   Best L¹ (quasi-uniform):   1.0600e+02
# │   Minimal L¹ mass:   1.0600e+02
# │   Status: DANGER ZONE
# │   Grain margin: 0.000833232
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 254 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=254
#   Best L¹ (quasi-uniform):   1.0464e+02
# │   Minimal L¹ mass:   1.0464e+02
# │   Status: DANGER ZONE
# │   Grain margin: 0.000817671
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 255 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=255
#   Best L¹ (quasi-uniform):   1.3152e+02
# │   Minimal L¹ mass:   1.3152e+02
# │   Status: DANGER ZONE
# │   Grain margin: 0.000802232
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 256 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=256
#   Best L¹ (quasi-uniform):   1.2926e+02
# │   Minimal L¹ mass:   1.2926e+02
# │   Status: DANGER ZONE
# │   Grain margin: 0.000786913
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 257 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=257
#   Best L¹ (quasi-uniform):   1.2705e+02
# │   Minimal L¹ mass:   1.2705e+02
# │   Status: DANGER ZONE
# │   Grain margin: 0.000771714
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 258 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=258
#   Best L¹ (quasi-uniform):   1.3156e+02
# │   Minimal L¹ mass:   1.3156e+02
# │   Status: DANGER ZONE
# │   Grain margin: 0.000756632
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 259 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=259
#   Best L¹ (quasi-uniform):   1.2934e+02
# │   Minimal L¹ mass:   1.2934e+02
# │   Status: DANGER ZONE
# │   Grain margin: 0.000741667
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 260 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=260
#   Best L¹ (quasi-uniform):   1.2717e+02
# │   Minimal L¹ mass:   1.2717e+02
# │   Status: DANGER ZONE
# │   Grain margin: 0.000726817
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 261 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=261
#   Best L¹ (quasi-uniform):   1.2505e+02
# │   Minimal L¹ mass:   1.2505e+02
# │   Status: DANGER ZONE
# │   Grain margin: 0.000712081
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 262 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=262
#   Best L¹ (quasi-uniform):   3.3890e+01
# │   Minimal L¹ mass:   3.3890e+01
# │   Status: DANGER ZONE
# │   Grain margin: 0.000697457
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 263 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=263
#   Best L¹ (quasi-uniform):   3.4279e+01
# │   Minimal L¹ mass:   3.4279e+01
# │   Status: DANGER ZONE
# │   Grain margin: 0.000682944
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 264 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=264
#   Best L¹ (quasi-uniform):   2.7895e+02
# │   Minimal L¹ mass:   2.7895e+02
# │   Status: DANGER ZONE
# │   Grain margin: 0.000668542
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 265 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=265
#   Best L¹ (quasi-uniform):   2.7507e+02
# │   Minimal L¹ mass:   2.7507e+02
# │   Status: DANGER ZONE
# │   Grain margin: 0.000654248
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 266 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=266
#   Best L¹ (quasi-uniform):   2.7125e+02
# │   Minimal L¹ mass:   2.7125e+02
# │   Status: DANGER ZONE
# │   Grain margin: 0.000640061
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 267 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=267
#   Best L¹ (quasi-uniform):   6.4488e+00
# │   Minimal L¹ mass:   6.4488e+00
# │   Status: STABLE
# │   Grain margin: 0.000625981
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 268 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=268
#   Best L¹ (quasi-uniform):   7.3865e+01
# │   Minimal L¹ mass:   7.3865e+01
# │   Status: DANGER ZONE
# │   Grain margin: 0.000612006
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 269 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=269
#   Best L¹ (quasi-uniform):   7.3027e+01
# │   Minimal L¹ mass:   7.3027e+01
# │   Status: DANGER ZONE
# │   Grain margin: 0.000598135
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 270 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=270
#   Best L¹ (quasi-uniform):   7.2163e+01
# │   Minimal L¹ mass:   7.2163e+01
# │   Status: DANGER ZONE
# │   Grain margin: 0.000584367
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 271 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=271
#   Best L¹ (quasi-uniform):   2.5817e+02
# │   Minimal L¹ mass:   2.5817e+02
# │   Status: DANGER ZONE
# │   Grain margin: 0.000570700
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 272 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=272
#   Best L¹ (quasi-uniform):   2.5452e+02
# │   Minimal L¹ mass:   2.5452e+02
# │   Status: DANGER ZONE
# │   Grain margin: 0.000557134
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 273 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=273
#   Best L¹ (quasi-uniform):   2.4567e+02
# │   Minimal L¹ mass:   2.4567e+02
# │   Status: DANGER ZONE
# │   Grain margin: 0.000543667
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 274 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=274
#   Best L¹ (quasi-uniform):   1.4555e+02
# │   Minimal L¹ mass:   1.4555e+02
# │   Status: DANGER ZONE
# │   Grain margin: 0.000530298
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 275 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=275
#   Best L¹ (quasi-uniform):   1.4193e+02
# │   Minimal L¹ mass:   1.4193e+02
# │   Status: DANGER ZONE
# │   Grain margin: 0.000517027
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 276 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=276
#   Best L¹ (quasi-uniform):   1.3841e+02
# │   Minimal L¹ mass:   1.3841e+02
# │   Status: DANGER ZONE
# │   Grain margin: 0.000503851
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 277 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=277
#   Best L¹ (quasi-uniform):   1.3501e+02
# │   Minimal L¹ mass:   1.3501e+02
# │   Status: DANGER ZONE
# │   Grain margin: 0.000490771
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 278 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=278
#   Best L¹ (quasi-uniform):   1.3170e+02
# │   Minimal L¹ mass:   1.3170e+02
# │   Status: DANGER ZONE
# │   Grain margin: 0.000477785
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 279 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=279
#   Best L¹ (quasi-uniform):   2.1912e+02
# │   Minimal L¹ mass:   2.1912e+02
# │   Status: DANGER ZONE
# │   Grain margin: 0.000464892
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 280 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=280
#   Best L¹ (quasi-uniform):   2.1225e+02
# │   Minimal L¹ mass:   2.1225e+02
# │   Status: DANGER ZONE
# │   Grain margin: 0.000452092
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 281 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=281
#   Best L¹ (quasi-uniform):   2.0564e+02
# │   Minimal L¹ mass:   2.0564e+02
# │   Status: DANGER ZONE
# │   Grain margin: 0.000439382
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 282 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=282
#   Best L¹ (quasi-uniform):   1.9927e+02
# │   Minimal L¹ mass:   1.9927e+02
# │   Status: DANGER ZONE
# │   Grain margin: 0.000426762
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 283 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=283
#   Best L¹ (quasi-uniform):   1.9315e+02
# │   Minimal L¹ mass:   1.9315e+02
# │   Status: DANGER ZONE
# │   Grain margin: 0.000414232
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 284 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=284
#   Best L¹ (quasi-uniform):   3.5157e+02
# │   Minimal L¹ mass:   3.5157e+02
# │   Status: DANGER ZONE
# │   Grain margin: 0.000401790
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 285 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=285
#   Best L¹ (quasi-uniform):   3.3952e+02
# │   Minimal L¹ mass:   3.3952e+02
# │   Status: DANGER ZONE
# │   Grain margin: 0.000389435
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 286 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=286
#   Best L¹ (quasi-uniform):   3.3107e+02
# │   Minimal L¹ mass:   3.3107e+02
# │   Status: DANGER ZONE
# │   Grain margin: 0.000377166
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 287 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=287
#   Best L¹ (quasi-uniform):   3.1841e+02
# │   Minimal L¹ mass:   3.1841e+02
# │   Status: DANGER ZONE
# │   Grain margin: 0.000364984
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 288 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=288
#   Best L¹ (quasi-uniform):   3.0632e+02
# │   Minimal L¹ mass:   3.0632e+02
# │   Status: DANGER ZONE
# │   Grain margin: 0.000352885
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 289 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=289
#   Best L¹ (quasi-uniform):   2.9476e+02
# │   Minimal L¹ mass:   2.9476e+02
# │   Status: DANGER ZONE
# │   Grain margin: 0.000340871
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 290 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=290
#   Best L¹ (quasi-uniform):   3.8525e+02
# │   Minimal L¹ mass:   3.8525e+02
# │   Status: DANGER ZONE
# │   Grain margin: 0.000328939
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 291 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=291
#   Best L¹ (quasi-uniform):   3.6705e+02
# │   Minimal L¹ mass:   3.6705e+02
# │   Status: DANGER ZONE
# │   Grain margin: 0.000317089
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 292 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=292
#   Best L¹ (quasi-uniform):   3.4984e+02
# │   Minimal L¹ mass:   3.4984e+02
# │   Status: DANGER ZONE
# │   Grain margin: 0.000305321
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 293 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=293
#   Best L¹ (quasi-uniform):   3.3354e+02
# │   Minimal L¹ mass:   3.3354e+02
# │   Status: DANGER ZONE
# │   Grain margin: 0.000293632
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 294 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=294
#   Best L¹ (quasi-uniform):   3.1811e+02
# │   Minimal L¹ mass:   3.1811e+02
# │   Status: DANGER ZONE
# │   Grain margin: 0.000282024
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 295 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=295
#   Best L¹ (quasi-uniform):   2.0933e+02
# │   Minimal L¹ mass:   2.0933e+02
# │   Status: DANGER ZONE
# │   Grain margin: 0.000270494
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 296 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=296
#   Best L¹ (quasi-uniform):   1.9887e+02
# │   Minimal L¹ mass:   1.9887e+02
# │   Status: DANGER ZONE
# │   Grain margin: 0.000259041
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 297 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=297
#   Best L¹ (quasi-uniform):   9.5918e+01
# │   Minimal L¹ mass:   9.5918e+01
# │   Status: DANGER ZONE
# │   Grain margin: 0.000247666
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 298 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=298
#   Best L¹ (quasi-uniform):   9.1625e+01
# │   Minimal L¹ mass:   9.1625e+01
# │   Status: DANGER ZONE
# │   Grain margin: 0.000236368
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 299 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=299
#   Best L¹ (quasi-uniform):   4.4378e+02
# │   Minimal L¹ mass:   4.4378e+02
# │   Status: DANGER ZONE
# │   Grain margin: 0.000225145
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 300 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=300
#   Best L¹ (quasi-uniform):   4.1483e+02
# │   Minimal L¹ mass:   4.1483e+02
# │   Status: DANGER ZONE
# │   Grain margin: 0.000213996
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 301 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=301
#   Best L¹ (quasi-uniform):   3.8795e+02
# │   Minimal L¹ mass:   3.8795e+02
# │   Status: DANGER ZONE
# │   Grain margin: 0.000202922
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 302 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=302
#   Best L¹ (quasi-uniform):   4.4610e+02
# │   Minimal L¹ mass:   4.4610e+02
# │   Status: DANGER ZONE
# │   Grain margin: 0.000191921
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 303 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=303
#   Best L¹ (quasi-uniform):   4.1089e+02
# │   Minimal L¹ mass:   4.1089e+02
# │   Status: DANGER ZONE
# │   Grain margin: 0.000180993
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 304 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=304
#   Best L¹ (quasi-uniform):   3.7866e+02
# │   Minimal L¹ mass:   3.7866e+02
# │   Status: DANGER ZONE
# │   Grain margin: 0.000170137
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 305 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=305
#   Best L¹ (quasi-uniform):   3.4916e+02
# │   Minimal L¹ mass:   3.4916e+02
# │   Status: DANGER ZONE
# │   Grain margin: 0.000159352
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 306 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=306
#   Best L¹ (quasi-uniform):   3.2213e+02
# │   Minimal L¹ mass:   3.2213e+02
# │   Status: DANGER ZONE
# │   Grain margin: 0.000148637
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 307 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=307
#   Best L¹ (quasi-uniform):   2.9735e+02
# │   Minimal L¹ mass:   2.9735e+02
# │   Status: DANGER ZONE
# │   Grain margin: 0.000137992
# └────────────────────────────────────────────────────────────────────────────────

# ┌── k = 308 ──────────────────────────────────────────────────────────────────────
#   → Switching to quasi-uniform verifier (full search intractable)

# Quick quasi-uniform verifier: k=308
#   Best L¹ (quasi-uniform):   1.3079e+03
# │   Minimal L¹ mass:   1.3079e+03
# │   Status: DANGER ZONE
# │   Grain margin: 0.000127416
# └────────────────────────────────────────────────────────────────────────────────

# !!! PRACTICAL RUPTURE THRESHOLD REACHED !!!

# ══════════════════════════════════════════════════════════════════════════════════════════
# FINAL SUMMARY & TERMINATION STATEMENT
# ══════════════════════════════════════════════════════════════════════════════════════════
# Last tested k: 308
# Last mass: 1.3079e+03

# At k=321: δ = 1/321 ≈ 0.0031153 < c_UFT-F = 0.0031193
# → Required gap falls below spectral grain → inevitable manifold rupture
# Lonely Runner Conjecture topologically terminated at k ≥ 321 in UFT-F framework

# Results saved to: lonely_runner_uftf_results.csv
# Total runtime: 317.3 minutes
# (base) brendanlynch@Brendans-Laptop lonelyRunner % python test3.py
