import pandas as pd
import numpy as np
import math

# ==============================================================================
# 1. ACOUSTIC DATA: Representative Frequencies for the Human Auditory Spectrum
# Frequency (nu) is in Hertz (Hz).
# The human hearing range is typically 20 Hz to 20,000 Hz.
# We map 7 regions for consistency.
# ==============================================================================

# Constants for normalization (based on 10 Hz to 20,000 Hz)
LOG_FREQ_MIN = 1.0          # log10(10 Hz)
LOG_FREQ_MAX = 4.30103      # log10(20000 Hz)
TOTAL_LOG_RANGE = LOG_FREQ_MAX - LOG_FREQ_MIN # 3.30103

AUDITORY_DATA = [
    {'Index': 0, 'Region': 'Infrasound', 'Frequency_Rep_Hz': 10},
    {'Index': 1, 'Region': 'Low Bass', 'Frequency_Rep_Hz': 40},
    {'Index': 2, 'Region': 'Mid Bass', 'Frequency_Rep_Hz': 100},
    {'Index': 3, 'Region': 'Lower Midrange', 'Frequency_Rep_Hz': 400},
    {'Index': 4, 'Region': 'Upper Midrange', 'Frequency_Rep_Hz': 2500},
    {'Index': 5, 'Region': 'High Treble', 'Frequency_Rep_Hz': 10000},
    {'Index': 6, 'Region': 'Upper Limit', 'Frequency_Rep_Hz': 20000}
]

# ==============================================================================
# 2. CORE FUNCTION: get_sound_assignment(data)
# ==============================================================================
def get_sound_assignment(data):
    """
    Calculates UFT-F inspired informational units for an auditory region.

    :param data: Dictionary containing 'Index', 'Region', and 'Frequency_Rep_Hz'.
    :return: A dictionary of calculated results.
    """
    
    index = data['Index']
    region = data['Region']
    frequency = data['Frequency_Rep_Hz']
    
    # Define default result for error handling
    default_results = {
        'Region': region, 'Acoustic_Index': index, 'Frequency_Rep_Hz': frequency,
        'Eatom (IU)': np.nan, 'f (1/sqrt(E))': np.nan, 
        'Norm. Position': np.nan, 'Mapping_Period': np.nan, 'Hypothetical_Qualia': np.nan, 
        'Error': 'Calculation Error'
    }

    try:
        # --- 1. Basic Conversions ---
        # Log of Frequency for normalization
        log10_frequency = np.log10(frequency)

        # --- 2. Calculation of Requested Columns ---
        
        # Acoustic_Index: Use the Region Index as the basis score
        acoustic_index = float(index)
        
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
        
        # Norm. Position: Normalized position on the total log-spectrum (10 Hz to 20 kHz)
        # Formula: (log10(frequency) - LOG_FREQ_MIN) / TOTAL_LOG_RANGE
        norm_position = (log10_frequency - LOG_FREQ_MIN) / TOTAL_LOG_RANGE

        # Mapping_Period: Simple grouping based on Index
        # Period 1: Infra/Low Bass (Index 0-1)
        # Period 2: Mid Bass/Lower Midrange (Index 2-3)
        # Period 3: Upper Midrange/High Treble (Index 4-5)
        # Period 4: Upper Limit (Index 6)
        mapping_period = math.ceil((index + 1) / 2.0)
        if index == 6: mapping_period = 4 # Separate category for Upper Limit
        
        # Hypothetical_Qualia: Combined Score
        # Formula: Acoustic_Index * f(1/sqrt(E))
        hypothetical_qualia = acoustic_index * f_E

    except Exception as e:
        print(f"Calculation Error for Region {region}: {e}")
        return {**default_results, 'Error': f'Calculation Error: {e}'}
        
    # --- END OF CALCULATIONS ---

    return {
        'Region': region,
        'Acoustic_Index': acoustic_index,
        'Frequency_Rep_Hz': frequency,
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
    print(f"Starting informational mapping for {len(AUDITORY_DATA)} auditory regions (Infrasound to Upper Limit)...")

    # 3.1 Run the mapping function for all regions
    try:
        results_list = [get_sound_assignment(data) for data in AUDITORY_DATA]
        
        # 3.2 Process and display results
        df_results = pd.DataFrame(results_list)
        
        # Filter out any error rows and drop the temp 'Error' column
        df_final = df_results[df_results['Error'].isna()].drop(columns=['Error'], errors='ignore')
        
        # Explicitly cast Mapping_Period to integer
        df_final['Mapping_Period'] = df_final['Mapping_Period'].astype(int)
        
        # Reorder columns for presentation
        df_final = df_final[[
            'Acoustic_Index', 'Region', 'Frequency_Rep_Hz', 
            'Eatom (IU)', 'f (1/sqrt(E))', 'Norm. Position', 
            'Mapping_Period', 'Hypothetical_Qualia'
        ]]
        
        # Display all results
        print("\nMapping complete. All Auditory results:")
        
        # Use a single, safe float format string for scientific notation and decimals
        markdown_output = df_final.to_markdown(
            index=False, 
            floatfmt=".4g"
        )
        print(markdown_output)
        
        print(f"\nSuccessfully processed {len(df_final)} auditory regions (out of {len(AUDITORY_DATA)} tested).")

    except Exception as e:
        print(f"\nFATAL ERROR during processing: {e}")