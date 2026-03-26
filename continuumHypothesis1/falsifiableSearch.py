import networkx as nx
from pulp import LpProblem, LpMinimize, LpVariable, lpSum, LpBinary, PULP_CBC_CMD, constants
import itertools
import math
from functools import lru_cache

# -------------------------------
# Core Functions
# -------------------------------

@lru_cache(maxsize=10)
def get_primes(n):
    """Cached prime generator"""
    primes = []
    chk = 2
    while len(primes) < n:
        is_prime = True
        for i in range(2, int(math.sqrt(chk)) + 1):
            if chk % i == 0:
                is_prime = False
                break
        if is_prime:
            primes.append(chk)
        chk += 1
    return tuple(primes)  # tuple for caching

def build_graph(n_primes, metric):
    """Build the prime-overlap graph at given metric"""
    primes = get_primes(n_primes)
    G = nx.Graph()
    G.add_nodes_from(primes)
    edges = 0
    for i in range(len(primes)):
        for j in range(i + 1, len(primes)):
            dist_eff = abs(primes[i] - primes[j]) / metric
            if math.exp(-dist_eff / n_primes) > 0.4146:
                G.add_edge(primes[i], primes[j])
                edges += 1
    return G, edges

def is_3_pageable(G, time_limit=60):
    """ILP check if book thickness <=3"""
    if G.number_of_edges() == 0:
        return True
    nodes = list(G.nodes())
    edges_list = [tuple(sorted(e)) for e in G.edges()]
    m = len(edges_list)
    
    prob = LpProblem("Book_Thickness_3", LpMinimize)
    y = LpVariable.dicts("y", (nodes, nodes), cat=LpBinary)
    x = LpVariable.dicts("x", (range(m), range(3)), cat=LpBinary)  # pages 0,1,2

    # Ordering constraints (transitive tournament)
    for u, v in itertools.combinations(nodes, 2):
        prob += y[u][v] + y[v][u] == 1
        for w in nodes:
            if u != w and v != w:
                prob += y[u][v] + y[v][w] - 1 <= y[u][w]

    # Each edge on exactly one page
    for i in range(m):
        prob += lpSum(x[i][p] for p in range(3)) == 1

    # Non-crossing per page (simplified crossing detection)
    for i in range(m):
        for j in range(i + 1, m):
            u, v = edges_list[i]
            a, b = edges_list[j]
            cross = LpVariable(f"c_{i}_{j}", cat=LpBinary)
            # Four possible crossing configurations
            prob += y[u][a] + y[a][v] + y[v][b] - 2 <= cross
            prob += y[a][u] + y[u][b] + y[b][v] - 2 <= cross
            prob += y[u][b] + y[b][v] + y[v][a] - 2 <= cross
            prob += y[b][u] + y[u][a] + y[a][v] - 2 <= cross
            for p in range(3):
                prob += x[i][p] + x[j][p] <= 1 + (1 - cross)

    status = prob.solve(PULP_CBC_CMD(msg=0, timeLimit=time_limit))
    return status == constants.LpStatusOptimal

def find_critical_metric(n_primes, low=0.70, high=1.00, precision=0.0005, max_iter=40):
    """Binary search for critical M where 3-page fails"""
    for _ in range(max_iter):
        mid = (low + high) / 2
        G, _ = build_graph(n_primes, mid)
        if is_3_pageable(G):
            high = mid  # still stable → try tighter squeeze
        else:
            low = mid   # fractured → need looser
    # Final value is the last stable M (just above fracture)
    return high

# -------------------------------
# Main Analysis Pipeline
# -------------------------------

