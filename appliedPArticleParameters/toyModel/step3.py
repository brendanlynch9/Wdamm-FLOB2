import numpy as np
import pandas as pd
import scipy.sparse as sp
import scipy.sparse.linalg as spla

# --------------------------------------------------
# STEP 3: Yukawa overlaps from eigenfunctions
# --------------------------------------------------

print("Loading Step-1 eigenvalues from CSV…")

# These are the positive eigenmodes you reported from Step 1
positive_modes = [
    (5, 0.26956453205472264),
    (6, 1.6524372070031994),
    (7, 2.684630729664764),
    (8, 4.914205784444167),
    (9, 4.922818390620404),
    (10, 8.415324237293675),
    (11, 8.426534015223003),
    (12, 12.722404198710095)
]

levels = np.array([pm[0] for pm in positive_modes])
lambdas_target = np.array([pm[1] for pm in positive_modes])

print(f"Positive eigenvalue levels: {levels}")
print(f"Lambdas: {lambdas_target}")

# ----------------------------
# Domain and potential
# ----------------------------
L = 10.0
N = 2000
x = np.linspace(-L/2, L/2, N)
dx = x[1] - x[0]

# Reconstruct the same potential as Step 1
num_wells = 6
well_centers = np.linspace(-3.5, 3.5, num_wells)
well_width = 0.35

V = np.zeros_like(x)
for c in well_centers:
    V -= 12.0 * np.exp(-((x - c) ** 2) / (2 * well_width ** 2))

# ----------------------------
# Build kinetic operator
# ----------------------------
diag_main = -2.0 * np.ones(N)
diag_off = np.ones(N - 1)
Laplacian = sp.diags([diag_off, diag_main, diag_off], offsets=[-1, 0, 1]) / (dx ** 2)

# ----------------------------
# Full Hamiltonian
# ----------------------------
H = -Laplacian + sp.diags(V, 0)

print("Diagonalizing Hamiltonian…")

num_modes = len(positive_modes) + 4  # compute slightly more
evals, evecs = spla.eigsh(H, k=num_modes, sigma=0.0, which="LM")

order = np.argsort(evals)
evals = evals[order]
evecs = evecs[:, order]

print(f"Computed {len(evals)} total eigenvalues.")

# ----------------------------
# Match numerically-computed eigenvalues
# ----------------------------

def match_lambda(lam):
    return np.argmin(np.abs(evals - lam))

indices = [match_lambda(l) for l in lambdas_target]

print("\nMatched eigenvalue indices:")
for idx, lev, lam in zip(indices, levels, lambdas_target):
    print(f"  Level {lev} → numerical idx {idx}, eigenvalue = {evals[idx]:.6f}")

# ----------------------------
# Extract eigenfunctions
# ----------------------------
psi = np.zeros((len(indices), N))
for i, idx in enumerate(indices):
    v = evecs[:, idx]
    v /= np.sqrt(np.sum(np.abs(v) ** 2) * dx)   # normalize
    psi[i] = v

# ----------------------------
# Yukawa overlaps Y_ij = ∫ ψ_i ψ_j dx
# ----------------------------
n = len(indices)
Y = np.zeros((n, n))

for i in range(n):
    for j in range(n):
        Y[i, j] = np.sum(psi[i] * psi[j]) * dx

# ----------------------------
# Save results
# ----------------------------
df = pd.DataFrame(Y, columns=[f"mode{lev}" for lev in levels])
df.index = [f"mode{lev}" for lev in levels]
df.to_csv("step3_yukawa_overlaps.csv")

print("\nSaved Yukawa overlap matrix to step3_yukawa_overlaps.csv\n")
print(Y)

# the output in terminal was:
# (base) brendanlynch@Mac appliedPArticleParameters % python step3.py
# Loading Step-1 eigenvalues from CSV…
# Positive eigenvalue levels: [ 5  6  7  8  9 10 11 12]
# Lambdas: [ 0.26956453  1.65243721  2.68463073  4.91420578  4.92281839  8.41532424
#   8.42653402 12.7224042 ]
# Diagonalizing Hamiltonian…
# Computed 12 total eigenvalues.

