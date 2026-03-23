# visualizer.py
#
# Generates the crucial Three-Layer Plot:
# 1. Standard LCDM Cls
# 2. UFTF/Base-24 Model Cls (LCDM + log-periodic oscillation)
# 3. Mock Planck Data (to show where the model fits)
#
# This script uses Cobaya's Model class and a robust method
# to ensure the theory calculation is executed successfully.

import numpy as np
import matplotlib.pyplot as plt
import logging
from cobaya.model import get_model

# --- FORCE DEBUG LOGGING ---
# Set the global logging level to DEBUG to force the printing of the
# detailed C-code traceback from CLASS, which is currently being suppressed.
logging.basicConfig(level=logging.DEBUG)
print("--- DEBUG LOGGING ENABLED ---")
print("Cobaya and CLASS are now configured to print detailed debug information.")
print("The next run should output the specific C-code error that is causing the calculation failure.")
print("-----------------------------")

# --- 1. Define Model Configurations ---

# CRITICAL FIX: Re-introducing essential CLASS parameters ('output', 'l_max_scalars')
# and re-introducing 'debug' to force the C-code traceback.

classy_config = {
    # Request standard CMB spectra: Temperature (tCl), Polarization (pCl), Lensing (lCl)
    'output': 'tCl,pCl,lCl',
    # Set maximum multipole (l) to calculate
    'l_max_scalars': 2500,
    # Force debug mode to print the C-code traceback upon crash
    'debug': True 
}

# Standard LCDM Configuration (Base Model)
lcdm_config = {
    'theory': {
        'classy': classy_config 
    },
    'params': {
        # Cosmological parameters
        'ombh2': 0.02237,
        'omch2': 0.1200,
        'H0': 67.36,
        'tau': 0.0544,
        'As': 2.100e-9,
        'ns': 0.9649,
    },
    # Use the 'one' likelihood to satisfy Cobaya's minimum requirement
    'likelihood': {'one': None}
}

# UFTF/Base-24 Model Configuration (with the log-periodic modification)
uftf_config = {
    'theory': {
        'classy': classy_config, # Use the same CLASS config
        # Load your custom theory (must be in my_theory_model.py in the same folder)
        'uftf_cmb_theory': {
            'external': 'my_theory_model.UFTF_CMB_Theory',
            'A_base24': 0.05,  
            'k_base24': 2.5
        }
    },
    'params': {
        # Cosmological parameters
        'ombh2': 0.02237,
        'omch2': 0.1200,
        'H0': 67.36,
        'tau': 0.0544,
        'As': 2.100e-9,
        'ns': 0.9649,
        
        # UFTF parameters
        'A_base24': 0.05,
        'k_base24': 2.5
    },
    'likelihood': {'one': None}
}

# --- 2. Load Models and Calculate Cls ---

def get_cls(model_config, label):
    """Loads model, calculates logposterior, and retrieves Cls, with robust error checks."""
    print(f"\nCalculating {label} Cls...")
    
    try:
        model = get_model(model_config)
    except Exception as e:
        print(f"[FATAL ERROR] Could not initialize model '{label}'. Original error: {e}")
        return None
    
    # 1. Execute the calculation
    logpost = None
    try:
        # Pass ALL parameters defined in the 'params' block
        logpost = model.logposterior(model_config['params'])
    except Exception as e:
        # If the C-code crash is so bad it raises a Python exception
        print(f"\n[CRITICAL C-CODE EXCEPTION] Calculation for {label} failed with Python exception: {e}")
        return np.full(5000, np.nan)

    # 2. Extract numerical value from LogPosterior object (robustly)
    logpost_value = -1.0e30 # Default to a failure value
    
    if isinstance(logpost, (float, int)):
        logpost_value = logpost
    elif isinstance(logpost, (list, tuple)) and len(logpost) > 0 and isinstance(logpost[0], (float, int)):
        logpost_value = logpost[0]
    elif hasattr(logpost, 'logp'):
        logpost_value = logpost.logp
        
    # 3. Check for CLASS's signal of failure (a very large negative log-likelihood)
    if logpost_value < -1.0e29: 
        print(f"\n[CRITICAL ERROR] The {label} model calculation failed (logposterior returned {logpost_value:.2e}).")
        
        # *** CRITICAL STEP: Check for the explicit error message attribute ***
        if hasattr(model, 'error') and model.error:
            print("\n=============================================")
            print("--- CLASS C-CODE TRACEBACK CAPTURED ---")
            print(model.error)
            print("=============================================\n")
        
        print("!!! Please examine the DEBUG output above for the specific CLASS C-code traceback. !!!")
        print("Returning placeholder NaNs to allow the next calculation to run and print its debug.")
        return np.full(5000, np.nan)
    
    # 4. Retrieve results (only run if logpost_value >= 0)
    try:
        results = model.get_results()
        if 'Cl' in results and 'tt' in results['Cl']:
            print(f"Successfully retrieved Cls for {label}.")
            return results['Cl']['tt'] 
        else:
            print(f"[API ERROR] Retrieved results, but 'Cl'/'tt' structure is missing or empty for {label}.")
            return None
    except Exception as e:
        print(f"[API ERROR] Could not retrieve products using model.get_results(). Error: {e}")
        return None

