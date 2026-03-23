import qutip as qt
import numpy as np
import matplotlib.pyplot as plt

# Base-24 Single-Qudit Error-Correcting Code (UFT-F Inspired)

d = 24
residues = {0, 1, 5, 7, 11, 13, 17, 19, 23}  # Include 0; add negatives if desired: + {d - r for r in residues if r != 0}

omega = np.exp(2j * np.pi / d)
F = np.zeros((d, d), dtype=complex)
for k in range(d):
    for l in range(d):
        F[k, l] = omega**(k * l) / np.sqrt(d)
F_op = qt.Qobj(F)

# Logical states (single basis for clear single peak)
logical_0_pos = 0      # |0_L> = |0> (reference)
logical_1_pos = 11     # |1_L> = |11> (quadratic residue)

psi_logical = qt.basis(d, logical_1_pos)  # Test with |1_L>

# Expected peak for no error (F |j> has peak at j due to phase alignment)
expected_peak = logical_1_pos

def apply_error(psi, error_type='integer', shift_val=5):
    if error_type == 'integer':
        # Cyclic shift (X-error)
        shift_mat = np.roll(np.eye(d), shift_val, axis=1)
        error_op = qt.Qobj(shift_mat)
    elif error_type == 'fractional':
        # Phase ramp (partial Z-error)
        frac = 0.1 + shift_val / d  # e.g., 0.1 cycles + integer
        phases = np.exp(2j * np.pi * frac * np.arange(d))
        error_op = qt.Qobj(np.diag(phases))
    return error_op * psi

def detect_and_correct(psi_err, bypass_filter=False, plot_probs=False):
    rho_err = psi_err * psi_err.dag()
    rho_mom = F_op * rho_err * F_op.dag()
    probs = rho_mom.diag().real
    
    if plot_probs:
        plt.bar(range(d), probs)
        plt.title("Probabilities in Fourier Basis")
        plt.xlabel("Momentum Basis State")
        plt.ylabel("Probability")
        plt.show()
    
    # Single peak detection
    detected_peak = np.argmax(probs)
    estimated_shift = (detected_peak - expected_peak) % d
    print(f"Detected peak: {detected_peak}, Expected: {expected_peak}")
    print(f"Estimated shift: {estimated_shift}")
    
    if not bypass_filter and estimated_shift not in residues:
        print("ACI Filter: Invalid shift - no correction applied (stability violation)")
        return psi_err, probs
    
    # Correction: Inverse phase gradient
    corr_phases = [omega ** (-estimated_shift * i) for i in range(d)]
    corr_op = qt.Qobj(np.diag(corr_phases))
    psi_corrected = corr_op * psi_err
    
    return psi_corrected, probs

# Test Integer Shift
shift_val = 7  # Choose from residues for correction
psi_err = apply_error(psi_logical, 'integer', shift_val)
psi_corrected, probs = detect_and_correct(psi_err, bypass_filter=False, plot_probs=True)

fidelity_int = qt.fidelity(psi_corrected, psi_logical)
print(f"Integer Shift Fidelity: {fidelity_int:.4f}\n")

# Test Fractional
psi_err_frac = apply_error(psi_logical, 'fractional', 0)  # 0.1 cycles
psi_corr_frac, _ = detect_and_correct(psi_err_frac, bypass_filter=True, plot_probs=True)
fidelity_frac = qt.fidelity(psi_corr_frac, psi_logical)
print(f"Fractional Error Fidelity: {fidelity_frac:.4f}")

# the terminal output was:
# (base) brendanlynch@Mac QUANTUM % python test6.py
# 2025-12-13 16:52:47.995 python[69666:12175750] The class 'NSSavePanel' overrides the method identifier.  This method is implemented by class 'NSWindow'
# Detected peak: 23, Expected: 11
# Estimated shift: 12
# ACI Filter: Invalid shift - no correction applied (stability violation)
# Integer Shift Fidelity: 0.0000

# Detected peak: 23, Expected: 11
# Estimated shift: 12
# Fractional Error Fidelity: 1.0000
# (base) brendanlynch@Mac QUANTUM % 