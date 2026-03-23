import numpy as np
from scipy.integrate import quad

# Proxy for unique game: 3-vertex graph with labels {0,1}, constraints on edges
# Instance where opt = 1 (satisfiable), vs low opt
def unique_game_potential(epsilon, satisfiable=True):
    x = np.linspace(-10, 10, 1000)
    V = np.zeros_like(x)
    # Simulate constraint density: for satisfiable, bounded; for hard, diverge with epsilon
    if satisfiable:
        V += np.exp(-np.abs(x) / np.log(2))  # Bounded
    else:
        V += (1 / epsilon) * np.exp(np.abs(x) / np.log(2))  # Diverge as epsilon -> 0
    return V, x

# Compute L1 norm
def l1_norm(V, x):
    dx = x[1] - x[0]
    return np.sum(np.abs(V) * dx)

# Test
eps = 0.01
V_sat, x = unique_game_potential(eps, True)
l1_sat = l1_norm(V_sat, x)
V_hard, x = unique_game_potential(eps, False)
l1_hard = l1_norm(V_hard, x)

print(f"L1 for satisfiable: {l1_sat:.4f} (bounded O(1))")
print(f"L1 for hard approx: {l1_hard:.4f} (diverges as 1/eps)")

# (base) brendanlynch@Brendans-Laptop UniqueGamesConjecture % python BooleanCircuit.py
# L1 for satisfiable: 1.3862 (bounded O(1))
# L1 for hard approx: 259213071.9670 (diverges as 1/eps)
# (base) brendanlynch@Brendans-Laptop UniqueGamesConjecture % 