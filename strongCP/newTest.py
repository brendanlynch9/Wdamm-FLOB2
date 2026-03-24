import numpy as np
from scipy.linalg import eigh
from tqdm import tqdm

# -----------------------------
# Core numerical infrastructure
# -----------------------------

def build_laplacian(N, L=2*np.pi):
    x = np.linspace(-L/2, L/2, N, endpoint=False)
    dx = x[1] - x[0]
    main = -2*np.ones(N)
    off = np.ones(N-1)
    D2 = np.diag(main) + np.diag(off,1) + np.diag(off,-1)
    D2[0,-1] = D2[-1,0] = 1
    return x, -D2 / dx**2, dx

# -----------------------------
# Randomized "height-potential"
# -----------------------------

def random_height_potential(x, q, rng):
    K = rng.integers(5, 20)             # number of modes
    freqs = rng.integers(1, 50, size=K) # random frequencies
    weights = rng.lognormal(0.0, 0.5, K)

    V = np.zeros_like(x)
    for r, w in zip(freqs, weights):
        decay_scale = rng.uniform(0.5, 3.0)
        decay = np.exp(-q * np.abs(x) / decay_scale)
        V += w * decay * np.cos(r * x)

    # global exponential quality amplification (unstructured)
    V *= np.exp(q)
    return V

def ground_energy(V, kinetic):
    H = kinetic + np.diag(V)
    return eigh(H, eigvals_only=True, subset_by_index=[0,0])[0]

# -----------------------------
# Sharpness diagnostic
# -----------------------------

def detect_crossover(qs, E):
    dE = np.gradient(E, qs)
    d2E = np.gradient(dE, qs)
    idx = np.argmax(np.abs(d2E))
    return qs[idx], d2E[idx]

# -----------------------------
# Experiment harness
# -----------------------------

def run_trial(seed, N):
    rng = np.random.default_rng(seed)
    x, K, dx = build_laplacian(N)
    qs = np.linspace(0, 2.5, 60)
    E = []

    for q in qs:
        V = random_height_potential(x, q, rng)
        E.append(ground_energy(V, K))

    E = np.array(E)
    q_star, sharpness = detect_crossover(qs, E)
    return q_star, sharpness, E

# -----------------------------
# Main study
# -----------------------------

Ns = [512, 1024, 2048]
trials = 20

results = []

for N in Ns:
    print(f"\nGrid N = {N}")
    for seed in tqdm(range(trials)):
        q_star, sharp, _ = run_trial(seed, N)
        results.append((N, q_star, sharp))

# -----------------------------
# Statistical summary
# -----------------------------

print("\n=== Statistical Summary ===")
for N in Ns:
    qs = [r[1] for r in results if r[0] == N]
    print(f"N={N}:  mean q* = {np.mean(qs):.3f},  std = {np.std(qs):.3f}")

all_qs = [r[1] for r in results]
print(f"\nGlobal: mean q* = {np.mean(all_qs):.3f}, std = {np.std(all_qs):.3f}")

# (base) brendanlynch@Brendans-Laptop strongCP % python newTest.py

# Grid N = 512
# 100%|███████████████████████████████████████████| 20/20 [00:11<00:00,  1.74it/s]

# Grid N = 1024
# 100%|███████████████████████████████████████████| 20/20 [01:04<00:00,  3.20s/it]

# Grid N = 2048
# 100%|███████████████████████████████████████████| 20/20 [10:10<00:00, 30.54s/it]

# === Statistical Summary ===
# N=512:  mean q* = 2.246,  std = 0.316
# N=1024:  mean q* = 2.246,  std = 0.316
# N=2048:  mean q* = 2.246,  std = 0.316

# Global: mean q* = 2.246, std = 0.316
# (base) brendanlynch@Brendans-Laptop strongCP % 