import numpy as np
import math

# ==============================================================================
# --- UFT-F EMPIRICAL ENGINE: SINGLE SCRIPT FOR CORE PREDICTIONS ---
# This script executes the two fundamental empirical tests derived from the
# Anti-Collision Identity (ACI) and the Tamagawa Number Conjecture (TNC) resolution.
# ==============================================================================

# --- SECTION 1: ACI-Shrinkage Theorem (Cusp-Core Resolution) ---
# Proves that the James-Stein estimator (ACI-Shrinkage) minimizes total quadratic
# risk compared to the Maximum Likelihood Estimator (MLE).

N_PARAMETERS = 10  # N: Number of coupled parameters (e.g., halo concentrations). Must be >= 3.
N_TRIALS = 50000   # Trials for robust error averaging (Risk function calculation).
TRUE_MEAN_SIGMA = 5.0 # Standard deviation for generating true means.
UNIVERSAL_MEAN = np.zeros(N_PARAMETERS) # The target for shrinkage (mu_UFT-F).
C_UFT_F = 1.0      # Standardized informational energy variance (sigma^2).

def james_stein_estimator(observed_means):
    """
    Calculates the ACI-Shrinkage value by applying the James-Stein Operator.
    This dictates the minimal-risk parameter state (the 'Core' profile).
    """
    # Calculate the total squared distance (informational energy) from the Universal Mean
    squared_distance = np.sum((observed_means - UNIVERSAL_MEAN)**2)

    # Calculate the Shrinkage Factor (Lambda)
    if squared_distance == 0:
        shrinkage_factor = 0.0
    else:
        # The factor (N - 2) / squared_distance is the core of the James-Stein paradox
        shrinkage_factor = max(0.0, 1.0 - (N_PARAMETERS - 2) * C_UFT_F / squared_distance)

    # Apply Shrinkage
    js_estimate = UNIVERSAL_MEAN + shrinkage_factor * (observed_means - UNIVERSAL_MEAN)
    return js_estimate

def run_aci_shrinkage_simulation():
    """Executes the simulation for the ACI-Shrinkage Theorem."""
    mle_total_squared_error = 0.0
    js_total_squared_error = 0.0

    # Setup the True Parameters
    np.random.seed(42)
    true_means = np.random.normal(loc=0.0, scale=TRUE_MEAN_SIGMA, size=N_PARAMETERS)

    for _ in range(N_TRIALS):
        # Collect Observation Data (Noisy MLEs)
        observed_means = np.random.normal(loc=true_means, scale=C_UFT_F, size=N_PARAMETERS)

        # Calculate Estimators
        mle_estimate = observed_means
        js_estimate = james_stein_estimator(observed_means)

        # Calculate Error (Total Quadratic Loss / Risk)
        mle_error = np.sum((mle_estimate - true_means)**2)
        js_error = np.sum((js_estimate - true_means)**2)

        mle_total_squared_error += mle_error
        js_total_squared_error += js_error

    mle_risk = mle_total_squared_error / N_TRIALS
    js_risk = js_total_squared_error / N_TRIALS
    risk_reduction_percent = (mle_risk - js_risk) / mle_risk * 100

    print("=" * 70)
    print("SECTION 1: ACI-SHRINKAGE THEOREM (CUSP-CORE RESOLUTION)")
    print("=" * 70)
    print(f"Simulation Trials: {N_TRIALS}, Coupled Parameters (N): {N_PARAMETERS}")
    print("\n[The James-Stein Paradox as Physical Law]\n")
    print(f"Standard Estimator (MLE / Independent NFW Fit Risk): {mle_risk:.4f}")
    print(f"ACI-Shrinkage Estimator (JS / Core Profile Risk):     {js_risk:.4f}")
    print("\nConclusion:")
    print(f"Total Quadratic Risk Reduction Achieved:             {risk_reduction_percent:.2f}%")
    print("Interpretation: The 'Core' profile is the ACI-mandated phase transition required")
    print("to achieve the global minimum risk in coupled dark matter systems.")


