import numpy as np
import matplotlib.pyplot as plt

# --- UFT-F Soliton Parameters Derived from ACI (Anti-Collision Identity) ---

# 1. Spectral Decay Rate (kappa): This constant is derived from the ACI/TNC/BSD
# framework and governs the shape and depth of the soliton.
kappa = 0.0558480080217728

# 2. Bound State Energy (E_0): For the one-soliton solution, the energy is E_0 = -kappa^2.
E0 = -1 * kappa**2

# 3. Wave Function Normalization Constant (c_0): Calculated to ensure the
# Graviton bound state is L^2-normalized: psi_0(x) is normalized to 1.
c0 = 0.1671047695635480

print("--- UFT-F Soliton Key Parameters ---")
print(f"Decay Rate (kappa): {kappa:.16f}")
print(f"Bound State Energy (E_0): {E0:.16f}")
print(f"Normalization Constant (c_0): {c0:.16f}")
print("------------------------------------")


# --- Soliton Functions ---

def sech(x):
    """Calculates the hyperbolic secant function: 1 / cosh(x)."""
    return 1.0 / np.cosh(x)

def potential_vx(x, k=kappa):
    """
    UFT-F Soliton Potential (Graviton Field Geometry): V(x) = -2*kappa^2 * sech^2(kappa*x).
    This is the stationary, reflectionless potential (the stable gravity well).
    """
    return -2.0 * k**2 * sech(k * x)**2

def bound_state_psi0(x, k=kappa, c=c0):
    """
    Normalized Bound State Wave Function (Graviton Field Amplitude): psi_0(x) = c_0 * sech(kappa*x).
    """
    return c * sech(k * x)

# --- Plotting Setup ---

# Define the range for the plot. A wide range shows the exponential decay characteristic of solitons.
x_min = -100
x_max = 100
num_points = 500
x_data = np.linspace(x_min, x_max, num_points)

# Calculate the values for the potential and the wave function
V_data = potential_vx(x_data)
Psi_data = bound_state_psi0(x_data)

# To visualize the wave function *in* the potential well, we shift its amplitude
# so that the zero-line of the wave function corresponds to the bound state energy E0.
Psi_data_shifted = Psi_data + E0

# --- Matplotlib Visualization ---

plt.figure(figsize=(10, 6), facecolor='white')
ax = plt.gca()

# 1. Plot the Potential V(x) (The Soliton Well)
ax.plot(x_data, V_data, label=r'$V(x) = -2\kappa^2 \text{sech}^2(\kappa x)$ (Soliton Potential)', 
        color='#CC0000', linewidth=3)

# 2. Plot the Bound State Energy Level E0
ax.axhline(E0, color='#0000CC', linestyle='--', linewidth=1.5, 
           label=r'Bound State Energy $E_0 = -\kappa^2$')

# 3. Plot the Normalized Bound State Wave Function psi_0(x)
ax.plot(x_data, Psi_data_shifted, 
        label=r'$\psi_0(x) + E_0$ (Normalized Graviton Bound State)', 
        color='#008800', linewidth=2.5)

# Fill the area under the wave function for a clearer visual representation of confinement
ax.fill_between(x_data, E0, Psi_data_shifted, color='#008800', alpha=0.15)


# --- Aesthetics and Labels ---
ax.set_title(
    r'UFT-F Soliton: Potential $V(x)$ and Confined Graviton Bound State $\psi_0(x)$', 
    fontsize=16, 
    fontweight='bold'
)
ax.set_xlabel('Position $x$ (normalized)', fontsize=14)
ax.set_ylabel('Energy / Amplitude', fontsize=14)
ax.legend(loc='upper right', fontsize=10, frameon=True, shadow=True)

# Highlight the central region around the potential minimum
ax.set_xlim(-50, 50)
ax.set_ylim(E0 - 0.002, np.max(Psi_data_shifted) + 0.002)

# Add grid and axes enhancements
ax.grid(True, which='both', linestyle=':', alpha=0.6)
ax.axvline(0, color='gray', linestyle='-', linewidth=0.5)
ax.axhline(0, color='black', linestyle='-', linewidth=0.5)

plt.tight_layout()
plt.show()

print("\nPlot generation complete. The figure shows the $\psi_0(x)$ function is localized and bound by the $V(x)$ potential at the energy level $E_0$.")


# the output was an image and this: 
# (base) brendanlynch@Mac gravityTime % python UFTFSolitonPotentialandBoundStatePlot.py
# /Users/brendanlynch/Desktop/zzzzzCompletePDFs/gravityTime/UFTFSolitonPotentialandBoundStatePlot.py:103: SyntaxWarning: invalid escape sequence '\p'
#   print("\nPlot generation complete. The figure shows the $\psi_0(x)$ function is localized and bound by the $V(x)$ potential at the energy level $E_0$.")
# --- UFT-F Soliton Key Parameters ---
# Decay Rate (kappa): 0.0558480080217728
# Bound State Energy (E_0): -0.0031190000000000
# Normalization Constant (c_0): 0.1671047695635480
# ------------------------------------

# Plot generation complete. The figure shows the $\psi_0(x)$ function is localized and bound by the $V(x)$ potential at the energy level $E_0$.
# (base) brendanlynch@Mac gravityTime % 