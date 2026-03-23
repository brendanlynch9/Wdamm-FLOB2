# step4_mass_matrices.py
# Build fermion mass matrices from Yukawa overlaps (toy model)
# Requires: numpy, scipy, pandas

import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla
import pandas as pd

# ---------- Parameters ----------
L = 10.0
N = 2000
k = 12
x = np.linspace(0, L, N, endpoint=False)
dx = x[1] - x[0]

# Higgs vev
v_GeV = 246.0

# Physical constants for comparison
m_e_MeV = 0.5109989461
m_mu_MeV = 105.6583745
m_tau_MeV = 1776.86

# ---------------- Build Laplacian ----------------
e = np.ones(N)
diag = -2.0 * e
off = e.copy()
data = np.vstack([off, diag, off])
offsets = [-1, 0, 1]
Laplacian = sp.diags(data, offsets, shape=(N, N), format='csr') / (dx**2)
Laplacian = Laplacian.tolil()
Laplacian[0, -1] = 1.0/(dx**2)
Laplacian[-1, 0] = 1.0/(dx**2)
Laplacian = Laplacian.tocsr()

# ---------------- Potential (same pattern used previously) ----------------
def gaussian_well(x, center, width, depth):
    return -depth * np.exp(-0.5 * ((x-center)/width)**2)

num_wells = 6
centers = np.linspace(0, L, num_wells, endpoint=False) + 0.5*L/num_wells
width = 0.2 * (L/num_wells)
depths = np.linspace(5.0, 1.0, num_wells)
V = np.zeros_like(x)
for c, d in zip(centers, depths):
    V += gaussian_well(x, c, width, d)

# ---------------- Hamiltonian ----------------
H = -Laplacian + sp.diags(V, 0, format='csr')

# ---------------- Eigen decomposition ----------------
eigvals, eigvecs = spla.eigsh(H, k=k, which='SM')
idx = np.argsort(eigvals)
eigvals = eigvals[idx]
eigvecs = eigvecs[:, idx]

# Normalize eigenvectors (L2)
norms = np.sqrt(np.sum(np.abs(eigvecs)**2, axis=0) * dx)
eigvecs_normed = eigvecs / norms

# Select positive eigenmodes (as earlier)
pos_mask = eigvals > 0
eigvals_pos = eigvals[pos_mask]
eigvecs_pos = eigvecs_normed[:, pos_mask]
levels_pos = np.where(pos_mask)[0] + 1

num_modes = eigvecs_pos.shape[1]
print(f"Found {num_modes} positive modes: levels {levels_pos.tolist()}")

# ---------------- Higgs profile ----------------
phi_center = L/2.0
phi_width = 0.5
phi_H = np.exp(-0.5 * ((x - phi_center) / phi_width)**2)
phi_H /= np.sqrt(np.trapz(np.abs(phi_H)**2, x))

# ---------------- Compute overlap matrix G ----------------
G = np.zeros((num_modes, num_modes))
for i in range(num_modes):
    psi_i = eigvecs_pos[:, i]
    for j in range(num_modes):
        psi_j = eigvecs_pos[:, j]
        G[i, j] = np.trapz(psi_i * phi_H * psi_j, x)

# Symmetrize
G = 0.5 * (G + G.T)

# ---------------- Scale to Yukawa matrix y ----------------
# SM electron Yukawa (dimensionless) = m_e (GeV) / v (GeV)
y_e_SM = (m_e_MeV / 1000.0) / v_GeV

diag0 = np.diag(G)[0]
if np.abs(diag0) < 1e-18:
    raise RuntimeError("First diagonal of G is (nearly) zero; cannot calibrate scale.")
scale = y_e_SM / diag0

y = scale * G

# ---------------- Build mass matrix M = y * v (GeV) ----------------
M = y * v_GeV  # GeV

# compute singular values (physical masses) from sqrt(eig(M^dagger M))
MtM = M.conj().T @ M
eigvals_mass2, _ = np.linalg.eigh(MtM)
eigvals_mass2_clipped = np.clip(eigvals_mass2, 0, None)
masses_GeV = np.sqrt(eigvals_mass2_clipped)
order = np.argsort(masses_GeV)[::-1]
masses_GeV_sorted = masses_GeV[order]
masses_MeV_sorted = masses_GeV_sorted * 1000.0

