from mpmath import mp
mp.dps = 50  # High precision

c_uft_f = mp.mpf('0.003119')
lambda_u = mp.mpf('0.0002073045')

# Compute proposed C_total = 331 / 22
c_total = mp.mpf(331) / mp.mpf(22)

# Compute product
product = c_total * lambda_u

# Difference
difference = c_uft_f - product

# Relative error in percent
relative_error = (difference / c_uft_f) * 100

print(f"C_total: {c_total}")
print(f"Product: {product}")
print(f"Difference: {difference}")
print(f"Relative error (%): {relative_error}")

# the output was:
# (base) brendanlynch@Mac axiomaticClosure % python verificationCheck.py
# C_total: 15.045454545454545454545454545454545454545454545455
# Product: 0.0031189904318181818181818181818181818181818181818182
# Difference: 0.0000000095681818181818181818181818181818181818181818223447
# Relative error (%): 0.00030677081815267131073479262001224168585502346336469
# (base) brendanlynch@Mac axiomaticClosure % 