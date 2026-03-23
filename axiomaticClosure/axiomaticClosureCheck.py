# Define the approximate constants from the manuscripts
c_uft_f = 0.003119
lambda_u = 0.0002073045

# Compute the ratio to see the effective scaling factor
ratio = c_uft_f / lambda_u
print(f"Ratio c_UFT-F / λ_u: {ratio:.6f}")

# Compute the hypothesized product
product = 15 * lambda_u
print(f"15 * λ_u: {product:.10f}")

# Compute difference and relative error
difference = c_uft_f - product
print(f"Difference: {difference:.10f}")
relative_error = (difference / c_uft_f) * 100
print(f"Relative error: {relative_error:.4f}%")

# the output was:
# (base) brendanlynch@Mac axiomaticClosure % python axiomaticClosureCheck.py
# Ratio c_UFT-F / λ_u: 15.045501
# 15 * λ_u: 0.0031095675
# Difference: 0.0000094325
# Relative error: 0.3024%
# (base) brendanlynch@Mac axiomaticClosure % 