import qutip as qt
import numpy as np

# --- UFT-F Constants ---
D = 24
J_val = (D - 1) / 2
OMEGA_U = 0.0002073045 

# 1. Operators & Aligned Basis
torsion_op = qt.Qobj(np.diag([np.exp(2j * np.pi * OMEGA_U * k) for k in range(D)]))
psi_twisted = (torsion_op * (qt.basis(D, 11) + qt.basis(D, 13)).unit()).unit()
rho_vec = qt.operator_to_vector(qt.ket2dm(psi_twisted))

# 2. Extreme Power Alignment
Jy2_aligned = torsion_op * qt.jmat(J_val, 'y')**2 * torsion_op.dag()

# --- Hardened Physical Environment ---
T1, T2_mag = 30.0, 2e-3
# We focus on the Z-noise (Dephasing) which the Octagon is built to kill
c_ops = [np.sqrt(1.0/T1) * qt.destroy(D), np.sqrt(1.0/T2_mag) * qt.jmat(J_val, 'z')]

BASE_RABI = 5.0 * 2 * np.pi * 1e9 # 5 GHz Hardware Limit
T_GATE = 4e-6 # 4 microseconds (Ultra-fast outrun)
N_PULSES = 8
tau = T_GATE / N_PULSES
pi_dur = np.pi / BASE_RABI

# --- Propagators ---
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

final_f = qt.fidelity(qt.vector_to_operator(v), qt.ket2dm(psi_twisted))**2

print(f"\n--- CGU High-Limit Results ---")
print(f"Final fidelity: {final_f:.6f}")
print(f"Is Fault-Tolerant (>0.999): {final_f > 0.999}")

# "(base) brendanlynch@Mac QUANTUM % python final_cgu_gate.py

# --- CGU High-Limit Results ---
# Final fidelity: 0.997983
# Is Fault-Tolerant (>0.999): False
# (base) brendanlynch@Mac QUANTUM % ""

# gemnini said: 
# We have hit 0.997983. We are now tantalizingly close—essentially at the "Two Nines and a Nine" level.The fact that we doubled the power and halved the time but only moved from 0.995 to 0.997 is a classic signal in quantum information: we have successfully suppressed the Environmental Noise ($T_2$), but we are now bumping into Operator Discretization Error.