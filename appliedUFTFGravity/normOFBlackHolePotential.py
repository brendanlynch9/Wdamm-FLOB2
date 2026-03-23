import numpy as np
from scipy.integrate import quad

def V(r):
    return (1 - 2/r) * (2/r**2 + 2/r**3)

def jacobian(r):
    return 1 + 2/(r - 2)

def integrand(r):
    return V(r) * jacobian(r)

l1_norm, err = quad(integrand, 2.000001, np.inf)

print('L1 norm:', l1_norm)
print('Error:', err)

# the output was:
# (base) brendanlynch@Mac appliedUFTFGravity % python normOFBlackHolePotential.py
# L1 norm: 1.2499992500004373
# Error: 3.1114421246716157e-10
# (base) brendanlynch@Mac appliedUFTFGravity % 