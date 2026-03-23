import numpy as np

# Improved UFT-F 3-Qudit Code - Higher Fidelity Demo

d = 24
residues = {0, 1, 5, 7, 11, 13, 17, 19, 23}

omega = np.exp(2j * np.pi / d)
F = np.zeros((d, d), dtype=complex)
for k in range(d):
    for l in range(d):
        F[k, l] = omega**(k * l) / np.sqrt(d)
F_inv = F.conj().T

omega_u = 0.0002073045
torsion_phase = np.exp(2j * np.pi * omega_u)

pos0, pos1 = 11, 13
psi_single_plus = (np.eye(d)[pos0] + np.eye(d)[pos1]) / np.sqrt(2)
psi_logical = np.kron(np.kron(psi_single_plus, psi_single_plus), psi_single_plus)

def apply_known_error(psi, shift_val=11):  # Use valid residue for demo
    shift_op = np.roll(np.eye(d), shift_val, axis=1)
    full_op = np.kron(np.kron(np.eye(d), np.eye(d)), shift_op)  # Error on third qudit
    return full_op @ psi

def apply_torsion_bias(psi):
    diag = np.diag([torsion_phase] * d)
    op = np.kron(np.kron(diag, diag), diag)
    return op @ psi

def apply_light_noise(psi, p_depol=0.01, gamma_amp=0.01):
    psi_noisy = psi.copy()
    noise_strength = 0.1
    for q in range(3):
        # Light random phase noise
        rand_phases = np.exp(1j * noise_strength * np.random.randn(d))
        phase_op = np.diag(rand_phases)
        op_list = [np.eye(d)] * 3
        op_list[q] = phase_op
        full_op = np.kron(np.kron(op_list[0], op_list[1]), op_list[2])
        psi_noisy = full_op @ psi_noisy
    psi_noisy /= np.linalg.norm(psi_noisy)
    return psi_noisy

def syndrome_measurement(psi):
    psi_3d = psi.reshape((d, d, d))
    shifts = []
    for q in range(3):
        marginal = np.sum(np.abs(psi_3d)**2, axis=tuple(i for i in range(3) if i != q))
        recovered = F_inv @ marginal
        probs = np.abs(recovered)**2
        peak = np.argmax(probs)
        # Center around average logical position
        center = (pos0 + pos1) / 2
        shift_est = (peak - center) % d
        shifts.append(int(np.round(shift_est)))
    print(f"Syndrome shifts: {shifts}")
    return shifts

def correct(psi, shifts):
    voted = max(set(shifts), key=shifts.count)
    print(f"Majority vote shift: {voted}")
    if voted not in residues:
        print("ACI Filter: Invalid — no correction")
        return psi
    print("ACI allows correction")
    corr = np.roll(np.eye(d), -voted, axis=1)
    full_corr = np.kron(np.kron(np.eye(d), np.eye(d)), corr)
    return full_corr @ psi

# Run improved demo
print("=== Improved UFT-F 3-Qudit Code (Valid Error + Light Noise) ===")
psi_torsion = apply_torsion_bias(psi_logical)
psi_error = apply_known_error(psi_torsion, shift_val=11)  # Valid residue
psi_noisy = apply_light_noise(psi_error, p_depol=0.01)

syndromes = syndrome_measurement(psi_noisy)
psi_corrected = correct(psi_noisy, syndromes)

fidelity = np.abs(np.vdot(psi_corrected, psi_logical))**2
print(f"Final Fidelity: {fidelity:.4f}")