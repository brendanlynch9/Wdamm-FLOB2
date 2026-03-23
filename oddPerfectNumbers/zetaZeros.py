import numpy as np
import os

np.set_printoptions(precision=6)

# ====================
# CONFIG / PARAMETERS
# ====================
RANK_LOCK = 16
RESIDUE_TARGET = 0.9895
RESIDUE_TOLERANCE = 0.005

PERTURB_STRENGTHS = [0.0, 0.01, 0.1]
DIMS_TO_TEST = [8, 12, 16, 20, 32]

ZETA_FILE = 'zeta_zeros_first_100k.txt'

MOCK_NUMBERS = {
    'even_perfect_small': 6,
    'even_perfect_larger': 28,
    'abundant_even': 12,
    'deficient_odd': 9,
    'mock_odd_abundant': 945,
    'hypothetical_odd_perfect': 1000001
}

# ====================
# Helper: sigma(n)
# ====================
def sigma(n):
    if n <= 0:
        return 0
    total = 1
    for i in range(2, int(np.sqrt(n)) + 1):
        if n % i == 0:
            total += i
            if i != n // i:
                total += n // i
    if n > 1:
        total += n
    return total

# ====================
# Load real zeta imaginary parts (now full 100k)
# ====================
def load_zeta_zeros(max_n=100000):
    if os.path.exists(ZETA_FILE):
        with open(ZETA_FILE, 'r') as f:
            lines = f.readlines()
        zeros = []
        for line in lines[:max_n]:
            stripped = line.strip()
            if stripped:
                try:
                    t = float(stripped)
                    zeros.append(t)
                except ValueError:
                    print(f"Skipping invalid line: {stripped}")
                    continue
        print(f"Loaded {len(zeros)} real zeta imaginary parts from {ZETA_FILE}")
        if len(zeros) < max_n:
            print(f"Warning: Only {len(zeros)} usable lines (less than requested {max_n})")
        return np.array(zeros)
    else:
        print(f"File {ZETA_FILE} not found. Using fallback mock.")
        # Hardcoded first 20 + log extension (fallback)
        real_first_20 = np.array([
            14.134725141734693790457251983562,
            21.022039638771554992628479593896,
            25.010857580145688763213790992562,
            30.424876125859513210311897530584,
            32.935061587739189690662368964074,
            37.586178158825671257217763480705,
            40.918719012147495187398126914633,
            43.327073280914999519496122165406,
            48.005150881167159727942472749427,
            49.773832477672302181916784678566,
            52.970321477714460644147296608051,
            56.446247697063394804367759476989,
            59.347044002602353079653648454466,
            60.831778524783677549965918945142,
            65.112544048081606660875046659085,
            67.079810529494173842424038152672,
            69.546401711173979843393908094908,
            72.067157674481907632449696042193,
            75.704690699083933168157219094901,
            77.144840068874805372682664856262
        ])
        extended = real_first_20.tolist()
        last = real_first_20[-1]
        for _ in range(max_n - len(real_first_20)):
            last += np.log(last + 10) / (2 * np.pi)
            extended.append(last)
        return np.array(extended[:max_n])

zeta_imags = load_zeta_zeros(100000)  # <--- FULL 100k

# ====================
# 1. Hermitian Stability Beyond Rank-16 (unchanged)
# ====================
def is_hermitian(M, atol=1e-8):
    return np.allclose(M, M.conj().T, atol=atol)

def build_perturbed_matrix(dim, strength=0.0):
    H_real = np.random.randn(dim, dim)
    H_real = (H_real + H_real.T) / 2
    anti_herm = 1j * (np.random.randn(dim, dim) - np.random.randn(dim, dim).T) / 2
    return H_real + strength * anti_herm

print("=== 1. Hermitian Stability Beyond Rank-16 ===")
print("Dim | Perturb | Hermitian? | Max |Im(eig)| | Stable?")
for dim in DIMS_TO_TEST:
    for strength in PERTURB_STRENGTHS:
        M = build_perturbed_matrix(dim, strength)
        herm_ok = is_hermitian(M)
        evals = np.linalg.eigvals(M)
        max_imag = np.max(np.abs(evals.imag))
        stable = max_imag < 1e-6
        status = "YES" if stable else "NO (leak!)"
        print(f"{dim:3d} | {strength:5.2f}   | {herm_ok:10} | {max_imag:12.6f} | {status}")

# ====================
# 2. Real Zeta Zeros Rank Proxy (very gentle linear)
# ====================
def compute_residue_proxy(zeros, target=RESIDUE_TARGET):
    if len(zeros) < 2:
        return 0.0
    gaps = np.diff(zeros)
    T_mid = zeros[:-1] + gaps / 2
    local_means = np.log(T_mid + 1e-10) / (2 * np.pi)
    norm_gaps = gaps / local_means
    
    mean_abs_dev = np.mean(np.abs(norm_gaps - 1.0))
    gap_std = np.std(norm_gaps)
    print(f"  [N={len(zeros)}] mean |norm_gap - 1| = {mean_abs_dev:.6f} | std(norm_gaps) = {gap_std:.6f}")
    
    penalty = (mean_abs_dev + gap_std) / 4.0
    score = 1 - penalty
    std_bonus = 0.05 * (1 - gap_std)
    scaled = 0.75 + (score + std_bonus) * 0.25
    final = np.clip(scaled, 0.75, 0.999)
    return final

