import pandas as pd
import numpy as np
import math

# ==============================================================================
# 1. COLOR DATA: 7 Perceptual Regions in the Visible Spectrum (Wavelength in nm)
# Frequency (nu) is derived from Wavelength (lambda) using c.
# ==============================================================================

# Constants
SPEED_OF_LIGHT = 299792458.0 # c in m/s
LAMBDA_RED_M = 700e-9       # 700 nm (m)
LAMBDA_VIOLET_M = 400e-9    # 400 nm (m)

# Constants for normalization (Log10 scale of Wavelengths)
LOG_LAMBDA_MAX = np.log10(LAMBDA_RED_M)      # log10(700 nm) ~ -7.1549
LOG_LAMBDA_MIN = np.log10(LAMBDA_VIOLET_M)   # log10(400 nm) ~ -7.3979
TOTAL_LOG_RANGE = LOG_LAMBDA_MAX - LOG_LAMBDA_MIN # 0.243

# DATA: 7 Color Regions ordered by increasing frequency (Index 0 is lowest frequency/Red)
COLOR_DATA = [
    {'Index': 0, 'Region': 'Deep Red', 'Lambda_Rep_nm': 700},
    {'Index': 1, 'Region': 'Orange', 'Lambda_Rep_nm': 620},
    {'Index': 2, 'Region': 'Yellow', 'Lambda_Rep_nm': 580},
    {'Index': 3, 'Region': 'Green', 'Lambda_Rep_nm': 530},
    {'Index': 4, 'Region': 'Cyan', 'Lambda_Rep_nm': 500},
    {'Index': 5, 'Region': 'Blue', 'Lambda_Rep_nm': 470},
    {'Index': 6, 'Region': 'Deep Violet', 'Lambda_Rep_nm': 400}
]

# ==============================================================================
# 2. CORE FUNCTION: get_color_assignment(data)
# ==============================================================================
def get_color_assignment(data):
    """
    Calculates UFT-F inspired informational units for a color qualia.
    """
    
    index = data['Index']
    region = data['Region']
    lambda_nm = data['Lambda_Rep_nm']
    lambda_m = lambda_nm * 1e-9 # Convert to meters
    
    default_results = {
        'Region': region, 'Color_Index': index, 'Lambda_Rep_nm': lambda_nm,
        'Frequency_Hz': np.nan, 'Eatom (IU)': np.nan, 'f (1/sqrt(E))': np.nan, 
        'Norm. Position': np.nan, 'Mapping_Period': np.nan, 'Hypothetical_Qualia': np.nan, 
        'Error': 'Calculation Error'
    }

    try:
        # --- 1. Base Conversions ---
        # Frequency (nu)
        frequency = SPEED_OF_LIGHT / lambda_m
        
        # Log of Wavelength for normalization
        log10_lambda = np.log10(lambda_m)
        
        # Base Metric: Natural Log of Frequency
        log_frequency = np.log(frequency)

        # --- 2. Calculation of Requested Columns ---
        
        color_index = float(index)
        
        # Eatom (IU): Informational Energy Unit
        # Formula: Index * ln(Frequency)
        Eatom_IU = color_index * log_frequency
        
        # f (1/sqrt(E)): Spectral Decay Factor
        # Formula: 1 / sqrt(Eatom (IU))
        if Eatom_IU > 0:
            f_E = 1.0 / np.sqrt(Eatom_IU)
        else:
            f_E = np.nan
        
        # Norm. Position: Normalized position on the total log-wavelength spectrum
        # Formula: (log10(lambda) - LOG_LAMBDA_MAX) / (LOG_LAMBDA_MIN - LOG_LAMBDA_MAX)
        # This forces Norm. Position to 0 at Red (max lambda) and 1 at Violet (min lambda)
        norm_position = (log10_lambda - LOG_LAMBDA_MAX) / (LOG_LAMBDA_MIN - LOG_LAMBDA_MAX)

        # Mapping_Period: Simple grouping based on Index
        # Period 1: Index 0-1 (Red/Orange)
        # Period 2: Index 2-3 (Yellow/Green)
        # Period 3: Index 4-5 (Cyan/Blue)
        # Period 4: Index 6 (Violet)
        mapping_period = math.ceil((index + 1) / 2.0)
        if index == 6: mapping_period = 4
        
        # Hypothetical_Qualia: Combined Score
        # Formula: Color_Index * f(1/sqrt(E))
        hypothetical_qualia = color_index * f_E

    except Exception as e:
        return {**default_results, 'Error': f'Calculation Error: {e}'}
        
    return {
        'Region': region, 'Color_Index': color_index, 'Lambda_Rep_nm': lambda_nm,
        'Frequency_Hz': frequency, 'Eatom (IU)': Eatom_IU, 'f (1/sqrt(E))': f_E,
        'Norm. Position': norm_position, 'Mapping_Period': mapping_period, 
        'Hypothetical_Qualia': hypothetical_qualia, 'Error': np.nan  
    }

# ==============================================================================
# 3. MAIN EXECUTION BLOCK 
# ==============================================================================

if __name__ == '__main__':
    print(f"Starting informational mapping for {len(COLOR_DATA)} color regions (Red to Violet)...")

    try:
        results_list = [get_color_assignment(data) for data in COLOR_DATA]
        df_results = pd.DataFrame(results_list)
        df_final = df_results[df_results['Error'].isna()].drop(columns=['Error'], errors='ignore')
        df_final['Mapping_Period'] = df_final['Mapping_Period'].astype(int)
        
        df_final = df_final[[
            'Color_Index', 'Region', 'Lambda_Rep_nm', 'Frequency_Hz', 
            'Eatom (IU)', 'f (1/sqrt(E))', 'Norm. Position', 
            'Mapping_Period', 'Hypothetical_Qualia'
        ]]
        
        print("\nMapping complete. All Color results:")
        
        markdown_output = df_final.to_markdown(
            index=False, 
            floatfmt=".4g"
        )
        print(markdown_output)
        
        print(f"\nSuccessfully processed {len(df_final)} color regions (out of {len(COLOR_DATA)} tested).")

    except Exception as e:
        print(f"\nFATAL ERROR during processing: {e}")