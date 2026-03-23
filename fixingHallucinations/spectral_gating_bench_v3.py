# spectral_gating_bench_v3.py
import time, random, json
import numpy as np
from scipy.stats import pearsonr, spearmanr
from spectral_graphs import compute_lambda2

def synthetic_hiddenstate_eigenvalue(token_ids):
    x = np.array(token_ids, dtype=float)
    return 1.0 / (1.0 + np.var(x) + 1e-12)

def bench_variant(variant, num_samples=2000, token_len=16, seed=123):
    random.seed(seed)
    times = []
    lam2s = []
    eig_surrs = []
    ns = set()

    # warmup to avoid first-call overhead
    for _ in range(200):
        tokens = [random.randint(1,1000) for _ in range(token_len)]
        n = int(np.floor(np.linalg.norm(tokens)**2)) % 24
        _ = compute_lambda2(n, variant=variant)

    for _ in range(num_samples):
        tokens = [random.randint(1,1000) for _ in range(token_len)]
        x = np.array(tokens, dtype=float)
        n = int(np.floor(np.linalg.norm(x)**2)) % 24
        ns.add(n)

        t0 = time.perf_counter()
        lam2 = compute_lambda2(n, variant=variant)
        t1 = time.perf_counter()

        times.append((t1-t0)*1e6)
        lam2s.append(lam2)
        eig_surrs.append(synthetic_hiddenstate_eigenvalue(tokens))

    lam2s = np.array(lam2s)
    eig_surrs = np.array(eig_surrs)
    times = np.array(times)

    # correlations if not constant
    const_flag = (np.max(lam2s) - np.min(lam2s)) < 1e-9
    if const_flag:
        pear_r = float('nan'); pear_p = float('nan')
        spear_r = float('nan'); spear_p = float('nan')
    else:
        pear_r, pear_p = pearsonr(lam2s, eig_surrs)
        spear_r, spear_p = spearmanr(lam2s, eig_surrs)

    return {
        "variant": variant,
        "n_unique": len(ns),
        "time_mean_us": float(np.mean(times)),
        "time_median_us": float(np.median(times)),
        "time_p95_us": float(np.percentile(times,95)),
        "time_std_us": float(np.std(times)),
        "lam2_mean": float(np.mean(lam2s)),
        "lam2_std": float(np.std(lam2s)),
        "lam2_min": float(np.min(lam2s)),
        "lam2_max": float(np.max(lam2s)),
        "pearson_r": float(pear_r) if not np.isnan(pear_r) else "NaN",
        "pearson_p": float(pear_p) if not np.isnan(pear_p) else "NaN",
        "spearman_r": float(spear_r) if not np.isnan(spear_r) else "NaN",
        "spearman_p": float(spear_p) if not np.isnan(spear_p) else "NaN"
    }

if __name__ == "__main__":
    results = {}
    for v in ["angular","residue"]:
        results[v] = bench_variant(v, num_samples=2000, token_len=16, seed=42)
    print(json.dumps(results, indent=2))

# the terminal output was:
# (base) brendanlynch@Brendans-Laptop fixingHallucinations % python spectral_gating_bench_v3.py
# {
#   "angular": {
#     "variant": "angular",
#     "n_unique": 24,
#     "time_mean_us": 209.98348790453747,
#     "time_median_us": 206.91700046882033,
#     "time_p95_us": 230.83605483407155,
#     "time_std_us": 165.77779344303832,
#     "lam2_mean": 6.15798031053444,
#     "lam2_std": 4.60000922935808,
#     "lam2_min": 2.9430355293715387,
#     "lam2_max": 21.746254627672318,
#     "pearson_r": 0.011350354308541168,
#     "pearson_p": 0.6119427439374612,
#     "spearman_r": -0.018519625897555396,
#     "spearman_p": 0.40779734213696983
#   },
#   "residue": {
#     "variant": "residue",
#     "n_unique": 24,
#     "time_mean_us": 217.84422446216922,
#     "time_median_us": 216.79099882021546,
#     "time_p95_us": 244.08811586908996,
#     "time_std_us": 10.069301388876136,
#     "lam2_mean": 0.2123186917412039,
#     "lam2_std": 0.14817818934049407,
#     "lam2_min": 0.005407704827514242,
#     "lam2_max": 0.5363370502546813,
#     "pearson_r": 0.009185184105952425,
#     "pearson_p": 0.6814203015388305,
#     "spearman_r": -0.002891663153611444,
#     "spearman_p": 0.897168909254036
#   }
# }
# (base) brendanlynch@Brendans-Laptop fixingHallucinations % 
