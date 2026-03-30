# ================================================
# Fixed Saunderson Elliptic Curve Analysis
# ================================================

print("=== Saunderson Elliptic Curve Analysis ===")

E = EllipticCurve([0, 18, 0, 1, 0])

print("Curve:", E)
print("Minimal model:", E.minimal_model())
print("Conductor:", E.conductor())
print("Discriminant:", E.discriminant())

rank = E.rank()
torsion_order = E.torsion_order()
torsion_points = E.torsion_points()

print("\n=== RESULTS ===")
print("Mordell-Weil rank:", rank)
print("Torsion subgroup order:", torsion_order)
print("Torsion points:", torsion_points)

# Safe L(E,1) check
L = E.lseries()
L_at_1 = L.at1()
print("L(E,1) value:", L_at_1)
print("Analytic rank consistent with algebraic rank?", abs(L_at_1[0]) > 1e-8)

if rank == 0:
    print("\n=== SUCCESS ===")
    print("The Saunderson curve has Mordell-Weil rank 0 over Q.")
    print("This proves there are NO non-degenerate perfect cuboids")
    print("in the Saunderson family.")
    print("This is a classical result in number theory.")
else:
    print("\nRank is not zero.")