def run_fracture_invariant_analysis(ns=[25, 31, 37, 41], prec_M=0.0005):
    results = []
    print("=== UFT-F Fracture Invariant Search ===")
    print(f"{'N':>4} | {'Crit M':>8} | {'Edges':>6} | {'Phi':>10} | {'Alpha':>8} | {'P=Phi*(1-M)':>12} | {'P=Phi*(1-M)^2':>14} | {'Leak Est %':>10}")
    print("-" * 80)

    for n in ns:
        crit_M = find_critical_metric(n, precision=prec_M)
        G, edges = build_graph(n, crit_M)
        phi = edges / (crit_M ** 2) if crit_M > 0 else 0
        alpha = phi / (n ** 2) if n > 0 else 0
        
        # Candidate invariants (critical pressures)
        p1 = phi * (1 - crit_M)                       # linear stress
        p2 = phi * (1 - crit_M)**2                     # quadratic (energy-like)
        # Could add more: phi / crit_M, phi * math.log(1/(1-crit_M)), etc.

        # Rough gauge leak estimate:
        # Assume max edges per page ~ 3*(n-1) for near-planar; excess needs offload
        max_per_page_approx = 3 * (n - 1)
        excess_edges = max(0, edges - 3 * max_per_page_approx)
        leak_frac = excess_edges / edges if edges > 0 else 0
        leak_pct = 100 * leak_frac

        results.append({
            'n': n, 'M': crit_M, 'edges': edges, 'phi': phi, 'alpha': alpha,
            'p1': p1, 'p2': p2, 'leak_pct': leak_pct
        })

        print(f"{n:4d} | {crit_M:8.4f} | {edges:6d} | {phi:10.2f} | {alpha:8.4f} | {p1:12.2f} | {p2:14.3f} | {leak_pct:10.1f}")

    # Invariant check
    print("\n=== Invariant Stability Check ===")
    p1_vals = [r['p1'] for r in results]
    p2_vals = [r['p2'] for r in results]
    print(f"P = Φ(1-M)   mean={sum(p1_vals)/len(p1_vals):.2f}  std={math.sqrt(sum((x-sum(p1_vals)/len(p1_vals))**2 for x in p1_vals)/len(p1_vals)):.2f}")
    print(f"P = Φ(1-M)^2 mean={sum(p2_vals)/len(p2_vals):.3f}  std={math.sqrt(sum((x-sum(p2_vals)/len(p2_vals))**2 for x in p2_vals)/len(p2_vals)):.3f}")
    print("Lower std → better invariant. If std << mean, strong candidate.")

    print("\nAlpha trend:", [f"{r['alpha']:.4f}" for r in results])
    print("Gauge leak required grows with N → UFT-F offload necessity ↑")

if __name__ == "__main__":
    # Run on your clusters (add more N as desired)
    run_fracture_invariant_analysis(ns=[25, 31, 37, 41], prec_M=0.0005)


#     (base) brendanlynch@Brendans-Laptop medicine % python falsifiableSearch.py
# === UFT-F Fracture Invariant Search ===
#    N |   Crit M |  Edges |        Phi |    Alpha |  P=Phi*(1-M) |  P=Phi*(1-M)^2 | Leak Est %
# --------------------------------------------------------------------------------
#   25 |   0.8178 |     99 |     148.04 |   0.2369 |        26.98 |          4.916 |        0.0
#   31 |   1.0000 |    166 |     166.00 |   0.1727 |         0.00 |          0.000 |        0.0
# ^CTraceback (most recent call last):
#   File "/Users/brendanlynch/Desktop/zzzzzCompletePDFs/medicine/falsifiableSearch.py", line 141, in <module>
#     run_fracture_invariant_analysis(ns=[25, 31, 37, 41], prec_M=0.0005)
#   File "/Users/brendanlynch/Desktop/zzzzzCompletePDFs/medicine/falsifiableSearch.py", line 104, in run_fracture_invariant_analysis
#     crit_M = find_critical_metric(n, precision=prec_M)
#              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
#   File "/Users/brendanlynch/Desktop/zzzzzCompletePDFs/medicine/falsifiableSearch.py", line 86, in find_critical_metric
#     if is_3_pageable(G):
#        ^^^^^^^^^^^^^^^^
#   File "/Users/brendanlynch/Desktop/zzzzzCompletePDFs/medicine/falsifiableSearch.py", line 78, in is_3_pageable
#     status = prob.solve(PULP_CBC_CMD(msg=0, timeLimit=time_limit))
#              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
#   File "/Users/brendanlynch/miniconda3/lib/python3.12/site-packages/pulp/pulp.py", line 2092, in solve
#     status = solver.actualSolve(self, **kwargs)
#              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
#   File "/Users/brendanlynch/miniconda3/lib/python3.12/site-packages/pulp/apis/coin_api.py", line 144, in actualSolve
#     return self.solve_CBC(lp, **kwargs)
#            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
#   File "/Users/brendanlynch/miniconda3/lib/python3.12/site-packages/pulp/apis/coin_api.py", line 222, in solve_CBC
#     if cbc.wait() != 0:
#        ^^^^^^^^^^
#   File "/Users/brendanlynch/miniconda3/lib/python3.12/subprocess.py", line 1264, in wait
#     return self._wait(timeout=timeout)
#            ^^^^^^^^^^^^^^^^^^^^^^^^^^^
#   File "/Users/brendanlynch/miniconda3/lib/python3.12/subprocess.py", line 2051, in _wait
#     (pid, sts) = self._try_wait(0)
#                  ^^^^^^^^^^^^^^^^^
#   File "/Users/brendanlynch/miniconda3/lib/python3.12/subprocess.py", line 2009, in _try_wait
#     (pid, sts) = os.waitpid(self.pid, wait_flags)
#                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
# KeyboardInterrupt

# (base) brendanlynch@Brendans-Laptop medicine % 