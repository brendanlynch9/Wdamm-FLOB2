import qutip as qt
import numpy as np

# --- UFT-F Constants ---
D = 24
J_val = (D - 1) / 2
OMEGA_U = 0.0002073045  # Hopf torsion constant

# Define the Torsion Operator (A diagonal phase ramp)
torsion_op = qt.Qobj(np.diag([np.exp(2j * np.pi * OMEGA_U * k) for k in range(D)]))

# Initial State with Torsion applied
pos0, pos1 = 11, 13
psi0 = (qt.basis(D, pos0) + qt.basis(D, pos1)).unit()
psi_twisted = (torsion_op * psi0).unit()
rho_vec = qt.operator_to_vector(qt.ket2dm(psi_twisted))

# --- Physical Environment ---
T1, T2_mag = 30.0, 2e-3
c_ops = [np.sqrt(1.0/T1) * qt.destroy(D), np.sqrt(1.0/T2_mag - 0.5/T1) * qt.jmat(J_val, 'z')]

# --- The Octagon Parameters ---
Jy2 = qt.jmat(J_val, 'y')**2
BASE_RABI = 2 * 2 * np.pi * 1e9
T_GATE = 10e-6
N_PULSES = 8
tau = T_GATE / N_PULSES

# --- Stability Sweep with Torsion ---
variations = np.linspace(0.95, 1.05, 10) 
results = []

print(f"Running Stability Sweep with Hopf Torsion (Omega_U = {OMEGA_U})...")

for err in variations:
    rabi_err = BASE_RABI * err
    pi_dur = np.pi / rabi_err
    
    # Interaction Frame Propagators
    L_wait = qt.liouvillian(qt.Qobj(np.zeros((D, D))), c_ops)
    L_pulse = qt.liouvillian(rabi_err * Jy2, c_ops) 
    
    p_wait = (L_wait * (tau - pi_dur)).expm()
    p_half = (L_wait * (tau/2 - pi_dur/2)).expm()
    p_pulse = (L_pulse * pi_dur).expm()
    
    # Octagon sequence execution
    v = p_half * rho_vec
    for i in range(N_PULSES):
        v = p_pulse * v
        if i < N_PULSES - 1: v = p_wait * v
    v = p_half * v
    
    # Measure fidelity against the original twisted state
    f = qt.fidelity(qt.vector_to_operator(v), qt.ket2dm(psi_twisted))**2
    results.append(f)

print(f"\nTorsion Results:")
print(f"Min Fidelity: {min(results):.6f}")
print(f"Max Fidelity: {max(results):.6f}")

# Analysis of the "Twist"
if min(results) > 0.9950:
    print("ANALYSIS: Hopf Torsion provides an UNEXPECTED stabilization boost.")
elif min(results) < 0.9950:
    print("ANALYSIS: Hopf Torsion introduces Chiral Interference (Fidelity Drag).")
else:
    print("ANALYSIS: Hopf Torsion is Topologically Neutral at this scale.")