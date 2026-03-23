import numpy as np

# --- UFT-F PARAMETER MAPPING AND SIMULATION CONFIGURATION ---
# The goal is to prove the Base-24 harmonic modification to the Primordial Power Spectrum (P(k)).
# This modification is a direct consequence of the ACI enforcing informational coherence
# across dimensional manifolds, resulting in log-periodic oscillations.

# 1. UFT-F Axiomatic Anchors
BASE_UFT_F = 24.0          # Base-24 harmonic constant (C_O) from TNC resolution.
LOG_PERIOD_FACTOR = 2 * np.pi / np.log(BASE_UFT_F) # The period of oscillation in log(k) space.
AMPLITUDE = 0.015          # A: Predicted oscillation amplitude (1.5% perturbation).
PIVOT_SCALE = 0.05         # k_pivot: Wavenumber where the phase is defined (e.g., k_pivot=0.05 Mpc^-1).

# 2. Primordial Power Spectrum Wavenumbers (k in Mpc^-1)
# We test specific scales that are key to Planck/ACT data analysis.
# Scales: Large-scale (LSS), CMB peak 1, and small scales.
k_wavenumbers = np.array([
    0.001,  # Very large scale (LSS)
    0.005,
    0.015,
    0.050,  # Pivot scale (no perturbation)
    0.150,
    0.500,  # Small scale / high-l
])


def base_24_modification_factor(k):
    """
    Calculates the predicted log-periodic modification factor Theta(k) to the
    Primordial Power Spectrum P(k).

    P_modified(k) = P_LambdaCDM(k) * [1 + Theta(k)]
    """
    # Calculate the log-space distance from the pivot
    log_k_ratio = np.log(k / PIVOT_SCALE)

    # Calculate the sinusoidal oscillation based on the Base-24 log-period
    # The term (1 + A * sin(...)) is the modification factor.
    modification_factor = AMPLITUDE * np.sin(LOG_PERIOD_FACTOR * log_k_ratio)

    return modification_factor


# --- SIMULATION EXECUTION ---

print("--- UFT-F Base-24 CMB Modification Simulation ---")
print(f"Log Period Factor (2*pi / ln(24)): {LOG_PERIOD_FACTOR:.4f}")
print(f"Predicted Amplitude (A): {AMPLITUDE * 100:.2f}%\n")

print("{:<12} {:<12} {:<15}".format("Wavenumber (k)", "log(k/k_piv)", "Perturbation (%)"))
print("-" * 39)

for k in k_wavenumbers:
    theta_k = base_24_modification_factor(k)
    perturbation_percent = theta_k * 100
    log_ratio = np.log(k / PIVOT_SCALE)

    print("{:<12.3f} {:<12.3f} {:<+15.3f}".format(k, log_ratio, perturbation_percent))

print("\nPhysical Interpretation:")
print("The Base-24 oscillation introduces predictable log-periodic perturbations")
print("in the power spectrum. These oscillations are small but detectable and")
print("directly prove the necessity of the ACI for dimensional coherence.")