# ---------------- Save CSVs ----------------
pd.DataFrame(G, index=levels_pos, columns=levels_pos).to_csv("step4_overlap_G.csv")
pd.DataFrame(y, index=levels_pos, columns=levels_pos).to_csv("step4_yukawa_y.csv")
pd.DataFrame(M, index=levels_pos, columns=levels_pos).to_csv("step4_mass_matrix_M_GeV.csv")
pd.DataFrame({
    "mode_label_sorted": [f"mode_{levels_pos[i]}" for i in order],
    "mass_GeV": masses_GeV_sorted,
    "mass_MeV": masses_MeV_sorted
}).to_csv("step4_masses_sorted.csv", index=False)

# ---------------- Print summary ----------------
print("\nScale factor used to map first diagonal to SM electron Yukawa:", scale)
print("\nFirst few diagonal elements of G (overlaps):")
for i in range(min(6, num_modes)):
    print(f" Level {levels_pos[i]}: G_ii = {G[i,i]:.6g}")

print("\nPredicted masses (sorted, MeV):")
for label, mg in zip([f"mode_{levels_pos[i]}" for i in order], masses_MeV_sorted):
    print(f" {label}: {mg:.6g} MeV")

print("\nSaved CSVs: step4_overlap_G.csv, step4_yukawa_y.csv, step4_mass_matrix_M_GeV.csv, step4_masses_sorted.csv")


# the output in terminal was:
# (base) brendanlynch@Mac appliedPArticleParameters % python step4.py
# Found 8 positive modes: levels [5, 6, 7, 8, 9, 10, 11, 12]

# Scale factor used to map first diagonal to SM electron Yukawa: 1.9209029903879366e-05

# First few diagonal elements of G (overlaps):
#  Level 5: G_ii = 0.108138
#  Level 6: G_ii = 0.0956065
#  Level 7: G_ii = 0.152129
#  Level 8: G_ii = 0.124338
#  Level 9: G_ii = 0.15248
#  Level 10: G_ii = 0.124819

# Predicted masses (sorted, MeV):
#  mode_12: 2.69829 MeV
#  mode_11: 1.7613 MeV
#  mode_10: 0.310413 MeV
#  mode_9: 0.130516 MeV
#  mode_8: 0.00994267 MeV
#  mode_7: 0.00203868 MeV
#  mode_6: 0.000126808 MeV
#  mode_5: 9.19741e-06 MeV

# Saved CSVs: step4_overlap_G.csv, step4_yukawa_y.csv, step4_mass_matrix_M_GeV.csv, step4_masses_sorted.csv
# (base) brendanlynch@Mac appliedPArticleParameters % 

# step4_masses_sorted csv output was:
#  mode_label_sorted,mass_GeV,mass_MeV
# mode_12,0.0026982901026727894,2.6982901026727895
# mode_11,0.0017612957821375624,1.7612957821375623
# mode_10,0.0003104128007642414,0.31041280076424144
# mode_9,0.0001305157494152338,0.1305157494152338
# mode_8,9.942671972269684e-06,0.009942671972269683
# mode_7,2.0386829107046824e-06,0.0020386829107046822
# mode_6,1.2680784277966957e-07,0.00012680784277966956
# mode_5,9.197412992950185e-09,9.197412992950185e-06

# step4_mass_matrix_M_GeV csv output was:
# ,5,6,7,8,9,10,11,12
# 5,0.0005109989460999999,0.00046638495510178333,9.226501934296482e-05,0.0002751454484922868,0.0003645979393619535,-0.0004170530011816259,6.81389111205658e-05,-4.096826557597765e-05
# 6,0.00046638495510178333,0.0004517809226668715,0.00019904687284012985,0.0001826657765320022,0.00043465762257184924,-0.00040276352681595235,0.00016053397136589972,-0.00011186303057991837
# 7,9.226501934296482e-05,0.00019904687284012985,0.0007188758663493936,-0.0004702175193518031,0.0005771217895379067,2.5786607580516013e-05,0.0005850575047726487,-0.0004372481624550717
# 8,0.0002751454484922868,0.0001826657765320022,-0.0004702175193518031,0.0005875482527499603,-0.00016492430592998777,-0.0003922116895313051,-0.00043170514217961216,0.00035411934519249114
# 9,0.0003645979393619535,0.00043465762257184924,0.0005771217895379067,-0.00016492430592998777,0.0007205310143422496,-0.00032857099335160625,0.0005688020406906522,-0.0004664890896681431
# 10,-0.0004170530011816259,-0.00040276352681595235,2.5786607580516013e-05,-0.0003922116895313051,-0.00032857099335160625,0.0005898234223041641,-6.108001777010505e-06,7.05932413243356e-06
# 11,6.81389111205658e-05,0.00016053397136589972,0.0005850575047726487,-0.00043170514217961216,0.0005688020406906522,-6.108001777010505e-06,0.0006884570794615184,-0.000631407665781597
# 12,-4.096826557597765e-05,-0.00011186303057991837,-0.0004372481624550717,0.00035411934519249114,-0.0004664890896681431,7.05932413243356e-06,-0.000631407665781597,0.0006446162910804074

