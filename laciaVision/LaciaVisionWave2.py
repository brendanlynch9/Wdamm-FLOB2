import numpy as np
import csv
import os
from scipy.optimize import nnls

# Constants from Qualia_For_AGI9.pdf and UFT-F Framework
V_p = 720  # Proton Volume
V_n = 95232  # Neutron Volume Approximation
WAVE_LENGTH = 50  # Standard waveform length for qualia simulation
MATCH_THRESHOLD = 1e-6  # Dissonance threshold for exact match (falsifiable tolerance)
C_UFT_F = 0.00311903  # Modularity Constant (Spectral Floor)
LYNCH_SLOPE = -1.6466  # Navier-Stokes Inertial Slope for Turbulence Audit
DELTA_SAFETY = 0.08  # Triple-Point Filter Threshold for Fraud Detection
MULTI_MAX_ELEMENTS = 5  # Max elements in decomposition

# Periodic Table Elements (Z: Name) - Definitive Dictionary of Known Elements (1-118)
ELEMENTS = {
    1: "Hydrogen", 2: "Helium", 3: "Lithium", 4: "Beryllium", 5: "Boron",
    6: "Carbon", 7: "Nitrogen", 8: "Oxygen", 9: "Fluorine", 10: "Neon",
    11: "Sodium", 12: "Magnesium", 13: "Aluminum", 14: "Silicon", 15: "Phosphorus",
    16: "Sulfur", 17: "Chlorine", 18: "Argon", 19: "Potassium", 20: "Calcium",
    21: "Scandium", 22: "Titanium", 23: "Vanadium", 24: "Chromium", 25: "Manganese",
    26: "Iron", 27: "Cobalt", 28: "Nickel", 29: "Copper", 30: "Zinc",
    31: "Gallium", 32: "Germanium", 33: "Arsenic", 34: "Selenium", 35: "Bromine",
    36: "Krypton", 37: "Rubidium", 38: "Strontium", 39: "Yttrium", 40: "Zirconium",
    41: "Niobium", 42: "Molybdenum", 43: "Technetium", 44: "Ruthenium", 45: "Rhodium",
    46: "Palladium", 47: "Silver", 48: "Cadmium", 49: "Indium", 50: "Tin",
    51: "Antimony", 52: "Tellurium", 53: "Iodine", 54: "Xenon", 55: "Cesium",
    56: "Barium", 57: "Lanthanum", 58: "Cerium", 59: "Praseodymium", 60: "Neodymium",
    61: "Promethium", 62: "Samarium", 63: "Europium", 64: "Gadolinium", 65: "Terbium",
    66: "Dysprosium", 67: "Holmium", 68: "Erbium", 69: "Thulium", 70: "Ytterbium",
    71: "Lutetium", 72: "Hafnium", 73: "Tantalum", 74: "Tungsten", 75: "Rhenium",
    76: "Osmium", 77: "Iridium", 78: "Platinum", 79: "Gold", 80: "Mercury",
    81: "Thallium", 82: "Lead", 83: "Bismuth", 84: "Polonium", 85: "Astatine",
    86: "Radon", 87: "Francium", 88: "Radium", 89: "Actinium", 90: "Thorium",
    91: "Protactinium", 92: "Uranium", 93: "Neptunium", 94: "Plutonium", 95: "Americium",
    96: "Curium", 97: "Berkelium", 98: "Californium", 99: "Einsteinium", 100: "Fermium",
    101: "Mendelevium", 102: "Nobelium", 103: "Lawrencium", 104: "Rutherfordium", 105: "Dubnium",
    106: "Seaborgium", 107: "Bohrium", 108: "Hassium", 109: "Meitnerium", 110: "Darmstadtium",
    111: "Roentgenium", 112: "Copernicium", 113: "Nihonium", 114: "Flerovium", 115: "Moscovium",
    116: "Livermorium", 117: "Tennessine", 118: "Oganesson"
}

# CSV File for World Model (Known and Unknown Elements)
CSV_FILE = "lacia_world_model.csv"

