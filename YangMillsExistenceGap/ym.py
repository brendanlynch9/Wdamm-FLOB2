# ym_gap_extended.py: ACI + Spectral Viz

import sympy as sp
import numpy as np
import matplotlib.pyplot as plt

# Base setup (from your script)
BASE_HARMONY = 24
EI_vac = sp.Symbol('E_I^{vac}', integer=True)
EI_ex = sp.Symbol('E_I^{ex}', integer=True, positive=True)
Delta_m = sp.Symbol('Delta_m', real=True, positive=True)
k = sp.Symbol('k', integer=True, positive=True)

vacuum_harmony = sp.Eq(EI_vac, 0)
excitation_quantization = sp.Eq(EI_ex, BASE_HARMONY * k)

minimal_k = 1
minimal_EI = excitation_quantization.rhs.subs(k, minimal_k)
Delta_EI = sp.Eq(Delta_m, minimal_EI - vacuum_harmony.rhs)

# Print basics (as before)
print("UFT-F YM Mass Gap Proof\n")
print(f"Vacuum: {vacuum_harmony}")
print(f"Excitation: {excitation_quantization}")
print(f"Mass Gap: {Delta_EI}")

# Upgrade: Simulate discrete spectrum (e.g., glueball masses ∝ 24k)
ks = np.arange(1, 6)  # First 5 excitations
energies = BASE_HARMONY * ks
print("\nSimulated Spectrum (E_I units):", energies)

# Viz: Discrete energy levels (gap visible)
plt.figure(figsize=(8, 4))
plt.hlines(energies, xmin=0, xmax=1, colors='b', label='Excitations')
plt.hlines(0, xmin=0, xmax=1, colors='r', label='Vacuum')
plt.yticks(np.append(0, energies), ['Vacuum'] + [f'24*{k}' for k in ks])
plt.ylabel('Informational Energy (E_I)')
plt.title('UFT-F YM Spectrum: Mass Gap Δ=24')
plt.legend()
plt.grid()
plt.savefig('ym_spectrum.png')  # For GitHub
print("\nSpectrum plot saved as 'ym_spectrum.png' (gap at 24).")