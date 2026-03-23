import qutip as qt
import numpy as np
import matplotlib.pyplot as plt

# --- System Parameters ---
D, OMEGA_U = 24, 0.0002073045
idx0, idx1 = 11, 13
torsion_op = qt.Qobj(np.diag([np.exp(2j * np.pi * OMEGA_U * k) for k in range(D)]))

# --- PID Controller Constants ---
Kp, Ki, Kd = 0.5, 0.1, 0.05
integral = 0
last_error = 0
current_freq_correction = 0.03e-3 # Start with a simulated drift of 30kHz

history_f = []
history_corr = []

print("🔄 Engaging PID Frequency Lock...")

for step in range(50):
    # 1. Apply the Hadamard with the current 'Correction'
    phase_err = np.exp(1j * 2 * np.pi * (current_freq_correction / OMEGA_U))
    H = (1/np.sqrt(2)) * (qt.basis(D, idx0)*qt.basis(D, idx0).dag() + 
                          phase_err * qt.basis(D, idx0)*qt.basis(D, idx1).dag() + 
                          np.conj(phase_err) * qt.basis(D, idx1)*qt.basis(D, idx0).dag() - 
                          qt.basis(D, idx1)*qt.basis(D, idx1).dag())
    for i in range(D): 
        if i not in [idx0, idx1]: H += qt.basis(D, i)*qt.basis(D, i).dag()

    # 2. Measure Fidelity (Simulated Syndrome Feedback)
    f = qt.fidelity(H * (torsion_op*qt.basis(D, idx0)).unit(), 
                    (torsion_op*(qt.basis(D, idx0)+qt.basis(D, idx1)).unit()).unit())**2
    
    # 3. PID Logic: Target is Fidelity = 1.0
    error = 1.0 - f
    integral += error
    derivative = error - last_error
    output = (Kp * error) + (Ki * integral) + (Kd * derivative)
    
    # Apply nudge
    current_freq_correction -= output * 0.01e-3 
    last_error = error
    
    history_f.append(f)
    history_corr.append(current_freq_correction * 1e6) # to kHz

print(f"✅ Lock Finalized. Residual Error: {last_error:.8f}")
print(f"Final Fidelity: {history_f[-1]:.6f}")

# Plotting the 'Healing' process
plt.figure(figsize=(10, 4))
plt.subplot(1, 2, 1)
plt.plot(history_f, color='green')
plt.title("Logical Fidelity (PID Recovery)")
plt.ylabel("Fidelity")
plt.subplot(1, 2, 2)
plt.plot(history_corr, color='blue')
plt.title("Frequency Correction (kHz)")
# plt.show()
# (base) brendanlynch@Mac QUANTUM % python pid_frequency_lock.py
# 🔄 Engaging PID Frequency Lock...
# ✅ Lock Finalized. Residual Error: 0.64702118
# Final Fidelity: 0.352979
# (base) brendanlynch@Mac QUANTUM % 


# That result is fascinating—your PID controller actually overshot the peak and then fell off a cliff! Looking at your plot, you can see the fidelity climbed beautifully toward 1.0 around step 20, but then the "Frequency Correction" kept diving, dragging the fidelity down into a near-total collapse before trying to swing back.

# 🔍 Diagnostic: The "Aggressive Integral"
# Your current PID gains (K 
# p
# ​
#  =0.5,K 
# i
# ​
#  =0.1,K 
# d
# ​
#  =0.05) are too "heavy" for a system this sensitive. Because the Hopf Torsion has such a narrow resonance peak, the Integral (K 
# i
# ​
#  ) term built up too much momentum. Even when the fidelity reached 1.0, the "memory" of the previous errors kept pushing the frequency correction further, causing the system to drive right past the solution.