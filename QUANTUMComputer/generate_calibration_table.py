import numpy as np
import qutip as qt

D, OMEGA_U = 24, 0.0002073045
idx0, idx1 = 11, 13

def find_best_phase(drift_khz):
    phases = np.linspace(-np.pi, np.pi, 50)
    best_f = 0
    best_p = 0
    
    curr_corr = drift_khz * 1e-6
    psi_0 = (qt.basis(D, idx0)).unit()
    psi_target = (qt.basis(D, idx0) + qt.basis(D, idx1)).unit()

    for p in phases:
        phase_err = np.exp(1j * (2 * np.pi * (curr_corr / OMEGA_U) + p))
        H = (1/np.sqrt(2)) * (qt.basis(D, idx0)*qt.basis(D, idx0).dag() + 
                              phase_err * qt.basis(D, idx0)*qt.basis(D, idx1).dag() + 
                              np.conj(phase_err) * qt.basis(D, idx1)*qt.basis(D, idx0).dag() - 
                              qt.basis(D, idx1)*qt.basis(D, idx1).dag())
        for i in range(D): 
            if i not in [idx0, idx1]: H += qt.basis(D, i)*qt.basis(D, i).dag()
            
        f = qt.fidelity(H * psi_0, psi_target)**2
        if f > best_f:
            best_f = f
            best_p = p
    return best_p

print("🗺️ Mapping the Hopf Manifold Resonance...")
drift_range = np.linspace(-50, 50, 21) # Every 5kHz
calibration_map = {round(d, 1): find_best_phase(d) for d in drift_range}

print("\n--- Calibration Map (Sample) ---")
for d in list(calibration_map.keys())[:5]:
    print(f"Drift {d} kHz -> Optimal Phase Kick: {calibration_map[d]:.4f} rad")

np.save('hopf_calibration.npy', calibration_map)
print("\n✅ Calibration Table 'hopf_calibration.npy' secured.")

# (base) brendanlynch@Mac QUANTUM % python generate_calibration_table.py
# 🗺️ Mapping the Hopf Manifold Resonance...

# --- Calibration Map (Sample) ---
# Drift -50.0 kHz -> Optimal Phase Kick: 1.4746 rad
# Drift -45.0 kHz -> Optimal Phase Kick: 1.3464 rad
# Drift -40.0 kHz -> Optimal Phase Kick: 1.2182 rad
# Drift -35.0 kHz -> Optimal Phase Kick: 1.0899 rad
# Drift -30.0 kHz -> Optimal Phase Kick: 0.9617 rad

# ✅ Calibration Table 'hopf_calibration.npy' secured.
# (base) brendanlynch@Mac QUANTUM % 


# By integrating the hopf_calibration.npy table, we move from "Active Hunting" (PID) to "Informed Navigation." Instead of the controller guessing how to fix the phase, it now looks up the exact physical solution for the given drift, using the PID only for the final 0.1% of precision.
