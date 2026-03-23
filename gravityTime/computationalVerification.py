import numpy as np, sympy as sp
c_UFT_F = sp.Rational(331,22) * sp.Float('0.0002073045', dps=50)
print(float(c_UFT_F)) 

# output was:
# (base) brendanlynch@Mac gravityTime % python computationalVerification.py
# 0.0031189904318181818
# (base) brendanlynch@Mac gravityTime % 