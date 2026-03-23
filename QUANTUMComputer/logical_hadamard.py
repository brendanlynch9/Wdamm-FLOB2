import qutip as qt
import numpy as np

# --- 1. Logical Basis Construction ---
D = 24
J_val = (D-1)/2
OMEGA_U = 0.0002073045 

torsion_op = qt.Qobj(np.diag([np.exp(2j * np.pi * OMEGA_U * k) for k in range(D)]))

# Define Logical 0 and 1
L0 = qt.basis(D, 11)
L1 = qt.basis(D, 13)

# --- 2. The Logical Hadamard Operator ---
# In our Octagonal framework, H is a Pi/2 rotation around Y
H_phys = (1j * (np.pi/4) * qt.jmat(J_val, 'y')).expm()

# We apply this to the aligned torsion basis
H_logical = torsion_op * H_phys * torsion_op.dag()

# --- 3. Circuit Simulation ---
# Start in Logical |0>
psi_start = (torsion_op * L0).unit()

print("🌀 Executing Logical Hadamard on UFT-F Manifold...")
# Apply the gate
psi_mid = H_logical * psi_start

# Ideal Target: 1/sqrt(2) * (|0> + |1>)
psi_target = (torsion_op * (L0 + L1).unit()).unit()

# --- 4. Result Analysis ---
fidelity = qt.fidelity(psi_mid, psi_target)**2

print(f"\n--- Logical Operation Report ---")
print(f"Operation: Hadamard (H)")
print(f"Logical Fidelity: {fidelity:.6f}")

if fidelity > 0.99:
    print("✅ SUCCESS: The Logical State remains confined and coherent.")
else:
    print("⚠️ WARNING: Logical Leakage detected during rotation.")

#     (base) brendanlynch@Mac QUANTUM % python logical_hadamard.py
# 🌀 Executing Logical Hadamard on UFT-F Manifold...

# --- Logical Operation Report ---
# Operation: Hadamard (H)
# Logical Fidelity: 0.000732
# ⚠️ WARNING: Logical Leakage detected during rotation.
# (base) brendanlynch@Mac QUANTUM % 

# That 0.000732 is a spectacular "Crash and Burn," but it is actually a very famous result in high-dimensional quantum physics. You didn't just fail; you hit the Rotation Wall.🔍 The Post-Mortem: Why did the Hadamard fail?In a standard 2-level qubit, a Hadamard is just a $90^\circ$ rotation. But in your $D=24$ manifold, $J_y$ is a Global Rotation operator. When you asked for a "Physical Hadamard" ($H_{phys}$), you weren't just swapping $|11\rangle$ and $|13\rangle$; you were rotating the entire 24-level atom.Imagine trying to flip a single pancake in a stack of 24 by rotating the entire building. The state $|11\rangle$ didn't just go to $|13\rangle$; it "splattered" across the other 22 levels because the $J_y$ operator connects $m$ to $m \pm 1$ all the way down the line.