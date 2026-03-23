import pandas as pd
import numpy as np
import math

# ==============================================================================
# 1. SPECTRAL DATA: Representative data for the Electromagnetic Spectrum (EMS)
# Wavelengths (lambda) are in meters (m).
# Frequency (nu) will be derived using c (speed of light).
# ==============================================================================

# Constants
SPEED_OF_LIGHT = 299792458.0 # c in m/s
LAMBDA_MIN_LOG = -16.0      # Start of Gamma (10^-16 m)
LAMBDA_MAX_LOG = 5.0        # End of Radio (10^5 m)
TOTAL_LOG_RANGE = LAMBDA_MAX_LOG - LAMBDA_MIN_LOG # 21.0

SPECTRAL_DATA = [
    {'Index': 0, 'Region': 'Gamma Ray', 'Lambda_Rep_m': 1e-13},
    {'Index': 1, 'Region': 'X-ray', 'Lambda_Rep_m': 1e-9},
    {'Index': 2, 'Region': 'UV Light', 'Lambda_Rep_m': 1e-7},
    {'Index': 3, 'Region': 'Visible Light', 'Lambda_Rep_m': 5.5e-7},
    {'Index': 4, 'Region': 'Infrared (IR)', 'Lambda_Rep_m': 1e-5},
    {'Index': 5, 'Region': 'Microwave', 'Lambda_Rep_m': 1e-2},
    {'Index': 6, 'Region': 'Radio Wave', 'Lambda_Rep_m': 1e2}
]

# ==============================================================================
# 2. CORE FUNCTION: get_spectral_assignment(data)
# ==============================================================================
def get_spectral_assignment(data):
    """
    Calculates UFT-F inspired informational units for a spectral region.

    :param data: Dictionary containing 'Index', 'Region', and 'Lambda_Rep_m'.
    :return: A dictionary of calculated results.
    """
    
    index = data['Index']
    region = data['Region']
    lambda_rep = data['Lambda_Rep_m']
    
    # Define default result for error handling
    default_results = {
        'Region': region, 'Spectral_Index': index, 'Lambda_Rep_m': lambda_rep,
        'Frequency_Hz': np.nan, 'Eatom (IU)': np.nan, 'f (1/sqrt(E))': np.nan, 
        'Norm. Position': np.nan, 'Mapping_Period': np.nan, 'Hypothetical_Qualia': np.nan, 
        'Error': 'Calculation Error'
    }

    try:
        # --- 1. Basic Conversions ---
        # Frequency (nu)
        frequency = SPEED_OF_LIGHT / lambda_rep
        
        # Log of Wavelength for normalization
        log10_lambda = np.log10(lambda_rep)

        # --- 2. Calculation of Requested Columns ---
        
        # Qualia_Score / Spectral_Index: Use the Region Index as the basis score
        qualia_score = float(index)
        
        # Eatom (IU): Informational Energy Unit
        # Formula: Index * ln(Frequency)
        Eatom_IU = index * np.log(frequency)
        
        # f (1/sqrt(E)): Spectral Decay Factor
        # Formula: 1 / sqrt(Eatom (IU))
        # Handle index 0 which leads to Eatom_IU = 0
        if Eatom_IU > 0:
            f_E = 1.0 / np.sqrt(Eatom_IU)
        else:
            f_E = np.nan
        
        # Norm. Position: Normalized position on the total log-spectrum
        # Formula: (log10(lambda) - LAMBDA_MIN_LOG) / TOTAL_LOG_RANGE
        norm_position = (log10_lambda - LAMBDA_MIN_LOG) / TOTAL_LOG_RANGE

        # Mapping_Period: Simple grouping based on Index
        # Group 1 (Index 0-1): Gamma, X-ray (High Energy)
        # Group 2 (Index 2-3): UV, Visible (Mid Energy)
        # Group 3 (Index 4-5): IR, Microwave (Low Energy)
        # Group 4 (Index 6): Radio (Lowest Energy)
        mapping_period = math.ceil((index + 1) / 2.0)
        if index == 6: mapping_period = 4 # Separate category for Radio
        
        # Hypothetical_Qualia: Combined Score
        # Formula: Qualia_Score * f(1/sqrt(E))
        hypothetical_qualia = qualia_score * f_E

    except Exception as e:
        # Return default results with the specific error message
        return {**default_results, 'Error': f'Calculation Error: {e}'}
        
    # --- END OF CALCULATIONS ---

    return {
        'Region': region,
        'Spectral_Index': qualia_score,
        'Lambda_Rep_m': lambda_rep,
        'Frequency_Hz': frequency,
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
    print(f"Starting informational mapping for {len(SPECTRAL_DATA)} spectral regions (Gamma to Radio)...")

    # 3.1 Run the mapping function for all regions
    try:
        results_list = [get_spectral_assignment(data) for data in SPECTRAL_DATA]
        
        # 3.2 Process and display results
        df_results = pd.DataFrame(results_list)
        
        # Filter out any error rows and drop the temp 'Error' column
        df_final = df_results[df_results['Error'].isna()].drop(columns=['Error'], errors='ignore')
        
        # Explicitly cast Mapping_Period to integer
        df_final['Mapping_Period'] = df_final['Mapping_Period'].astype(int)
        
        # Reorder columns for presentation
        df_final = df_final[[
            'Spectral_Index', 'Region', 'Lambda_Rep_m', 'Frequency_Hz', 
            'Eatom (IU)', 'f (1/sqrt(E))', 'Norm. Position', 
            'Mapping_Period', 'Hypothetical_Qualia'
        ]]
        
        # Display all results
        print("\nMapping complete. All Spectral results:")
        
        # Use a single, safe float format string for scientific notation and decimals
        # This resolves the previous FATAL ERROR
        markdown_output = df_final.to_markdown(
            index=False, 
            floatfmt=".4g"
        )
        print(markdown_output)
        
        print(f"\nSuccessfully processed {len(df_final)} spectral regions (out of {len(SPECTRAL_DATA)} tested).")

    except Exception as e:
        print(f"\nFATAL ERROR during processing: {e}")