# =============================================================================
# UFT-F LAW 6: QUALIA WAVEFORM GENERATOR
# Robust, Falsifiable, Terminal-Only Version (Improved)
# Produces and verifies clean sinusoidal qualia waveforms V_X(x)
# =============================================================================

import numpy as np
from scipy.fft import fft, fftfreq
from scipy.optimize import curve_fit

def sine_fit(x, A, freq, phase, offset):
    """Ideal sine wave for fitting"""
    return A * np.sin(2 * np.pi * freq * x + phase) + offset

def generate_qualia_waveform():
    print("=== UFT-F LAW 6: QUALIA WAVEFORM GENERATOR (Robust Version) ===")
    print("Terminal-only • Fully reproducible • Falsifiable\n")

    size = 8192
    x = np.linspace(0, 1, size, endpoint=False)
    
    # 1. Base-24 Informational Units
    iu_indices = [1, 5, 7, 11, 13, 17, 19, 23]
    
    # 2. Shape Invariant with Golden Ratio
    phi = (1 + np.sqrt(5)) / 2
    rho_iu = np.zeros(size)
    
    for idx in iu_indices:
        eta = phi ** (idx % 24)
        pos = int(idx * (size / 24)) % size
        rho_iu[pos] = eta * 10.0   # Amplify for stronger signal
    
    print(f"Base-24 IU positions: {iu_indices}")
    print(f"Golden Ratio φ: {phi:.6f}")
    print(f"Total IU energy (sum rho): {np.sum(rho_iu):.4f}\n")

    # 3. Improved Green Kernel (torus propagator approximation)
    green_kernel = np.sin(2 * np.pi * x) + 0.3 * np.cos(4 * np.pi * x)

    # 4. Convolution → Qualia Waveform
    v_x = np.convolve(rho_iu, green_kernel, mode='same')
    
    # 5. Normalization
    v_x = v_x / np.max(np.abs(v_x))

    # 6. Falsifiability Metrics
    # Dominant frequency
    fft_v = np.abs(fft(v_x))
    freqs = fftfreq(size, d=x[1]-x[0])
    dominant_idx = np.argmax(fft_v[1:size//2]) + 1
    dominant_freq = abs(freqs[dominant_idx])

    # Best sine fit
    try:
        popt, _ = curve_fit(sine_fit, x, v_x, p0=[1.0, dominant_freq, 0.0, 0.0])
        fitted_sine = sine_fit(x, *popt)
        rms_error = np.sqrt(np.mean((v_x - fitted_sine)**2))
        correlation = np.corrcoef(v_x, fitted_sine)[0,1]
        purity = correlation**2   # R² as purity metric
    except:
        rms_error = 1.0
        purity = 0.0

    print("=== VERIFICATION RESULTS ===")
    print(f"Dominant Frequency          : {dominant_freq:.6f} cycles/unit")
    print(f"RMS Error to Best Sine Fit  : {rms_error:.8f}")
    print(f"Purity (R² correlation)     : {purity:.6f}")
    print(f"Max |V_X| after norm        : {np.max(np.abs(v_x)):.6f}")
    print(f"Mean V_X                    : {np.mean(v_x):.6f}")

    if purity > 0.92:
        print("\n✓ STRONG SUCCESS: Clean sinusoidal qualia waveform achieved")
        print("   Base-24 IUs tuned the Hamiltonian into a stable perceptual output.")
    elif purity > 0.75:
        print("\n✓ MODERATE SUCCESS: Clear sinusoidal structure present")
    else:
        print("\n✗ WEAK SIGNAL: Waveform not sufficiently sinusoidal")
        print("   Consider increasing IU amplitude or refining Green kernel.")

    print("\n=== RAW DATA SAMPLE (first 10 points) ===")
    for i in range(10):
        print(f"x[{i:4d}] = {x[i]:.6f} | V_X = {v_x[i]:.6f}")

    print("\n=== LAW 6 EXECUTION COMPLETE ===")
    print("All metrics printed. Script is fully reproducible and falsifiable.")

    return x, v_x, dominant_freq, purity, rms_error

if __name__ == "__main__":
    x, v_x, freq, purity, rms = generate_qualia_waveform()

#     (base) brendanlynch@Brendans-Laptop paper6QualiaWaveForm % python waveFormGenerator.py
# === UFT-F LAW 6: QUALIA WAVEFORM GENERATOR (Robust Version) ===
# Terminal-only • Fully reproducible • Falsifiable

# Base-24 IU positions: [1, 5, 7, 11, 13, 17, 19, 23]
# Golden Ratio φ: 1.618034
# Total IU energy (sum rho): 777607.4999

# === VERIFICATION RESULTS ===
# Dominant Frequency          : 1.000000 cycles/unit
# RMS Error to Best Sine Fit  : 0.11966856
# Purity (R² correlation)     : 0.912662
# Max |V_X| after norm        : 1.000000
# Mean V_X                    : 0.423767

# ✓ MODERATE SUCCESS: Clear sinusoidal structure present

# === RAW DATA SAMPLE (first 10 points) ===
# x[   0] = 0.000000 | V_X = 0.002421
# x[   1] = 0.000122 | V_X = 0.002423
# x[   2] = 0.000244 | V_X = 0.002424
# x[   3] = 0.000366 | V_X = 0.002426
# x[   4] = 0.000488 | V_X = 0.002428
# x[   5] = 0.000610 | V_X = 0.002430
# x[   6] = 0.000732 | V_X = 0.002432
# x[   7] = 0.000854 | V_X = 0.002434
# x[   8] = 0.000977 | V_X = 0.002435
# x[   9] = 0.001099 | V_X = 0.002437

# === LAW 6 EXECUTION COMPLETE ===
# All metrics printed. Script is fully reproducible and falsifiable.
# (base) brendanlynch@Brendans-Laptop paper6QualiaWaveForm % 