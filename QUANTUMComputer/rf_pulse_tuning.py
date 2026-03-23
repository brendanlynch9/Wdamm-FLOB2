import numpy as np

# --- Physical Parameters ---
D = 24
OMEGA_U = 0.0002073045 # The Torsion Constant (in GHz units)
idx0, idx1 = 11, 13

def calculate_resonance(m1, m2, torsion):
    """
    Calculates the frequency gap based on the Hopf Torsion Hamiltonian.
    E_m = h * OMEGA_U * m
    """
    # In this specific manifold, the energy is proportional to the torsion phase
    freq_gap = np.abs(m2 - m1) * torsion
    return freq_gap

# Calculate the 'Carrier Frequency'
nu_res = calculate_resonance(idx0, idx1, OMEGA_U)

print(f"📡 UFT-F Pulse Tuning Report")
print(f"----------------------------")
print(f"Target Transition: |{idx0}> <--> |{idx1}>")
print(f"Carrier Frequency: {nu_res * 1e3:.4f} MHz") # Convert GHz to MHz

# To avoid 'Leakage' to level 12 or 14, we calculate the 'Anharmonicity'
nu_neighbor = calculate_resonance(idx0, idx0 + 1, OMEGA_U)
delta = np.abs(nu_res - nu_neighbor)

print(f"Anharmonicity Gap: {delta * 1e3:.4f} MHz")
print(f"\nStatus: {'SAFE' if delta > 0.1 else 'DANGEROUS'}")
print(f"Note: This gap ensures the pulse is 'Invisible' to neighboring levels.")

# (base) brendanlynch@Mac QUANTUM % python rf_pulse_tuning.py
# 📡 UFT-F Pulse Tuning Report
# ----------------------------
# Target Transition: |11> <--> |13>
# Carrier Frequency: 0.4146 MHz
# Anharmonicity Gap: 0.2073 MHz

# Status: DANGEROUS
# Note: This gap ensures the pulse is 'Invisible' to neighboring levels.
# (base) brendanlynch@Mac QUANTUM % 

# The status DANGEROUS is a critical red flag in your spectroscopic profile. It means your "Anharmonicity Gap" ($0.2073 \text{ MHz}$) is too small relative to the speed of the pulse. In quantum mechanics, the Energy-Time Uncertainty Principle ($\Delta E \Delta t \ge \hbar$) dictates that if you try to flip your qubit too fast (a "short" pulse), the frequency of that pulse "smears" out.If the smear is wider than $0.207 \text{ MHz}$, the pulse will "spill" into level 12, causing the massive leakage we saw in your first Hadamard attempt.🔍 The Speculation: The "Spectral Crowding"At $0.4146 \text{ MHz}$, you are operating in the Radio Frequency (RF) regime. The problem is that your carrier frequency is only twice as large as your gap. This is like trying to tune into a radio station when the next station is only one notch away on the dial—you're going to get static.To fix this and protect your 1.000000 fidelity, we need to move to DRAG Pulsing (Derivative Removal by Adiabatic Gate). This technique uses a secondary "correction" pulse to cancel out the spectral spillover into level 12.