print("\n=== 2. Real Zeta Zeros Rank Proxy Convergence (very gentle linear) ===")
print("N         | Residue Proxy | Locked? (±0.005 of 0.9895)")
Ns = [100, 400, 800, 1600, 2400, 3200, 4000, 8000, 16000, 32000, 64000, 100000]
for N in Ns:
    if N > len(zeta_imags):
        print(f"{N:9d} | (data only up to {len(zeta_imags)}) | -")
        continue
    subset = zeta_imags[:N]
    r = compute_residue_proxy(subset)
    locked = abs(r - RESIDUE_TARGET) < RESIDUE_TOLERANCE
    print(f"{N:9d} | {r:.6f}         | {'YES' if locked else 'NO'}")

# ====================
# 3. Abundancy / Defect Stability (unchanged)
# ====================
print("\n=== 3. Mock Abundancy / Defect Stability ===")
print("Number     | Type               | sigma(n) | 2*n    | Abundancy | Defect | Stable?")
for name, n_val in MOCK_NUMBERS.items():
    n = int(n_val)
    s = sigma(n)
    abund = s / n if n > 0 else 0
    defect = s - 2 * n
    stable = (abs(defect) < 1e-6) or (n % 2 == 0 and defect <= 0)
    status = "Stable (perfect-like)" if stable else "Potential divergence (odd-like)"
    print(f"{n:10d} | {name:18} | {s:8d} | {2*n:6d} | {abund:9.4f} | {defect:6d} | {status}")

print("\nScript complete.")
print("Full 100k zeros loaded — check high-N residue climb.")


# (base) brendanlynch@Brendans-Laptop oddPerfectNumbers % python zetaZeros.py
# Loaded 100000 real zeta imaginary parts from zeta_zeros_first_100k.txt
# === 1. Hermitian Stability Beyond Rank-16 ===
# Dim | Perturb | Hermitian? | Max |Im(eig)| | Stable?
#   8 |  0.00   |          1 |     0.000000 | YES
#   8 |  0.01   |          0 |     0.014393 | NO (leak!)
#   8 |  0.10   |          0 |     0.098437 | NO (leak!)
#  12 |  0.00   |          1 |     0.000000 | YES
#  12 |  0.01   |          0 |     0.010442 | NO (leak!)
#  12 |  0.10   |          0 |     0.099656 | NO (leak!)
#  16 |  0.00   |          1 |     0.000000 | YES
#  16 |  0.01   |          0 |     0.018411 | NO (leak!)
#  16 |  0.10   |          0 |     0.114317 | NO (leak!)
#  20 |  0.00   |          1 |     0.000000 | YES
#  20 |  0.01   |          0 |     0.019222 | NO (leak!)
#  20 |  0.10   |          0 |     0.137680 | NO (leak!)
#  32 |  0.00   |          1 |     0.000000 | YES
#  32 |  0.01   |          0 |     0.021926 | NO (leak!)
#  32 |  0.10   |          0 |     0.150823 | NO (leak!)

# === 2. Real Zeta Zeros Rank Proxy Convergence (very gentle linear) ===
# N         | Residue Proxy | Locked? (±0.005 of 0.9895)
#   [N=100] mean |norm_gap - 1| = 2.127188 | std(norm_gaps) = 2.045525
#       100 | 0.750000         | NO
#   [N=400] mean |norm_gap - 1| = 0.989630 | std(norm_gaps) = 1.336349
#       400 | 0.850422         | NO
#   [N=800] mean |norm_gap - 1| = 0.678580 | std(norm_gaps) = 1.067191
#       800 | 0.890049         | NO
#   [N=1600] mean |norm_gap - 1| = 0.492744 | std(norm_gaps) = 0.850585
#      1600 | 0.917910         | NO
#   [N=2400] mean |norm_gap - 1| = 0.429525 | std(norm_gaps) = 0.745594
#      2400 | 0.929735         | NO
#   [N=3200] mean |norm_gap - 1| = 0.401558 | std(norm_gaps) = 0.679509
#      3200 | 0.936439         | NO
#   [N=4000] mean |norm_gap - 1| = 0.388103 | std(norm_gaps) = 0.632733
#      4000 | 0.940789         | NO
#   [N=8000] mean |norm_gap - 1| = 0.383005 | std(norm_gaps) = 0.509077
#      8000 | 0.950381         | NO
#   [N=16000] mean |norm_gap - 1| = 0.414091 | std(norm_gaps) = 0.412904
#     16000 | 0.955652         | NO
#   [N=32000] mean |norm_gap - 1| = 0.462922 | std(norm_gaps) = 0.338462
#     32000 | 0.958183         | NO
#   [N=64000] mean |norm_gap - 1| = 0.516831 | std(norm_gaps) = 0.280515
#     64000 | 0.959159         | NO
#   [N=100000] mean |norm_gap - 1| = 0.550834 | std(norm_gaps) = 0.250211
#    100000 | 0.959307         | NO

# === 3. Mock Abundancy / Defect Stability ===
# Number     | Type               | sigma(n) | 2*n    | Abundancy | Defect | Stable?
#          6 | even_perfect_small |       12 |     12 |    2.0000 |      0 | Stable (perfect-like)
#         28 | even_perfect_larger |       56 |     56 |    2.0000 |      0 | Stable (perfect-like)
#         12 | abundant_even      |       28 |     24 |    2.3333 |      4 | Potential divergence (odd-like)
#          9 | deficient_odd      |       13 |     18 |    1.4444 |     -5 | Potential divergence (odd-like)
#        945 | mock_odd_abundant  |     1920 |   1890 |    2.0317 |     30 | Potential divergence (odd-like)
#    1000001 | hypothetical_odd_perfect |  1010004 | 2000002 |    1.0100 | -989998 | Potential divergence (odd-like)

# Script complete.
# Full 100k zeros loaded — check high-N residue climb.
# (base) brendanlynch@Brendans-Laptop oddPerfectNumbers % 
