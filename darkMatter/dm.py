import math

# Known constants from physics (CODATA)
alpha_observed_known = 0.0072973525693  # Precise α
G_physical = 6.67430e-11  # m^3 kg^-1 s^-2

# Theory constants
P_p = 137
S_graviton = 0.04344799
E_proton = 720
E_neutron = 95232
M_I = P_p
T_I = 24
epsilon = math.pi

# Derive alpha_ideal
alpha_ideal = 1 / P_p

# Perturbation delta and C_coupling
ratio = alpha_observed_known / alpha_ideal
delta = 1 - ratio
C_coupling = delta / S_graviton

# Informational length LI
L3 = E_proton * 22 * epsilon / 3
LI = L3 ** (1/3)

# G_informational
denom = M_I * T_I ** 2
numer = S_graviton * L3
G_info = numer / denom

# Universal scaling C_S
C_S = G_physical / G_info

# Nuclear signatures
S_strong_example = 1 * E_proton + 1 * E_neutron  # For deuterium Z=1, N=1
S_weak = abs(E_proton - E_neutron)

# Output
print(f"Derived alpha_ideal: {alpha_ideal:.8f}")
print(f"Measured alpha_observed: {alpha_observed_known:.8f}")
print(f"Delta (perturbation): {delta:.6f}")
print(f"C_coupling: {C_coupling:.5f}")
print(f"LI: {LI:.3f}")
print(f"G_informational: {G_info:.6f}")
print(f"C_S: {C_S:.3e}")
print(f"S_strong (deuterium example): {S_strong_example}")
print(f"S_weak: {S_weak}")