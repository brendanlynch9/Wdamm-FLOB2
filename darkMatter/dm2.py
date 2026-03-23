#!/usr/bin/env python3
# dark_matter_is_information.py
import numpy as np

# ---------- UFT-F constants ----------
P_p      = 137
E_p      = 720
E_n      = 95232
S_grav   = 0.04344799
c_UFT    = 0.00311934
T_I      = 24
M_I      = P_p

# ---------- Physical constants ----------
G  = 6.67430e-11      # m^3 kg^-1 s^-2
H0 = 2.2e-18          # s^-1  (70 km/s/Mpc)
c  = 2.99792458e8     # m/s

# ---------- Informational length ----------
epsilon = np.pi
L3 = E_p * 22 * epsilon / 3
L_I = L3**(1/3)

# ---------- Scaling constant C_S ----------
denom = M_I * T_I**2
numer = S_grav * L3
G_info = numer / denom
C_S = G / G_info

# ---------- Dark-matter density ----------
Omega_DM = 2*np.pi*G*S_grav*c_UFT * (H0/c)

# ---------- Print ----------
print(f"Proton signature          : {P_p}")
print(f"Informational length L_I  : {L_I:.3f}")
print(f"G_informational           : {G_info:.6f}")
print(f"Universal scaling C_S     : {C_S:.3e}")
print(f"Calculated Ω_DM           : {Omega_DM:.4f}")
print(f"Observed Ω_DM (Planck)    : ~0.27")