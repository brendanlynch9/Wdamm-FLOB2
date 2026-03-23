import numpy as np
from scipy.optimize import minimize
import time

np.set_printoptions(precision=7, suppress=True, linewidth=140)

# ────────────────────────────────────────────────
#  Helper functions
# ────────────────────────────────────────────────

def mst_length(points: np.ndarray) -> float:
    """Very basic MST length (Prim-like)"""
    n = len(points)
    if n <= 1:
        return 0.0
    dist = np.linalg.norm(points[:, None] - points[None, :], axis=-1)
    visited = np.zeros(n, dtype=bool)
    min_dist = np.full(n, np.inf)
    min_dist[0] = 0
    total = 0.0

    for _ in range(n):
        u = np.argmin(np.where(visited, np.inf, min_dist))
        visited[u] = True
        total += min_dist[u]
        for v in range(n):
            if not visited[v] and dist[u, v] < min_dist[v]:
                min_dist[v] = dist[u, v]
    return total


def geometric_median(points: np.ndarray, eps=1e-10, max_iter=300) -> np.ndarray:
    """Improved Weiszfeld-style geometric median approximation"""
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


def total_length_from_point(points: np.ndarray, pt: np.ndarray) -> float:
    return np.sum(np.linalg.norm(points - pt, axis=1))


# ────────────────────────────────────────────────
#  Test cases — including several pathological ones
# ────────────────────────────────────────────────

TEST_CASES = [
    {"name": "Equilateral triangle side 2", "points": np.array([[0.,0.], [2.,0.], [1., np.sqrt(3)]])},

    {"name": "Square 1×1", "points": np.array([[0,0], [0,1], [1,0], [1,1]], dtype=float)},

    {"name": "Near-collinear 10 pts", "points": np.array([
        [0, 0], [1, 0.004], [2, -0.003], [3, 0.006], [4, -0.002],
        [5, 0.005], [6, -0.004], [7, 0.003], [8, -0.005], [9, 0]
    ])},

    {"name": "Regular pentagon", "points": np.array([
        [np.cos(2*np.pi*k/5), np.sin(2*np.pi*k/5)] for k in range(5)
    ]) * 3.0},

    {"name": "Two tight clusters far apart (12 pts)", "points": np.concatenate([
        np.random.RandomState(41).normal(0, 0.08, (6,2)),
        np.random.RandomState(42).normal(10, 0.08, (6,2))
    ])},

    {"name": "Almost degenerate rectangle + outlier (15 pts)", "points": np.concatenate([
        np.array([[0,0], [0,0.01], [4,0], [4,0.01]]),
        np.random.RandomState(55).normal([2, 5], 0.15, (11,2))
    ])},

    {"name": "Random uniform 20 pts", "points": np.random.RandomState(123).uniform(-5, 5, (20,2))},

    {"name": "Random uniform 30 pts", "points": np.random.RandomState(2025).uniform(-6, 6, (30,2))},
]

GRID_STEPS = [1/8, 1/12, 1/16, 1/20, 1/24, 1/32]
GRID_NAMES = ["1/8", "1/12", "1/16", "1/20", "1/24", "1/32"]


def run_all_tests():
    print("\n" + "═"*110)
    print("  MULTI-GRID QUANTIZATION COMPARISON — PURE CLASSICAL GEOMETRY")
    print("  Geometric median → round to grid → total star length from that point")
    print("  No UFT-F, no spectral stuff — just numbers")
    print("═"*110)
    print(f"{'Case':<32} {'n':>4} {'MST':>10} {'Best median':>14}  ", end="")
    for gname in GRID_NAMES:
        print(f"{gname:>12}", end="")
    print("   worst grid error %")
    print("─"*140)

    for case in TEST_CASES:
        name = case["name"]
        pts = case["points"]
        n = len(pts)

        start = time.time()
        best_pt = geometric_median(pts)
        best_len = total_length_from_point(pts, best_pt)
        mst = mst_length(pts)
        t_median = time.time() - start

        grid_results = []
        errors_pct = []

        for step in GRID_STEPS:
            q_pt = np.round(best_pt / step) * step
            q_len = total_length_from_point(pts, q_pt)
            rel_err_pct = 100.0 * (q_len - best_len) / best_len if best_len > 1e-8 else 0.0
            grid_results.append(q_len)
            errors_pct.append(rel_err_pct)

        worst_error = max(errors_pct) if errors_pct else 0.0

        print(f"{name:<32} {n:>4} {mst:10.5f} {best_len:14.7f}  ", end="")
        for ql, ep in zip(grid_results, errors_pct):
            print(f"{ql:12.7f} ", end="")
        print(f"  {worst_error:6.3f}%")

        # Extra line with error percentages
        print(" " * 70 + "errors % →", "  ".join(f"{e:6.3f}%" for e in errors_pct))

        print("─"*140)

    print("\nQuick summary observations:")
    print("• Lower grid step (finer grid) → almost always lower error (expected)")
    print("• 1/24 vs 1/32 — how much better is 1/32 really?")
    print("• Look for cases where error stays surprisingly small even on coarse grids")
    print("• Pathological cases (clusters, near-collinear, pentagon) are most revealing")

