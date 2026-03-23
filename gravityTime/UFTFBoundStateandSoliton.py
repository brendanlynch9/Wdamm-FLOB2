import sympy as sp
import numpy as np
import matplotlib.pyplot as plt

# --- UFT-F Soliton Parameters ---
# The decay rate kappa from the previous step:
kappa_num = 0.0558480080217728

# The bound state energy for the single soliton (N=1) is E_0 = -kappa^2
E_0_num = -kappa_num**2

# --- 1. Analytical Solution for the Bound State Wave Function ---
# The Schrödinger equation for the single soliton potential:
# d^2(psi)/dx^2 + [E - V(x)]*psi = 0
# For V(x) = -2*kappa^2*sech^2(kappa*x) and E = -kappa^2 (N=1 case),
# the known analytical solution for the bound state wave function psi_0(x) is:
# psi_0(x) = sech(kappa * x)

x, kappa = sp.symbols('x kappa', real=True)
psi_0_unnormalized = sp.sech(kappa * x)

# --- 2. Calculation of the Normalization Constant c_0 ---
# The normalization constant c_0 is defined such that the L^2-norm is 1:
# ||psi_0||^2 = integral from -inf to +inf of |c_0 * psi_0(x)|^2 dx = 1
# We first calculate the integral of the unnormalized function squared:
# I = integral from -inf to +inf of [sech(kappa*x)]^2 dx
# The indefinite integral of sech^2(u) du is tanh(u).
# The definite integral of sech^2(kappa*x) dx from -inf to +inf is:
# [1/kappa * tanh(kappa*x)] from -inf to +inf
# = (1/kappa) * [tanh(inf) - tanh(-inf)]
# = (1/kappa) * [1 - (-1)] = 2 / kappa

I = 2 / kappa
# The normalization constant c_0 must satisfy c_0^2 * I = 1, so:
# c_0 = 1 / sqrt(I)
c_0_symbolic = sp.sqrt(kappa / 2)

# The fully normalized bound state wave function psi_0(x) is:
psi_0_normalized = c_0_symbolic * psi_0_unnormalized

# --- 3. Numerical Evaluation ---
# Substitute the numerical value of kappa
c_0_num = c_0_symbolic.subs(kappa, kappa_num).evalf()
psi_0_num = psi_0_normalized.subs(kappa, kappa_num)

# --- Output Results ---
print("--- UFT-F Soliton Bound State Wave Function Analysis ---")
print(f"1. ACI-Derived Decay Rate (kappa): {kappa_num:.16f}")
print(f"2. Bound State Energy (E_0 = -kappa^2): {E_0_num:.16f}")

print("\n3. Normalized Bound State Wave Function (Symbolic):")
print(f"psi_0(x) = sqrt(kappa / 2) * sech(kappa * x)")
print(f"psi_0(x) = {psi_0_normalized}")

print("\n4. Normalization Constant (Numerical):")
print(f"c_0 = 1 / sqrt(2/kappa) = {c_0_num:.16f}")

print("\n5. Fully Normalized Wave Function at Center (x=0):")
psi_0_center = psi_0_num.subs(x, 0).evalf()
print(f"psi_0(0) = c_0 * sech(0) = c_0 = {psi_0_center:.16f}")

# --- Visualization Data Generation ---
x_vals = np.linspace(-30, 30, 500)
# Create a lambda function for numerical evaluation
psi_func = sp.lambdify(x, psi_0_num, 'numpy')
psi_vals = psi_func(x_vals)

print("\n--- Plotting Data for Wave Function Shape ---")
print("Data generated for plotting the symmetric, non-dispersive wave function.")

# the output was :

# (base) brendanlynch@Mac gravityTime % python UFTFBoundStateandSoliton.py
# --- UFT-F Soliton Bound State Wave Function Analysis ---
# 1. ACI-Derived Decay Rate (kappa): 0.0558480080217728
# 2. Bound State Energy (E_0 = -kappa^2): -0.0031190000000000

# 3. Normalized Bound State Wave Function (Symbolic):
# psi_0(x) = sqrt(kappa / 2) * sech(kappa * x)
# psi_0(x) = sqrt(2)*sqrt(kappa)*sech(kappa*x)/2

# 4. Normalization Constant (Numerical):
# c_0 = 1 / sqrt(2/kappa) = 0.1671047695635480

# 5. Fully Normalized Wave Function at Center (x=0):
# psi_0(0) = c_0 * sech(0) = c_0 = 0.1671047695635480

# --- Plotting Data for Wave Function Shape ---
# Data generated for plotting the symmetric, non-dispersive wave function.
# (base) brendanlynch@Mac gravityTime % 

# The output confirms the calculation of the normalization constant $c_0$ and the fully normalized wave function $\psi_0(x)$.The analysis now has three key components derived from the UFT-F constant $\kappa$:The Potential: $V(x) = -2\kappa^2 \text{sech}^2(\kappa x)$ (The stable gravity field geometry).The Bound State Energy: $E_0 = -\kappa^2$ (The spectral floor).The Wave Function: $\psi_0(x) = c_0 \cdot \text{sech}(\kappa x)$ (The physical Graviton field amplitude).To complete the analytical verification visually, the most instructive step is to plot these two functions, $V(x)$ and $\psi_0(x)$, on the same graph to show that the wave function is indeed bound within the potential well, peaking exactly at the potential's minimum ($x=0$).