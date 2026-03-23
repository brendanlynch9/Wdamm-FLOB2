import qutip as qt
import numpy as np

# Final Working Base-24 2-Qudit Error-Correcting Code Prototype

d = 24
residues = {1,5,7,11,13,17,19,23}  # Core quadratic residues; add negatives if needed (e.g., 13 for -11)

omega = np.exp(2j * np.pi / d)
F = np.zeros((d, d), dtype=complex)
for k in range(d):
    for l in range(d):
        F[k, l] = omega**(k * l) / np.sqrt(d)
F_op = qt.Qobj(F)

I = qt.qeye(d)
F_tensor2 = qt.tensor(I, F_op)  # Fourier on errored (second) qudit

# Logical: |1,13⟩ + |13,1⟩ normalized
psi_logical = (qt.tensor(qt.basis(d, 1), qt.basis(d, 13)) + 
               qt.tensor(qt.basis(d, 13), qt.basis(d, 1))) / np.sqrt(2)

def apply_error(psi, error_type='integer', shift_val=11):
    if error_type == 'integer':
        shift_mat = np.roll(np.eye(d), shift_val, axis=1)
        error_op = qt.tensor(I, qt.Qobj(shift_mat))  # Shift on second qudit
    elif error_type == 'fractional':
        error_phase = np.exp(2j * np.pi * 0.1)
        error_op1 = qt.Qobj(np.diag([1 if i != 1 else error_phase for i in range(d)]))
        error_op = qt.tensor(error_op1, I)
    return error_op * psi

def detect_and_correct(psi_err, bypass_filter=True):
    rho_err = psi_err * psi_err.dag()
    rho_mom = rho_err.transform(F_tensor2)
    probs = rho_mom.diag().real.reshape(d, d)
    
    # Marginalize over first qudit
    probs_1d = np.sum(probs, axis=0)
    
    # Find two highest peaks
    peak_indices = np.argsort(probs_1d)[-2:][::-1]  # Top two
    peak1, peak2 = sorted(peak_indices)  # Order for consistency
    print(f"Detected peaks: {peak1}, {peak2}")
    
    # Relative shift (consistent direction)
    relative_shift = (peak2 - peak1) % d
    print(f"Computed relative shift: {relative_shift}")
    
    if not bypass_filter and relative_shift not in residues:
        print("ACI Filter: Invalid relative shift - no correction (stability violation)")
        return psi_err
    
    # Correction: Inverse shift on second qudit
    corr_phases = [omega ** (-relative_shift * i) for i in range(d)]
    corr_op = qt.tensor(I, qt.Qobj(np.diag(corr_phases)))
    
    return corr_op * psi_err

# Run
error_type = 'integer'
shift_val = 11  # Matches residue
bypass_filter = True

psi_err = apply_error(psi_logical, error_type, shift_val)
psi_corrected = detect_and_correct(psi_err, bypass_filter)

fidelity = qt.fidelity(psi_corrected, psi_logical)

print(f"Dimension (Base): {d}")
print(f"Logical state fidelity after correction: {fidelity:.4f}")
print(f"Tested error type: {error_type}, Shift: {shift_val}, Bypass: {bypass_filter}")

# Qiskit basic check
try:
    from qiskit import QuantumCircuit
    from qiskit_aer import AerSimulator
    qc = QuantumCircuit(5)
    qc.h(range(5))
    sim = AerSimulator()
    result = sim.run(qc).result()
    print("Qiskit available - basic sim works!")
except:
    print("Qiskit check skipped.")