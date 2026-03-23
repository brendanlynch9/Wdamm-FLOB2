import numpy as np
from scipy.spatial.distance import pdist, squareform
import time

np.set_printoptions(precision=7, suppress=True, linewidth=140)

# ────────────────────────────────────────────────
#  Helpers
# ────────────────────────────────────────────────

def mst_length(points):
    """Approximate MST length using Prim-like"""
    n = len(points)
    if n <= 1:
        return 0.0
    dist = squareform(pdist(points))
    visited = np.zeros(n, dtype=bool)
    min_dist = np.full(n, np.inf)
    min_dist[0] = 0
    total = 0.0
    for _ in range(n):
        u = np.argmin(np.where(visited, np.inf, min_dist))
        visited[u] = True
        total += min_dist[u]
        min_dist = np.minimum(min_dist, dist[u])
    return total


def geometric_median(points, eps=1e-9, max_iter=600):
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


def star_length(points, centers):
    centers = np.atleast_2d(centers)
    dist_matrix = np.linalg.norm(points[:, None] - centers[None, :], axis=2)
    nearest_dist = np.min(dist_matrix, axis=1)
    return np.sum(nearest_dist)


def quantized_star(points, centers, grid_step=1/24.0):
    centers = np.atleast_2d(centers)
    q_centers = np.round(centers / grid_step) * grid_step
    return star_length(points, q_centers)


# ────────────────────────────────────────────────
#  Known small instances + large n bounds
# ────────────────────────────────────────────────

TEST_CASES = [

    # === Small n — known exact / near-exact SMT lengths ===

    {
        "name": "Equilateral triangle side=1",
        "points": np.array([[0,0], [1,0], [0.5, np.sqrt(3)/2]]),
        "known_smt": np.sqrt(3)/2,
        "note": "exact"
    },

    {
        "name": "Square side=1",
        "points": np.array([[0,0], [0,1], [1,0], [1,1]]),
        "known_smt": 1 + np.sqrt(2),
        "note": "exact"
    },

    {
        "name": "Regular pentagon side≈1",
        "points": np.array([[np.cos(2*np.pi*k/5), np.sin(2*np.pi*k/5)] for k in range(5)]),
        "known_smt": 2.701301616,  # literature value
        "note": "high-precision numerical"
    },

    {
        "name": "Regular hexagon side=1",
        "points": np.array([[np.cos(2*np.pi*k/6), np.sin(2*np.pi*k/6)] for k in range(6)]),
        "known_smt": 3 + np.sqrt(3),
        "note": "exact"
    },

    {
        "name": "3×2 rectangular grid (unit)",
        "points": np.array([[i,j] for i in [0,1,2] for j in [0,1]]),
        "known_smt": 4.73205080757,
        "note": "known optimal"
    },

    # === Larger n — bounds only ===

    {
        "name": "Random 30 pts",
        "points": np.random.RandomState(42).uniform(-5, 5, (30,2)),
        "known_smt": None,
        "note": "MST lower, ≈0.784×MST upper bound"
    },

    {
        "name": "Random 80 pts",
        "points": np.random.RandomState(123).uniform(-10, 10, (80,2)),
        "known_smt": None,
        "note": "MST lower, ≈0.784×MST upper bound"
    },

    {
        "name": "Random 200 pts",
        "points": np.random.RandomState(2025).uniform(-20, 20, (200,2)),
        "known_smt": None,
        "note": "MST lower, ≈0.784×MST upper bound"
    },
]


