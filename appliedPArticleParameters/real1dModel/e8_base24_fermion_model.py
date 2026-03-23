# e8_base24_fermion_model.py (UPGRADED FROM toy1d.py)
#
# Purpose: Replaces the arbitrary 1D potential with the axiomatic E8/Base-24 structure
# and uses the derived UFT-F Modularity Constant (C_UFTF) for a rigorous toy simulation
# of the fermion mass spectrum (eigenvalues).

import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla
import pandas as pd
import math

# ------------------------------------------------------------------
# 1. AXIOMATIC CONSTANTS (Derived from UFT-F Corpus)
# ------------------------------------------------------------------

# Hopf Torsion Invariant (omega_u): Source of T-breaking/CP-violation
# omega_u = phi_u / (2*pi) approx 0.0002073045
OMEGA_U = 0.0002073045

# Modularity Constant (C_UFTF): The spectral floor.
# C_UFTF = (331/22) * omega_u approx 0.003119337523010599
C_UFTF = (331.0 / 22.0) * OMEGA_U

# Base-24 Mass Gap (Delta_m): The minimal quantum step
DELTA_M = 24.0

# -----------------------
# 2. DOMAIN AND GRID SETUP (Compactified 1D Manifold Proxy)
# -----------------------
L = 10.0               # domain length (compactified circle)
N = 2000               # grid points
k = 12                 # number of eigenpairs to compute
x = np.linspace(0, L, N, endpoint=False)
dx = x[1] - x[0]

# -----------------------
# 3. BASE-24 INFORMATIONAL POTENTIAL (V_info)
# -----------------------
# V_info is now constructed as a Base-24 Fourier series, enforcing the harmonic
# quantization and L1-integrability (LIC) required by ACI.
# This replaces the Gaussian well sum.

def base24_informational_potential(x, L, N_modes=48):
    V = np.zeros_like(x)
    # The ACI/LIC requires rapid decay of the Fourier coefficients for L1-integrability.
    # We use a 1/n^(1+epsilon) decay (as seen in time operator potentials)
    epsilon = 0.1
    A = 30.0 # Amplitude scale (adjust for spectral floor shift)

    for n in range(1, N_modes + 1):
        # We use cos for a symmetric potential that is L1-integrable
        coeff = A / (n**(1.0 + epsilon))
        V += coeff * np.cos(2.0 * np.pi * n * x / (L / (DELTA_M/2.0)))
        # Note: L / (DELTA_M/2.0) sets the Base-24 period (L/12 in this 1D toy)
    
    # Shift the entire potential up to ensure most eigenvalues are non-negative,
    # simulating the vacuum energy setting the spectral floor.
    V_min = np.min(V)
    V = V - V_min + (DELTA_M / L)**2 # Add spectral floor proportional to Base-24
    return V

# --- Build the Potential and Check LIC ---
V = base24_informational_potential(x, L)
l1_norm = np.sum(np.abs(V)) * dx
print(f"L1 norm of V_info (LIC Check): {l1_norm:.4f} (Finite = LIC Satisfied)")


# -----------------------
# 4. BUILD HAMILTONIAN H_SM
# -----------------------

# Laplacian with periodic BCs (unchanged from toy1d.py, representing the kinetic term)
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

# Full Hamiltonian: H = -Laplacian + V_info
H = -Laplacian + sp.diags(V)
H = H.tocsr() # Sparse Hamiltonian

# -----------------------
# 5. SOLVE EIGENVALUE PROBLEM
# -----------------------
# Compute the k lowest eigenvalues and corresponding eigenvectors
eigenvalues, eigenvectors = spla.eigs(H, k=k, which='SR')

# Sort results by real part of the eigenvalue
idx = eigenvalues.argsort().real
eigenvalues = eigenvalues[idx].real
eigenvectors = eigenvectors[:, idx].real

# -----------------------
# 6. SPECTRAL MASS MAPPING (Phi_SM)
# -----------------------

# Apply the spectral map (Phi_SM) using the ACI-derived constants.
# Mass squared is proportional to eigenvalue: m^2 = C_UFTF^2 / Delta_m * lambda
# m_i = C_UFTF * sqrt(lambda_i / Delta_m)
results = []
for level, l in enumerate(eigenvalues):
    # Only positive eigenvalues yield real mass (Mass Gap)
    mass_i = C_UFTF * math.sqrt(l / DELTA_M) if l > 0 else 0.0
    results.append({
        'level': level + 1,
        'eigenvalue_lambda': l,
        'mass_m_i (C_UFTF units)': mass_i
    })

df = pd.DataFrame(results)

# Filter for the observable, positive mass modes
df_positive = df[df['mass_m_i (C_UFTF units)'] > 1e-10].reset_index(drop=True)

# -----------------------
# 7. OUTPUT
# -----------------------
print("\n--- E8/Base-24 Spectral Model Results (Fermion Masses) ---")
print(f"Modularity Constant C_UFTF: {C_UFTF:.15f}")
print(f"Mass Gap Delta_m: {DELTA_M:.1f}")
print(df_positive)

# Save the primary results for Step 2 (Calibration)
df_positive.to_csv('e8_base24_modes_for_step2.csv', index=False)
print("\nResults saved to 'e8_base24_modes_for_step2.csv'")

# Save the full eigenvector data for Step 3 (Yukawa Couplings)
# We only save the modes with non-zero mass
eigenvector_df = pd.DataFrame(eigenvectors[:, df['eigenvalue_lambda'] > 1e-10])
eigenvector_df.columns = [f"mode{i}" for i in df_positive['level']]
eigenvector_df.to_csv('e8_base24_eigenvectors_for_step3.csv', index=False)
print("Eigenvectors saved to 'e8_base24_eigenvectors_for_step3.csv'")

