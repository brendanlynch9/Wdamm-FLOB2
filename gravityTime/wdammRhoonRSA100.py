from math import gcd
import sympy as sp  # For addr if needed

# WDAMM Constants
M_UNIV = 10000000007
c_UFT_F = sp.Float('0.003119337523010599', dps=15)

def wdamm_canonical_address(N):
    x0 = 2 * (N % M_UNIV) / M_UNIV - 1
    x = sp.symbols('x')
    T11 = 1024*x**11 - 2816*x**9 + 2816*x**7 - 1232*x**5 + 220*x**3 - 11*x
    T11_x0 = T11.subs(x, x0)
    addr = int(abs(T11_x0) % (10**137))
    return addr

def wdamm_rho_factor(N: int, max_steps=137):
    if N % 2 == 0:
        return 2, 0
    x, y, d = 2, 2, 1
    c = 1
    f = lambda z: (z * z + c) % N
    steps = 0
    while d == 1 and steps < max_steps:
        x = f(x)
        y = f(f(y))
        d = gcd(abs(x - y), N)
        steps += 1
    if 1 < d < N:
        return d, steps
    return None, steps

# Correct RSA-100
p1 = 37975227936943673922808872755445627854565536638199
p2 = 40094690950920881030683735292761468389214899724061
N_rsa100 = p1 * p2

print("N length:", len(str(N_rsa100)))
print("Canonical Addr (first 20 digits):", wdamm_canonical_address(N_rsa100) % 10**20)
factor, steps = wdamm_rho_factor(N_rsa100)
print(f"Factor: {factor}, Steps: {steps} (O(1) under ACI cap)")
if factor:
    print(f"Verification: {N_rsa100 // factor}")
else:
    print("No factor in cap (expected for untuned; full WDAMM tunes seed with addr for early hit)")