# Matched eigenvalue indices:
#   Level 5 → numerical idx 6, eigenvalue = -0.071059
#   Level 6 → numerical idx 8, eigenvalue = 2.331172
#   Level 7 → numerical idx 8, eigenvalue = 2.331172
#   Level 8 → numerical idx 9, eigenvalue = 4.079664
#   Level 9 → numerical idx 9, eigenvalue = 4.079664
#   Level 10 → numerical idx 11, eigenvalue = 8.274896
#   Level 11 → numerical idx 11, eigenvalue = 8.274896
#   Level 12 → numerical idx 11, eigenvalue = 8.274896

# Saved Yukawa overlap matrix to step3_yukawa_overlaps.csv

# [[ 1.00000000e+00  1.06634728e-16  1.06634728e-16 -1.77724546e-17
#   -1.77724546e-17 -8.88622731e-17 -8.88622731e-17 -8.88622731e-17]
#  [ 1.06634728e-16  1.00000000e+00  1.00000000e+00  1.42179637e-16
#    1.42179637e-16 -8.88622731e-17 -8.88622731e-17 -8.88622731e-17]
#  [ 1.06634728e-16  1.00000000e+00  1.00000000e+00  1.42179637e-16
#    1.42179637e-16 -8.88622731e-17 -8.88622731e-17 -8.88622731e-17]
#  [-1.77724546e-17  1.42179637e-16  1.42179637e-16  1.00000000e+00
#    1.00000000e+00  2.66586819e-16  2.66586819e-16  2.66586819e-16]
#  [-1.77724546e-17  1.42179637e-16  1.42179637e-16  1.00000000e+00
#    1.00000000e+00  2.31041910e-16  2.31041910e-16  2.31041910e-16]
#  [-8.88622731e-17 -8.88622731e-17 -8.88622731e-17  2.66586819e-16
#    2.31041910e-16  1.00000000e+00  1.00000000e+00  1.00000000e+00]
#  [-8.88622731e-17 -8.88622731e-17 -8.88622731e-17  2.66586819e-16
#    2.31041910e-16  1.00000000e+00  1.00000000e+00  1.00000000e+00]
#  [-8.88622731e-17 -8.88622731e-17 -8.88622731e-17  2.66586819e-16
#    2.31041910e-16  1.00000000e+00  1.00000000e+00  1.00000000e+00]]
# (base) brendanlynch@Mac appliedPArticleParameters % 


# step3_yukawa_overlaps csv output was: 
# ,mode5,mode6,mode7,mode8,mode9,mode10,mode11,mode12
# mode5,0.9999999999999998,1.0663472772787614e-16,1.0663472772787614e-16,-1.777245462131269e-17,-1.777245462131269e-17,-8.886227310656345e-17,-8.886227310656345e-17,-8.886227310656345e-17
# mode6,1.0663472772787614e-16,1.0,1.0,1.4217963697050151e-16,1.4217963697050151e-16,-8.886227310656345e-17,-8.886227310656345e-17,-8.886227310656345e-17
# mode7,1.0663472772787614e-16,1.0,1.0,1.4217963697050151e-16,1.4217963697050151e-16,-8.886227310656345e-17,-8.886227310656345e-17,-8.886227310656345e-17
# mode8,-1.777245462131269e-17,1.4217963697050151e-16,1.4217963697050151e-16,0.9999999999999999,0.9999999999999999,2.6658681931969034e-16,2.6658681931969034e-16,2.6658681931969034e-16
# mode9,-1.777245462131269e-17,1.4217963697050151e-16,1.4217963697050151e-16,0.9999999999999999,1.0000000000000002,2.3104191007706496e-16,2.3104191007706496e-16,2.3104191007706496e-16
# mode10,-8.886227310656345e-17,-8.886227310656345e-17,-8.886227310656345e-17,2.6658681931969034e-16,2.3104191007706496e-16,1.0,1.0,1.0
# mode11,-8.886227310656345e-17,-8.886227310656345e-17,-8.886227310656345e-17,2.6658681931969034e-16,2.3104191007706496e-16,1.0,1.0,1.0
# mode12,-8.886227310656345e-17,-8.886227310656345e-17,-8.886227310656345e-17,2.6658681931969034e-16,2.3104191007706496e-16,1.0,1.0,1.0
