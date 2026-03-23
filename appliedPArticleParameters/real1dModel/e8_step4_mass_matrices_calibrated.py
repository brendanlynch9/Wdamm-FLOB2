# e8_step4_mass_matrices_calibrated.py
# Calculates the Fermion Mass Matrix (M) and the physical mass eigenvalues (M_i)
# using the Yukawa overlap matrix (Y) and applying the necessary UFT-F mass scale correction.

import numpy as np
import math
import pandas as pd

# ------------------------------------------------------------------
# 1. AXIOMATIC CONSTANTS AND PHYSICAL TARGETS
# ------------------------------------------------------------------

# Higgs vacuum expectation value (vev)
v_GeV = 246.0

# Physical constants for comparison (Measured Lepton Masses in MeV)
m_e_MeV = 0.5109989461
m_mu_MeV = 105.6583745
m_tau_MeV = 1776.86

# ------------------------------------------------------------------
# 2. YUKAWA MATRIX INPUT (The calculated output from e8_step3_yukawa_overlaps.py)
# ------------------------------------------------------------------
# This 8x8 matrix is for modes 5 through 12.
Y = np.array([
    [0.9999999999999998, 1.0663472772787614e-16, -1.777245462131269e-17, 1.0125982220091774e-12, 5.84355174092437e-13, 1.8217345091703666e-13, -1.8958738012267616e-06, 3.750610542396944e-07],
    [1.0663472772787614e-16, 1.0, 1.4217963697050151e-16, 1.1384742122810854e-12, 5.378945037996561e-13, -3.535894170335805e-13, 1.83650781571899e-06, 8.091336294314222e-07],
    [-1.777245462131269e-17, 1.4217963697050151e-16, 1.0, -7.384610762992763e-13, 7.50298083812139018e-12, -1.503800155291437e-12, 8.091336294314222e-07, 7.425438070406594e-07],
    [1.0125982220091774e-12, 1.1384742122810854e-12, -7.384610762992763e-13, 0.8217971940520429, 0.5533959390254017, -6.093124547230063e-13, 1.7669009047636149e-06, -1.6372501090079364e-06],
    [5.84355174092437e-13, 5.378945037996561e-13, 7.50298083812139018e-12, 0.5533959390254017, 0.8217971940520429, 3.942245242987747e-13, 1.4821054445607864e-06, 6.525771193735761e-07],
    [1.8217345091703666e-13, -3.535894170335805e-13, -1.503800155291437e-12, -6.093124547230063e-13, 3.942245242987747e-13, 0.9999999999999998, -1.6953374031773411e-06, 2.7698744357953574e-07],
    [-1.8958738012267616e-06, 1.83650781571899e-06, 8.091336294314222e-07, 1.7669009047636149e-06, 1.4821054445607864e-06, -1.6953374031773411e-06, 0.9999999999999998, 1.0663472772787614e-16],
    [3.750610542396944e-07, 8.091336294314222e-07, 7.425438070406594e-07, -1.6372501090079364e-06, 6.525771193735761e-07, 2.7698744357953574e-07, 1.0663472772787614e-16, 1.0]
])

# ----------------- Core Mass Matrix Calculation -----------------
print("--- Step 4: Calibrated Fermion Mass Matrix Calculation ---")

# 1. Standard Model Scaling Factor from Higgs VEV (in GeV)
C_scale = v_GeV / math.sqrt(2.0)

# 2. Construct the Mass Matrix M (in GeV)
# M_ij = C_scale * Y_ij
M_uncalibrated = C_scale * Y

# 3. Calculate Singular Values (Uncalibrated Mass Eigenvalues)
singular_values_GeV_uncalib = np.linalg.svd(M_uncalibrated, compute_uv=False)
mass_eigenvalues_GeV_uncalib = np.sort(singular_values_GeV_uncalib)[::-1] # Sort descending

# The largest calculated singular value is at index 0. We use this to derive the correction factor.
max_mass_calc_MeV = mass_eigenvalues_GeV_uncalib[0] * 1000.0

# 4. Global Calibration Factor (C_corr)
# C_corr is the factor needed to map the largest calculated mass (m_max_calc) to the target Tau mass (m_tau_MeV).
C_corr = m_tau_MeV / max_mass_calc_MeV
print(f"Uncalibrated max mass (MeV): {max_mass_calc_MeV:.8f} MeV")
print(f"Calibration Factor (C_corr): {C_corr:.10f}")

# 5. Apply Calibration to Masses
mass_eigenvalues_MeV = mass_eigenvalues_GeV_uncalib * 1000.0 * C_corr
m_calc_MeV = mass_eigenvalues_MeV[:3] # Get the top three masses (Tau, Muon, Electron)

# 6. Summary and Comparison
print("\nPredicted Physical Mass Eigenvalues (Leptons) (in MeV):")
# Assign labels based on magnitude (m_tau > m_mu > m_e). Since mass_eigenvalues_MeV is descending:
print(f"  Tau Mass (m_tau)      : {m_calc_MeV[0]:.8f} MeV (Target: {m_tau_MeV} MeV)")
print(f"  Muon Mass (m_mu)      : {m_calc_MeV[1]:.8f} MeV (Target: {m_mu_MeV} MeV)")
print(f"  Electron Mass (m_e)   : {m_calc_MeV[2]:.8f} MeV (Target: {m_e_MeV} MeV)")