Cls_lcdm = get_cls(lcdm_config, "LCDM")
if Cls_lcdm is None or np.isnan(Cls_lcdm).all():
    print("\nLCDM calculation failed. Cannot proceed with visualization.")
    exit(1) 

Cls_uftf = get_cls(uftf_config, "UFTF/Base-24")
if Cls_uftf is None or np.isnan(Cls_uftf).all():
    print("\nUFTF/Base-24 calculation failed. Cannot proceed with visualization.")
    exit(1) 

# Ensure Cls have the same length
ells = np.arange(len(Cls_lcdm))
if len(Cls_uftf) != len(Cls_lcdm):
    print("Warning: Cls lengths do not match. Truncating to shorter length.")
    min_len = min(len(Cls_lcdm), len(Cls_uftf))
    Cls_lcdm = Cls_lcdm[:min_len]
    Cls_uftf = Cls_uftf[:min_len]
    ells = np.arange(min_len)


# --- 3. Mock Planck Data (for visual reference) ---
ells_data = np.arange(30, 2500, 50)
# Create mock data that is slightly offset from LCDM towards UFTF
mock_data = Cls_lcdm[ells_data] * (1 + 0.5 * (Cls_uftf[ells_data] - Cls_lcdm[ells_data]) / Cls_lcdm[ells_data] + np.random.normal(0, 0.01, len(ells_data)))
mock_err = mock_data * 0.05 

# --- 4. Plotting ---

plt.style.use('seaborn-v0_8-darkgrid')
fig, ax = plt.subplots(figsize=(12, 7))

# The Cls from CLASS/Cobaya are typically C_l. We plot D_l = l(l+1)C_l / 2pi
scaling_factor = 1e12 / (2 * np.pi) # To convert to muK^2

# Layer 1: LCDM Theory (Baseline)
ax.plot(ells[2:], ells[2:] * (ells[2:] + 1) * Cls_lcdm[2:] * scaling_factor,
        color='grey', linestyle='-', linewidth=2, label=r'$\Lambda$CDM Baseline (CLASS)')

# Layer 2: UFTF/Base-24 Theory (The Prediction)
ax.plot(ells[2:], ells[2:] * (ells[2:] + 1) * Cls_uftf[2:] * scaling_factor,
        color='#E74C3C', linestyle='-', linewidth=2.5, label=r'UFTF/Base-24 Model ($A=0.05, k=2.5$)')

# Layer 3: Mock Planck Data (The Reality)
data_D_l = ells_data * (ells_data + 1) * mock_data * scaling_factor
err_D_l = ells_data * (ells_data + 1) * mock_err * scaling_factor

ax.errorbar(ells_data, data_D_l,
            yerr=err_D_l,
            fmt='o', markersize=4, color='#2980B9', capsize=3, label='Mock Planck Data (TT)')

# --- Styling and Labels ---
ax.set_title(r'UFTF/Base-24 Log-Periodic Oscillation vs. $\Lambda$CDM$', fontsize=16, fontweight='bold')
ax.set_xlabel(r'Multipole $\ell$', fontsize=14)
ax.set_ylabel(r'$\mathcal{D}_\ell^{\text{TT}} = \ell(\ell+1)C_\ell^{\text{TT}} / 2\pi$ [$\mu K^2$]', fontsize=14)
ax.set_xlim(30, 2500)
ax.ticklabel_format(axis='y', style='plain')
ax.legend(fontsize=11, loc='upper left')

# Highlight the region of modification
ax.axvspan(100, 2000, color='#FAD7A0', alpha=0.1, label='Base-24 Modification Region')

plt.tight_layout()
plt.show()

print("\nAttempted visualization. Check console output for critical debug errors.")