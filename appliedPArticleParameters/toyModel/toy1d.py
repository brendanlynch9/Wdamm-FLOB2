# Toy spectral model for "Step 1" — builds H = -d^2/dx^2 + V(x), computes low eigenpairs,
# maps eigenvalues -> masses via m = C_UFTF * sqrt(lambda / Delta_m),
# and saves results to CSV.

import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla
import pandas as pd
import math

# -----------------------
# Parameters (changeable)
# -----------------------
L = 10.0              # domain length (compactified 1D circle of length L)
N = 2000              # grid points (larger N -> better accuracy)
Delta_m = 24.0        # Base-24 mass gap from the paper
C_UFTF = 1.0          # Modularity constant (set per theory; user can change)
k = 12                # number of eigenpairs to compute

# -----------------------
# Grid (periodic)
# -----------------------
x = np.linspace(0, L, N, endpoint=False)
dx = x[1] - x[0]

# Build finite-difference Laplacian with periodic BCs (sparse)
e = np.ones(N)
diag = -2.0 * e
off = e.copy()
data = np.vstack([off, diag, off])
offsets = [-1, 0, 1]
Laplacian = sp.diags(data, offsets, shape=(N, N), format='csr') / (dx**2)
# periodic wrap
Laplacian = Laplacian.tolil()
Laplacian[0, -1] = 1.0/(dx**2)
Laplacian[-1, 0] = 1.0/(dx**2)
Laplacian = Laplacian.tocsr()

# -----------------------
# Construct a potential V(x)
# -----------------------
def gaussian_well(x, center, width, depth):
    return -depth * np.exp(-0.5 * ((x-center)/width)**2)

# Place several wells (toy pattern)
num_wells = 6
centers = np.linspace(0, L, num_wells, endpoint=False) + 0.5*L/num_wells
width = 0.2 * (L/num_wells)
depths = np.linspace(5.0, 1.0, num_wells)  # varying depths
V = np.zeros_like(x)
for c, d in zip(centers, depths):
    V += gaussian_well(x, c, width, d)

# Ensure V is L1 integrable on the compact domain (finite integral)
l1_norm = np.trapz(np.abs(V), x)

# -----------------------
# Hamiltonian H = -Lap + V (note Laplacian built with negative sign already)
# -----------------------
H = -Laplacian + sp.diags(V, 0, format='csr')

# Compute lowest k eigenvalues/eigenvectors using eigsh (sparse)
eigvals, eigvecs = spla.eigsh(H, k=k, which='SM')

# Sort eigenpairs
idx = np.argsort(eigvals)
eigvals = eigvals[idx]
eigvecs = eigvecs[:, idx]

# Map eigenvalues -> masses via the ansatz m = C_UFTF * sqrt(lambda / Delta_m)
masses = C_UFTF * np.sqrt(np.maximum(eigvals, 0) / Delta_m)

# Prepare results table for first few eigenvalues/masses and ratios
n_show = min(10, len(eigvals))
rows = []
for i in range(n_show):
    rows.append({
        'level': i+1,
        'eigenvalue_lambda': float(eigvals[i]),
        'mass_m_i': float(masses[i])
    })

df = pd.DataFrame(rows)

# Compute example ratios (first three levels) when available
ratios = {}
if len(masses) >= 3:
    ratios['m1:m2'] = masses[0] / masses[1] if masses[1] != 0 else np.nan
    ratios['m2:m3'] = masses[1] / masses[2] if masses[2] != 0 else np.nan
    ratios['m1:m3'] = masses[0] / masses[2] if masses[2] != 0 else np.nan

# Display / save outputs
print(f"Parameters: L={L}, N={N}, Delta_m={Delta_m}, C_UFTF={C_UFTF}, num_wells={num_wells}")
print(f"L1 norm of potential V over domain = {l1_norm:.6g} (finite, so LIC satisfied in this toy model)")
print("\nLowest eigenvalues (lambda) and mapped masses (m_i):")
print(df.to_string(index=False))

if ratios:
    print("\nExample mass ratios (first three levels):")
    for kname, rval in ratios.items():
        print(f"  {kname} = {rval:.6g}")

# Save results to CSV
out_path = "step1_spectral_results.csv"
df.to_csv(out_path, index=False)
print(f"\nSaved results CSV: {out_path}")

# Optional: in the special notebook environment I used, this displays a friendly interactive table.
# Uncomment if running in that environment:
# import caas_jupyter_tools as jt
# jt.display_dataframe_to_user("Toy spectral results (Step 1)", df)


# output in terminal was:
#  (base) brendanlynch@Mac appliedPArticleParameters % python toy1d.py
# Parameters: L=10.0, N=2000, Delta_m=24.0, C_UFTF=1.0, num_wells=6
# L1 norm of potential V over domain = 15.0084 (finite, so LIC satisfied in this toy model)

# Lowest eigenvalues (lambda) and mapped masses (m_i):
#  level  eigenvalue_lambda  mass_m_i
#      1          -2.180427  0.000000
#      2          -1.461553  0.000000
#      3          -0.932076  0.000000
#      4          -0.189345  0.000000
#      5           0.269565  0.105980
#      6           1.652437  0.262396
#      7           2.684631  0.334454
#      8           4.914206  0.452503
#      9           4.922818  0.452899
#     10           8.415324  0.592147

# Example mass ratios (first three levels):
#   m1:m2 = nan
#   m2:m3 = nan
#   m1:m3 = nan

# Saved results CSV: step1_spectral_results.csv
# (base) brendanlynch@Mac appliedPArticleParameters % 

# output from the step1_spectral_results CSV was:
# level,eigenvalue_lambda,mass_m_i
# 1,-2.1804271164524587,0.0
# 2,-1.4615526577268372,0.0
# 3,-0.9320755195088594,0.0
# 4,-0.18934455430110816,0.0
# 5,0.26956453205472264,0.10598044867936779
# 6,1.6524372070031994,0.2623957893941897
# 7,2.684630729664764,0.33445420274834614
# 8,4.914205784444167,0.45250256833728614
# 9,4.922818390620404,0.4528989213307058
# 10,8.415324237293675,0.5921473717641889