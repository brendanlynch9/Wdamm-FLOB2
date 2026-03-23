import pandas as pd
import numpy as np
import math

# ==============================================================================
# 1. OLFACTION DATA: 7 Olfactory Qualia and Approximate Molar Thresholds (M)
# Index is assigned 0-6 based on increasing sensitivity (decreasing threshold).
# ==============================================================================

# Constants for normalization (Log10 scale from 10^-12 M to 10^-6 M)
LOG10_MIN = -12.0    # Log10(10^-12 M) - Putrid/Most Sensitive (Boundary)
LOG10_MAX = -6.0     # Log10(10^-6 M) - Fragrant/Least Sensitive (Boundary)
TOTAL_LOG_RANGE = LOG10_MAX - LOG10_MIN # 6.0

# DATA: 7 Olfactory Regions ordered by increasing sensitivity (Index 0 is least sensitive)
OLFACTION_DATA = [
    # Lowest Sensitivity/Highest Threshold
    {'Index': 0, 'Region': 'Fragrant (Floral)', 'Threshold_M': 1e-6},
    {'Index': 1, 'Region': 'Resinous (Camphor)', 'Threshold_M': 1e-7},
    {'Index': 2, 'Region': 'Ethereal (Fruity)', 'Threshold_M': 1e-8},
    {'Index': 3, 'Region': 'Spicy (Aromatic)', 'Threshold_M': 1e-9},
    {'Index': 4, 'Region': 'Burnt (Empyreumatic)', 'Threshold_M': 1e-10},
    {'Index': 5, 'Region': 'Chemical (Pungent)', 'Threshold_M': 1e-11},
    # Highest Sensitivity/Lowest Threshold
    {'Index': 6, 'Region': 'Putrid (Foul)', 'Threshold_M': 1e-12} 
]

# ==============================================================================
# 2. CORE FUNCTION: get_smell_assignment(data)
# ==============================================================================
def get_smell_assignment(data):
    """
    Calculates UFT-F inspired informational units for an olfactory qualia.
    """
    
    index = data['Index']
    region = data['Region']
    rho_thr = data['Threshold_M']
    
    default_results = {
        'Region': region, 'Olfaction_Index': index, 'Threshold_M': rho_thr,
        'Eatom (IU)': np.nan, 'f (1/sqrt(E))': np.nan, 
        'Norm. Position': np.nan, 'Mapping_Period': np.nan, 'Hypothetical_Qualia': np.nan, 
        'Error': 'Calculation Error'
    }

    try:
        # --- 1. Base Conversions ---
        log10_rho_thr = np.log10(rho_thr)
        # Base Metric: Natural Log of Perceptual Sensitivity (1/Threshold)
        log_sensitivity = -np.log(rho_thr) 
        
        # --- 2. Calculation of Requested Columns ---
        
        olfaction_index = float(index)
        
        # Eatom (IU): Informational Energy Unit: Index * ln(1/Threshold)
        Eatom_IU = olfaction_index * log_sensitivity
        
        # f (1/sqrt(E)): Spectral Decay Factor
        if Eatom_IU > 0:
            f_E = 1.0 / np.sqrt(Eatom_IU)
        else:
            f_E = np.nan
        
        # Norm. Position: Normalized position on the log-threshold spectrum
        # Note: log10_rho_thr goes from -6 (fragrant) to -12 (putrid)
        norm_position = (log10_rho_thr - LOG10_MAX) / (LOG10_MIN - LOG10_MAX)

        # Mapping_Period: Simple grouping based on Index
        mapping_period = math.ceil((index + 1) / 2.0)
        if index == 6: mapping_period = 4
        
        # Hypothetical_Qualia: Combined Score: Index * f(1/sqrt(E))
        hypothetical_qualia = olfaction_index * f_E

    except Exception as e:
        return {**default_results, 'Error': f'Calculation Error: {e}'}
        
    return {
        'Region': region, 'Olfaction_Index': olfaction_index, 'Threshold_M': rho_thr,
        'Eatom (IU)': Eatom_IU, 'f (1/sqrt(E))': f_E,
        'Norm. Position': norm_position, 'Mapping_Period': mapping_period, 
        'Hypothetical_Qualia': hypothetical_qualia, 'Error': np.nan  
    }

# ==============================================================================
# 3. MAIN EXECUTION BLOCK 
# ==============================================================================

if __name__ == '__main__':
    print(f"Starting informational mapping for {len(OLFACTION_DATA)} olfactory regions (Fragrant to Putrid)...")

    try:
        results_list = [get_smell_assignment(data) for data in OLFACTION_DATA]
        df_results = pd.DataFrame(results_list)
        df_final = df_results[df_results['Error'].isna()].drop(columns=['Error'], errors='ignore')
        df_final['Mapping_Period'] = df_final['Mapping_Period'].astype(int)
        
        df_final = df_final[[
            'Olfaction_Index', 'Region', 'Threshold_M', 
            'Eatom (IU)', 'f (1/sqrt(E))', 'Norm. Position', 
            'Mapping_Period', 'Hypothetical_Qualia'
        ]]
        
        print("\nMapping complete. All Olfaction results:")
        
        markdown_output = df_final.to_markdown(
            index=False, 
            floatfmt=".4g"
        )
        print(markdown_output)
        
        print(f"\nSuccessfully processed {len(df_final)} olfactory regions (out of {len(OLFACTION_DATA)} tested).")

    except Exception as e:
        print(f"\nFATAL ERROR during processing: {e}")