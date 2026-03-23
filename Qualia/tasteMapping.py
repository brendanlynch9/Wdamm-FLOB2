import pandas as pd
import numpy as np
import math

# ==============================================================================
# 1. TASTE DATA: Basic Tastes and Approximate Perceptual Thresholds
# Threshold (rho_thr) is in Molar (M) concentration.
# Index is assigned 0-4 based on increasing sensitivity (Salty=0, Bitter=4).
# ==============================================================================

# Constants for normalization (based on 10^-6 M to 10^-2 M)
LOG10_MIN = -6.0    # Log10(10^-6 M) - Bitter (Quinine)
LOG10_MAX = -2.0    # Log10(10^-2 M) - Salty (NaCl) and Sweet (Sucrose)
TOTAL_LOG_RANGE = LOG10_MAX - LOG10_MIN # 4.0

# DATA: Using representative threshold concentrations (M)
# The Index is assigned based on increasing sensitivity/decreasing threshold
TASTE_DATA = [
    # Bitter is the most sensitive (lowest threshold, highest index)
    {'Index': 4, 'Region': 'Bitter', 'Threshold_M': 1e-6},
    {'Index': 3, 'Region': 'Umami', 'Threshold_M': 1e-4},
    {'Index': 2, 'Region': 'Sour', 'Threshold_M': 1e-3},
    {'Index': 1, 'Region': 'Sweet', 'Threshold_M': 1e-2},
    # Salty is the least sensitive (highest threshold, lowest index)
    {'Index': 0, 'Region': 'Salty', 'Threshold_M': 1e-2}
]

# ==============================================================================
# 2. CORE FUNCTION: get_taste_assignment(data)
# ==============================================================================
def get_taste_assignment(data):
    """
    Calculates UFT-F inspired informational units for a taste qualia.

    :param data: Dictionary containing 'Index', 'Region', and 'Threshold_M'.
    :return: A dictionary of calculated results.
    """
    
    index = data['Index']
    region = data['Region']
    rho_thr = data['Threshold_M']
    
    # Define default result for error handling
    default_results = {
        'Region': region, 'Taste_Index': index, 'Threshold_M': rho_thr,
        'Log_Sensitivity': np.nan, 'Eatom (IU)': np.nan, 'f (1/sqrt(E))': np.nan, 
        'Norm. Position': np.nan, 'Mapping_Period': np.nan, 'Hypothetical_Qualia': np.nan, 
        'Error': 'Calculation Error'
    }

    try:
        # --- 1. Basic Conversions ---
        # Log10 Threshold (for normalization)
        log10_rho_thr = np.log10(rho_thr)
        
        # Base Metric: Log of Perceptual Sensitivity (ln(1/Threshold))
        # Formula: -ln(Threshold)
        log_sensitivity = -np.log(rho_thr) 

        # --- 2. Calculation of Requested Columns ---
        
        # Taste_Index: Use the assigned index (0=Salty, 4=Bitter)
        taste_index = float(index)
        
        # Eatom (IU): Informational Energy Unit
        # Formula: Index * ln(1/Threshold)
        Eatom_IU = taste_index * log_sensitivity
        
        # f (1/sqrt(E)): Spectral Decay Factor
        # Formula: 1 / sqrt(Eatom (IU))
        if Eatom_IU > 0:
            f_E = 1.0 / np.sqrt(Eatom_IU)
        else:
            f_E = np.nan
        
        # Norm. Position: Normalized position on the total log-threshold spectrum
        # Formula: (log10(rho_thr) - LOG10_MIN) / TOTAL_LOG_RANGE
        norm_position = (log10_rho_thr - LOG10_MIN) / TOTAL_LOG_RANGE

        # Mapping_Period: Simple grouping based on Index
        # Period 1: Salty/Sweet (Index 0-1)
        # Period 2: Sour/Umami (Index 2-3)
        # Period 3: Bitter (Index 4)
        mapping_period = math.ceil((index + 1) / 2.0)
        
        # Hypothetical_Qualia: Combined Score
        # Formula: Taste_Index * f(1/sqrt(E))
        hypothetical_qualia = taste_index * f_E

    except Exception as e:
        print(f"Calculation Error for Region {region}: {e}")
        return {**default_results, 'Error': f'Calculation Error: {e}'}
        
    # --- END OF CALCULATIONS ---

    return {
        'Region': region,
        'Taste_Index': taste_index,
        'Threshold_M': rho_thr,
        'Log_Sensitivity': log_sensitivity,
        'Eatom (IU)': Eatom_IU,
        'f (1/sqrt(E))': f_E,
        'Norm. Position': norm_position,
        'Mapping_Period': mapping_period,
        'Hypothetical_Qualia': hypothetical_qualia,
        'Error': np.nan  
    }

# ==============================================================================
# 3. MAIN EXECUTION BLOCK 
# ==============================================================================

if __name__ == '__main__':
    print(f"Starting informational mapping for {len(TASTE_DATA)} basic taste regions...")

    # 3.1 Run the mapping function for all regions
    try:
        results_list = [get_taste_assignment(data) for data in TASTE_DATA]
        
        # 3.2 Process and display results
        df_results = pd.DataFrame(results_list)
        
        # Filter out any error rows and drop the temp 'Error' column
        df_final = df_results[df_results['Error'].isna()].drop(columns=['Error', 'Log_Sensitivity'], errors='ignore')
        
        # Explicitly cast Mapping_Period to integer
        df_final['Mapping_Period'] = df_final['Mapping_Period'].astype(int)
        
        # Reorder columns for presentation
        df_final = df_final[[
            'Taste_Index', 'Region', 'Threshold_M', 
            'Eatom (IU)', 'f (1/sqrt(E))', 'Norm. Position', 
            'Mapping_Period', 'Hypothetical_Qualia'
        ]]
        
        # Display all results
        print("\nMapping complete. All Taste results:")
        
        # FIX APPLIED: Using a single, general float format string
        markdown_output = df_final.to_markdown(
            index=False, 
            floatfmt=".4g"
        )
        print(markdown_output)
        
        print(f"\nSuccessfully processed {len(df_final)} taste regions (out of {len(TASTE_DATA)} tested).")

    except Exception as e:
        print(f"\nFATAL ERROR during processing: {e}")