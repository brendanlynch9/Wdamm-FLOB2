from math import pi, log

def uft_gauge():
    c_uft_f = 0.003119
    omega_u = 0.0002073045
    N_base = 24
    
    alpha_em = 1/127.95
    sw2 = 0.2312
    alpha2 = alpha_em / (1 - sw2)
    alpha1 = 5/3 * alpha_em / sw2
    
    # Strong from spectral + torsion
    alpha3 = 8 * pi * c_uft_f * N_base * (1 + omega_u**2)
    
    # RG to GUT
    t = log(2e16 / 91.2)
    alpha_gut = alpha3 / (1 + alpha3 * t / (2*pi) - omega_u)
    
    print("UFT-F Gauge Closure:")
    print(f"α1≈{alpha1:.4f} | α2≈{alpha2:.4f} | α3≈{alpha3:.4f} (PDG 0.118)")
    print(f"α_GUT≈{alpha_gut:.4f} (base-24 = 0.0417)")

uft_gauge()

# (base) brendanlynch@Brendans-Laptop Quarks % python gaugeCoupling.py    
# UFT-F Gauge Closure:
# α1≈0.0563 | α2≈0.0102 | α3≈1.8813 (PDG 0.118)
# α_GUT≈0.1728 (base-24 = 0.0417)
# (base) brendanlynch@Brendans-Laptop Quarks % 