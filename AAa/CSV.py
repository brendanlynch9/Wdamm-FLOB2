import pandas as pd
import numpy as np
import statsmodels.api as sm
from scipy.stats import pearsonr, norm
from tqdm import tqdm

# --- 1. Load Data (Replace 'your_data.csv' with your actual file path) ---
try:
    df = pd.read_csv('your_data.csv')
except FileNotFoundError:
    print("Error: CSV file not found. Please provide the correct path.")
    # Create a dummy DataFrame for demonstration purposes
    data = {
        'model': np.repeat(['TinyLlama-1.1B', 'Phi-2'], 100),
        'lambda2_diag': np.random.uniform(0.1, 0.6, 200),  # O(1) diagnostic
        'lambda11_eigen': np.random.uniform(0.01, 0.1, 200), # 11th eigenvalue
        'seq_length': np.random.randint(50, 500, 200),
        'mean_token_id': np.random.uniform(100, 3000, 200)
    }
    df = pd.DataFrame(data)
    df['n'] = 200
    # Apply RoPE correlation trend for realism
    df.loc[df['model'] == 'TinyLlama-1.1B', 'lambda11_eigen'] -= 0.05 * df['lambda2_diag']
    print("Using dummy data for demonstration.")

# --- 2. Calculate Fisher Z-Transform for 95% CI ---
def fisher_z_ci(r, n, confidence=0.95):
    """Calculates the 95% Confidence Interval for Pearson's r."""
    z = 0.5 * np.log((1 + r) / (1 - r))
    se = 1 / np.sqrt(n - 3)
    z_crit = norm.ppf(1 - (1 - confidence) / 2)
    z_min = z - z_crit * se
    z_max = z + z_crit * se
    r_min = (np.exp(2 * z_min) - 1) / (np.exp(2 * z_min) + 1)
    r_max = (np.exp(2 * z_max) - 1) / (np.exp(2 * z_max) + 1)
    return r_min, r_max

# --- 3. Run Permutation Test (Tier 1, #2 Verification) ---
def permutation_p_value(X, Y, n_perms=10000):
    """Calculates p-value using a permutation test."""
    r_obs, _ = pearsonr(X, Y)
    perm_rs = []
    for _ in tqdm(range(n_perms), desc="Running Permutation Test"):
        X_perm = np.random.permutation(X)
        r_perm, _ = pearsonr(X_perm, Y)
        perm_rs.append(r_perm)
    
    # Two-tailed p-value
    p_val = np.sum(np.abs(perm_rs) >= np.abs(r_obs)) / n_perms
    return p_val

# --- 4. Main Analysis and Output (Tier 1, #2 Table Data) ---
results = []
for model_name, group in df.groupby('model'):
    X = group['lambda2_diag']
    Y = group['lambda11_eigen']
    n = len(group)
    
    # Standard Pearson Correlation
    r, p_standard = pearsonr(X, Y)
    
    # 95% CI
    r_min, r_max = fisher_z_ci(r, n)
    
    # Permutation P-value (run this only once per model, takes time)
    # p_perm = permutation_p_value(X, Y, n_perms=10000)

    results.append({
        'Model': model_name,
        'n': n,
        'r': r,
        'r_ci': f'[{r_min:.3f}, {r_max:.3f}]',
        'p_standard': p_standard,
        # 'p_perm': p_perm # Uncomment if you run the permutation test
    })

df_results = pd.DataFrame(results)
print("\n--- Correlation Results (for Table 1) ---")
print(df_results)


# --- 5. Partial Correlation / Confounder Regression (Tier 1, #1) ---
partial_results = []
for model_name, group in df.groupby('model'):
    Y = group['lambda11_eigen']
    X_main = group['lambda2_diag']
    
    # Confounders to control for (Tier 1, #1 requirement)
    X_control = group[['seq_length', 'mean_token_id']]
    
    # Add constant for intercept
    X = sm.add_constant(pd.concat([X_main, X_control], axis=1))
    
    # OLS Regression
    model = sm.OLS(Y, X).fit()
    
    # Get the P-value and Coefficient for the main diagnostic (lambda2_diag)
    lambda2_p = model.pvalues['lambda2_diag']
    lambda2_beta = model.params['lambda2_diag']
    
    partial_results.append({
        'Model': model_name,
        'n': len(group),
        'Beta_lambda2': lambda2_beta,
        'P_value_controlled': lambda2_p,
        'R_squared': model.rsquared_adj,
        'Controls': 'Seq Length, Mean Token ID'
    })

df_partial = pd.DataFrame(partial_results)
print("\n--- Confounder Regression Results (for Appendix) ---")
print(df_partial)

# the output was:
# (base) brendanlynch@Mac zzzzzzzhourglass % python CSV.py
# Error: CSV file not found. Please provide the correct path.
# Using dummy data for demonstration.

# --- Correlation Results (for Table 1) ---
#             Model    n         r              r_ci  p_standard
# 0           Phi-2  100  0.043195   [-0.155, 0.238]    0.669582
# 1  TinyLlama-1.1B  100 -0.372190  [-0.530, -0.190]    0.000137

# --- Confounder Regression Results (for Appendix) ---
#             Model    n  ...  R_squared                   Controls
# 0           Phi-2  100  ...  -0.005586  Seq Length, Mean Token ID
# 1  TinyLlama-1.1B  100  ...   0.139302  Seq Length, Mean Token ID

# [2 rows x 6 columns]
# (base) brendanlynch@Mac zzzzzzzhourglass % 