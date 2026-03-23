import numpy as np
from scipy.optimize import nnls
import matplotlib.pyplot as plt

# 1. THE UFT-F BASIS (Axiomatic Frequency Scaling)
def generate_basis(num_elements=118, samples=50):
    t = np.linspace(0, 1, samples)
    basis = []
    for Z in range(1, num_elements + 1):
        # f_Z = 1 / sqrt(Z * V_const)
        freq = 1 / np.sqrt(Z * 0.003119) 
        wave = np.sin(2 * np.pi * freq * t)
        basis.append(wave / np.linalg.norm(wave))
    return np.array(basis).T, t

# 2. ADVERSARIAL NOISE (The Spectral Mimic)
def generate_mimic_noise(target_element_wave, samples=50):
    # Mimics the frequency but forces a high-frequency entropy spike 
    # (Violates the Lynch Slope while maintaining low L2 residual)
    noise = np.random.normal(0, 0.05, samples)
    mimic = target_element_wave + noise
    # Intentional Slope Corruption: Adding high-freq energy
    mimic += 0.2 * np.sin(2 * np.pi * 45 * np.linspace(0, 1, samples)) 
    return mimic / np.linalg.norm(mimic)

# 3. THE NAVIER-STOKES AUDIT (The Lynch Slope Check)
def navier_stokes_audit(signal, lynch_slope=-1.6466):
    psd = np.abs(np.fft.fft(signal))**2
    freqs = np.fft.fftfreq(len(signal))
    
    # Filter for positive frequencies and log-transform
    mask = freqs > 0
    log_k = np.log(freqs[mask])
    log_E = np.log(psd[mask])
    
    # Calculate empirical slope
    slope, _ = np.polyfit(log_k, log_E, 1)
    dissonance = abs(slope - lynch_slope)
    return dissonance, slope

# 4. THE SOVEREIGN ENCODER (Audit vs. Inference)
A, t = generate_basis()
iron_wave = A[:, 25] # Iron (Z=26)
signal = generate_mimic_noise(iron_wave)

# Statistical Inference (NNLS)
weights_inf, _ = nnls(A, signal)

# Sovereign Audit (Navier-Stokes Gate)
diss, empirical_slope = navier_stokes_audit(signal)
is_physical = diss < 0.5 # Modularity threshold

print(f"--- Perceptual Audit Results ---")
print(f"Inference Identity: Z={np.argmax(weights_inf)+1}")
print(f"Empirical Slope: {empirical_slope:.4f} (Target: -1.6466)")
print(f"Sovereign Decision: {'ACCEPTED' if is_physical else 'REJECTED - MANIFOLD BREACH'}")

# (base) brendanlynch@Brendans-Laptop laciaVision % python Sovereign_Audit_Test.py 
# --- Perceptual Audit Results ---
# Inference Identity: Z=28
# Empirical Slope: -1.7256 (Target: -1.6466)
# Sovereign Decision: ACCEPTED
# (base) brendanlynch@Brendans-Laptop laciaVision % 
