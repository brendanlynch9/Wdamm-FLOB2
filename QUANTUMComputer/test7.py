import qutip as qt
import numpy as np
import matplotlib.pyplot as plt

# Working Base-24 Single-Qudit Shift/Phase Error Code (UFT-F: ACI Filter + Base-24 QFT)

d = 24
residues = {0, 1, 5, 7, 11, 13, 17, 19, 23}  # Quadratic residues for ACI stability

omega = np.exp(2j * np.pi / d)
F = np.zeros((d, d), dtype=complex)
for k in range(d):
    for l in range(d):
        F[k, l] = omega**(k * l) / np.sqrt(d)
F_op = qt.Qobj(F)
F_inv_op = F_op.dag()  # Inverse QFT

# Logical state: Basis at residue position
logical_pos = 11  # |1_L> = |11>
psi_logical = qt.basis(d, logical_pos)

def apply_error(psi, error_type='integer', shift_val=7):
    if error_type == 'integer':
        # Cyclic shift X^s
        shift_mat = np.roll(np.eye(d), shift_val, axis=1)
        error_op = qt.Qobj(shift_mat)
    elif error_type == 'fractional':
        # Phase ramp Z^f (partial shift f * d)
        f = 0.1  # Fraction of full cycle
        phases = np.exp(2j * np.pi * f * np.arange(d))
        error_op = qt.Qobj(np.diag(phases))
    return error_op * psi

def detect_and_correct(psi_err, bypass_filter=False, plot_probs=False):
    # Apply QFT to error (shifts become phases)
    psi_fourier = F_op * psi_err
    
    # To detect: Apply inverse QFT to recover shifted basis peak
    psi_recovered = F_inv_op * psi_fourier  # Should be shifted |logical_pos + shift>
    probs = (psi_recovered * psi_recovered.dag()).diag().real
    
    if plot_probs:
        plt.bar(range(d), probs)
        plt.title("Recovered Probabilities (Peak at Shifted Position)")
        plt.xlabel("Computational Basis State")
        plt.ylabel("Probability")
        plt.show()
    
    # Detect peak (shifted position)
    detected_pos = np.argmax(probs)
    estimated_shift = (detected_pos - logical_pos) % d
    print(f"Detected position: {detected_pos}, Expected: {logical_pos}")
    print(f"Estimated shift: {estimated_shift}")
    
    if not bypass_filter and estimated_shift not in residues:
        print("ACI Filter: Invalid shift - no correction applied (stability violation)")
        return psi_err, probs
    
    # Correction: Inverse shift (cyclic back)
    if error_type == 'integer':
        corr_shift = -estimated_shift % d
        corr_mat = np.roll(np.eye(d), corr_shift, axis=1)
        corr_op = qt.Qobj(corr_mat)
    else:
        # For fractional: Inverse phase ramp
        corr_phases = np.exp(-2j * np.pi * (estimated_shift / d) * np.arange(d))
        corr_op = qt.Qobj(np.diag(corr_phases))
    
    psi_corrected = corr_op * psi_err
    return psi_corrected, probs

# Test Integer (shift=7 in residues)
error_type = 'integer'
shift_val = 7
bypass_filter = False  # Strict ACI
psi_err = apply_error(psi_logical, error_type, shift_val)
psi_corrected, probs = detect_and_correct(psi_err, bypass_filter, plot_probs=True)

fidelity_int = qt.fidelity(psi_corrected, psi_logical)
print(f"Integer Shift ({shift_val}) Fidelity: {fidelity_int:.4f}\n")

# Test Fractional
error_type = 'fractional'
bypass_filter = True  # Bypass for partial
psi_err_frac = apply_error(psi_logical, error_type)
psi_corr_frac, _ = detect_and_correct(psi_err_frac, bypass_filter, plot_probs=True)
fidelity_frac = qt.fidelity(psi_corr_frac, psi_logical)
print(f"Fractional Error Fidelity: {fidelity_frac:.4f}")