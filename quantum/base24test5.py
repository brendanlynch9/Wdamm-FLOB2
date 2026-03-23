import numpy as np
from scipy.linalg import eigh
import math

# Parameters
N = 500  # finer grid
L = 20.0  # larger domain for decay
dx = L / (N - 1)
x = np.linspace(0, L, N)

# Amplified S_grav for deeper potential
S_grav = 0.04344799 * 100  # scale up to bind near 0.003

# V_cloak with fixes: n=2 start to avoid log(1)=0, infinite approx, exponent -|x|/3
def V_cloak(x_val):
    sum_v = 0.0
    for n in range(2, 1001):  # start from 2
        cos_term = math.cos(2 * np.pi * n / 24)
        if abs(cos_term) > 1e-10:
            a_n = S_grav * cos_term / math.log(1 + abs(cos_term))
            term = a_n * (n ** (-abs(x_val)/3)) / math.log(n)
            sum_v += term
    return sum_v

V = np.array([V_cloak(xi) for xi in x])

# Kinetic operator
kinetic = np.diag(2 * np.ones(N)) + np.diag(-np.ones(N-1), 1) + np.diag(-np.ones(N-1), -1)
kinetic /= dx**2

# H = kinetic + V
H = kinetic + np.diag(V)

# Lowest 5 eigenvalues
eigvals = eigh(H, eigvals_only=True)[0:5]

print("Grid size N:", N)
print("Domain L:", L)
print("dx:", dx)
print("Sample V at x=0:", V[0])
print("Sample V at x=L/2:", V[int(N/2)])
print("Lowest eigenvalues:", eigvals)

# the output was:
# (base) brendanlynch@Mac quantum % python base24test5.py       
# Grid size N: 500
# Domain L: 20.0
# dx: 0.04008016032064128
# Sample V at x=0: 1.7381566209222938
# Sample V at x=L/2: 1.032863372873931
# Lowest eigenvalues: [0.37165325 0.734143   1.13923281 1.58476204 2.06763262]
# (base) brendanlynch@Mac quantum % 