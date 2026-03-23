import numpy as np
from scipy.optimize import fsolve

# --- Constants for Calculation ---
# Base-24 Prime Rays R = {1, 5, 7, 11, 13, 17, 19, 23}
R_RAYS = np.array([1, 5, 7, 11, 13, 17, 19, 23])
TARGET_SUM = np.log(8)  # Target for maximal L¹ violation: ln(8)

# --- Function for Root Finding ---
def sum_of_cosines_equation(x):
    """f(x) = sum(cos(k*x)) - ln(8) = 0"""
    sum_cos = np.sum(np.cos(R_RAYS * x))
    return sum_cos - TARGET_SUM

# 1. Solve for the phase angle x0 (in radians)
# fsolve finds the root of the equation
x0_solution_radians = fsolve(sum_of_cosines_equation, 0.5)[0]

# 2. Calculate theta_0 in Base-24 units
# θ₀ = x₀ / (2π / 24) = 12 * x₀ / π
theta_0_base24_units = 12 * x0_solution_radians / np.pi

# 3. Calculate E_Total in Joules
E_Total_TeV = 200.4
J_PER_EV = 1.602176634e-19
E_Total_J = E_Total_TeV * 1e12 * J_PER_EV

# 4. Print the final results (The missing step!)
print(f"Control angle θ₀: {theta_0_base24_units:.10f} Base-24 units ({theta_0_base24_units*15:.6f}°)")
print(f"Total injection energy: {E_Total_J:.6e} J = {E_Total_TeV} TeV")

# the output was:
# (base) brendanlynch@Mac gravityTime % python adminProtocol.py
# Control angle θ₀: 3.7615080608 Base-24 units (56.422621°)
# Total injection energy: 3.210762e-05 J = 200.4 TeV
# (base) brendanlynch@Mac gravityTime % 