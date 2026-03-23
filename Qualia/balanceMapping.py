import pandas as pd
import numpy as np
import math

# ==============================================================================
# 1. BALANCE DATA: 7 Vestibular/Balance Qualia and Angular Velocity Proxy (omega)
# Proxy (omega) is a standardized unit representing the magnitude of angular
# velocity or equivalent gravitational/linear acceleration force.
# ==============================================================================

# Constants for normalization (Log10 scale from 10^-1 rad/s to 10^5 rad/s)
# This represents a range from nearly static to extreme rotation/acceleration.
LOG10_MIN = -1.0    # Log10(0.1) - Gravity/Static Sense (Boundary)
LOG10_MAX = 5.0     # Log10(100000) - Spin/Max Rotation (Boundary)
TOTAL_LOG_RANGE = LOG10_MAX - LOG10_MIN # 6.0

# DATA: 7 Vestibular Regions ordered by increasing informational complexity/sensitivity
BALANCE_DATA = [
    # Lowest Index/Energy - Static/Constant Force
    {'Index': 0, 'Region': 'Gravity/Static', 'Omega_Proxy_rad_s': 0.1},
    {'Index': 1, 'Region': 'Linear Acceleration', 'Omega_Proxy_rad_s': 1.0},
    {'Index': 2, 'Region': 'Vertical Motion', 'Omega_Proxy_rad_s': 10.0},
    {'Index': 3, 'Region': 'Horizontal Motion', 'Omega_Proxy_rad_s': 100.0},
    {'Index': 4, 'Region': 'Pitch/Roll Tilt', 'Omega_Proxy_rad_s': 1000.0},
    {'Index': 5, 'Region': 'Yaw Rotation (Turn)', 'Omega_Proxy_rad_s': 10000.0},
    # Highest Index/Energy - Extreme Rotation
    {'Index': 6, 'Region': 'Spin/Rotation Max', 'Omega_Proxy_rad_s': 100000.0}
]

# ==============================================================================
# 2. CORE FUNCTION: get_balance_assignment(data)
# ==============================================================================
def get_balance_assignment(data):
    """
    Calculates UFT-F inspired informational units for a balance qualia.
    """
    
    index = data['Index']
    region = data['Region']
    omega = data['Omega_Proxy_rad_s']
    
    default_results = {
        'Region': region, 'Balance_Index': index, 'Omega_Proxy_rad_s': omega,
        'Eatom (IU)': np.nan, 'f (1/sqrt(E))': np.nan, 
        'Norm. Position': np.nan, 'Mapping_Period': np.nan, 'Hypothetical_Qualia': np.nan, 
        'Error': 'Calculation Error'
    }

    try:
        # --- 1. Base Conversions ---
        log10_omega = np.log10(omega)
        
        # Base Metric: Natural Log of Angular Velocity Proxy
        log_omega = np.log(omega)

        # --- 2. Calculation of Requested Columns ---
        
        balance_index = float(index)
        
        # Eatom (IU): Informational Energy Unit
        # Formula: Index * ln(Omega)
        Eatom_IU = balance_index * log_omega
        
        # f (1/sqrt(E)): Spectral Decay Factor
        # Formula: 1 / sqrt(Eatom (IU))
        # Handle cases where Eatom_IU <= 0 (Index 0 or log(omega) <= 0)
        if Eatom_IU > 0:
            f_E = 1.0 / np.sqrt(Eatom_IU)
        else:
            f_E = np.nan
        
        # Norm. Position: Normalized position on the total log-omega spectrum
        norm_position = (log10_omega - LOG10_MIN) / TOTAL_LOG_RANGE

        # Mapping_Period: Simple grouping based on Index
        # Period 1: Index 0-1 (Static/Linear)
        # Period 2: Index 2-3 (Translational Motion)
        # Period 3: Index 4-5 (Angular Rotation)
        # Period 4: Index 6 (Maximum Spin)
        mapping_period = math.ceil((index + 1) / 2.0)
        if index == 6: mapping_period = 4
        
        # Hypothetical_Qualia: Combined Score
        # Formula: Balance_Index * f(1/sqrt(E))
        hypothetical_qualia = balance_index * f_E

    except Exception as e:
        return {**default_results, 'Error': f'Calculation Error: {e}'}
        
    return {
        'Region': region, 'Balance_Index': balance_index, 'Omega_Proxy_rad_s': omega,
        'Eatom (IU)': Eatom_IU, 'f (1/sqrt(E))': f_E,
        'Norm. Position': norm_position, 'Mapping_Period': mapping_period, 
        'Hypothetical_Qualia': hypothetical_qualia, 'Error': np.nan  
    }

# ==============================================================================
# 3. MAIN EXECUTION BLOCK 
# ==============================================================================

if __name__ == '__main__':
    print(f"Starting informational mapping for {len(BALANCE_DATA)} balance regions (Gravity to Spin)...")

    try:
        results_list = [get_balance_assignment(data) for data in BALANCE_DATA]
        df_results = pd.DataFrame(results_list)
        df_final = df_results[df_results['Error'].isna()].drop(columns=['Error'], errors='ignore')
        df_final['Mapping_Period'] = df_final['Mapping_Period'].astype(int)
        
        df_final = df_final[[
            'Balance_Index', 'Region', 'Omega_Proxy_rad_s', 
            'Eatom (IU)', 'f (1/sqrt(E))', 'Norm. Position', 
            'Mapping_Period', 'Hypothetical_Qualia'
        ]]
        
        print("\nMapping complete. All Balance results:")
        
        markdown_output = df_final.to_markdown(
            index=False, 
            floatfmt=".4g"
        )
        print(markdown_output)
        
        print(f"\nSuccessfully processed {len(df_final)} balance regions (out of {len(BALANCE_DATA)} tested).")

    except Exception as e:
        print(f"\nFATAL ERROR during processing: {e}")