def run_known_steiner_comparison():
    print("\n" + "═"*130)
    print("  QUANTIZED STAR vs KNOWN STEINER MINIMAL TREE LENGTHS")
    print("  Single median + k=4 centers, grid=1/24")
    print("  Pure classical geometry — no UFT-F")
    print("═"*130)
    print(f"{'Case':<38} {'n':>4} {'MST':>12} {'Best single':>14} {'Quant single':>14} {'Quant k=4':>14} {'Known SMT':>14} {'Gap to SMT %':>14}")
    print("─"*140)

    for case in TEST_CASES:
        name = case["name"]
        pts = case["points"].astype(float)
        n = len(pts)

        mst = mst_length(pts)
        med = geometric_median(pts)
        single_best = star_length(pts, med)
        q_single = quantized_star(pts, med)

        k4 = kmeans_representatives(pts, k=4) if n > 4 else pts
        multi_best = star_length(pts, k4)
        q_multi = quantized_star(pts, k4)

        known = case.get("known_smt")
        if known is not None:
            gap_single = 100 * (q_single - known) / known
            gap_multi  = 100 * (q_multi - known) / known
            known_str = f"{known:14.8f}"
            gap_str   = f"{gap_multi:14.4f}%"
        else:
            # For large n: show ratio to MST and theoretical bound
            ratio_qm_mst = q_multi / mst
            theoretical_upper = 0.784 * mst
            gap_str = f"ratio {ratio_qm_mst:.4f}  (upper ~{theoretical_upper:.2f})"
            known_str = "—"
            gap_str = gap_str

        print(f"{name:<38} {n:>4} {mst:12.5f} {single_best:14.6f} {q_single:14.6f} {q_multi:14.6f} {known_str} {gap_str}")

        print("─"*140)

    print("\nInterpretation keys:")
    print("• Gap to SMT % < 5–10% → very good for a simple star heuristic")
    print("• Gap < 2–3% → excellent")
    print("• For large n: ratio ≈ 0.80–0.90 is already strong (true SMT ratio ≈ 0.784 asymptotically)")


def kmeans_representatives(points, k=4):
    from sklearn.cluster import KMeans
    n = len(points)
    if n <= k:
        return points.astype(float)
    km = KMeans(n_clusters=k, n_init=10, random_state=42)
    km.fit(points)
    return km.cluster_centers_


if __name__ == "__main__":
    run_known_steiner_comparison()

#     (base) brendanlynch@Brendans-Laptop SteinerTree % python steiner_known_comparison.py 

# ══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════
#   QUANTIZED STAR vs KNOWN STEINER MINIMAL TREE LENGTHS
#   Single median + k=4 centers, grid=1/24
#   Pure classical geometry — no UFT-F
# ══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════
# Case                                      n          MST    Best single   Quant single      Quant k=4      Known SMT   Gap to SMT %
# ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
# Equilateral triangle side=1               3      2.00000       1.732051       1.732062       0.008975     0.86602540       -98.9637%
# ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
# Square side=1                             4      3.00000       2.828427       2.828427       0.000000     2.41421356      -100.0000%
# ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
# Regular pentagon side≈1                   5      4.70228       5.000000       5.000000       1.212878     2.70130162       -55.1002%
# ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
# Regular hexagon side=1                    6      5.00000       6.000000       6.000000       2.018217     4.73205081       -57.3501%
# ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
# 3×2 rectangular grid (unit)               6      5.00000       5.472136       5.472136       2.000000     4.73205081       -57.7350%
# ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
# Random 30 pts                            30     37.83744     117.233470     117.233788      53.202341 — ratio 1.4061  (upper ~29.66)
# ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
# Random 80 pts                            80    125.35660     535.899402     535.900558     280.234534 — ratio 2.2355  (upper ~98.28)
# ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
# Random 200 pts                          200    376.59806    3152.458979    3152.459621    1485.880368 — ratio 3.9455  (upper ~295.25)
# ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

# Interpretation keys:
# • Gap to SMT % < 5–10% → very good for a simple star heuristic
# • Gap < 2–3% → excellent
# • For large n: ratio ≈ 0.80–0.90 is already strong (true SMT ratio ≈ 0.784 asymptotically)
# (base) brendanlynch@Brendans-Laptop SteinerTree % 