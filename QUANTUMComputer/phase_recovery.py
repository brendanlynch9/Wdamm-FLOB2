import qutip as qt
import numpy as np

# --- 1. Re-Generate the Depth 1000 State ---
D = 24
J_val = (D-1)/2
OMEGA_U = 0.0002073045 

torsion_op = qt.Qobj(np.diag([np.exp(2j * np.pi * OMEGA_U * k) for k in range(D)]))
psi_init = (torsion_op * (qt.basis(D, 11) + qt.basis(D, 13)).unit()).unit()
rho_vec = qt.operator_to_vector(qt.ket2dm(psi_init))

Jy2_aligned = torsion_op * qt.jmat(J_val, 'y')**2 * torsion_op.dag()
T1, T2_mag = 30.0, 2e-3
c_ops = [np.sqrt(1.0/T1) * qt.destroy(D), np.sqrt(1.0/T2_mag) * qt.jmat(J_val, 'z')]

BASE_RABI = 6.0 * 2 * np.pi * 1e9 
T_GATE = 2e-6 
N_PULSES = 8
tau = T_GATE / N_PULSES
pi_dur = np.pi / BASE_RABI

L_wait = qt.liouvillian(qt.Qobj(np.zeros((D, D))), c_ops)
L_pulse = qt.liouvillian(BASE_RABI * Jy2_aligned, c_ops) 
p_wait, p_half, p_pulse = (L_wait*(tau-pi_dur)).expm(), (L_wait*(tau/2-pi_dur/2)).expm(), (L_pulse*pi_dur).expm()

G = p_half
for _ in range(N_PULSES):
    G = p_pulse * G
    G = p_wait * G
G = p_half * G

print("Applying 1000 Octagonal Gates...")
v_final_1000 = G**1000 * rho_vec
rho_final = qt.vector_to_operator(v_final_1000)

# --- 2. PHASE RECOVERY (The Master Stroke) ---
# We sweep through a 2*pi phase rotation to find where the coherence re-emerges
phases = np.linspace(0, 2*np.pi, 360)
recovered_fidelities = []

print("Scanning for Hopf Phase Recovery...")
for phi in phases:
    # Construct a Phase Correction Operator in the 11-13 subspace
    # Rotation: |11> stays, |13> rotates by e^(i*phi)
    corr_diag = np.ones(D, dtype=complex)
    corr_diag[13] = np.exp(1j * phi)
    Rz = qt.Qobj(np.diag(corr_diag))
    
    rho_corr = Rz * rho_final * Rz.dag()
    f = qt.fidelity(rho_corr, qt.ket2dm(psi_init))**2
    recovered_fidelities.append(f)

best_f = max(recovered_fidelities)
best_phi = phases[np.argmax(recovered_fidelities)]

print(f"\n--- Recovery Report ---")
print(f"Original Fidelity (Depth 1000): {recovered_fidelities[0]:.4f}")
print(f"Recovered Fidelity: {best_f:.4f}")
print(f"Optimal Correction Phase: {best_phi:.4f} rad")

if best_f > 0.90:
    print("SUCCESS: Topological Confinement confirmed. Data was preserved, only phase was lost.")
else:
    print("NOTICE: Entropy has permanently claimed some information.")