# the terminal output was:
# (base) brendanlynch@Mac appliedPArticleParameters % python e8_base24_fermion_model.py
# L1 norm of V_info (LIC Check): 272.1683 (Finite = LIC Satisfied)

# --- E8/Base-24 Spectral Model Results (Fermion Masses) ---
# Modularity Constant C_UFTF: 0.003118990431818
# Mass Gap Delta_m: 24.0
#     level  eigenvalue_lambda  mass_m_i (C_UFTF units)
# 0       1          20.721013                 0.002898
# 1       2          20.985334                 0.002917
# 2       3          20.985334                 0.002917
# 3       4          21.749200                 0.002969
# 4       5          21.749200                 0.002969
# 5       6          22.912751                 0.003048
# 6       7          22.912751                 0.003048
# 7       8          24.265048                 0.003136
# 8       9          24.265048                 0.003136
# 9      10          25.428387                 0.003210
# 10     11          25.428387                 0.003210
# 11     12          25.904892                 0.003240

# Results saved to 'e8_base24_modes_for_step2.csv'
# Eigenvectors saved to 'e8_base24_eigenvectors_for_step3.csv'
# (base) brendanlynch@Mac appliedPArticleParameters % 

# e8_base24_eigenvectors_for_step3.csv output was:

# too extensive to copy 

# e8 base 24 models for step 2 were: 
# level,eigenvalue_lambda,mass_m_i (C_UFTF units)
# 1,20.721012632484324,0.002898103619990042
# 2,20.98533411537212,0.002916529447089215
# 3,20.985334115375476,0.0029165294470894485
# 4,21.74919954094936,0.0029691357933736974
# 5,21.749199540951288,0.0029691357933738292
# 6,22.91275096962152,0.0030475233305761107
# 7,22.91275096962406,0.00304752333057628
# 8,24.265048497590936,0.0031361657200592147
# 9,24.265048497593224,0.003136165720059363
# 10,25.42838746160404,0.0032104642023673175
# 11,25.42838746160404,0.0032104642023673175
# 12,25.904891623243813,0.0032404051330635775

# gemini said:
# Step 2: Mass Calibration and Generational Gap AnalysisWe must now perform the calibration (Step 2) to link the model's spectral data to physical MeV units.1. Calculation of the Physical Scaling Factor ($A$)The analytical Mass Map $\Phi_{SM}$ is:$$m_i = A \cdot \left(\text{C}_{\text{UFT-F}} \cdot \sqrt{\frac{\lambda_i}{\Delta_m}}\right)$$We calibrate the first non-zero mode (Level 1) to the physical electron mass ($\mathbf{m_e}$):ParameterValueSourceElectron Mass ($\mathbf{m_e}$)$0.5109989461 \text{ MeV}$ExperimentalModel Mass ($\mathbf{m_{model, 1}}$)$0.0028981036 \text{ C}_{\text{UFT-F}} \text{ units}$Output: Level 1Modularity Constant ($\mathbf{C_{UFT-F}}$)$0.00311899043$AxiomaticThe required unit conversion/scaling factor ($A$) is:$$A = \frac{\text{Target } m_e}{\text{Model } m_{model, 1}} = \frac{0.5109989461}{0.0028981036} \approx \mathbf{176.328325}$$2. Calibrated Mass SpectrumApplying the factor $A$ to the first few positive modes yields a fine structure of the spectral floor:Levelλi​mmodel,i​ (CUFT−F​ units)mi,calibrated​ (MeV)mi​/me​ Ratio1 ($\mathbf{e}$ Candidate)$20.7210$$0.0028981$$0.510999$ (Target)$1.000$2 ($\mu'$ Candidate)$20.9853$$0.0029165$$0.514210$$1.006$4 ($\tau'$ Candidate)$21.7492$$0.0029691$$0.523455$$1.024$12 (Highest Mode)$25.9049$$0.0032404$$0.571439$$1.118$3. Model Failure and Theoretical MandateThe 1D model fails to capture the generational separation.The model's highest computed mass ($0.57 \text{ MeV}$) is only $\approx 1.12$ times the electron mass, yet the required physical mass ratios for the muon and tau are vastly larger:Target $\mathbf{m_\mu / m_e}$ Ratio: $\frac{105.658 \text{ MeV}}{0.510998 \text{ MeV}} \approx \mathbf{206.77}$Target $\mathbf{m_\tau / m_e}$ Ratio: $\frac{1776.86 \text{ MeV}}{0.510998 \text{ MeV}} \approx \mathbf{3477.1}$This failure is an expected and crucial analytical result:The simplified $\mathbf{1D \text{ Schrödinger operator}}$ ($H_{toy} = -\frac{d^2}{dx^2} + V_{info}(x)$) is only capable of generating the Base-24 fine-structure of the spectral floor. It cannot reproduce the immense generational energy gaps that span four orders of magnitude.The Theory Mandates:The mass separation must come from the geometry of the full $\mathbf{E_8/K3}$ manifold. The generational modes ($\mathbf{e, \mu, \tau}$) correspond to higher-order cycles/modes that satisfy the Dirac operator's stability conditions on the compactified manifold, leading to eigenvalues ($\lambda$) that satisfy the required quadratic ratios:$$\frac{\lambda_\mu}{\lambda_e} \approx 42,751 \quad \text{and} \quad \frac{\lambda_\tau}{\lambda_e} \approx 12,090,288$$