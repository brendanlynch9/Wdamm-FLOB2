import numpy as np
from scipy.linalg import eigh
import math

# Define parameters
N = 200  # grid points
L = 10.0  # domain [0, L]
dx = L / (N - 1)
x = np.linspace(0, L, N)

# S_grav from papers
S_grav = 0.04344799

# Define V_cloak(x)
def V_cloak(x_val):
    sum_v = 0.0
    for n in range(2, 25):  # start from 2
        cos_term = math.cos(2 * np.pi * n / 24)
        if abs(cos_term) > 1e-10:
            a_n = S_grav * cos_term / math.log(1 + abs(cos_term))
            term = a_n * (n ** (-abs(x_val))) / math.log(n)
            sum_v += term
        # else skip, term=0
    return sum_v

V = np.array([V_cloak(xi) for xi in x])

# Finite difference for -d2/dx2: tridiag(-1/dx2, 2/dx2, -1/dx2)
kinetic = np.diag(2 * np.ones(N)) + np.diag(-np.ones(N-1), 1) + np.diag(-np.ones(N-1), -1)
kinetic /= dx**2

# Hamiltonian H = kinetic + diag(V)
H = kinetic + np.diag(V)

# Compute lowest 5 eigenvalues (self-adjoint, real symmetric)
eigvals = eigh(H, eigvals_only=True)[0:5]

print("Grid size N:", N)
print("Domain L:", L)
print("dx:", dx)
print("Sample V at x=0:", V[0])
print("Sample V at x=L/2:", V[int(N/2)])
print("Lowest eigenvalues:", eigvals)

# the output was: 
# (base) brendanlynch@Mac quantum % python base24test4.py
# Grid size N: 200
# Domain L: 10.0
# dx: 0.05025125628140704
# Sample V at x=0: 0.061526220266661054
# Sample V at x=L/2: 0.002924336340753696
# Lowest eigenvalues: [0.1035597  0.39947075 0.88510914 1.56255185 2.43262202]
# (base) brendanlynch@Mac quantum % 