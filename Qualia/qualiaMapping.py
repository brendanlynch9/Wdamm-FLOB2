# Column,Placeholder Formula,Description
# Eatom (IU),Z⋅ln(AtomicMass),An informational unit of energy.
# f (1/sqrt(E)),1/Eatom (IU)​,A spectral frequency/decay factor based on the square root of the energy.
# Norm. Position,Z/118,Linear position normalization across the 118 elements.
# Mapping_Period,(Actual Periodic Table Period),The official period number (row) of the element.
# Hypothetical_Qualia,Qualia_Score⋅f (1/sqrt(E)),A combined final score.

import pandas as pd
import numpy as np

# ==============================================================================
# 1. ELEMENT DATA: Complete set for Z=1 to Z=118
# ==============================================================================

ELEMENT_DATA_Z1_118 = [
    {'Z': 1, 'Symbol': 'H', 'Name': 'Hydrogen', 'AtomicMass': 1.008},
    {'Z': 2, 'Symbol': 'He', 'Name': 'Helium', 'AtomicMass': 4.0026},
    {'Z': 3, 'Symbol': 'Li', 'Name': 'Lithium', 'AtomicMass': 6.94},
    {'Z': 4, 'Symbol': 'Be', 'Name': 'Beryllium', 'AtomicMass': 9.0122},
    {'Z': 5, 'Symbol': 'B', 'Name': 'Boron', 'AtomicMass': 10.81},
    {'Z': 6, 'Symbol': 'C', 'Name': 'Carbon', 'AtomicMass': 12.011},
    {'Z': 7, 'Symbol': 'N', 'Name': 'Nitrogen', 'AtomicMass': 14.007},
    {'Z': 8, 'Symbol': 'O', 'Name': 'Oxygen', 'AtomicMass': 15.999},
    {'Z': 9, 'Symbol': 'F', 'Name': 'Fluorine', 'AtomicMass': 18.998},
    {'Z': 10, 'Symbol': 'Ne', 'Name': 'Neon', 'AtomicMass': 20.180},
    {'Z': 11, 'Symbol': 'Na', 'Name': 'Sodium', 'AtomicMass': 22.990},
    {'Z': 12, 'Symbol': 'Mg', 'Name': 'Magnesium', 'AtomicMass': 24.305},
    {'Z': 13, 'Symbol': 'Al', 'Name': 'Aluminum', 'AtomicMass': 26.982},
    {'Z': 14, 'Symbol': 'Si', 'Name': 'Silicon', 'AtomicMass': 28.085},
    {'Z': 15, 'Symbol': 'P', 'Name': 'Phosphorus', 'AtomicMass': 30.974},
    {'Z': 16, 'Symbol': 'S', 'Name': 'Sulfur', 'AtomicMass': 32.06},
    {'Z': 17, 'Symbol': 'Cl', 'Name': 'Chlorine', 'AtomicMass': 35.45},
    {'Z': 18, 'Symbol': 'Ar', 'Name': 'Argon', 'AtomicMass': 39.948},
    {'Z': 19, 'Symbol': 'K', 'Name': 'Potassium', 'AtomicMass': 39.098},
    {'Z': 20, 'Symbol': 'Ca', 'Name': 'Calcium', 'AtomicMass': 40.078},
    {'Z': 21, 'Symbol': 'Sc', 'Name': 'Scandium', 'AtomicMass': 44.956},
    {'Z': 22, 'Symbol': 'Ti', 'Name': 'Titanium', 'AtomicMass': 47.867},
    {'Z': 23, 'Symbol': 'V', 'Name': 'Vanadium', 'AtomicMass': 50.942},
    {'Z': 24, 'Symbol': 'Cr', 'Name': 'Chromium', 'AtomicMass': 51.996},
    {'Z': 25, 'Symbol': 'Mn', 'Name': 'Manganese', 'AtomicMass': 54.938},
    {'Z': 26, 'Symbol': 'Fe', 'Name': 'Iron', 'AtomicMass': 55.845},
    {'Z': 27, 'Symbol': 'Co', 'Name': 'Cobalt', 'AtomicMass': 58.933},
    {'Z': 28, 'Symbol': 'Ni', 'Name': 'Nickel', 'AtomicMass': 58.693},
    {'Z': 29, 'Symbol': 'Cu', 'Name': 'Copper', 'AtomicMass': 63.546},
    {'Z': 30, 'Symbol': 'Zn', 'Name': 'Zinc', 'AtomicMass': 65.38},
    {'Z': 31, 'Symbol': 'Ga', 'Name': 'Gallium', 'AtomicMass': 69.723},
    {'Z': 32, 'Symbol': 'Ge', 'Name': 'Germanium', 'AtomicMass': 72.63},
    {'Z': 33, 'Symbol': 'As', 'Name': 'Arsenic', 'AtomicMass': 74.922},
    {'Z': 34, 'Symbol': 'Se', 'Name': 'Selenium', 'AtomicMass': 78.971},
    {'Z': 35, 'Symbol': 'Br', 'Name': 'Bromine', 'AtomicMass': 79.904},
    {'Z': 36, 'Symbol': 'Kr', 'Name': 'Krypton', 'AtomicMass': 83.798},
    {'Z': 37, 'Symbol': 'Rb', 'Name': 'Rubidium', 'AtomicMass': 85.468},
    {'Z': 38, 'Symbol': 'Sr', 'Name': 'Strontium', 'AtomicMass': 87.62},
    {'Z': 39, 'Symbol': 'Y', 'Name': 'Yttrium', 'AtomicMass': 88.906},
    {'Z': 40, 'Symbol': 'Zr', 'Name': 'Zirconium', 'AtomicMass': 91.224},
    {'Z': 41, 'Symbol': 'Nb', 'Name': 'Niobium', 'AtomicMass': 92.906},
    {'Z': 42, 'Symbol': 'Mo', 'Name': 'Molybdenum', 'AtomicMass': 95.96},
    {'Z': 43, 'Symbol': 'Tc', 'Name': 'Technetium', 'AtomicMass': 98.0},
    {'Z': 44, 'Symbol': 'Ru', 'Name': 'Ruthenium', 'AtomicMass': 101.07},
    {'Z': 45, 'Symbol': 'Rh', 'Name': 'Rhodium', 'AtomicMass': 102.91},
    {'Z': 46, 'Symbol': 'Pd', 'Name': 'Palladium', 'AtomicMass': 106.42},
    {'Z': 47, 'Symbol': 'Ag', 'Name': 'Silver', 'AtomicMass': 107.87},
    {'Z': 48, 'Symbol': 'Cd', 'Name': 'Cadmium', 'AtomicMass': 112.41},
    {'Z': 49, 'Symbol': 'In', 'Name': 'Indium', 'AtomicMass': 114.82},
    {'Z': 50, 'Symbol': 'Sn', 'Name': 'Tin', 'AtomicMass': 118.71},
    {'Z': 51, 'Symbol': 'Sb', 'Name': 'Antimony', 'AtomicMass': 121.76},
    {'Z': 52, 'Symbol': 'Te', 'Name': 'Tellurium', 'AtomicMass': 127.60},
    {'Z': 53, 'Symbol': 'I', 'Name': 'Iodine', 'AtomicMass': 126.90},
    {'Z': 54, 'Symbol': 'Xe', 'Name': 'Xenon', 'AtomicMass': 131.29},
    {'Z': 55, 'Symbol': 'Cs', 'Name': 'Cesium', 'AtomicMass': 132.91},
    {'Z': 56, 'Symbol': 'Ba', 'Name': 'Barium', 'AtomicMass': 137.33},
    {'Z': 57, 'Symbol': 'La', 'Name': 'Lanthanum', 'AtomicMass': 138.91},
    {'Z': 58, 'Symbol': 'Ce', 'Name': 'Cerium', 'AtomicMass': 140.12},
    {'Z': 59, 'Symbol': 'Pr', 'Name': 'Praseodymium', 'AtomicMass': 140.91},
    {'Z': 60, 'Symbol': 'Nd', 'Name': 'Neodymium', 'AtomicMass': 144.24},
    {'Z': 61, 'Symbol': 'Pm', 'Name': 'Promethium', 'AtomicMass': 145.0},
    {'Z': 62, 'Symbol': 'Sm', 'Name': 'Samarium', 'AtomicMass': 150.36},
    {'Z': 63, 'Symbol': 'Eu', 'Name': 'Europium', 'AtomicMass': 151.96},
    {'Z': 64, 'Symbol': 'Gd', 'Name': 'Gadolinium', 'AtomicMass': 157.25},
    {'Z': 65, 'Symbol': 'Tb', 'Name': 'Terbium', 'AtomicMass': 158.93},
    {'Z': 66, 'Symbol': 'Dy', 'Name': 'Dysprosium', 'AtomicMass': 162.50},
    {'Z': 67, 'Symbol': 'Ho', 'Name': 'Holmium', 'AtomicMass': 164.93},
    {'Z': 68, 'Symbol': 'Er', 'Name': 'Erbium', 'AtomicMass': 167.26},
    {'Z': 69, 'Symbol': 'Tm', 'Name': 'Thulium', 'AtomicMass': 168.93},
    {'Z': 70, 'Symbol': 'Yb', 'Name': 'Ytterbium', 'AtomicMass': 173.05},
    {'Z': 71, 'Symbol': 'Lu', 'Name': 'Lutetium', 'AtomicMass': 174.97},
    {'Z': 72, 'Symbol': 'Hf', 'Name': 'Hafnium', 'AtomicMass': 178.49},
    {'Z': 73, 'Symbol': 'Ta', 'Name': 'Tantalum', 'AtomicMass': 180.95},
    {'Z': 74, 'Symbol': 'W', 'Name': 'Tungsten', 'AtomicMass': 183.84},
    {'Z': 75, 'Symbol': 'Re', 'Name': 'Rhenium', 'AtomicMass': 186.21},
    {'Z': 76, 'Symbol': 'Os', 'Name': 'Osmium', 'AtomicMass': 190.23},
    {'Z': 77, 'Symbol': 'Ir', 'Name': 'Iridium', 'AtomicMass': 192.22},
    {'Z': 78, 'Symbol': 'Pt', 'Name': 'Platinum', 'AtomicMass': 195.08},
    {'Z': 79, 'Symbol': 'Au', 'Name': 'Gold', 'AtomicMass': 196.97},
    {'Z': 80, 'Symbol': 'Hg', 'Name': 'Mercury', 'AtomicMass': 200.59},
    {'Z': 81, 'Symbol': 'Tl', 'Name': 'Thallium', 'AtomicMass': 204.38},
    {'Z': 82, 'Symbol': 'Pb', 'Name': 'Lead', 'AtomicMass': 207.2},
    {'Z': 83, 'Symbol': 'Bi', 'Name': 'Bismuth', 'AtomicMass': 208.98},
    {'Z': 84, 'Symbol': 'Po', 'Name': 'Polonium', 'AtomicMass': 209.0},
    {'Z': 85, 'Symbol': 'At', 'Name': 'Astatine', 'AtomicMass': 210.0},
    {'Z': 86, 'Symbol': 'Rn', 'Name': 'Radon', 'AtomicMass': 222.0},
    {'Z': 87, 'Symbol': 'Fr', 'Name': 'Francium', 'AtomicMass': 223.0},
    {'Z': 88, 'Symbol': 'Ra', 'Name': 'Radium', 'AtomicMass': 226.0},
    {'Z': 89, 'Symbol': 'Ac', 'Name': 'Actinium', 'AtomicMass': 227.0},
    {'Z': 90, 'Symbol': 'Th', 'Name': 'Thorium', 'AtomicMass': 232.04},
    {'Z': 91, 'Symbol': 'Pa', 'Name': 'Protactinium', 'AtomicMass': 231.04},
    {'Z': 92, 'Symbol': 'U', 'Name': 'Uranium', 'AtomicMass': 238.03},
    {'Z': 93, 'Symbol': 'Np', 'Name': 'Neptunium', 'AtomicMass': 237.0},
    {'Z': 94, 'Symbol': 'Pu', 'Name': 'Plutonium', 'AtomicMass': 244.0},
    {'Z': 95, 'Symbol': 'Am', 'Name': 'Americium', 'AtomicMass': 243.0},
    {'Z': 96, 'Symbol': 'Cm', 'Name': 'Curium', 'AtomicMass': 247.0},
    {'Z': 97, 'Symbol': 'Bk', 'Name': 'Berkelium', 'AtomicMass': 247.0},
    {'Z': 98, 'Symbol': 'Cf', 'Name': 'Californium', 'AtomicMass': 251.0},
    {'Z': 99, 'Symbol': 'Es', 'Name': 'Einsteinium', 'AtomicMass': 252.0},
    {'Z': 100, 'Symbol': 'Fm', 'Name': 'Fermium', 'AtomicMass': 257.0},
    {'Z': 101, 'Symbol': 'Md', 'Name': 'Mendelevium', 'AtomicMass': 258.0},
    {'Z': 102, 'Symbol': 'No', 'Name': 'Nobelium', 'AtomicMass': 259.0},
    {'Z': 103, 'Symbol': 'Lr', 'Name': 'Lawrencium', 'AtomicMass': 262.0},
    {'Z': 104, 'Symbol': 'Rf', 'Name': 'Rutherfordium', 'AtomicMass': 267.0},
    {'Z': 105, 'Symbol': 'Db', 'Name': 'Dubnium', 'AtomicMass': 268.0},
    {'Z': 106, 'Symbol': 'Sg', 'Name': 'Seaborgium', 'AtomicMass': 271.0},
    {'Z': 107, 'Symbol': 'Bh', 'Name': 'Bohrium', 'AtomicMass': 272.0},
    {'Z': 108, 'Symbol': 'Hs', 'Name': 'Hassium', 'AtomicMass': 270.0},
    {'Z': 109, 'Symbol': 'Mt', 'Name': 'Meitnerium', 'AtomicMass': 276.0},
    {'Z': 110, 'Symbol': 'Ds', 'Name': 'Darmstadtium', 'AtomicMass': 281.0},
    {'Z': 111, 'Symbol': 'Rg', 'Name': 'Roentgenium', 'AtomicMass': 280.0},
    {'Z': 112, 'Symbol': 'Cn', 'Name': 'Copernicium', 'AtomicMass': 285.0},
    {'Z': 113, 'Symbol': 'Nh', 'Name': 'Nihonium', 'AtomicMass': 286.0},
    {'Z': 114, 'Symbol': 'Fl', 'Name': 'Flerovium', 'AtomicMass': 289.0},
    {'Z': 115, 'Symbol': 'Mc', 'Name': 'Moscovium', 'AtomicMass': 290.0},
    {'Z': 116, 'Symbol': 'Lv', 'Name': 'Livermorium', 'AtomicMass': 293.0},
    {'Z': 117, 'Symbol': 'Ts', 'Name': 'Tennessine', 'AtomicMass': 294.0},
    {'Z': 118, 'Symbol': 'Og', 'Name': 'Oganesson', 'AtomicMass': 294.0}
]

