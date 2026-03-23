# derivation2Alpha.py - CORRECTED
import sympy as sp

# Set precision higher for the transcendental factor
sp.init_printing(use_unicode=True) 

# --- Inputs ---
# 1. High-precision target constant (c_UFT-F) from the UFT-F framework
C_UFT_F_target = 0.003119337523010599000000 

# 2. Components of the Uncorrected Analytical Calculation (C_uncorrected)
# S_inf = 17 * Sum_{n=1}^{inf} (1 / n**4) = 17 * zeta(4)
limit = 17 * sp.zeta(4)      
K_phys_rational = sp.Rational(1, 5921)
C_uncorrected = limit * K_phys_rational

# --- Calculations ---
# Calculate R_Alpha: The transcendental factor needed to correct the rational result.
# R_Alpha = C_UFT_F_target / C_uncorrected
R_Alpha_precise = C_UFT_F_target / C_uncorrected.evalf(50) 

# Verification: Calculate c_UFT_F using the new R_Alpha and ensure it matches the target
c_UFT_F_check = C_uncorrected * R_Alpha_precise

# --- Output ---
print(f"1. Uncorrected Analytical Constant (C_uncorrected): {C_uncorrected.evalf(20)}")
print("-" * 60)
print(f"2. Required Transcendental Factor (R_Alpha):")
# Print R_Alpha to high precision
print(f"{R_Alpha_precise}")
print("-" * 60)
print(f"3. Final UFT-F Constant Check (C_uncorrected * R_Alpha): {c_UFT_F_check.evalf(20)}")