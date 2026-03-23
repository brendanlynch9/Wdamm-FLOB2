import numpy as np
from sympy import symbols, Poly
from sympy.polys.numberfields import galois_group

def uftf_topological_check(poly_coeffs):
    z = symbols('z')
    f = Poly(poly_coeffs, z)
    G, _ = galois_group(f)
    order = G.order()
    
    # UFT-F Constant: Lambda_0 (Modularity Constant)
    lambda_0 = 15.045 # Refined from 331/22
    
    # Check if the Group Order 'collides' with the K3 Rank (22)
    # The ACI requires a 'Gap' between order and topological capacity
    spectral_ratio = order / 22.0
    
    # Falsifiable Prediction: If ratio > 10^3 without automorphy, 
    # the arithmetic manifold becomes non-self-adjoint.
    is_topologically_stable = spectral_ratio < 1000 # Simplified bound
    
    print(f"Group: {G} | Order: {order} | Spectral Ratio: {spectral_ratio:.2f}")
    return is_topologically_stable

# Test a quintic (A5)
uftf_topological_check([1, 1, -4, -3, 3, 1])
# Test a large symmetric group (S7 - order 5040)
uftf_topological_check([1, 0, 0, 0, 0, 0, 0, -1])

# (base) brendanlynch@Brendans-Laptop Galois % python galois3.py
# Group: PermutationGroup([
#     (0 1 2 3 4)]) | Order: 5 | Spectral Ratio: 0.23
# Traceback (most recent call last):
#   File "/Users/brendanlynch/Desktop/zzzzzCompletePDFs/Galois/galois3.py", line 28, in <module>
#     uftf_topological_check([1, 0, 0, 0, 0, 0, 0, -1])
#   File "/Users/brendanlynch/Desktop/zzzzzCompletePDFs/Galois/galois3.py", line 8, in uftf_topological_check
#     G, _ = galois_group(f)
#            ^^^^^^^^^^^^^^^
#   File "/Users/brendanlynch/miniconda3/lib/python3.12/site-packages/sympy/polys/numberfields/galoisgroups.py", line 622, in galois_group
#     return F.galois_group(by_name=by_name, max_tries=max_tries,
#            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
#   File "/Users/brendanlynch/miniconda3/lib/python3.12/site-packages/sympy/polys/polytools.py", line 4124, in galois_group
#     raise ValueError('Polynomial must be irreducible and univariate over ZZ or QQ.')
# ValueError: Polynomial must be irreducible and univariate over ZZ or QQ.
# (base) brendanlynch@Brendans-Laptop Galois % 