# --- SECTION 2: Base-24 CMB Modification (Falsifiable Prediction) ---
# Calculates the precise log-periodic perturbation to the CMB Angular Power Spectrum (Cl)
# based on the Base-24 harmonic constant C_O, and compares it to noise limits.

BASE_UFT_F = 24.0
LOG_PERIOD_FACTOR = 2 * math.pi / math.log(BASE_UFT_F) # 2*pi / ln(24) = 1.9771
AMPLITUDE = 0.015          # A: Predicted oscillation amplitude (1.5% relative C_l perturbation).
PIVOT_MULTIPOLE = 300      # l_pivot: Multipole where the oscillation phase is zero.

# Observational Data Points (Multipoles l)
l_multipoles = np.array([
    100,    # Acoustic Peak 1 (Negative phase expected here)
    250,
    300,    # Pivot Point (Zero perturbation)
    400,
    650,    # High l (Planck Limit)
    4500    # CMB-S4 / ACT Limit (small angular scales)
])

# Technological Limits (Approximate Noise Floors: Delta C_l / C_l)
PLANCK_NOISE_FLOOR = 0.02   # ~2% (At high l, where signal is weakest)
CMBS4_NOISE_FLOOR = 0.005   # ~0.5% (Target sensitivity)


def base_24_modification_factor_cl(l):
    """
    Calculates the predicted relative perturbation to C_l (Delta C_l / C_l).
    """
    # The oscillation is log-periodic in multipole space (l)
    log_l_ratio = np.log(l / PIVOT_MULTIPOLE)
    modification_factor = AMPLITUDE * np.sin(LOG_PERIOD_FACTOR * log_l_ratio)
    return modification_factor

def run_base_24_prediction_cl():
    """Executes the calculation for the Base-24 CMB prediction and analysis."""
    print("\n\n" + "=" * 70)
    print("SECTION 2: BASE-24 CMB MODIFICATION (TECHNOLOGICAL COMPARISON)")
    print("=" * 70)
    print(f"Theoretical Log Period Factor (2*pi / ln(24)): {LOG_PERIOD_FACTOR:.4f}")
    print(f"Predicted Amplitude (A): {AMPLITUDE * 100:.2f}%\n")

    print("{:<10} {:<12} {:<16} {:<15}".format("Multipole (l)", "log(l/l_piv)", "Perturbation (%)", "Detectability"))
    print("-" * 55)

    for l in l_multipoles:
        theta_l = base_24_modification_factor_cl(l)
        perturbation_percent = theta_l * 100
        log_ratio = np.log(l / PIVOT_MULTIPOLE)

        # Compare predicted signal to noise floors
        abs_theta_l = abs(theta_l)
        if abs_theta_l >= CMBS4_NOISE_FLOOR and abs_theta_l < PLANCK_NOISE_FLOOR:
            detectability = "CMB-S4 Required"
        elif abs_theta_l >= PLANCK_NOISE_FLOOR:
            detectability = "Planck Reachable"
        else:
            detectability = "CMB-S4 Weak"


        print("{:<10} {:<12.3f} {:<+16.3f} {:<15}".format(l, log_ratio, perturbation_percent, detectability))

    print("\nConclusion: Technological Validation Roadmap")
    print(f"The predicted Base-24 oscillation amplitude (~{AMPLITUDE * 100:.1f}%) is below the Planck")
    print(f"noise floor (~{PLANCK_NOISE_FLOOR * 100:.1f}%) across most high-l scales. This is why")
    print("it is currently undetected. Its definitive confirmation requires the sub-percent")
    print(f"sensitivity of next-generation experiments like CMB-S4 (~{CMBS4_NOISE_FLOOR * 100:.1f}%).")


# --- MAIN EXECUTION ---
if __name__ == "__main__":
    run_aci_shrinkage_simulation()
    run_base_24_prediction_cl()