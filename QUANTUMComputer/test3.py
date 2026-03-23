import qutip as qt
import numpy as np

# Final Prototype: Base-24 2-qudit code with robust fixes

d = 24
# Extended residues including negatives mod 24 for torsion symmetry (e.g., -1≡23, -5≡19, -11≡13)
residues = {0,1,5,7,11,13,17,19,23,24-1,24-5,24-7,24-11,24-13,24-17,24-19}  # {0,1,5,7,11,13,17,19,23,23,19,17,13,13,7,5}

omega = np.exp(2j * np.pi / d)
F = np.zeros((d, d), dtype=complex)
for k in range(d):
    for l in range(d):
        F[k, l] = omega**(k * l) / np.sqrt(d)
F_op = qt.Qobj(F)

I = qt.qeye(d)
F_tensor1 = qt.tensor(F_op, I)  # For first qudit
F_tensor2 = qt.tensor(I, F_op)  # For second (errored) qudit

# Logical state: |1,13⟩ + |13,1⟩
psi_logical = (qt.tensor(qt.basis(d, 1), qt.basis(d, 13)) + qt.tensor(qt.basis(d, 13), qt.basis(d, 1))) / np.sqrt(2)

def apply_error(psi, error_type='integer'):
    if error_type == 'integer':
        shift = 11  # Prime residue for reliable match
        shift_mat = np.roll(np.eye(d), shift, axis=1)
        error_op = qt.tensor(I, qt.Qobj(shift_mat))  # Error on second qudit
    elif error_type == 'fractional':
        error_phase = np.exp(2j * np.pi * 0.1)
        error_op1 = qt.Qobj(np.diag([1 if i != 1 else error_phase for i in range(d)]))
        error_op = qt.tensor(error_op1, I)
    return error_op * psi

def detect_and_correct(psi_err, F_tensor, bypass_filter=True):
    rho_err = psi_err * psi_err.dag()
    rho_mom = rho_err.transform(F_tensor)
    probs = rho_mom.diag().real

    # Better detection: Circular shift consideration (find peak, check wraps)
    probs_1d = np.sum(probs.reshape(d, d), axis=0 if F_tensor == F_tensor2 else 1)  # Marginalize correctly
    detected_shift = np.argmax(probs_1d)
    # Adjust for possible wrap (if peak near edge)
    if detected_shift > d//2:
        detected_shift -= d  # Prefer negative for symmetry

    print(f"Detected shift (adjusted): {detected_shift} (raw argmax: {np.argmax(probs_1d)})")

    norm_shift = detected_shift % d
    if not bypass_filter and norm_shift not in residues:
        print("ACI Filter: Invalid shift - no correction applied (stability violation)")
        return psi_err

    # Correction on errored qudit
    corr_phases = [omega ** (-detected_shift * i) for i in range(d)]
    corr_op_single = qt.Qobj(np.diag(corr_phases))
    corr_op = qt.tensor(I, corr_op_single) if F_tensor == F_tensor2 else qt.tensor(corr_op_single, I)
    
    return corr_op * psi_err

# Run
error_type = 'integer'
bypass_filter = True  # Set False for strict ACI testing
psi_err = apply_error(psi_logical, error_type)
psi_corrected = detect_and_correct(psi_err, F_tensor2, bypass_filter)  # Target second qudit

fidelity = qt.fidelity(psi_corrected, psi_logical)
print(f"Dimension (Base): {d}")
print(f"Logical state fidelity after correction: {fidelity:.4f}")
print(f"Tested error type: {error_type}, Bypass filter: {bypass_filter}")

# Qiskit (Optional - Simplified)
try:
    from qiskit import QuantumCircuit
    from qiskit_aer import AerSimulator
    from qiskit.quantum_info import Statevector

    qc = QuantumCircuit(5)
    # Simple demo prep (H on qubits for superposition)
    qc.h(range(5))
    sim = AerSimulator()
    result = sim.run(qc).result()
    print("Qiskit available - basic sim works!")
except ImportError:
    print("Qiskit not available locally.")
except Exception as e:
    print(f"Qiskit sim error: {e}")