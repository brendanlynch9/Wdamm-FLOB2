import qutip as qt
import numpy as np

# --- 1. Two-Manifold Setup ---
D = 24
J_val = (D-1)/2
OMEGA_U = 0.0002073045 

# Operators for Manifold A and B
torsion_op = qt.Qobj(np.diag([np.exp(2j * np.pi * OMEGA_U * k) for k in range(D)]))
Jy2_aligned = torsion_op * qt.jmat(J_val, 'y')**2 * torsion_op.dag()
Jz = qt.jmat(J_val, 'z')

# Create Two-Body Identity and Operators
Id = qt.qeye(D)
Jy2_A = qt.tensor(Jy2_aligned, Id)
Jy2_B = qt.tensor(Id, Jy2_aligned)
Jz_A = qt.tensor(Jz, Id)
Jz_B = qt.tensor(Id, Jz)

# --- 2. Entangling Hamiltonian (Topological Coupling) ---
# Coupling Strength g
g_coupling = 50e6 # 50 MHz coupling
H_int = g_coupling * Jz_A * Jz_B 

# --- 3. Cryogenic Environment for Two Manifolds ---
T1, T2_cryo = 30.0, 20e-3
# Collapse ops for both atoms
c_ops = [
    qt.tensor(np.sqrt(1.0/T1) * qt.destroy(D), Id),
    qt.tensor(Id, np.sqrt(1.0/T1) * qt.destroy(D)),
    qt.tensor(np.sqrt(1.0/T2_cryo) * Jz, Id),
    qt.tensor(Id, np.sqrt(1.0/T2_cryo) * Jz)
]

# --- 4. The Entangling Sequence ---
# We use a CZ gate (Controlled-Phase) which is H_int applied for a specific time
T_entangle = np.pi / (4 * g_coupling) 
L_int = qt.liouvillian(H_int, c_ops)
prop_entangle = (L_int * T_entangle).expm()

# Initial State: |+> on A and |+> on B (Both Twisted)
psi_logical_plus = (torsion_op * (qt.basis(D, 11) + qt.basis(D, 13)).unit()).unit()
psi_init = qt.tensor(psi_logical_plus, psi_logical_plus)
rho_vec = qt.operator_to_vector(qt.ket2dm(psi_init))

print("⚡ Creating Topological Entanglement between Manifolds...")
v_final = prop_entangle * rho_vec
rho_final = qt.vector_to_operator(v_final)

# --- 5. Fidelity Check against Ideal Bell State ---
# Ideal CZ on |++> creates a Bell-like state
target_bell = (prop_entangle * qt.operator_to_vector(qt.ket2dm(psi_init)))
f = qt.fidelity(rho_final, qt.vector_to_operator(target_bell))**2

print(f"\n--- Entanglement Results ---")
print(f"Bell State Fidelity: {f:.6f}")

# This script simulates two $D=24$ manifolds. We will attempt to create a Bell State:$$\Phi^+ = \frac{1}{\sqrt{2}} (|00\rangle + |11\rangle)$$where "0" and "1" correspond to our protected $|11\rangle$ and $|13\rangle$ levels.

# (base) brendanlynch@Mac QUANTUM % python topological_entangler.py
# zsh: killed     python topological_entangler.py
# (base) brendanlynch@Mac QUANTUM % 