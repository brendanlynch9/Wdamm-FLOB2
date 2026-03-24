import numpy as np
from scipy.linalg import eigh
import matplotlib.pyplot as plt
from tqdm import tqdm

# === Standard numerical setup — nothing exotic ===

# Periodic domain [-pi, pi] as proxy for the potential coordinate x
N = 2048
theta = np.linspace(-np.pi, np.pi, N, endpoint=False)
dtheta = theta[1] - theta[0]
print(f"Grid: N={N}, dtheta={dtheta:.6f}")

# Finite-difference Laplacian (periodic boundary)
diag = np.ones(N) * (-2.0)
off_diag = np.ones(N)
Laplacian = np.diag(diag) + np.diag(off_diag[:-1], 1) + np.diag(off_diag[:-1], -1)
Laplacian /= dtheta**2
Laplacian[0, -1] = Laplacian[-1, 0] = 1.0 / dtheta**2
kinetic = -Laplacian  # -Δ

# Height potential proxy (direct from abc paper eq. 2, approximated harmonically)
prime_like_freqs = np.array([1, 5, 7, 11, 13, 17, 19, 23])  # example frequencies

def height_potential(theta, q):
    """
    Vanilla approximation of V_abc(x) = sum_p log(p+1) exp(-q |x| / log(p+2))
    Use cos(r θ) + exp(-q |θ|) envelope for periodic domain
    Multiply by exp(q - 1) as in paper eq. (1)
    """
    V = np.zeros_like(theta)
    for r in prime_like_freqs:
        weight = np.log(r + 1.0)
        decay = np.exp(-q * np.abs(theta) / np.log(r + 2.0))
        V += weight * decay * np.cos(r * theta)
    V *= np.exp(q - 1.0)  # the key amplification from paper
    V -= 0.8              # small offset so low-q starts positive (allows crossing)
    return V

def L1_norm(V):
    return np.sum(np.abs(V)) * dtheta

# Sweep quality parameter q
q_values = np.linspace(0.0, 2.5, 120)  # focused around 1.18
E0_list = []
L1_list = []

for q in tqdm(q_values, desc="Sweeping q"):
    V = height_potential(theta, q)
    H = kinetic + np.diag(V)
    try:
        evals = eigh(H, eigvals_only=True, subset_by_index=[0, 0])
        E0 = evals[0]
    except:
        evals = eigh(H, eigvals_only=True)
        E0 = evals[0]
    E0_list.append(E0)
    L1_list.append(L1_norm(V))

E0_arr = np.array(E0_list)
L1_arr = np.array(L1_list)

# Detect zero-crossing (positive → negative)
sign_changes = np.diff(np.sign(E0_arr))
cross_idx = np.where(sign_changes != 0)[0]

if len(cross_idx) > 0:
    idx = cross_idx[0]
    q1, q2 = q_values[idx], q_values[idx + 1]
    e1, e2 = E0_arr[idx], E0_arr[idx + 1]
    q_star = q1 - e1 * (q2 - q1) / (e2 - e1)
    print(f"\nPHASE TRANSITION (E₀ zero-crossing) at q ≈ {q_star:.4f}")
    print(f"E₀ near cross: {e1:.6f} → {e2:.6f}")
else:
    print("\nNo zero-crossing found.")
    min_idx = np.argmin(E0_arr)
    print(f"Minimum E₀ = {E0_arr[min_idx]:.6f} at q = {q_values[min_idx]:.4f}")

# Summary stats
print(f"\nq = 0.0: E₀ = {E0_arr[0]:.6f}, L¹ ≈ {L1_arr[0]:.2f}")
print(f"q = {q_values[-1]:.2f}: E₀ = {E0_arr[-1]:.6f}, L¹ ≈ {L1_arr[-1]:.2f}")

if E0_arr[-1] < -1.0 and L1_arr[-1] > 50:
    print(" → High-q collapse signature detected")

# Plot
plt.figure(figsize=(12, 5))

plt.subplot(1, 2, 1)
plt.plot(q_values, E0_arr, 'b-', lw=2, label='Ground state E₀')
plt.axhline(0, color='k', ls='--', alpha=0.7)
plt.xlabel('q (quality proxy)')
plt.ylabel('E₀')
plt.title('Ground State Energy vs Quality')
plt.grid(True, alpha=0.3)
plt.legend()

plt.subplot(1, 2, 2)
plt.plot(q_values, L1_arr, 'r-', lw=2, label='L¹ norm')
plt.xlabel('q')
plt.ylabel('L¹ norm')
plt.title('L¹ Norm Growth')
plt.grid(True, alpha=0.3)
plt.legend()

plt.tight_layout()
plt.savefig('vanilla_abc_benchmark_final.png', dpi=150)
plt.close()
print("Plot saved: vanilla_abc_benchmark_final.png")

# (base) brendanlynch@Brendans-Laptop strongCP % python vanilla_abc_benchmark_final.py
# Grid: N=2048, dtheta=0.003068
# Sweeping q: 100%|█████████████████████████████| 120/120 [01:01<00:00,  1.96it/s]

# No zero-crossing found.
# Minimum E₀ = -0.948092 at q = 2.5000

# q = 0.0: E₀ = -0.858734, L¹ ≈ 9.08
# q = 2.50: E₀ = -0.948092, L¹ ≈ 36.97
# Plot saved: vanilla_abc_benchmark_final.png
# (base) brendanlynch@Brendans-Laptop strongCP % 