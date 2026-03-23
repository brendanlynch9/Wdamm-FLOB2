# e8_step4_mass_matrices.py
# Calculates the Fermion Mass Matrix (M) and the physical mass eigenvalues (M_i)
# using the Yukawa overlap matrix (Y) from the previous step.

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
# Note the intentional off-diagonal mixing between modes 8 and 9 (Y[3,4] and Y[4,3]).
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
print("--- Step 4: Fermion Mass Matrix Calculation ---")

# 1. Scaling factor from Higgs VEV
C_scale = v_GeV / math.sqrt(2.0)
print(f"Scaling constant (v_GeV / sqrt(2)): {C_scale:.4f} GeV")

# 2. Construct the Mass Matrix M (in GeV)
# M_ij = C_scale * Y_ij
M = C_scale * Y

# 3. Calculate Singular Values (Physical Mass Eigenvalues)
# Singular values of M are the physical masses (mass eigenstates).
singular_values = np.linalg.svd(M, compute_uv=False)
mass_eigenvalues_GeV = np.sort(singular_values)[::-1] # Sort descending

# 4. Filter and Convert to MeV for comparison
# The three largest non-zero masses are predicted to be the three charged leptons (e, mu, tau).
m_calc_MeV = mass_eigenvalues_GeV[:3] * 1000.0

# 5. Summary and Comparison
print("\nPredicted Physical Mass Eigenvalues (Leptons) (in MeV):")
print(f"  Electron Mass (m_e)   : {m_calc_MeV[0]:.8f} MeV (Target: {m_e_MeV} MeV)")
print(f"  Muon Mass (m_mu)      : {m_calc_MeV[1]:.8f} MeV (Target: {m_mu_MeV} MeV)")
print(f"  Tau Mass (m_tau)      : {m_calc_MeV[2]:.8f} MeV (Target: {m_tau_MeV} MeV)")

# 6. Save results
results_df = pd.DataFrame({
    'Mass_Eigenvalue_GeV': mass_eigenvalues_GeV,
    'Mass_Eigenvalue_MeV': mass_eigenvalues_GeV * 1000.0
})
# Assign generation labels based on magnitude
labels = ['m_electron (Gen 1)', 'm_muon (Gen 2)', 'm_tau (Gen 3)'] + [f'Heavy Mass (Mode {i+4})' for i in range(5)]
results_df['Generation_Label'] = labels
results_df.to_csv('e8_step4_mass_eigenvalues.csv', index=False)
print("\nResults saved to: e8_step4_mass_eigenvalues.csv")

# ----------------- END OF STEP 4 -----------------

