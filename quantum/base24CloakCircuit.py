import numpy as np
import qutip as qt
import math

# Params: Reduced N for faster run, adjust up if needed
N = 100  # Start small, increase to 500 once working
L = 20.0
dx = L / (N - 1)
x = np.linspace(0, L, N)
S_grav = 0.04344799 * 100

def V_cloak(x_val):
    sum_v = 0.0
    for n in range(2, 1001):
        cos_term = math.cos(2 * np.pi * n / 24)
        if abs(cos_term) > 1e-10:
            a_n = S_grav * cos_term / math.log(1 + abs(cos_term))
            term = a_n * (n ** (-abs(x_val)/3)) / math.log(n)
            sum_v += term
    return sum_v

V = np.array([V_cloak(xi) for xi in x])

# QuTiP operators (hbar=1, m=1)
position = qt.position(N)
momentum = qt.momentum(N)
H = (momentum**2 / 2) + qt.qdiags(V, 0)  # Fixed: qdiags for diagonal V

# Initial Gaussian ψ0 at x=5, sigma=1 (loop build)
psi0 = qt.basis(N, 0) * 0.0  # Initialize as zero ket
for i in range(N):
    psi0 += math.exp(-((x[i] - 5)**2) / 2) * qt.basis(N, i)
psi0 = psi0.unit()  # Normalize

# Times for evolution (fewer for speed)
times = np.linspace(0, 10, 50)

# Unitary evolution (no noise)
result = qt.mesolve(H, psi0, times)
rho_final = result.states[-1] * result.states[-1].dag()
entropy_final = qt.entropy_vn(rho_final)

# Noisy evolution (dephasing, gamma=0.1)
gamma = 0.1
c_ops = [np.sqrt(gamma) * position]  # position-based dephasing
result_noisy = qt.mesolve(H, psi0, times, c_ops=c_ops)
rho_noisy_final = result_noisy.states[-1] * result_noisy.states[-1].dag()
entropy_noisy_final = qt.entropy_vn(rho_noisy_final)

# Without cloak (V=0) for comparison
H_no_cloak = momentum**2 / 2
result_no_cloak_noisy = qt.mesolve(H_no_cloak, psi0, times, c_ops=c_ops)
rho_no_cloak_noisy_final = result_no_cloak_noisy.states[-1] * result_no_cloak_noisy.states[-1].dag()
entropy_no_cloak_noisy = qt.entropy_vn(rho_no_cloak_noisy_final)

print("Entropy at t=10 (cloaked, no noise):", entropy_final)
print("Entropy at t=10 (cloaked + noise):", entropy_noisy_final)
print("Entropy at t=10 (no cloak + noise):", entropy_no_cloak_noisy)

# the output was: 
# (base) brendanlynch@Mac quantum % python base24CloakCircuit.py
# Entropy at t=10 (cloaked, no noise): 1.738631012207262e-13
# Entropy at t=10 (cloaked + noise): 0.21905011584710848
# Entropy at t=10 (no cloak + noise): 0.34703009697212384
# (base) brendanlynch@Mac quantum % 