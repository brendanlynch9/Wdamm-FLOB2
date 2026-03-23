import pandas as pd
import numpy as np
import math

# ==============================================================================
# 1. HAPTICS DATA: 7 Tactile Qualia and Standardized Physical Intensity Proxy (P)
# The Proxy Value (P) is a standardized unit representing the log-scale intensity
# required to elicit the perception (e.g., in standardized Pa or relative units).
# ==============================================================================

# Constants for normalization (Log10 scale from 10^-1 to 10^5)
LOG10_MIN = -1.0    # Log10(0.1) - Soft/Compliance (Boundary)
LOG10_MAX = 5.0     # Log10(100000) - Pain/Nociception (Boundary)
TOTAL_LOG_RANGE = LOG10_MAX - LOG10_MIN # 6.0

# DATA: 7 Tactile Regions ordered by increasing physical intensity/complexity index.
HAPTICS_DATA = [
    {'Index': 0, 'Region': 'Soft (Compliance)', 'Proxy_Value_P': 0.1},      # Lowest force/highest compliance
    {'Index': 1, 'Region': 'Vibration/Tickle', 'Proxy_Value_P': 1.0},       # Simple, transient mechanical input
    {'Index': 2, 'Region': 'Texture (Smooth)', 'Proxy_Value_P': 10.0},      # Low roughness, minimal friction
    {'Index': 3, 'Region': 'Wetness/Slimy', 'Proxy_Value_P': 100.0},        # Complex multi-modal (thermal + pressure + adhesion)
    {'Index': 4, 'Region': 'Temperature (Thermal)', 'Proxy_Value_P': 1000.0}, # Dedicated thermal channel
    {'Index': 5, 'Region': 'Hard (Stiffness)', 'Proxy_Value_P': 10000.0},   # High force/stiffness
    {'Index': 6, 'Region': 'Pain (Nociception)', 'Proxy_Value_P': 100000.0} # Maximum force/damage threshold
]

# ==============================================================================
# 2. CORE FUNCTION: get_haptics_assignment(data)
# ==============================================================================
def get_haptics_assignment(data):
    """
    Calculates UFT-F inspired informational units for a haptics qualia.
    """
    
    index = data['Index']
    region = data['Region']
    P = data['Proxy_Value_P']
    
    default_results = {
        'Region': region, 'Haptics_Index': index, 'Proxy_Value_P': P,
        'Eatom (IU)': np.nan, 'f (1/sqrt(E))': np.nan, 
        'Norm. Position': np.nan, 'Mapping_Period': np.nan, 'Hypothetical_Qualia': np.nan, 
        'Error': 'Calculation Error'
    }

    try:
        # --- 1. Base Conversions ---
        # Log10 Proxy Value (for normalization)
        log10_P = np.log10(P)
        
        # Base Metric: Natural Log of the Proxy Value
        log_P = np.log(P)

        # --- 2. Calculation of Requested Columns ---
        
        # Haptics_Index: Use the assigned index (0-6)
        haptics_index = float(index)
        
        # Eatom (IU): Informational Energy Unit
        # Formula: Index * ln(Proxy_Value_P)
        Eatom_IU = haptics_index * log_P
        
        # f (1/sqrt(E)): Spectral Decay Factor
        # Formula: 1 / sqrt(Eatom (IU))
        # Handle index 0 which leads to Eatom_IU = 0
        if Eatom_IU > 0:
            f_E = 1.0 / np.sqrt(Eatom_IU)
        else:
            f_E = np.nan
        
        # Norm. Position: Normalized position on the total log-intensity spectrum
        # Formula: (log10(P) - LOG10_MIN) / TOTAL_LOG_RANGE
        norm_position = (log10_P - LOG10_MIN) / TOTAL_LOG_RANGE

        # Mapping_Period: Simple grouping based on Index
        # Period 1: Index 0-1 (Low Intensity/Compliance)
        # Period 2: Index 2-3 (Texture/Mid-range)
        # Period 3: Index 4-5 (Thermal/High Stiffness)
        # Period 4: Index 6 (Maximum/Pain)
        mapping_period = math.ceil((index + 1) / 2.0)
        if index == 6: mapping_period = 4
        
        # Hypothetical_Qualia: Combined Score
        # Formula: Haptics_Index * f(1/sqrt(E))
        hypothetical_qualia = haptics_index * f_E

    except Exception as e:
        return {**default_results, 'Error': f'Calculation Error: {e}'}
        
    return {
        'Region': region, 'Haptics_Index': haptics_index, 'Proxy_Value_P': P,
        'Eatom (IU)': Eatom_IU, 'f (1/sqrt(E))': f_E,
        'Norm. Position': norm_position, 'Mapping_Period': mapping_period, 
        'Hypothetical_Qualia': hypothetical_qualia, 'Error': np.nan  
    }

# ==============================================================================
# 3. MAIN EXECUTION BLOCK 
# ==============================================================================

if __name__ == '__main__':
    print(f"Starting informational mapping for {len(HAPTICS_DATA)} haptic regions (Soft to Pain)...")

    try:
        results_list = [get_haptics_assignment(data) for data in HAPTICS_DATA]
        df_results = pd.DataFrame(results_list)
        df_final = df_results[df_results['Error'].isna()].drop(columns=['Error'], errors='ignore')
        df_final['Mapping_Period'] = df_final['Mapping_Period'].astype(int)
        
        df_final = df_final[[
            'Haptics_Index', 'Region', 'Proxy_Value_P', 
            'Eatom (IU)', 'f (1/sqrt(E))', 'Norm. Position', 
            'Mapping_Period', 'Hypothetical_Qualia'
        ]]
        
        print("\nMapping complete. All Haptics results:")
        
        markdown_output = df_final.to_markdown(
            index=False, 
            floatfmt=".4g"
        )
        print(markdown_output)
        
        print(f"\nSuccessfully processed {len(df_final)} haptic regions (out of {len(HAPTICS_DATA)} tested).")

    except Exception as e:
        print(f"\nFATAL ERROR during processing: {e}")