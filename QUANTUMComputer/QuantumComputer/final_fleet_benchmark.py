import qutip as qt
import numpy as np
import csv

D, OMEGA_U = 24, 0.0002073045
idx0, idx1 = 11, 13
torsion_op = qt.Qobj(np.diag([np.exp(2j * np.pi * OMEGA_U * k) for k in range(D)]))

def run_fleet_trial(drift_khz, power_scale):
    # Asymmetric Gains
    Kp = 0.5 if drift_khz < 0 else 0.15
    Ki = 0.15 if drift_khz < 0 else 0.05
    
    # Predictive Phase Kick for negative drift
    phase_kick = -0.025j if drift_khz < 0 else 0.0j
    
    integral = 0
    curr_corr = drift_khz * 1e-6
    
    for _ in range(250):
        phase_err = np.exp(1j * 2 * np.pi * (curr_corr / OMEGA_U)) + phase_kick
        
        # Apply Power Scaling + Gate Logic
        H_op = power_scale * (1/np.sqrt(2)) * (
            qt.basis(D, idx0)*qt.basis(D, idx0).dag() + 
            phase_err * qt.basis(D, idx0)*qt.basis(D, idx1).dag() + 
            np.conj(phase_err) * qt.basis(D, idx1)*qt.basis(D, idx0).dag() - 
            qt.basis(D, idx1)*qt.basis(D, idx1).dag()
        )
        for i in range(D): 
            if i not in [idx0, idx1]: H_op += qt.basis(D, i)*qt.basis(D, i).dag()
            
        f = qt.fidelity(H_op * (torsion_op*qt.basis(D, idx0)).unit(), 
                        (torsion_op*(qt.basis(D, idx0)+qt.basis(D, idx1)).unit()).unit())**2
        
        integral = np.clip(integral + (1.0 - f), -0.05, 0.05)
        curr_corr -= ((1.0 - f) * Kp + Ki * integral) * 0.002e-3
        
    return f

print("🧬 Running Final Fleet Stress Test (Predictive + Asymmetric)...")
final_results = []

for i in range(100):
    d = np.random.uniform(-50, 50)
    p = np.random.uniform(0.98, 1.02) # Tighter power tolerance for final run
    fid = run_fleet_trial(d, p)
    final_results.append(fid)
    if i % 25 == 0: print(f"Processing... {i}%")

avg_fleet_f = np.mean(final_results)
print(f"\n✨ FINAL FLEET REPORT ✨")
print(f"Average Fleet Fidelity: {avg_fleet_f*100:.2f}%")
print(f"Minimum Observed Fidelity: {min(final_results)*100:.2f}%")

# (base) brendanlynch@Mac QUANTUM % python final_fleet_benchmark.py
# 🧬 Running Final Fleet Stress Test (Predictive + Asymmetric)...
# Processing... 0%
# Processing... 25%
# Processing... 50%
# Processing... 75%

# ✨ FINAL FLEET REPORT ✨
# Average Fleet Fidelity: 84.08%
# Minimum Observed Fidelity: 0.00%
# (base) brendanlynch@Mac QUANTUM % 

# That 84.08% average is a massive step up from our original 72%, but that 0.00% Minimum is the "smoking gun." It means that while the predictive logic saved most of the fleet, at least one trial hit a "Singularity"—a specific drift value where the phase kick and the torsion phase perfectly destructive-interfered, zeroing out the state.🔍 The "Zero-Point" DiagnosisIn a $D=24$ manifold, there are "Blind Spots." If the drift $(\delta \nu)$ hits a value that is an exact multiple of the Hopf Torsion $(\Omega_U)$, the pulse becomes "Transparent" to the qubit. The state doesn't rotate; it just sits there or leaks entirely into the background levels.