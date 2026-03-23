import numpy as np

np.set_printoptions(precision=6)  # Nicer float display

# ====================
# CONFIG / PARAMETERS
# ====================
RANK_LOCK = 16              # Your "Rank-16" stability threshold
RESIDUE_TARGET = 0.9895     # Observed Rank-16 residue ~99.05% precision
RESIDUE_TOLERANCE = 0.005   # How close to call "locked"

PERTURB_STRENGTHS = [0.0, 0.01, 0.1]  # Test no / mild / strong "defect"
DIMS_TO_TEST = [8, 12, 16, 20, 32]    # Around and beyond rank lock

# Mock odd perfect candidates (small abundants + hypotheticals)
MOCK_NUMBERS = {
    'even_perfect_small': 6,
    'even_perfect_larger': 28,
    'abundant_even': 12,
    'deficient_odd': 9,
    'mock_odd_abundant': 945,
    'hypothetical_odd_perfect': 1000001
}

# ====================
# Helper: sigma(n) - divisor sum
# ====================
def sigma(n):
    """Simple divisor sum function (sigma(n)) for small n"""
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
# 1. Self-Adjoint / Hermitian Stability Test with Perturbation
# ====================
def is_hermitian(M, atol=1e-8):
    return np.allclose(M, M.conj().T, atol=atol)

def build_perturbed_matrix(dim, strength=0.0):
    # Real symmetric base (Hermitian real part)
    H_real = np.random.randn(dim, dim)
    H_real = (H_real + H_real.T) / 2
    
    # Anti-Hermitian perturbation (mimics "odd defect" or beyond-rank instability)
    anti_herm = 1j * (np.random.randn(dim, dim) - np.random.randn(dim, dim).T) / 2
    
    return H_real + strength * anti_herm

print("=== 1. Hermitian Stability Beyond Rank-16 ===")
print("Dim | Perturb | Hermitian? | Max |Im(eig)| | Stable (real evals)?")
for dim in DIMS_TO_TEST:
    for strength in PERTURB_STRENGTHS:
        M = build_perturbed_matrix(dim, strength)
        herm_ok = is_hermitian(M)
        evals = np.linalg.eigvals(M)
        max_imag = np.max(np.abs(evals.imag))
        stable = max_imag < 1e-6  # Threshold for "real enough"
        status = "YES" if stable else "NO (leak!)"
        print(f"{dim:3d} | {strength:5.2f}   | {herm_ok:10} | {max_imag:12.6f} | {status}")

# ====================
# 2. Mock Rank-16 Residue Convergence (your ~0.9895 floor)
# ====================
def mock_rank_residue(N, target=RESIDUE_TARGET):
    converged = target * (1 - np.exp(-N / 800))  # Approach floor
    osc = 0.003 * np.sin(N / 50)                 # Empirical wobble
    noise = np.random.normal(0, 0.0005)
    return np.clip(converged + osc + noise, 0.85, 0.999)

print("\n=== 2. Mock Rank-16 Residue Convergence ===")
print("N     | Residue    | Locked? (within ±0.005 of 0.9895)")
for N in [400, 800, 1600, 2400, 3200, 4000]:
    r = mock_rank_residue(N)
    locked = abs(r - RESIDUE_TARGET) < RESIDUE_TOLERANCE
    print(f"{N:5d} | {r:.6f}   | {'YES' if locked else 'NO'}")

# ====================
# 3. Toy "Defect" Check for Odd Perfects (Abundancy as Mock L1-like Divergence)
# ====================
print("\n=== 3. Mock Abundancy / Defect Stability for Perfect Candidates ===")
print("Number     | Type               | sigma(n) | 2*n    | Abundancy σ(n)/n | Defect (σ-2n) | Stable?")
for name, n_val in MOCK_NUMBERS.items():
    n = int(n_val)
    s = sigma(n)
    abund = s / n if n > 0 else 0
    defect = s - 2 * n
    stable = (abs(defect) < 1e-6) or (n % 2 == 0 and defect <= 0)
    status = "Stable (perfect-like)" if stable else "Potential divergence (odd-like)"
    print(f"{n:10d} | {name:18} | {s:8d} | {2*n:6d} | {abund:14.4f} | {defect:11d} | {status}")

print("\nScript complete. No crashes — ready for iteration.")
print("Falsify Hermitian stability: set PERTURB_STRENGTHS = [0.0] → no leak at any dim.")

# (base) brendanlynch@Brendans-Laptop oddPerfectNumbers % python standardMath.py
# === 1. Hermitian Stability Beyond Rank-16 ===
# Dim | Perturb | Hermitian? | Max |Im(eig)| | Stable (real evals)?
#   8 |  0.00   |          1 |     0.000000 | YES
#   8 |  0.01   |          0 |     0.010468 | NO (leak!)
#   8 |  0.10   |          0 |     0.182487 | NO (leak!)
#  12 |  0.00   |          1 |     0.000000 | YES
#  12 |  0.01   |          0 |     0.011035 | NO (leak!)
#  12 |  0.10   |          0 |     0.179167 | NO (leak!)
#  16 |  0.00   |          1 |     0.000000 | YES
#  16 |  0.01   |          0 |     0.017179 | NO (leak!)
#  16 |  0.10   |          0 |     0.202848 | NO (leak!)
#  20 |  0.00   |          1 |     0.000000 | YES
#  20 |  0.01   |          0 |     0.008534 | NO (leak!)
#  20 |  0.10   |          0 |     0.126220 | NO (leak!)
#  32 |  0.00   |          1 |     0.000000 | YES
#  32 |  0.01   |          0 |     0.014141 | NO (leak!)
#  32 |  0.10   |          0 |     0.246524 | NO (leak!)

# === 2. Mock Rank-16 Residue Convergence ===
# N     | Residue    | Locked? (within ±0.005 of 0.9895)
#   400 | 0.850000   | NO
#   800 | 0.850000   | NO
#  1600 | 0.856866   | NO
#  2400 | 0.937503   | NO
#  3200 | 0.973947   | NO
#  4000 | 0.979724   | NO

# === 3. Mock Abundancy / Defect Stability for Perfect Candidates ===
# Number     | Type               | sigma(n) | 2*n    | Abundancy σ(n)/n | Defect (σ-2n) | Stable?
#          6 | even_perfect_small |       12 |     12 |         2.0000 |           0 | Stable (perfect-like)
#         28 | even_perfect_larger |       56 |     56 |         2.0000 |           0 | Stable (perfect-like)
#         12 | abundant_even      |       28 |     24 |         2.3333 |           4 | Potential divergence (odd-like)
#          9 | deficient_odd      |       13 |     18 |         1.4444 |          -5 | Potential divergence (odd-like)
#        945 | mock_odd_abundant  |     1920 |   1890 |         2.0317 |          30 | Potential divergence (odd-like)
#    1000001 | hypothetical_odd_perfect |  1010004 | 2000002 |         1.0100 |     -989998 | Potential divergence (odd-like)

# Script complete. No crashes — ready for iteration.
# Falsify Hermitian stability: set PERTURB_STRENGTHS = [0.0] → no leak at any dim.
# (base) brendanlynch@Brendans-Laptop oddPerfectNumbers % 