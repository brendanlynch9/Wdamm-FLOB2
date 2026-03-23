import numpy as np
import qutip as qt
import math
import matplotlib.pyplot as plt
from scipy.linalg import eigh

# Params
N = 100
L = 20.0
dx = L / (N - 1)
x = np.linspace(0, L, N)
S_grav = 0.04344799 * 100

# V_cloak with residue filter
def V_cloak(x_val):
    sum_v = 0.0
    residues = {1,5,7,11,13,17,19,23}
    for n in range(2, 1001):
        res = n % 24
        if res in residues:
            cos_term = math.cos(2 * np.pi * n / 24)
            if abs(cos_term) > 1e-10:
                a_n = S_grav * cos_term / math.log(1 + abs(cos_term))
                term = a_n * (n ** (-abs(x_val)/3)) / math.log(n)
                sum_v += term
    return sum_v

V = np.array([V_cloak(xi) for xi in x])

# Operators
position = qt.position(N)
momentum = qt.momentum(N)
H = (momentum**2 / 2) + qt.qdiags(V, 0)

# Initial psi0
psi0 = qt.basis(N, 0) * 0.0
for i in range(N):
    psi0 += math.exp(-((x[i] - 5)**2) / 2) * qt.basis(N, i)
psi0 = psi0.unit()

# Times
times = np.linspace(0, 10, 50)

# Unitary
result = qt.mesolve(H, psi0, times)
rho = result.states[-1] * result.states[-1].dag()
entropy_final = qt.entropy_vn(rho)

# Noisy
gamma_dephase = 0.5
gamma_damp = 0.1
c_ops = [np.sqrt(gamma_dephase) * position, np.sqrt(gamma_damp) * qt.destroy(N)]

result_noisy = qt.mesolve(H, psi0, times, c_ops)
rho_noisy = result_noisy.states[-1] * result_noisy.states[-1].dag()
entropy_noisy_final = qt.entropy_vn(rho_noisy)

# No cloak noisy
H_no_cloak = momentum**2 / 2
result_no_cloak_noisy = qt.mesolve(H_no_cloak, psi0, times, c_ops)
rho_no_cloak_noisy = result_no_cloak_noisy.states[-1] * result_no_cloak_noisy.states[-1].dag()
entropy_no_cloak_noisy = qt.entropy_vn(rho_no_cloak_noisy)

print("Entropy cloaked no noise:", entropy_final)
print("Entropy cloaked noise:", entropy_noisy_final)
print("Entropy no cloak noise:", entropy_no_cloak_noisy)

# Bipartite
dims = [[50, 50], [50, 50]]

# For cloaked
rho = rho.reshape([50,50,50,50])
rho.dims = dims
S_A = qt.entropy_vn(qt.partial_trace(rho, [0]))
S_B = qt.entropy_vn(qt.partial_trace(rho, [1]))
S_AB = qt.entropy_vn(rho)
mut_ent = S_A + S_B - S_AB
print("Mutual entropy cloaked t=10:", mut_ent)

# For cloaked noisy
rho_noisy = rho_noisy.reshape([50,50,50,50])
rho_noisy.dims = dims
S_A_noisy = qt.entropy_vn(qt.partial_trace(rho_noisy, [0]))
S_B_noisy = qt.entropy_vn(qt.partial_trace(rho_noisy, [1]))
S_AB_noisy = qt.entropy_vn(rho_noisy)
mut_ent_noisy = S_A_noisy + S_B_noisy - S_AB_noisy
print("Mutual entropy cloaked noise t=10:", mut_ent_noisy)

# Plot
plt.figure()
plt.plot(x, np.abs(psi0.full().flatten())**2, label='t=0')
plt.plot(x, np.abs(result_noisy.states[-1].full().flatten())**2, label='t=10 cloaked noisy')
plt.legend()
plt.title('Wavefunction spreading')
plt.savefig('plot.png')
print("Plot saved as plot.png")

# Describe plot
prob_t0 = np.abs(psi0.full().flatten())**2
prob_t10 = np.abs(result_noisy.states[-1].full().flatten())**2
print("Max prob t=0:", np.max(prob_t0), "at x:", x[np.argmax(prob_t0)])
print("Max prob t=10:", np.max(prob_t10), "at x:", x[np.argmax(prob_t10)])
print("Std prob t=0:", np.std(prob_t0))
print("Std prob t=10:", np.std(prob_t10))

# Attractive V
S_grav_neg = -S_grav
def V_neg(x_val):
    sum_v = 0.0
    residues = {1,5,7,11,13,17,19,23}
    for n in range(2, 1001):
        res = n % 24
        if res in residues:
            cos_term = math.cos(2 * np.pi * n / 24)
            if abs(cos_term) > 1e-10:
                a_n = S_grav_neg * cos_term / math.log(1 + abs(cos_term))
                term = a_n * (n ** (-abs(x_val)/3)) / math.log(n)
                sum_v += term
    return sum_v

V_neg = np.array([V_neg(xi) for xi in x])
print("Min V_neg:", np.min(V_neg))

# Kinetic
kinetic_np = np.diag(2.0 / dx**2 * np.ones(N)) - np.diag(1.0 / dx**2 * np.ones(N-1), 1) - np.diag(1.0 / dx**2 * np.ones(N-1), -1)

H_np_neg = kinetic_np + np.diag(V_neg)
eigvals_neg = eigh(H_np_neg, eigvals_only=True)[0:5]
print("Eigenvalues attractive:", eigvals_neg)