# step 4 G overlap CSV output was:
# ,5,6,7,8,9,10,11,12
# 5,0.1081382817667369,0.09869700920419099,0.01952524703831862,0.058226648534166335,0.07715670452787766,-0.08825731500553075,0.01441964768473793,-0.008669759263031051
# 6,0.09869700920419099,0.09560648428935484,0.0421225659744542,0.03865597642131312,0.09198282857619894,-0.08523335729084815,0.033972414153084565,-0.02367260443970673
# 7,0.01952524703831862,0.0421225659744542,0.15212947420714423,-0.09950806158682476,0.12213128650672496,0.005456996452991539,0.12381065319940532,-0.09253104209788604
# 8,0.058226648534166335,0.03865597642131312,-0.09950806158682476,0.12433774862423178,-0.03490150263705316,-0.08300036334408442,-0.0913580207189553,0.07493921038730295
# 9,0.07715670452787766,0.09198282857619894,0.12213128650672496,-0.03490150263705316,0.15247973884346713,-0.06953263393322023,0.1203706501063187,-0.09871904630067545
# 10,-0.08825731500553075,-0.08523335729084815,0.005456996452991539,-0.08300036334408442,-0.06953263393322023,0.1248192230542621,-0.0012925835214243932,0.0014939036331523775
# 11,0.01441964768473793,0.033972414153084565,0.12381065319940532,-0.0913580207189553,0.1203706501063187,-0.0012925835214243932,0.1456922097615153,-0.13361933638627516
# 12,-0.008669759263031051,-0.02367260443970673,-0.09253104209788604,0.07493921038730295,-0.09871904630067545,0.0014939036331523775,-0.13361933638627516,0.1364145633729752

# step 4 yukawa CSV output was:
# ,5,6,7,8,9,10,11,12
# 5,2.077231488211382e-06,1.8958738012267616e-06,3.750610542396944e-07,1.1184774328954748e-06,1.4821054445607864e-06,-1.6953374031773411e-06,2.7698744357953574e-07,-1.6653766494299858e-07
# 6,1.8958738012267616e-06,1.83650781571899e-06,8.091336294314222e-07,7.425438070406594e-07,1.7669009047636149e-06,-1.6372501090079364e-06,6.525771193735761e-07,-4.54727766585034e-07
# 7,3.750610542396944e-07,8.091336294314222e-07,2.9222596193064782e-06,-1.9114533306983864e-06,2.346023534706938e-06,1.048236080508781e-07,2.3782825397262143e-06,-1.7774315546954134e-06
# 8,1.1184774328954748e-06,7.425438070406594e-07,-1.9114533306983864e-06,2.3884075315039035e-06,-6.704240078454788e-07,-1.5943564615093703e-06,-1.754898951949643e-06,1.4395095333028095e-06
# 9,1.4821054445607864e-06,1.7669009047636149e-06,2.346023534706938e-06,-6.704240078454788e-07,2.9289878631798763e-06,-1.3356544445187246e-06,2.3122034174416757e-06,-1.8962971124721263e-06
# 10,-1.6953374031773411e-06,-1.6372501090079364e-06,1.048236080508781e-07,-1.5943564615093703e-06,-1.3356544445187246e-06,2.3976561882283095e-06,-2.4829275516302863e-08,2.869643956273805e-08
# 11,2.7698744357953574e-07,6.525771193735761e-07,2.3782825397262143e-06,-1.754898951949643e-06,2.3122034174416757e-06,-2.4829275516302863e-08,2.798606014071213e-06,-2.566697828380476e-06
# 12,-1.6653766494299858e-07,-4.54727766585034e-07,-1.7774315546954134e-06,1.4395095333028095e-06,-1.8962971124721263e-06,2.869643956273805e-08,-2.566697828380476e-06,2.6203914271561275e-06
