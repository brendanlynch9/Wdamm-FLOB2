import sympy as sp
import matplotlib.pyplot as plt
import numpy as np

# Define symbols
Z, Ep, En, Eatom = sp.symbols('Z Ep En Eatom')
f, t = sp.symbols('f t')

# IU constants
Ep_val = 720
En_val = 95232

# Function to compute Eatom for element Z (assuming N ≈ Z for simplicity)
def compute_Eatom(Z_val):
    N_val = Z_val  # Approximate N = Z
    return Z_val * Ep_val + N_val * En_val

# Waveform function
def waveform(E):
    f_expr = 1 / sp.sqrt(E)
    return sp.sin(2 * sp.pi * f_expr * t)

# Example for Hydrogen (Z=1, N=0)
E_H = compute_Eatom(1)
psi_H = waveform(E_H)

# Numerical plot
t_num = np.linspace(0, 10, 1000)
f_H_num = 1 / np.sqrt(float(E_H))
psi_H_num = np.sin(2 * np.pi * f_H_num * t_num)

plt.plot(t_num, psi_H_num)
plt.title('Qualia Waveform for Hydrogen')
plt.xlabel('Time')
plt.ylabel('Amplitude')
plt.show()