class LaciaVision:
    def __init__(self):
        # Precompute Dictionary of Known Elemental Waveforms (O(1) Access)
        self.element_waveforms = {Z: self.generate_qualia_waveform(Z) for Z in ELEMENTS}
        # Load Existing World Model from CSV (if exists)
        self.unknown_count = 0
        self.load_world_model()

    def generate_qualia_waveform(self, Z):
        """Generate Perceptual Waveform from Informational Units (Qualia_For_AGI9.pdf)"""
        E_atom = Z * V_p + Z * V_n  # Elemental Energy
        f_num = 1 / np.sqrt(E_atom)  # Frequency from E_atom
        t_num = np.linspace(0, 10, WAVE_LENGTH)
        return np.sin(2 * np.pi * f_num * t_num)

    def navier_stokes_audit(self, waveform):
        """Falsifiable Audit for Physical Validity (NavierStokes.pdf & NS2.pdf)"""
        fft_wave = np.abs(np.fft.fft(waveform))
        fft_wave = fft_wave[1:len(fft_wave)//2]  # Positive frequencies
        k = np.arange(1, len(fft_wave) + 1)
        safe_v = np.where(fft_wave > 1e-12, fft_wave, 1e-12)
        log_k, log_E = np.log(k), np.log(safe_v)
        obs_slope, _ = np.polyfit(log_k, log_E, 1)
        dissonance = abs(obs_slope - LYNCH_SLOPE)
        is_valid = dissonance < DELTA_SAFETY * 10 
        return is_valid, dissonance

    def decompose_multi(self, input_waveform, max_elements=MULTI_MAX_ELEMENTS):
        """Multi-Element Decomposition using Non-Negative Least Squares"""
        Z_list = list(self.element_waveforms.keys())
        A = np.column_stack([self.element_waveforms[Z] for Z in Z_list])
        b = input_waveform
        
        # NNLS: Returns (x, residual_norm)
        w, residual_norm = nnls(A, b)
        
        w_sum = np.sum(w)
        if w_sum > 0:
            w /= w_sum
        
        indices = np.argsort(w)[::-1]
        composition = {}
        for idx in indices[:max_elements]:
            if w[idx] > 0.01:
                Z = Z_list[idx]
                name = ELEMENTS.get(Z, f"Unknown_{abs(Z)}")
                composition[name] = w[idx]
        
        # Error fix: residual_norm is already the Euclidean norm (float)
        # We divide by length to get mean dissonance comparable to single-element check
        diss = (residual_norm**2) / WAVE_LENGTH
        return composition, diss

    def identify_element(self, input_waveform):
        """O(1) Dictionary Match for Elemental Composition"""
        input_waveform = np.array(input_waveform)
        if len(input_waveform) != WAVE_LENGTH:
            raise ValueError(f"Input waveform must be length {WAVE_LENGTH}")
        
        is_valid, dissonance = self.navier_stokes_audit(input_waveform)
        if not is_valid:
            print(f"Waveform Rejected: Manifold Breach (Dissonance: {dissonance:.6f})")
            return None, dissonance
        
        min_diss = float('inf')
        closest_Z = None
        for Z, stored_wave in self.element_waveforms.items():
            diss = np.mean((input_waveform - stored_wave)**2)
            if diss < min_diss:
                min_diss = diss
                closest_Z = Z
        
        if min_diss < MATCH_THRESHOLD:
            element_name = ELEMENTS.get(closest_Z, f"Unknown_{abs(closest_Z)}")
            print(f"Identified Element: {element_name} (Z={closest_Z}, Dissonance: {min_diss:.10f})")
            return closest_Z, min_diss
        else:
            composition, multi_diss = self.decompose_multi(input_waveform)
            if multi_diss < MATCH_THRESHOLD * 10:
                print(f"Identified Mixture (Dissonance: {multi_diss:.10f}):")
                for name, weight in composition.items():
                    print(f" - {name}: {weight:.2f}")
                return composition, multi_diss
            else:
                self.unknown_count += 1
                new_Z = -self.unknown_count 
                self.element_waveforms[new_Z] = input_waveform
                print(f"New Unknown Element Stored as Z={new_Z} (Dissonance to Closest: {min_diss:.10f})")
                return new_Z, min_diss

    def aerohaptic_feedback(self, dissonance):
        """Aerohaptic Feedback Mapping"""
        if dissonance < 1e-8:
            print("Aerohaptic: Smooth Hum (Valid Element - Low Intensity <3W/cm²)")
        elif dissonance < MATCH_THRESHOLD:
            print("Aerohaptic: Gentle Vibration (Close Match - Medium Intensity)")
        else:
            print("Aerohaptic: Sharp Warning (Breach Detected - High Intensity Spike)")

    def log_to_world_model(self, result, dissonance, waveform):
        """Append to CSV World Model"""
        if isinstance(result, dict):
            Z = "Mixture"
            element_name = "; ".join([f"{name}:{weight:.2f}" for name, weight in result.items()])
        else:
            Z = result
            element_name = ELEMENTS.get(Z, f"Unknown_{abs(Z)}")
        
        waveform_str = ','.join([f"{val:.6f}" for val in waveform])
        row = [Z, element_name, dissonance, waveform_str]
        
        file_exists = os.path.isfile(CSV_FILE)
        with open(CSV_FILE, 'a', newline='') as csvfile:
            writer = csv.writer(csvfile)
            if not file_exists:
                writer.writerow(["Z/Mixture", "Element_Name/Composition", "Dissonance", "Waveform"])
            writer.writerow(row)
        print(f"Logged to World Model: {CSV_FILE}")

    def load_nist_csv(self, file_path):
        """Load real NIST ionization data and map to qualia waveforms"""
        if not os.path.isfile(file_path):
            print(f"NIST file not found: {file_path}")
            return
        with open(file_path, 'r') as csvfile:
            reader = csv.reader(csvfile)
            next(reader) 
            for row in reader:
                try:
                    Z = int(row[0])
                    name = row[1]
                    ion_eV = float(row[2])
                    E_proxy = ion_eV * 10000 
                    f_num = 1 / np.sqrt(E_proxy)
                    t_num = np.linspace(0, 10, WAVE_LENGTH)
                    waveform = np.sin(2 * np.pi * f_num * t_num)
                    self.element_waveforms[Z] = waveform
                    print(f"Loaded real NIST: Z={Z} {name} ({ion_eV} eV)")
                except (ValueError, IndexError):
                    continue

    def load_world_model(self):
        """Load Existing World Model from CSV"""
        if os.path.isfile(CSV_FILE):
            with open(CSV_FILE, 'r') as csvfile:
                reader = csv.reader(csvfile)
                next(reader) 
                for row in reader:
                    Z_str = row[0]
                    if Z_str == "Mixture":
                        continue 
                    Z = int(Z_str)
                    waveform = np.array([float(val) for val in row[3].split(',')])
                    self.element_waveforms[Z] = waveform
                    if Z < 0:
                        self.unknown_count = max(self.unknown_count, abs(Z))
            print(f"Loaded World Model from {CSV_FILE}")

    def process_waveform(self, input_waveform):
        """Main Entry: Identify, Audit, Log"""
        result, dissonance = self.identify_element(input_waveform)
        if result is not None:
            self.log_to_world_model(result, dissonance, input_waveform)
            self.aerohaptic_feedback(dissonance)
        return result, dissonance

# --- Example Usage ---
if __name__ == "__main__":
    lacia = LaciaVision()
    
    # Load NIST data if file exists
    lacia.load_nist_csv('nist_ionization.csv')
    
    # Example 1: Known Element (Gold, Z=79)
    gold_wave = lacia.generate_qualia_waveform(79)
    lacia.process_waveform(gold_wave)
    
    # Example 2: Mixture
    carbon_wave = lacia.generate_qualia_waveform(6)
    oxygen_wave = lacia.generate_qualia_waveform(8)
    silicon_wave = lacia.generate_qualia_waveform(14)
    desk_wave = 0.7 * carbon_wave + 0.2 * oxygen_wave + 0.1 * silicon_wave
    lacia.process_waveform(desk_wave)

# Terminal output:
#     (base) brendanlynch@Brendans-Laptop LaciaMemory % python LaciaVisionWave2.py
# Loaded real NIST: Z=1 Hydrogen (13.598434599702 eV)
# Loaded real NIST: Z=2 Helium (24.587389011 eV)
# Loaded real NIST: Z=3 Lithium (5.391714996 eV)
# Loaded real NIST: Z=4 Beryllium (9.322699 eV)
# Loaded real NIST: Z=5 Boron (8.298019 eV)
# Loaded real NIST: Z=6 Carbon (11.260288 eV)
# Loaded real NIST: Z=7 Nitrogen (14.53413 eV)
# Loaded real NIST: Z=8 Oxygen (13.618055 eV)
# Loaded real NIST: Z=9 Fluorine (17.42282 eV)
# Loaded real NIST: Z=10 Neon (21.564541 eV)
# Loaded real NIST: Z=11 Sodium (5.13907696 eV)
# Loaded real NIST: Z=12 Magnesium (7.646236 eV)
# Loaded real NIST: Z=13 Aluminum (5.985769 eV)
# Loaded real NIST: Z=14 Silicon (8.15168 eV)
# Loaded real NIST: Z=15 Phosphorus (10.486686 eV)
# Loaded real NIST: Z=16 Sulfur (10.3600167 eV)
# Loaded real NIST: Z=17 Chlorine (12.967633 eV)
# Loaded real NIST: Z=18 Argon (15.7596119 eV)
# Loaded real NIST: Z=19 Potassium (4.34066373 eV)
# Loaded real NIST: Z=20 Calcium (6.113154921 eV)
# Loaded real NIST: Z=21 Scandium (6.56149 eV)
# Loaded real NIST: Z=22 Titanium (6.82812 eV)
# Loaded real NIST: Z=23 Vanadium (6.746187 eV)
# Loaded real NIST: Z=24 Chromium (6.76651 eV)
# Loaded real NIST: Z=25 Manganese (7.434038 eV)
# Loaded real NIST: Z=26 Iron (7.9024681 eV)
# Loaded real NIST: Z=27 Cobalt (7.88101 eV)
# Loaded real NIST: Z=28 Nickel (7.639878 eV)
# Loaded real NIST: Z=29 Copper (7.72638 eV)
# Loaded real NIST: Z=30 Zinc (9.394197 eV)
# Loaded real NIST: Z=31 Gallium (5.999302 eV)
# Loaded real NIST: Z=32 Germanium (7.899435 eV)
# Loaded real NIST: Z=33 Arsenic (9.78855 eV)
# Loaded real NIST: Z=34 Selenium (9.752368 eV)
# Loaded real NIST: Z=35 Bromine (11.81381 eV)
# Loaded real NIST: Z=36 Krypton (13.9996055 eV)
# Loaded real NIST: Z=37 Rubidium (4.1771281 eV)
# Loaded real NIST: Z=38 Strontium (5.69486745 eV)
# Loaded real NIST: Z=39 Yttrium (6.21726 eV)
# Loaded real NIST: Z=40 Zirconium (6.634126 eV)
# Loaded real NIST: Z=41 Niobium (6.75885 eV)
# Loaded real NIST: Z=42 Molybdenum (7.09243 eV)
# Loaded real NIST: Z=43 Technetium (7.11938 eV)
# Loaded real NIST: Z=44 Ruthenium (7.3605 eV)
# Loaded real NIST: Z=45 Rhodium (7.4589 eV)
# Loaded real NIST: Z=46 Palladium (8.336839 eV)
# Loaded real NIST: Z=47 Silver (7.576234 eV)
# Loaded real NIST: Z=48 Cadmium (8.99382 eV)
# Loaded real NIST: Z=49 Indium (5.7863558 eV)
# Loaded real NIST: Z=50 Tin (7.343918 eV)
# Loaded real NIST: Z=51 Antimony (8.608389 eV)
# Loaded real NIST: Z=52 Tellurium (9.009808 eV)
# Loaded real NIST: Z=53 Iodine (10.451236 eV)
# Loaded real NIST: Z=54 Xenon (12.1298437 eV)
# Loaded real NIST: Z=55 Cesium (3.89390572743 eV)
# Loaded real NIST: Z=56 Barium (5.2116646 eV)
# Loaded real NIST: Z=57 Lanthanum (5.5769 eV)
# Loaded real NIST: Z=58 Cerium (5.5386 eV)
# Loaded real NIST: Z=59 Praseodymium (5.4702 eV)
# Loaded real NIST: Z=60 Neodymium (5.52475 eV)
# Loaded real NIST: Z=61 Promethium (5.58187 eV)
# Loaded real NIST: Z=62 Samarium (5.643722 eV)
# Loaded real NIST: Z=63 Europium (5.670385 eV)
# Loaded real NIST: Z=64 Gadolinium (6.1498 eV)
# Loaded real NIST: Z=65 Terbium (5.8638 eV)
# Loaded real NIST: Z=66 Dysprosium (5.939061 eV)
# Loaded real NIST: Z=67 Holmium (6.0215 eV)
# Loaded real NIST: Z=68 Erbium (6.1077 eV)
# Loaded real NIST: Z=69 Thulium (6.184402 eV)
# Loaded real NIST: Z=70 Ytterbium (6.25416 eV)
# Loaded real NIST: Z=71 Lutetium (5.425871 eV)
# Loaded real NIST: Z=72 Hafnium (6.82507 eV)
# Loaded real NIST: Z=73 Tantalum (7.549571 eV)
# Loaded real NIST: Z=74 Tungsten (7.86403 eV)
# Loaded real NIST: Z=75 Rhenium (7.83352 eV)
# Loaded real NIST: Z=76 Osmium (8.43823 eV)
# Loaded real NIST: Z=77 Iridium (8.96702 eV)
# Loaded real NIST: Z=78 Platinum (8.95883 eV)
# Loaded real NIST: Z=79 Gold (9.225554 eV)
# Loaded real NIST: Z=80 Mercury (10.437504 eV)
# Loaded real NIST: Z=81 Thallium (6.1082873 eV)
# Loaded real NIST: Z=82 Lead (7.4166799 eV)
# Loaded real NIST: Z=83 Bismuth (7.285516 eV)
# Loaded real NIST: Z=84 Polonium (8.41807 eV)
# Loaded real NIST: Z=85 Astatine (9.31751 eV)
# Loaded real NIST: Z=86 Radon (10.7485 eV)
# Loaded real NIST: Z=87 Francium (4.0727411 eV)
# Loaded real NIST: Z=88 Radium (5.2784239 eV)
# Loaded real NIST: Z=89 Actinium (5.380235 eV)
# Loaded real NIST: Z=90 Thorium (6.3067 eV)
# Loaded real NIST: Z=91 Protactinium (5.89 eV)
# Loaded real NIST: Z=92 Uranium (6.19405 eV)
# Loaded real NIST: Z=93 Neptunium (6.265608 eV)
# Loaded real NIST: Z=94 Plutonium (6.02576 eV)
# Loaded real NIST: Z=95 Americium (5.97381 eV)
# Loaded real NIST: Z=96 Curium (5.992241 eV)
# Loaded real NIST: Z=97 Berkelium (6.19785 eV)
# Loaded real NIST: Z=98 Californium (6.281878 eV)
# Loaded real NIST: Z=99 Einsteinium (6.3684 eV)
# Loaded real NIST: Z=100 Fermium (6.5 eV)
# Loaded real NIST: Z=101 Mendelevium (6.58 eV)
# Loaded real NIST: Z=102 Nobelium (6.62621 eV)
# Loaded real NIST: Z=103 Lawrencium (4.96 eV)
# Loaded real NIST: Z=104 Rutherfordium (6.02 eV)
# Loaded real NIST: Z=105 Dubnium (6.8 eV)
# Loaded real NIST: Z=106 Seaborgium (7.8 eV)
# Loaded real NIST: Z=107 Bohrium (7.7 eV)
# Loaded real NIST: Z=108 Hassium (7.6 eV)
# Identified Mixture (Dissonance: 0.0000000000):
#  - Meitnerium: 1.00
# Logged to World Model: lacia_world_model.csv
# Aerohaptic: Smooth Hum (Valid Element - Low Intensity <3W/cm²)
# Identified Mixture (Dissonance: 0.0000000000):
#  - Meitnerium: 0.92
#  - Helium: 0.08
# Logged to World Model: lacia_world_model.csv
# Aerohaptic: Smooth Hum (Valid Element - Low Intensity <3W/cm²)
# (base) brendanlynch@Brendans-Laptop LaciaMemory % 

# lacia_world_model.csv generated was:
# Z/Mixture,Element_Name/Composition,Dissonance,Waveform
# Mixture,Meitnerium:1.00,2.866430590690079e-22,"0.000000,0.000466,0.000931,0.001397,0.001863,0.002329,0.002794,0.003260,0.003726,0.004192,0.004657,0.005123,0.005589,0.006055,0.006520,0.006986,0.007452,0.007917,0.008383,0.008849,0.009315,0.009780,0.010246,0.010712,0.011178,0.011643,0.012109,0.012575,0.013040,0.013506,0.013972,0.014437,0.014903,0.015369,0.015834,0.016300,0.016766,0.017232,0.017697,0.018163,0.018629,0.019094,0.019560,0.020025,0.020491,0.020957,0.021422,0.021888,0.022354,0.022819"
# Mixture,Meitnerium:0.92; Helium:0.08,2.131466759212322e-18,"0.000000,0.001586,0.003173,0.004759,0.006345,0.007932,0.009518,0.011104,0.012690,0.014276,0.015863,0.017449,0.019035,0.020621,0.022207,0.023793,0.025378,0.026964,0.028550,0.030136,0.031721,0.033307,0.034892,0.036477,0.038062,0.039648,0.041233,0.042817,0.044402,0.045987,0.047571,0.049156,0.050740,0.052324,0.053908,0.055492,0.057076,0.058659,0.060243,0.061826,0.063409,0.064992,0.066575,0.068157,0.069740,0.071322,0.072904,0.074486,0.076068,0.077649"
