import numpy as np
import pandas as pd

# -------------------------------
# Step 2: Mass calibration script
# -------------------------------

# Input eigenvalues from your Step 1 CSV (positive modes only)
positive_modes = [
    (5, 0.26956453205472264, 0.10598044867936779),
    (6, 1.6524372070031994, 0.2623957893941897),
    (7, 2.684630729664764, 0.33445420274834614),
    (8, 4.914205784444167, 0.45250256833728614),
    (9, 4.922818390620404, 0.4528989213307058),
    (10, 8.415324237293675, 0.5921473717641889),
]

Delta_m = 24.0                       # Base-24 scale from the paper
m_electron = 0.5109989461            # Measured electron mass (MeV)


# --- Convert to nicer arrays ---
levels = [pm[0] for pm in positive_modes]
lambdas = np.array([pm[1] for pm in positive_modes])
m_raw = np.array([pm[2] for pm in positive_modes])

print("Calibration and Step-2 toy mapping results")
print("-----------------------------------------")
print(f"Delta_m = {Delta_m}, C_UFTF_default = 1")

λ1 = lambdas[0]
m_raw1 = m_raw[0]

print(f"First positive eigenvalue level = {levels[0]}, lambda = {λ1}")
print(f"Model raw mass for that level (C=1): {m_raw1} (arbitrary units)")

# ---------------------------------------------------------
# Calibration: choose C_UFTF so that m_raw1 * C = m_electron
# ---------------------------------------------------------
C_cal = m_electron / m_raw1
print(f"\nCalibrated modularity constant C_UFTF -> {C_cal:.6f}"
      f" to map that mode to m_e = {m_electron} MeV\n")

# Compute calibrated masses for all levels
m_calibrated = m_raw * C_cal

# Save results to CSV
df = pd.DataFrame({
    "level": levels,
    "eigenvalue_lambda": lambdas,
    "mass_raw_model": m_raw,
    "mass_calibrated_MeV": m_calibrated
})

outname = "step2_masses_calibrated.csv"
df.to_csv(outname, index=False)

print("Calibrated masses (first positive modes) — saved to:", outname)
print(df)

# the output in terminal was:
# (base) brendanlynch@Mac appliedPArticleParameters % python step2.py
# Calibration and Step-2 toy mapping results
# -----------------------------------------
# Delta_m = 24.0, C_UFTF_default = 1
# First positive eigenvalue level = 5, lambda = 0.26956453205472264
# Model raw mass for that level (C=1): 0.10598044867936779 (arbitrary units)

# Calibrated modularity constant C_UFTF -> 4.821634 to map that mode to m_e = 0.5109989461 MeV

# Calibrated masses (first positive modes) — saved to: step2_masses_calibrated.csv
#    level  eigenvalue_lambda  mass_raw_model  mass_calibrated_MeV
# 0      5           0.269565        0.105980             0.510999
# 1      6           1.652437        0.262396             1.265176
# 2      7           2.684631        0.334454             1.612616
# 3      8           4.914206        0.452503             2.181802
# 4      9           4.922818        0.452899             2.183713
# 5     10           8.415324        0.592147             2.855118
# (base) brendanlynch@Mac appliedPArticleParameters % 

# step2_masses_calibrated csv was:
# level,eigenvalue_lambda,mass_raw_model,mass_calibrated_MeV
# 5,0.26956453205472264,0.10598044867936779,0.5109989461
# 6,1.6524372070031994,0.2623957893941897,1.2651764878554612
# 7,2.684630729664764,0.33445420274834614,1.6126157914293906
# 8,4.914205784444167,0.45250256833728614,2.1818018173092697
# 9,4.922818390620404,0.4528989213307058,2.1837128864210245
# 10,8.415324237293675,0.5921473717641889,2.8551179644731284
