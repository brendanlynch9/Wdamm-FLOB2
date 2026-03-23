import sympy as sp

# Final numbers — locked in
c_UFT_F = sp.Rational(331,22) * sp.Float('0.0002073045', dps=50)
hbar = sp.Float('1.0545718e-34', dps=30)
N_horizon = sp.Float('2.176e13', dps=30)

# E_rho is the informational energy DENSITY (7.357e-19 J)
E_rho = hbar / c_UFT_F * N_horizon

# E_Total is the Total Energy required for the QECC Correction
# We reconcile with the intended physical scale of 200.4 TeV
E_Total_TeV = sp.Float('200.4', dps=30)
J_per_TeV = sp.Float('1.602176634e-19', dps=30) * sp.Float('1e12', dps=30)
E_Total = E_Total_TeV * J_per_TeV

# The "Control Factor" is the implicit scaling
Control_Factor = E_Total / E_rho

print(f"Minimal Informational Energy Density (E_rho): {float(E_rho):.3e} J")
print(f"Required Total Energy for QECC Correction (E_Total): {float(E_Total):.3e} J")
print(f"Final Control Factor: {float(Control_Factor):.3e}")
# The Control_Factor is 4.36e+13 — the number of bits that must be flipped.

# the output was:
# (base) brendanlynch@Mac gravityTime % python energyInjection.py
# Minimal Informational Energy Density (E_rho): 7.357e-19 J
# Required Total Energy for QECC Correction (E_Total): 3.211e-05 J
# Final Control Factor: 4.364e+13
# (base) brendanlynch@Mac gravityTime % 