if __name__ == "__main__":
    run_all_tests()

#     (base) brendanlynch@Brendans-Laptop SteinerTree % python falsifiable2.py

# ══════════════════════════════════════════════════════════════════════════════════════════════════════════════
#   MULTI-GRID QUANTIZATION COMPARISON — PURE CLASSICAL GEOMETRY
#   Geometric median → round to grid → total star length from that point
#   No UFT-F, no spectral stuff — just numbers
# ══════════════════════════════════════════════════════════════════════════════════════════════════════════════
# Case                                n        MST    Best median           1/8        1/12        1/16        1/20        1/24        1/32   worst grid error %
# ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
# Equilateral triangle side 2         3    4.00000      3.4641016     3.4655461    3.4641248    3.4642458    3.4644316    3.4641248    3.4642458    0.042%
#                                                                       errors % →  0.042%   0.001%   0.004%   0.010%   0.001%   0.004%
# ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
# Square 1×1                          4    3.00000      2.8284271     2.8284271    2.8284271    2.8284271    2.8284271    2.8284271    2.8284271    0.000%
#                                                                       errors % →  0.000%   0.000%   0.000%   0.000%   0.000%   0.000%
# ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
# Near-collinear 10 pts              10    9.00024     25.0000523    25.0000558   25.0000558   25.0000558   25.0000558   25.0000558   25.0000558    0.000%
#                                                                       errors % →  0.000%   0.000%   0.000%   0.000%   0.000%   0.000%
# ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
# Regular pentagon                    5   14.10685     15.0000000    15.0000000   15.0000000   15.0000000   15.0000000   15.0000000   15.0000000    0.000%
#                                                                       errors % →  0.000%   0.000%   0.000%   0.000%   0.000%   0.000%
# ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
# Two tight clusters far apart (12 pts)   12   14.70319     85.3043238    85.3043488   85.3043488   85.3043488   85.3043488   85.3043488   85.3043488    0.000%
#                                                                       errors % →  0.000%   0.000%   0.000%   0.000%   0.000%   0.000%
# ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
# Almost degenerate rectangle + outlier (15 pts)   15   10.28939     23.5958531    23.6584237   23.6212162   23.6364009   23.6276550   23.6051103   23.5970478    0.265%
#                                                                       errors % →  0.265%   0.107%   0.172%   0.135%   0.039%   0.005%
# ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
# Random uniform 20 pts              20   27.75127     58.8601565    58.8601782   58.8686826   58.8601782   58.8630180   58.8601782   58.8601782    0.014%
#                                                                       errors % →  0.000%   0.014%   0.000%   0.005%   0.000%   0.000%
# ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
# Random uniform 30 pts              30   46.49160    149.9610835   149.9694175  149.9628172  149.9620974  149.9620285  149.9611738  149.9617873    0.006%
#                                                                       errors % →  0.006%   0.001%   0.001%   0.001%   0.000%   0.000%
# ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

# Quick summary observations:
# • Lower grid step (finer grid) → almost always lower error (expected)
# • 1/24 vs 1/32 — how much better is 1/32 really?
# • Look for cases where error stays surprisingly small even on coarse grids
# • Pathological cases (clusters, near-collinear, pentagon) are most revealing
# (base) brendanlynch@Brendans-Laptop SteinerTree % 


# Key observations (standard geometry only)

# The quantization error is shockingly small in almost every case
# For n = 20 and n = 30 random points → error ≤ 0.014% even on coarse grids
# For 1/24 grid specifically: error is 0.000% – 0.039% across all tested cases
# → This is orders of magnitude better than one would naively expect from rounding each coordinate to the nearest multiple of ≈0.0417.

# Pathological / degenerate cases behave surprisingly well
# Near-collinear 10 points → 0.000% error on every grid
# Two tight clusters far apart → 0.000% error
# Regular pentagon → 0.000% error
# These are exactly the kinds of configurations where one would expect rounding to cause visible damage — and yet it doesn’t (or the damage is below numerical precision).

# The only case with meaningful error is the “almost degenerate rectangle + outlier”
# Here the geometric median is in a somewhat sensitive position
# 1/8 grid pays 0.265%
# 1/24 grid pays only 0.039%
# 1/32 grid pays 0.005%
# → Even in this relatively sensitive case, the 1/24 grid is already very close to excellent.

# Finer grid is better — but the gains are diminishing
# 1/24 is already very close to 1/32 in almost every case.
# Going from 1/24 to 1/32 gives almost no further improvement in most instances → suggests that ~1/24 resolution is already near the “knee” of the error-vs-grid-size curve for these point counts.
# 30-point random case is particularly striking
# Best continuous length ≈ 149.961
# After 1/24 quantization → length increase ≤ 0.00009 (i.e. relative error ~0.00006%)
# That is an extraordinarily small perturbation for rounding 2 coordinates of a single point to 1/24 resolution.

# A very surprising empirical observation:
# For many sets of points in the plane (including degenerate, clustered, symmetric and random configurations up to n=30), the geometric median rounded to the nearest point on a 1/24 grid produces a star connecting all terminals whose total length is extremely close (often within 0.001%–0.04%) to the length obtained from the exact geometric median.
# This is not what most people would have predicted before running the experiment.