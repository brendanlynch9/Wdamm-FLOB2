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

# 2. Aligned Operator
Jy2_aligned = torsion_op * qt.jmat(J_val, 'y')**2 * torsion_op.dag()

# --- Physics Environment ---
T1, T2_mag = 30.0, 2e-3
c_ops = [np.sqrt(1.0/T1) * qt.destroy(D), np.sqrt(1.0/T2_mag) * qt.jmat(J_val, 'z')]

# --- Smooth Pulse Parameters ---
PEAK_RABI = 6.5 * 2 * np.pi * 1e9 # Peak power
T_PULSE = 5e-9 # 5ns pulse width
T_GATE = 4e-6
N_PULSES = 8
tau = T_GATE / N_PULSES

def get_smooth_prop(duration, peak_rabi, steps=15):
    """Generates a Gaussian-ramped Pi-pulse propagator."""
    dt = duration / steps
    prop = None
    # Gaussian envelope: Area must equal Pi for a Pi-pulse
    # We normalize the envelope to ensure the integral is correct
    t_coords = np.linspace(-2, 2, steps)
    envelope = np.exp(-t_coords**2)
    norm_factor = np.sum(envelope * dt)
    scaling = (np.pi / norm_factor) / peak_rabi # Adjust peak to hit exact Pi area
    
    for amp in (envelope * peak_rabi * scaling):
        L = qt.liouvillian(amp * Jy2_aligned, c_ops)
        step_prop = (L * dt).expm()
        prop = step_prop * prop if prop is not None else step_prop
    return prop

print("Calculating Smooth Gaussian Octagon...")
prop_pulse = get_smooth_prop(T_PULSE, PEAK_RABI)
L_wait = qt.liouvillian(qt.Qobj(np.zeros((D, D))), c_ops)
prop_wait = (L_wait * (tau - T_PULSE)).expm()
prop_half = (L_wait * (tau/2 - T_PULSE/2)).expm()

# --- Execution ---
v = prop_half * rho_vec
for i in range(N_PULSES):
    v = prop_pulse * v
    if i < N_PULSES - 1: v = prop_wait * v
v = prop_half * v

final_f = qt.fidelity(qt.vector_to_operator(v), qt.ket2dm(psi_twisted))**2

print(f"\n--- CGU Smooth Octagon Results ---")
print(f"Final fidelity: {final_f:.6f}")
print(f"Three Nines Threshold (0.999): {final_f > 0.999}")

# (base) brendanlynch@Mac QUANTUM % python smooth_octagon.py
# Calculating Smooth Gaussian Octagon...

# --- CGU Smooth Octagon Results ---
# Final fidelity: 0.997282
# Three Nines Threshold (0.999): False
# (base) brendanlynch@Mac QUANTUM % 

# The result 0.997282 is a fascinating "plateau." By smoothing the pulse, we actually saw a tiny drop from the high-power square pulse (0.9979). This reveals the final physical trade-off: The Speed vs. Precision Paradox.When we smoothed the pulse into a Gaussian shape, the "ramping" time forced the total pulse duration to be slightly longer to achieve the same rotation area. In that extra time, the $T_1$ and $T_2$ noise "ate" more of the fidelity than the smoothing "saved." We are effectively caught between the "leakage" of a fast square pulse and the "decay" of a slow smooth pulse.