# 7. Save results
results_df = pd.DataFrame({
    'Mass_Eigenvalue_GeV': mass_eigenvalues_GeV_uncalib * C_corr,
    'Mass_Eigenvalue_MeV': mass_eigenvalues_MeV
})
# Assign generation labels based on magnitude
labels = ['m_tau (Gen 3)', 'm_muon (Gen 2)', 'm_electron (Gen 1)'] + [f'Heavy Mass (Mode {i+4})' for i in range(5)]
results_df['Generation_Label'] = labels
results_df.to_csv('e8_step4_mass_eigenvalues_calibrated.csv', index=False)
print("\nResults saved to: e8_step4_mass_eigenvalues_calibrated.csv")

# ----------------- END OF STEP 4 -----------------

# the output was:
# (base) brendanlynch@Mac appliedPArticleParameters % python e8_step4_mass_matrices_calibrated.py
# --- Step 4: Calibrated Fermion Mass Matrix Calculation ---
# Uncalibrated max mass (MeV): 239212.46390337 MeV
# Calibration Factor (C_corr): 0.0074279574

# Predicted Physical Mass Eigenvalues (Leptons) (in MeV):
#   Tau Mass (m_tau)      : 1776.86000000 MeV (Target: 1776.86 MeV)
#   Muon Mass (m_mu)      : 1292.08453586 MeV (Target: 105.6583745 MeV)
#   Electron Mass (m_e)   : 1292.08182427 MeV (Target: 0.5109989461 MeV)

# Results saved to: e8_step4_mass_eigenvalues_calibrated.csv
# (base) brendanlynch@Mac appliedPArticleParameters % 

# gemini said:
# This output confirms the successful global **mass scale calibration** within the $\mathbf{UFT-F}$ spectral framework, but simultaneously reveals the inherent limitations of the simplified $\mathbf{1D}$ toy model.

# ***

# ## Analysis of Calibrated Results

# The script, which applies a global correction factor $\mathbf{C_{\text{corr}}}$ derived from the $\mathbf{m_{\tau}}$ mass, yielded the following results:

# ### 1. The Calibration Success

# The **Tau Mass ($\mathbf{m_{\tau}}$)** is fixed by the calibration factor $\mathbf{C_{\text{corr}}}$ (0.0074279574) to match its physical target:
# * **Predicted $\mathbf{m_{\tau}}$:** $1776.86 \text{ MeV}$ (Matches Target)

# ### 2. The Generational Hierarchy Failure

# The model fails to generate the required mass hierarchy between the second and first generations ($\mathbf{m_{\mu}}$ and $\mathbf{m_{e}}$), which were nearly degenerate in the uncalibrated $\mathbf{Y}$ matrix:

# | Particle | Predicted Mass (MeV) | Target Mass (MeV) | Discrepancy (Factor) |
# | :--- | :--- | :--- | :--- |
# | **Muon ($\mathbf{m_{\mu}}$)** | **1292.08** | $105.66$ | $\approx 12.2 \times$ too large |
# | **Electron ($\mathbf{m_{e}}$)** | **1292.08** | $0.511$ | $\approx 2528 \times$ too large |

# The predicted values for $\mathbf{m_{\mu}}$ and $\mathbf{m_{e}}$ are nearly identical ($\approx 1292 \text{ MeV}$), which is incorrect, as the physical masses differ by a factor of roughly $207$ ($\mathbf{m_{\mu}/m_{e}} \approx 207$).

# ***

# ## Conclusion: Limitation of the Toy Model

# This systematic failure indicates that the **simplified 1D Base-24 Toy Potential** ($\mathbf{V_{\text{info}}(x)}$) used to generate the eigenstates is **not sufficiently complex** or geometrically constrained to reproduce the physical **generational mass hierarchy**.

# In the $\mathbf{UFT-F}$ context, the calculation requires a model that correctly enforces the $\mathbf{E}_8/\mathbf{K}3$ synthesis, where:

# 1.  **Dimensionality:** The $\mathbf{1D}$ model fails to capture the necessary mixing and spectral splitting derived from the full $8\times 8$ $\mathbf{E}_8$ lattice geometry embedded in the $24$-dimensional space, which demands a higher-dimensional or more intricate potential structure.
# 2.  **Spectral Splitting:** The near-degenerate uncalibrated masses show that the $1\text{D}$ potential is not strongly enough perturbed to separate the intermediate $\mathbf{m_{\mu}}$ and $\mathbf{m_{e}}$ modes to the required degree.

# To proceed toward physical accuracy in the $\mathbf{UFT-F}$ framework, the next step involves moving beyond this $1\text{D}$ Toy Model to a **$2\text{D}$ or $3\text{D}$ lattice simulation** of the informational potential, often constrained by $\mathbf{K3}$ surface topology, to generate the requisite **spectral fine-structure** that achieves the correct mass ratios.