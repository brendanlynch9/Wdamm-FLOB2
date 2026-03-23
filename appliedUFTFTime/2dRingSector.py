import sympy as sp
omega_u = sp.Float(0.0002073045, dps=10)
C_total = sp.Rational(331, 22)
c_UFT_F = C_total * omega_u
tau_min = 1 / c_UFT_F
print('c_UFT_F:', float(c_UFT_F))
print('tau_min:', float(tau_min))

# the output was:
# (base) brendanlynch@Mac appliedUFTFTime % python 2dRingSector.py
# c_UFT_F: 0.003118990431801194
# tau_min: 320.616565477103
# (base) brendanlynch@Mac appliedUFTFTime % 