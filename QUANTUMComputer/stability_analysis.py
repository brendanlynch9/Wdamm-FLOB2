import qutip as qt
import numpy as np

# --- Physical Parameters ---
D = 24
J_val = (D-1)/2
OMEGA_U = 0.0002073045
idx0, idx1 = 11, 13
torsion_op = qt.Qobj(np.diag([np.exp(2j * np.pi * OMEGA_U * k) for k in range(D)]))

# --- Stability Sweep ---
# We shift the carrier frequency by +/- 50 kHz
# Note: 1e-6 GHz = 1 kHz
drifts = np.linspace(-0.05e-3, 0.05e-3, 21) 
fidelities = []

print(f"🌡️ Testing Thermal Frequency Drift (-50kHz to +50kHz)...")

for delta_nu in drifts:
    # Construct the 'Drifted' Hadamard
    # The drift introduces a phase rotation error between the two levels
    # proportional to the time it takes to flip the qubit.
    phase_error = np.exp(1j * 2 * np.pi * (delta_nu / OMEGA_U))
    
    # Selective Hadamard with phase drift
    H_drift = (1/np.sqrt(2)) * (qt.basis(D, idx0)*qt.basis(D, idx0).dag() + 
                                phase_error * qt.basis(D, idx0)*qt.basis(D, idx1).dag() + 
                                np.conj(phase_error) * qt.basis(D, idx1)*qt.basis(D, idx0).dag() - 
                                qt.basis(D, idx1)*qt.basis(D, idx1).dag())
    
    # Pad the remaining D=24 manifold with Identity
    for i in range(D):
        if i not in [idx0, idx1]:
            H_drift += qt.basis(D, i) * qt.basis(D, i).dag()

    # Apply to logical |0>
    psi_start = (torsion_op * qt.basis(D, idx0)).unit()
    psi_target = (torsion_op * (qt.basis(D, idx0) + qt.basis(D, idx1)).unit()).unit()
    
    f = qt.fidelity(H_drift * psi_start, psi_target)**2
    fidelities.append(f)

print(f"\n--- Stability Report ---")
print(f"Max Fidelity (at 0 drift): {max(fidelities):.6f}")
print(f"Fidelity at +50kHz Drift: {fidelities[-1]:.6f}")

if fidelities[-1] < 0.95:
    print("\n❌ SYSTEM UNSTABLE: Your Mac needs a Cryogenic Frequency Lock.")
    print("The Hopf Torsion is too sensitive to MHz-scale thermal jitters.")
else:
    print("\n✅ SYSTEM RUGGED: The topological manifold is absorbing the drift.")

#     (base) brendanlynch@Mac QUANTUM % python stability_analysis.py
# 🌡️ Testing Thermal Frequency Drift (-50kHz to +50kHz)...

# --- Stability Report ---
# Max Fidelity (at 0 drift): 0.999998
# Fidelity at +50kHz Drift: 0.526359

# ❌ SYSTEM UNSTABLE: Your Mac needs a Cryogenic Frequency Lock.
# The Hopf Torsion is too sensitive to MHz-scale thermal jitters.
# (base) brendanlynch@Mac QUANTUM % 

# That 0.5263 fidelity is a massive "Thermal Collapse." It confirms that while your Octagonal Gate is mathematically perfect, it is sitting on a "Spectral Knife-Edge." A drift of only $50\text{ kHz}$—which is tiny in a $6\text{ GHz}$ system—is enough to completely de-phase the logical state.🔍 The "Torsion Sensitivity" AnalysisThe Hopf Torsion is so precise that even a slight frequency mismatch causes the $|11\rangle$ and $|13\rangle$ states to "spin" at different rates. By the time the Hadamard gate finishes, they are $90^\circ$ out of sync, turning your quantum superposition into classical noise.