# ==============================================================================
# 2. HELPER FUNCTION: get_period(Z)
# ==============================================================================
def get_period(Z):
    """Returns the period (row) number of the Periodic Table for a given atomic number Z."""
    if Z in range(1, 3): return 1
    if Z in range(3, 11): return 2
    if Z in range(11, 19): return 3
    if Z in range(19, 37): return 4
    if Z in range(37, 55): return 5
    if Z in range(55, 87): return 6
    if Z in range(87, 119): return 7
    return np.nan

# ==============================================================================
# 3. CORE FUNCTION: get_qualia_assignment(Z, df)
# ==============================================================================
def get_qualia_assignment(Z, df):
    """
    Retrieves element data and calculates Qualia Score and new UFT-F related parameters.

    :param Z: The atomic number (int)
    :param df: The DataFrame containing element data (pandas.DataFrame)
    :return: A dictionary of results with all calculated columns.
    """
    
    # 1. Filter the DataFrame for the atomic number Z
    filtered_df = df[df['Z'] == Z]
    
    # Define a default dictionary for missing elements, including new columns
    default_results = {
        'Z': Z, 'Symbol': None, 'Name': None, 
        'Qualia_Score': np.nan, 'Eatom (IU)': np.nan, 'f (1/sqrt(E))': np.nan, 
        'Norm. Position': np.nan, 'Mapping_Period': np.nan, 'Hypothetical_Qualia': np.nan, 
        'Error': 'Element Missing'
    }

    if filtered_df.empty:
        print(f"Warning: Element Z={Z} not found in the input DataFrame `df_complete`. Skipping.")
        return default_results
        
    element_data = filtered_df.iloc[0]
    symbol = element_data['Symbol']
    atomic_mass = element_data['AtomicMass']

    # --- UFT-F CALCULATION LOGIC ---
    try:
        # Qualia_Score (Placeholder from previous step: log(mass+Z) * Z/100)
        qualia_score = np.log(atomic_mass + Z) * (Z / 100)
        
        # Eatom (IU): Informational Energy
        # Formula: Z * ln(Atomic Mass)
        Eatom_IU = Z * np.log(atomic_mass)
        
        # f (1/sqrt(E)): Spectral Frequency/Decay Factor
        # Formula: 1 / sqrt(Eatom (IU))
        # Ensure E > 0 for log and E > 0 for sqrt (Atomic Mass >= 1, Z >= 1, so Eatom_IU > 0)
        if Eatom_IU <= 0:
            f_E = np.nan
        else:
            f_E = 1.0 / np.sqrt(Eatom_IU)

        # Norm. Position: Linear Normalization of Z
        # Formula: Z / 118
        norm_position = Z / 118.0

        # Mapping_Period: Look up the Periodic Table Period (using helper)
        mapping_period = get_period(Z)

        # Hypothetical_Qualia: Combined Score
        # Formula: Qualia_Score * f(1/sqrt(E))
        hypothetical_qualia = qualia_score * f_E

    except Exception as e:
        # If any calculation fails, return error with partial results
        print(f"Calculation Error for Z={Z}: {e}")
        error_results = {
            'Z': Z, 'Symbol': symbol, 'Name': element_data.get('Name'), 
            'Qualia_Score': qualia_score if 'qualia_score' in locals() else np.nan,
            'Eatom (IU)': Eatom_IU if 'Eatom_IU' in locals() else np.nan,
            'f (1/sqrt(E))': f_E if 'f_E' in locals() else np.nan, 
            'Norm. Position': norm_position if 'norm_position' in locals() else np.nan,
            'Mapping_Period': mapping_period if 'mapping_period' in locals() else np.nan,
            'Hypothetical_Qualia': hypothetical_qualia if 'hypothetical_qualia' in locals() else np.nan,
            'Error': f'Calculation Error: {e}'
        }
        return error_results
        
    # --- END OF CALCULATIONS ---

    return {
        'Z': Z,
        'Symbol': symbol,
        'Name': element_data.get('Name'),
        'Qualia_Score': qualia_score,
        'Eatom (IU)': Eatom_IU,
        'f (1/sqrt(E))': f_E,
        'Norm. Position': norm_position,
        'Mapping_Period': mapping_period,
        'Hypothetical_Qualia': hypothetical_qualia,
        'Error': np.nan  
    }

# ==============================================================================
# 4. MAIN EXECUTION BLOCK 
# ==============================================================================

# 4.1 Load/Create the DataFrame for all 118 elements
df_elements = pd.DataFrame(ELEMENT_DATA_Z1_118)
df_complete = df_elements.copy() 

# 4.2 Define the elements to test (now set for all 118 elements)
elements_to_test = list(range(1, 119)) # Z=1 through Z=118

print(f"Starting qualia mapping for {len(elements_to_test)} elements (Z=1 to Z=118)...")

# 4.3 Run the main loop
try:
    results_list = [get_qualia_assignment(z, df_complete) for z in elements_to_test]
    
    # 4.4 Process and display results
    df_results = pd.DataFrame(results_list)
    
    # Filter out any error rows and drop the temp 'Error' column
    df_final = df_results[df_results['Error'].isna()].drop(columns=['Error'], errors='ignore')
    
    # Display all 118 results
    print("\nMapping complete. All 118 results:")
    print(df_final.to_markdown(index=False, floatfmt=".6f"))
    
    print(f"\nSuccessfully processed {len(df_final)} elements (out of {len(elements_to_test)} tested).")

except Exception as e:
    print(f"\nFATAL ERROR during processing: {e}")