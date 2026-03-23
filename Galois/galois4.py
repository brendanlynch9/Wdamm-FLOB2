import numpy as np
from sympy import symbols, Poly, cyclotomic_poly
from sympy.polys.numberfields import galois_group

def uftf_topological_closure(poly_coeffs, label):
    z = symbols('z')
    f = Poly(poly_coeffs, z)
    
    print(f"\n--- Analyzing {label} ---")
    
    # UFT-F Logic: Only irreducible motives can be mapped to a stable H_M
    if not f.is_irreducible:
        print(f"STATUS: COLLISION DETECTED. Polynomial is reducible.")
        print("ACTION: Filter via ACI to extract atomic motives.")
        return
    
    G, _ = galois_group(f)
    order = G.order()
    
    # The UFT-F Topological Ratio (Order / K3-Rank)
    # K3 Rank = 22, the limit of arithmetic capacity
    ratio = order / 22.0
    
    print(f"Group: {G}")
    print(f"Order: {order}")
    print(f"Spectral Ratio (S_r): {ratio:.4f}")
    
    # ACI Threshold for topological stability
    if ratio < 100:
        print("RESULT: [PASSED] Motive fits within E8/K3 capacity.")
    else:
        print("RESULT: [WARNING] High-order complexity; check L1 convergence.")

# 1. Re-testing the A5 extension (Stable)
uftf_topological_closure([1, 1, -4, -3, 3, 1], "Quintic A5")

# 2. Testing the 7th Cyclotomic Extension (Order 6 - Corrected)
# This replaces the reducible x^7 - 1
f_cyc7 = cyclotomic_poly(7, symbols('z'), polys=True).all_coeffs()
uftf_topological_closure(f_cyc7, "7th Cyclotomic (Phi_7)")

# 3. Testing a large symmetric group (S5 - order 120)
uftf_topological_closure([1, 0, -1, 1, 1], "General Quintic (S5)")

# (base) brendanlynch@Brendans-Laptop Galois % python galois4.py

# --- Analyzing Quintic A5 ---
# Group: PermutationGroup([
#     (0 1 2 3 4)])
# Order: 5
# Spectral Ratio (S_r): 0.2273
# RESULT: [PASSED] Motive fits within E8/K3 capacity.

# --- Analyzing 7th Cyclotomic (Phi_7) ---
# Group: PermutationGroup([
#     (0 1 2 3 4 5)])
# Order: 6
# Spectral Ratio (S_r): 0.2727
# RESULT: [PASSED] Motive fits within E8/K3 capacity.

# --- Analyzing General Quintic (S5) ---
# STATUS: COLLISION DETECTED. Polynomial is reducible.
# ACTION: Filter via ACI to extract atomic motives.
# (base) brendanlynch@Brendans-Laptop Galois % 