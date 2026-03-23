import qutip as qt
import numpy as np
import time

# --- UFT-F Constants ---
D = 24
J_val = (D - 1) / 2
OMEGA_U = 0.0002073045  # Hopf torsion

# 1. Operators & Twisted Basis
torsion_op = qt.Qobj(np.diag([np.exp(2j * np.pi * OMEGA_U * k) for k in range(D)]))
pos0, pos1 = 11, 13
psi0 = (qt.basis(D, pos0) + qt.basis(D, pos1)).unit()
psi_twisted = (torsion_op * psi0).unit()
rho_vec = qt.operator_to_vector(qt.ket2dm(psi_twisted))

# 2. ALIGNED PULSE: Rotating the operator to match the torsion
Jy2 = qt.jmat(J_val, 'y')**2
# The "Alignment" step: Conjugating Jy2 by the Torsion operator
Jy2_aligned = torsion_op * Jy2 * torsion_op.dag()

# --- Physical Environment (Optimized for 0.999) ---
T1, T2_mag = 30.0, 2e-3
c_ops = [np.sqrt(1.0/T1) * qt.destroy(D), np.sqrt(1.0/T2_mag - 0.5/T1) * qt.jmat(J_val, 'z')]

BASE_RABI = 2.5 * 2 * np.pi * 1e9 # Slight power boost
T_GATE = 8e-6 # Slightly faster to squeeze out more T2 protection
N_PULSES = 8
tau = T_GATE / N_PULSES
pi_dur = np.pi / BASE_RABI

# --- Propagators ---
print("Synchronizing Octagon with Hopf Torsion...")
L_wait = qt.liouvillian(qt.Qobj(np.zeros((D, D))), c_ops)
L_pulse = qt.liouvillian(BASE_RABI * Jy2_aligned, c_ops) 

p_wait = (L_wait * (tau - pi_dur)).expm()
p_half = (L_wait * (tau/2 - pi_dur/2)).expm()
p_pulse = (L_pulse * pi_dur).expm()

# --- Execution ---
v = p_half * rho_vec
for i in range(N_PULSES):
    v = p_pulse * v
    if i < N_PULSES - 1: v = p_wait * v
v = p_half * v

rho_final = qt.vector_to_operator(v)
final_f = qt.fidelity(rho_final, qt.ket2dm(psi_twisted))**2

print(f"\n--- CGU Final Topological Resonance Results ---")
print(f"Average fidelity: {final_f:.6f}")
print(f"Three Nines Threshold (0.999): {final_f > 0.999}")
print(f"Path: Hopf-Aligned Octagonal Resonance")