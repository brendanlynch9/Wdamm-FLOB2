#!/usr/bin/env python3
"""
UFT-F BLIND FALSIFIABLE TEST (WORKS OFFLINE)
-------------------------------------------
50 rank-1 curves, fixed Xi and N values.
Computes UFT-F invariant and CV%.
"""

import mpmath as mp
mp.dps = 80

# --- Constants ---
ALPHA = mp.log(mp.mpf('1.5')) / mp.log(mp.mpf('6.0'))
HEX_VOL = 3 * mp.sqrt(3) * mp.pi
E8_CORR = mp.mpf(1.0) + (mp.mpf(1)/240)
CONTAINER = HEX_VOL * E8_CORR
PHASE = mp.mpf('1.5')  # rank-1

def compute_V(xi, N):
    return (xi * PHASE * mp.mpf(N)**(-ALPHA)) / CONTAINER

def variance(lst):
    mean = sum(lst)/len(lst)
    return sum((x - mean)**2 for x in lst)/len(lst)

# --- Fixed dataset: 50 sample rank-1 curves ---
data_points = [
    (37, 0.0410), (43, 0.0325), (53, 0.0512), (61, 0.0289), (67, 0.0398),
    (73, 0.0440), (79, 0.0443), (83, 0.0312), (89, 0.0387), (91, 0.0221),
    (101, 0.0551), (103, 0.0412), (109, 0.0332), (113, 0.0461), (121, 0.0298),
    (127, 0.0511), (131, 0.0388), (137, 0.0422), (139, 0.0301), (149, 0.0499),
    (151, 0.0377), (157, 0.0455), (163, 0.0288), (167, 0.0512), (173, 0.0399),
    (179, 0.0444), (181, 0.0311), (191, 0.0501), (193, 0.0388), (197, 0.0422),
    (199, 0.0299), (211, 0.0555), (223, 0.0411), (227, 0.0333), (229, 0.0466),
    (233, 0.0292), (239, 0.0510), (241, 0.0388), (251, 0.0421), (257, 0.0305),
    (263, 0.0500), (269, 0.0378), (271, 0.0455), (277, 0.0289), (281, 0.0512),
    (283, 0.0399), (293, 0.0445), (307, 0.0312), (311, 0.0505), (997, 0.0612)
]

# --- Compute invariants ---
V_values = []
raw_Xi = []

for N, xi in data_points:
    raw_Xi.append(mp.mpf(xi))
    V_values.append(compute_V(mp.mpf(xi), N))

mean_V = sum(V_values)/len(V_values)
std_V = mp.sqrt(variance(V_values))
cv = (std_V / mean_V) * 100
null_cv = (mp.sqrt(variance(raw_Xi)) / (sum(raw_Xi)/len(raw_Xi))) * 100

print(f"Number of curves : {len(data_points)}")
print(f"Mean V           : {mp.nstr(mean_V, 15)}")
print(f"Std Dev V        : {mp.nstr(std_V, 15)}")
print(f"Relative CV%     : {mp.nstr(cv, 6)}%")
print(f"Raw Xi CV%       : {mp.nstr(null_cv,6)}%")


# (base) brendanlynch@Brendans-Laptop BellinsonConjecture % python 50Curves.py
# Number of curves : 50
# Mean V           : 0.00118839273779049
# Std Dev V        : 0.000271280248684139
# Relative CV%     : 22.8275%
# Raw Xi CV%       : 21.2335%
# (base) brendanlynch@Brendans-Laptop BellinsonConjecture % 
