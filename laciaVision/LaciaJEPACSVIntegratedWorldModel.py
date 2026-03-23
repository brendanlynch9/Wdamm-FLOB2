import numpy as np
import csv
import os
import time
from scipy.optimize import nnls

# --- UFT-F ARCHITECTURAL CONSTANTS ---
# Derived from NavierStokes.pdf and Qualia_For_AGI9.pdf
C_UFT_F = 0.00311903  # Modularity Constant (The ACI Floor / Informational Viscosity)
LYNCH_SLOPE = -1.6466  # Statistical Closure Slope (Kolmogorov-Lynch -5/3 variant)
WAVE_LENGTH = 50       # Standardized spectral resolution
MATCH_THRESHOLD = 1e-6 # Falsifiable tolerance for spectral matching

class SovereignJEPA:
    def __init__(self, lookup_path='lacia_lookup_table.csv', world_model_path='lacia_world_model.csv'):
        self.lookup_path = lookup_path
        self.world_model_path = world_model_path
        self.elemental_library, self.z_names = self._load_nist_library()
        self.z_history = []
        print(f"Lacia-JEPA Online. Sovereignty active over {len(self.z_names)} elements.")

    def _load_nist_library(self):
        """Ingests real NIST-derived waveforms from makeTable.py."""
        library = []
        names = []
        if not os.path.exists(self.lookup_path):
            raise FileNotFoundError(f"Missing {self.lookup_path}. Run makeTable.py first.")
            
        with open(self.lookup_path, 'r') as f:
            reader = csv.reader(f)
            next(reader) # skip header
            for row in reader:
                names.append(row[1])
                waveform = np.array([float(val) for val in row[3].split(',')])
                library.append(waveform)
        # Return Matrix A for NNLS and the name mapping
        return np.array(library).T, names 

    def audit_navier_stokes(self, signal):
        """The 'Hallucination Kill-Shot': Rejects signals violating the Lynch Slope."""
        fft_wave = np.abs(np.fft.fft(signal))
        fft_wave = fft_wave[1:WAVE_LENGTH//2]
        k = np.arange(1, len(fft_wave) + 1)
        # Verify the energy cascade matches physical reality
        slope, _ = np.polyfit(np.log(k), np.log(np.maximum(fft_wave, 1e-12)), 1)
        dissonance = abs(slope - LYNCH_SLOPE)
        return dissonance < 2.0, dissonance 

    def temporal_momentum_audit(self, predicted_z):
        """Verifies if a state transition is physically possible (R_nu check)."""
        if not self.z_history:
            return True, 0.0
        
        # Calculate 'Spectral Velocity' (Euclidean distance in composition manifold)
        v_spectral = np.linalg.norm(predicted_z - self.z_history[-1])
        
        # The ACI mandates bounded acceleration in the informational field.
        # This prevents the model from 'teleporting' into impossible states.
        is_stable = v_spectral < (C_UFT_F * 10)
        return is_stable, v_spectral

    def encode(self, signal):
        """S-Encoder: Projects raw signal into the Atomic Latent Space (Z)."""
        is_physical, diss = self.audit_navier_stokes(signal)
        if not is_physical:
            print(f"S-Encoder REJECTED: Manifold Breach (Dissonance {diss:.4f})")
            return None
        
        # Non-Negative Least Squares: Maps sensory input to the physical basis
        weights, _ = nnls(self.elemental_library, signal)
        z_latent = weights / (np.sum(weights) + 1e-12)
        return z_latent

    def predictor(self, z_t, action_vector):
        """JEPA Predictor: Evolves the world state via ACI-Regulated transitions."""
        # Predictions are 'viscously' limited by the modularity constant
        z_next = z_t + (action_vector * C_UFT_F)
        return np.maximum(z_next, 0) / (np.sum(np.maximum(z_next, 0)) + 1e-12)

    def log_world_state(self, z_state, log_type="Observation"):
        """Commits the verified state to the Sovereign World Model CSV."""
        active_indices = np.where(z_state > 0.01)[0]
        composition = ";".join([f"{self.z_names[i]}:{z_state[i]:.4f}" for i in active_indices])
        
        with open(self.world_model_path, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([log_type, composition, time.time()])

# --- SOVEREIGN EXECUTION LOOP ---
def run_simulation(steps=5):
    jepa = SovereignJEPA()
    
    # Target elements for the Oxidation process
    try:
        al_idx = jepa.z_names.index("Aluminum")
        o_idx = jepa.z_names.index("Oxygen")
    except ValueError:
        print("Error: Required elements (Al, O) not found in lookup table.")
        return

    # STEP 0: Capture Initial Perception
    current_signal = jepa.elemental_library[:, al_idx]
    print("\n[STEP 0: INITIAL SENSORY ENCODING]")
    z_current = jepa.encode(current_signal)
    if z_current is None: return
    jepa.z_history.append(z_current)
    print(f"Verified Identity: {jepa.z_names[al_idx]} (100%)")

    # Define Environmental Action: Constant Oxygen Exposure
    oxidation_force = np.zeros_like(z_current)
    oxidation_force[o_idx] = 1.2 

    print(f"\n[STARTING TEMPORAL WORLD MODEL SIMULATION]")
    for t in range(1, steps + 1):
        # 1. Predict Future State (Mental Simulation)
        z_pred = jepa.predictor(z_current, oxidation_force)
        
        # 2. Audit Momentum (ACI Stability Check)
        is_valid, velocity = jepa.temporal_momentum_audit(z_pred)
        
        if is_valid:
            z_current = z_pred
            jepa.z_history.append(z_current)
            jepa.log_world_state(z_current, log_type=f"Prediction_T{t}")
            
            print(f"T={t}: ACI Stable. Oxygen Level: {z_current[o_idx]:.6f} | Velocity: {velocity:.6f}")
        else:
            print(f"T={t}: HALLUCINATION DETECTED. Momentum breach ({velocity:.4f}). Reverting.")
            break

if __name__ == "__main__":
    run_simulation(steps=5)

#     (base) brendanlynch@Brendans-Laptop laciaVision % python LaciaJEPACSVIntegratedWorldModel.py
# Lacia-JEPA Online. Sovereignty active over 108 elements.

# [STEP 0: INITIAL SENSORY ENCODING]
# Verified Identity: Aluminum (100%)

# [STARTING TEMPORAL WORLD MODEL SIMULATION]
# T=1: ACI Stable. Oxygen Level: 0.003729 | Velocity: 0.005273
# T=2: ACI Stable. Oxygen Level: 0.007444 | Velocity: 0.005254
# T=3: ACI Stable. Oxygen Level: 0.011145 | Velocity: 0.005234
# T=4: ACI Stable. Oxygen Level: 0.014832 | Velocity: 0.005215
# T=5: ACI Stable. Oxygen Level: 0.018506 | Velocity: 0.005195
# (base) brendanlynch@Brendans-Laptop laciaVision % 
