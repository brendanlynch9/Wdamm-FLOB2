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

# Periodic Table Elements (Z: Name) - Full Dictionary (1-118)
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

# CSV File for World Model
CSV_FILE = "lacia_world_model.csv"

class LaciaVision:
    def __init__(self):
        # Precompute known elemental waveforms
        self.element_waveforms = {Z: self.generate_qualia_waveform(Z) for Z in ELEMENTS}
        self.unknown_count = 0
        self.load_world_model()

    def generate_qualia_waveform(self, Z):
        E_atom = Z * V_p + Z * V_n
        f_num = 1 / np.sqrt(E_atom)
        t_num = np.linspace(0, 10, WAVE_LENGTH)
        return np.sin(2 * np.pi * f_num * t_num)

    def navier_stokes_audit(self, waveform):
        fft_wave = np.abs(np.fft.fft(waveform))[1:WAVE_LENGTH//2]
        k = np.arange(1, len(fft_wave) + 1)
        safe_v = np.where(fft_wave > 1e-12, fft_wave, 1e-12)
        log_k, log_E = np.log(k), np.log(safe_v)
        obs_slope, _ = np.polyfit(log_k, log_E, 1)
        dissonance = abs(obs_slope - LYNCH_SLOPE)
        is_valid = dissonance < DELTA_SAFETY * 10
        return is_valid, dissonance

    def decompose_multi(self, input_waveform):
        Z_list = list(self.element_waveforms.keys())
        A = np.column_stack([self.element_waveforms[Z] for Z in Z_list])
        b = input_waveform
        w, _ = nnls(A, b)
        w_sum = np.sum(w)
        if w_sum > 0:
            w /= w_sum
        indices = np.argsort(w)[::-1]
        composition = {}
        for idx in indices[:MULTI_MAX_ELEMENTS]:
            if w[idx] > 0.01:
                Z = Z_list[idx]
                name = ELEMENTS.get(Z, f"Unknown_{abs(Z)}")
                composition[name] = w[idx]
        residual = A @ w - b
        diss = np.mean(residual**2)
        return composition, diss

    def identify_element(self, input_waveform):
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
            name = ELEMENTS.get(closest_Z, f"Unknown_{abs(closest_Z)}")
            print(f"Identified Element: {name} (Z={closest_Z}, Dissonance: {min_diss:.10f})")
            return closest_Z, min_diss
        else:
            composition, multi_diss = self.decompose_multi(input_waveform)
            if multi_diss < MATCH_THRESHOLD * 50:
                print(f"Identified Mixture (Dissonance: {multi_diss:.10f}):")
                for name, weight in composition.items():
                    print(f" - {name}: {weight:.2%}")
                return composition, multi_diss
            else:
                self.unknown_count += 1
                new_Z = -self.unknown_count
                self.element_waveforms[new_Z] = input_waveform
                print(f"New Unknown Element Stored as Z={new_Z} (Closest Dissonance: {min_diss:.10f})")
                return new_Z, min_diss

    def aerohaptic_feedback(self, dissonance):
        if dissonance < 1e-8:
            print("Aerohaptic: Smooth Hum (Pure Resonance - Low Intensity <3W/cm²)")
        elif dissonance < MATCH_THRESHOLD:
            print("Aerohaptic: Gentle Vibration (Strong Match - Medium Intensity)")
        elif dissonance < 0.01:
            print("Aerohaptic: Subtle Pulse (Mixture Detected - Balanced Intensity)")
        else:
            print("Aerohaptic: Sharp Warning Spike (Breach/Unknown - High Intensity)")

    def log_to_world_model(self, result, dissonance, waveform):
        if isinstance(result, dict):
            Z = "Mixture"
            name = "; ".join([f"{n}:{w:.2%}" for n, w in result.items()])
        else:
            Z = result
            name = ELEMENTS.get(Z, f"Unknown_{abs(Z)}")
        waveform_str = ','.join(f"{v:.6f}" for v in waveform)
        row = [Z, name, dissonance, waveform_str]
        file_exists = os.path.isfile(CSV_FILE)
        with open(CSV_FILE, 'a', newline='') as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(["Z/Mixture", "Element_Name/Composition", "Dissonance", "Waveform"])
            writer.writerow(row)
        print(f"Logged to World Model: {CSV_FILE}")

    def load_nist_csv(self, file_path):
        if not os.path.isfile(file_path):
            print(f"NIST file not found: {file_path}")
            return
        with open(file_path, 'r') as f:
            reader = csv.reader(f)
            next(reader, None)  # Skip header
            for row in reader:
                if len(row) < 3:
                    continue
                try:
                    Z = int(row[0])
                    name = row[1].strip()
                    ion_eV = float(row[2])
                    E_proxy = ion_eV * 10000  # Scale to approximate E_atom
                    f_num = 1 / np.sqrt(E_proxy)
                    t_num = np.linspace(0, 10, WAVE_LENGTH)
                    waveform = np.sin(2 * np.pi * f_num * t_num)
                    self.element_waveforms[Z] = waveform
                    print(f"Loaded NIST: Z={Z} {name} ({ion_eV} eV)")
                except (ValueError, IndexError):
                    continue

    def load_world_model(self):
        if os.path.isfile(CSV_FILE):
            with open(CSV_FILE, 'r') as f:
                reader = csv.reader(f)
                next(reader, None)
                for row in reader:
                    if len(row) < 4:
                        continue
                    try:
                        Z_str = row[0]
                        if Z_str == "Mixture":
                            continue
                        Z = int(Z_str)
                        waveform = np.array([float(v) for v in row[3].split(',')])
                        self.element_waveforms[Z] = waveform
                        if Z < 0:
                            self.unknown_count = max(self.unknown_count, abs(Z))
                    except:
                        continue
            print(f"Loaded existing world model from {CSV_FILE}")

    def process_waveform(self, input_waveform):
        result, dissonance = self.identify_element(input_waveform)
        if result is not None:
            self.log_to_world_model(result, dissonance, input_waveform)
            self.aerohaptic_feedback(dissonance)
        return result, dissonance

# --- Example Usage ---
if __name__ == "__main__":
    lacia = LaciaVision()

    # Uncomment to load real NIST data
    lacia.load_nist_csv('nist_ionization.csv')

    # Test 1: Pure Gold
    gold_wave = lacia.generate_qualia_waveform(79)
    lacia.process_waveform(gold_wave)

    # Test 2: Wood-like mixture
    carbon = lacia.generate_qualia_waveform(6)
    oxygen = lacia.generate_qualia_waveform(8)
    hydrogen = lacia.generate_qualia_waveform(1)
    silicon = lacia.generate_qualia_waveform(14)
    wood_wave = 0.75 * carbon + 0.15 * oxygen + 0.08 * hydrogen + 0.02 * silicon
    lacia.process_waveform(wood_wave)

    # Test 3: Chaos
    chaos = np.random.rand(WAVE_LENGTH) * 10
    lacia.process_waveform(chaos)

    # Test 4: Composite
    carbon = lacia.generate_qualia_waveform(6)   # Main component of cellulose
    oxygen = lacia.generate_qualia_waveform(8)   # Abundant in organic compounds
    hydrogen = lacia.generate_qualia_waveform(1) # High in hydrocarbons
    silicon = lacia.generate_qualia_waveform(14)  # Trace in some woods/plants
    wood_desk_wave = (0.75 * carbon + 
                  0.15 * oxygen + 
                  0.08 * hydrogen + 
                  0.02 * silicon)
lacia.process_waveform(wood_desk_wave)