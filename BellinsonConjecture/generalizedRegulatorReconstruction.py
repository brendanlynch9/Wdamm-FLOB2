import mpmath as mp

# 1. Precision
mp.dps = 60

# 2. Arithmetic Coefficients a_n
A_N = [0, 1, -2, -3, 2, -2, 6, -1, 0, 6, 4, -5, -6, 0, -2, 9, -7, 3, -8, -1, -6,
       -1, -10, -6, -3, 15, -1, 12, -7, 0, -10, 12, -3, 15, 6, 6, -12, -6, -8, 12,
       -12, 18, 0, -3, -6, 12, -12, -10, 15, 0, 18]

# Constants
CONDUCTOR = 37
OMEGA_REAL = mp.mpf('2.993454416')
TAMAGAWA = 3
R_ALPHA = mp.mpf(1) + mp.mpf(1)/240
PHASE_SHIFT = mp.mpf('1.5')
HEX_VOL = 3*mp.sqrt(3)*mp.pi
C_UFT_F = mp.mpf('0.00311905')

def motivic_l_prime(coeffs, N):
    tot = mp.mpf(0)
    for n in range(1, len(coeffs)):
        x = 2*mp.pi*n/mp.sqrt(N)
        tot += coeffs[n]/mp.mpf(n) * mp.expint(1, x)
    return 2*tot

print("\nFull 37a1 Regulator Reconstruction")
print("-"*60)
Lp = motivic_l_prime(A_N, CONDUCTOR)
R_std = Lp/(OMEGA_REAL*TAMAGAWA)
R_uftf = R_std/(HEX_VOL*R_ALPHA)

print("L'(E,1) approx      :", mp.nstr(Lp, 12))
print("Standard regulator  :", mp.nstr(R_std, 12))
print("UFT-F reg. approx   :", mp.nstr(R_uftf, 15))
print("Target (UFT-F)      :", mp.nstr(C_UFT_F, 15))

error = abs(R_uftf - C_UFT_F)/C_UFT_F
print("Relative error (%)  :", mp.nstr(error*100, 6))

# (base) brendanlynch@Brendans-Laptop BellinsonConjecture % python generalizedRegulatorReconstruction.py

# Full 37a1 Regulator Reconstruction
# ------------------------------------------------------------
# L'(E,1) approx      : 0.305999789643
# Standard regulator  : 0.0340743220728
# UFT-F reg. approx   : 0.00207868972067838
# Target (UFT-F)      : 0.00311905
# Relative error (%)  : 33.355
# (base) brendanlynch@Brendans-Laptop BellinsonConjecture % 