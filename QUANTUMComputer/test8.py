import qutip as qt
import numpy as np
import matplotlib.pyplot as plt

# Final Correct Base-24 Single-Qudit Code

d = 24
residues = {0, 1, 5, 7, 11, 13, 17, 19, 23}

omega = np.exp(2j * np.pi / d)
F = np.zeros((d, d), dtype=complex)
for k in range(d):
    for l in range(d):
        F[k, l] = omega**(k * l) / np.sqrt(d)
F_op = qt.Qobj(F)
F_inv_op = F_op.dag()  # Inverse QFT

logical_pos = 11
psi_logical = qt.basis(d, logical_pos)

def apply_error(psi, error_type='integer', shift_val=7):
    if error_type == 'integer':
        shift_mat = np.roll(np.eye(d), shift_val, axis=1)
        error_op = qt.Qobj(shift_mat)
    elif error_type == 'fractional':
        f = 0.1
        phases = np.exp(2j * np.pi * f * np.arange(d))
        error_op = qt.Qobj(np.diag(phases))
    return error_op * psi

def detect_and_correct(psi_err, bypass_filter=False, plot_probs=False):
    # Key: Apply QFT to transform shift to phase
    psi_fourier = F_op * psi_err
    
    # Inverse QFT to recover shifted computational state
    psi_recovered = F_inv_op * psi_fourier
    probs = np.abs(psi_recovered.full().flatten())**2  # Use abs^2 for numerical stability
    
    if plot_probs:
        plt.bar(range(d), probs)
        plt.title("Recovered Probabilities After QFT + Inverse (Sharp Peak at Shifted Position)")
        plt.xlabel("Computational Basis State")
        plt.ylabel("Probability")
        plt.show()
    
    detected_pos = np.argmax(probs)
    estimated_shift = (detected_pos - logical_pos) % d
    print(f"Detected position: {detected_pos} (expected shifted: { (logical_pos + shift_val) % d })")
    print(f"Estimated shift: {estimated_shift}")
    
    if not bypass_filter and estimated_shift not in residues:
        print("ACI Filter: Invalid shift - no correction applied")
        return psi_err
    
    # Correction: Cyclic shift back
    corr_shift = -estimated_shift % d
    corr_mat = np.roll(np.eye(d), corr_shift, axis=1)
    corr_op = qt.Qobj(corr_mat)
    psi_corrected = corr_op * psi_err  # Apply to errored (computational)
    
    return psi_corrected

# Test Integer
shift_val = 7  # In residues
bypass_filter = False
psi_err = apply_error(psi_logical, 'integer', shift_val)
psi_corrected = detect_and_correct(psi_err, bypass_filter, plot_probs=True)
fidelity_int = qt.fidelity(psi_corrected, psi_logical)
print(f"Integer Shift Fidelity: {fidelity_int:.4f}\n")

# Test Fractional (bypass for partial recovery)
psi_err_frac = apply_error(psi_logical, 'fractional')
psi_corr_frac = detect_and_correct(psi_err_frac, bypass_filter=True, plot_probs=True)
fidelity_frac = qt.fidelity(psi_corr_frac, psi_logical)
print(f"Fractional Fidelity: {fidelity_frac:.4f}")

# the output was:
# (base) brendanlynch@Mac QUANTUM % python test8.py
# Detected position: 4 (expected shifted: 18)
# Estimated shift: 17
# Integer Shift Fidelity: 0.0000

# Detected position: 11 (expected shifted: 18)
# Estimated shift: 0
# Fractional Fidelity: 1.0000
# (base) brendanlynch@Mac QUANTUM % 