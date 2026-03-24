import numpy as np
from scipy.linalg import eigh
from tqdm import tqdm

# -----------------------------
# Discretization
# -----------------------------

def build_laplacian(N, L=2*np.pi):
    x = np.linspace(-L/2, L/2, N, endpoint=False)
    dx = x[1] - x[0]
    main = -2*np.ones(N)
    off = np.ones(N-1)
    D2 = np.diag(main) + np.diag(off,1) + np.diag(off,-1)
    D2[0,-1] = D2[-1,0] = 1
    return x, -D2/dx**2, dx

# -----------------------------
# Random potential
# -----------------------------

def random_height_potential(x, q, rng):
    K = rng.integers(5, 20)
    freqs = rng.integers(1, 50, K)
    weights = rng.lognormal(0.0, 0.5, K)

    V = np.zeros_like(x)
    for r, w in zip(freqs, weights):
        decay = np.exp(-q*np.abs(x)/rng.uniform(0.5, 3.0))
        V += w * decay * np.cos(r*x)
    return V

# -----------------------------
# Amplification laws
# -----------------------------

def amplify(V, q, law):
    if law == "exponential":
        return np.exp(q) * V
    if law == "polynomial":
        return (1 + q)**4 * V
    if law == "linear":
        return (1 + q) * V
    if law == "superexp":
        return np.exp(q**2) * V
    raise ValueError("Unknown law")

def ground_energy(V, K):
    H = K + np.diag(V)
    return eigh(H, eigvals_only=True, subset_by_index=[0,0])[0]

def detect_crossover(qs, E):
    d2 = np.gradient(np.gradient(E, qs), qs)
    return qs[np.argmax(np.abs(d2))]

# -----------------------------
# Trial
# -----------------------------

def run_trial(seed, N, law):
    rng = np.random.default_rng(seed)
    x, K, dx = build_laplacian(N)
    qs = np.linspace(0, 2.5, 60)
    E = []
    for q in qs:
        V = amplify(random_height_potential(x, q, rng), q, law)
        E.append(ground_energy(V, K))
    return detect_crossover(qs, np.array(E))

# -----------------------------
# Main experiment
# -----------------------------

laws = ["linear", "polynomial", "exponential", "superexp"]
Ns = [512, 1024]
trials = 15

print("\n=== Amplification Law Comparison ===\n")

for law in laws:
    qs = []
    print(f"Law: {law}")
    for N in Ns:
        for seed in tqdm(range(trials)):
            qs.append(run_trial(seed, N, law))
    print(f"  mean q* = {np.mean(qs):.3f}, std = {np.std(qs):.3f}\n")

# (base) brendanlynch@Brendans-Laptop strongCP % python newTest2.py

# === Amplification Law Comparison ===

# Law: linear
# 100%|███████████████████████████████████████████| 15/15 [00:08<00:00,  1.69it/s]
# 100%|███████████████████████████████████████████| 15/15 [00:47<00:00,  3.19s/it]
#   mean q* = 0.551, std = 0.729

# Law: polynomial
# 100%|███████████████████████████████████████████| 15/15 [00:08<00:00,  1.73it/s]
# 100%|███████████████████████████████████████████| 15/15 [00:49<00:00,  3.27s/it]
#   mean q* = 2.362, std = 0.140

# Law: exponential
# 100%|███████████████████████████████████████████| 15/15 [00:08<00:00,  1.71it/s]
# 100%|███████████████████████████████████████████| 15/15 [00:47<00:00,  3.17s/it]
#   mean q* = 2.229, std = 0.360

# Law: superexp
# 100%|███████████████████████████████████████████| 15/15 [00:08<00:00,  1.71it/s]
# 100%|███████████████████████████████████████████| 15/15 [00:47<00:00,  3.18s/it]
#   mean q* = 2.460, std = 0.052

# (base) brendanlynch@Brendans-Laptop strongCP % 