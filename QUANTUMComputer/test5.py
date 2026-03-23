import qutip as qt
import numpy as np

# Robust Base-24 Single-Qudit Code (Perfect for integer shifts)

d = 24
residues = {1,5,7,11,13,17,19,23}  # Quadratic residues for ACI filter

omega = np.exp(2j * np.pi / d)
F = np.zeros((d, d), dtype=complex)
for k in range(d):
    for l in range(d):
        F[k, l] = omega**(k * l) / np.sqrt(d)
F_op = qt.Qobj(F)

# Logical states: Simple basis for clear peaks (use residue positions)
psi_0 = qt.basis(d, 1)   # |0_L⟩ = |1⟩ (residue)
psi_1 = qt.basis(d, 13)  # |1_L⟩ = |13⟩ (residue)

# Example: Start with superposition for testing (will have two peaks, but detectable)
psi_logical = (psi_0 + psi_1) / np.sqrt(2)

def apply_error(psi, error_type='integer', shift_val=11):
    if error_type == 'integer':
        shift_mat = np.roll(np.eye(d), shift_val, axis=1)
        error_op = qt.Qobj(shift_mat)
    elif error_type == 'fractional':
        error_phase = np.exp(2j * np.pi * 0.1)
        phases = np.exp(2j * np.pi * error_phase * np.arange(d) / d)  # Global phase ramp
        error_op = qt.Qobj(np.diag(phases))
    return error_op * psi

def detect_and_correct(psi_err, bypass_filter=True):
    rho_err = psi_err * psi_err.dag()
    rho_mom = F_op * rho_err * F_op.dag()
    probs = rho_mom.diag().real
    
    # Find peaks (for superposition: top 2)
    peak_indices = np.argsort(probs)[-2:][::-1]
    print(f"Detected peaks: {peak_indices}")
    
    # For simple demo: Assume single peak or average shift from known original (1 and 13)
    original_positions = np.array([1, 13])
    detected_shifts = (peak_indices - original_positions) % d
    relative_shift = np.mean(detected_shifts)  # Approximate; or use mode for integer
    relative_shift = int(np.round(relative_shift))
    
    print(f"Estimated shift: {relative_shift}")
    
    if not bypass_filter and relative_shift % d not in residues:
        print("ACI Filter triggered - no correction")
        return psi_err
    
    # Correction
    corr_phases = [omega ** (-relative_shift * i) for i in range(d)]
    corr_op = qt.Qobj(np.diag(corr_phases))
    
    return corr_op * psi_err

# Run
error_type = 'integer'
shift_val = 11
bypass_filter = True

psi_err = apply_error(psi_logical, error_type, shift_val)
psi_corrected = detect_and_correct(psi_err, bypass_filter)

fidelity = qt.fidelity(psi_corrected, psi_logical)
print(f"Fidelity: {fidelity:.4f}")

# For perfect case: Use single basis state
psi_single = psi_0
psi_err_single = apply_error(psi_single, 'integer', 5)
psi_corr_single = detect_and_correct(psi_err_single, bypass_filter=False)  # Will use peak detection
print("Single state fidelity:", qt.fidelity(psi_corr_single, psi_single))

# the output in terminal was:
# (base) brendanlynch@Mac QUANTUM % python test5.py
# Detected peaks: [22 20]
# Estimated shift: 14
# Fidelity: 0.0000
# Detected peaks: [23 22]
# Estimated shift: 16
# ACI Filter triggered - no correction
# Single state fidelity: 0.0
# (base) brendanlynch@Mac QUANTUM % 
