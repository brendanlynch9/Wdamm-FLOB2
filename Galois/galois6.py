import numpy as np

def abc_spectral_governor(a, b, c, label):
    # Calculate rad(abc)
    def get_prime_factors(n):
        factors = set()
        d, temp = 2, n
        while d * d <= temp:
            if temp % d == 0:
                factors.add(d); temp //= d
                while temp % d == 0: temp //= d
            d += 1
        if temp > 1: factors.add(temp)
        return factors

    primes = get_prime_factors(a) | get_prime_factors(b) | get_prime_factors(c)
    rad_abc = 1
    for p in primes: rad_abc *= p
    
    # Calculate Quality (q)
    q = np.log(c) / np.log(rad_abc)
    
    # UFT-F Potental L1 Norm Scaling (from AABC_conjecture.pdf)
    # The 'Informational Mass' of the triple
    l1_norm = np.exp(q - 1.0) * sum(np.log(p + 1) for p in primes)
    
    # Modularity Constant Threshold (Derived from Es/K3)
    C_UFTF = 15.04
    is_stable = l1_norm < C_UFTF

    print(f"{label:20} | q: {q:.4f} | L1: {l1_norm:7.4f} | {'[STABLE]' if is_stable else '[COLLAPSE]'}")

print("UFT-F ABC Radical Stability Analysis")
print("-" * 60)
abc_spectral_governor(1, 2, 3, "Minimal Triple")
abc_spectral_governor(1, 8, 9, "Small (3^2=8+1)")
abc_spectral_governor(1, 2400, 2401, "High Qual (7^4)")
abc_spectral_governor(2, 6436341, 6436343, "Frey-Hellegouarch") # Simulated

# (base) brendanlynch@Brendans-Laptop Galois % python galois6.py
# UFT-F ABC Radical Stability Analysis
# ------------------------------------------------------------
# Minimal Triple       | q: 0.6131 | L1:  1.6877 | [STABLE]
# Small (3^2=8+1)      | q: 1.2263 | L1:  3.1159 | [STABLE]
# High Qual (7^4)      | q: 1.4557 | L1: 10.0251 | [STABLE]
# Frey-Hellegouarch    | q: 1.6299 | L1: 19.4568 | [COLLAPSE]
# (base) brendanlynch@Brendans-Laptop Galois % 