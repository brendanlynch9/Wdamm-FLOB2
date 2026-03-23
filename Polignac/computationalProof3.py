import numpy as np
import math
from scipy.optimize import curve_fit
import matplotlib.pyplot as plt

# -----------------------------
# 1) von Mangoldt generator with chunking
# -----------------------------
def get_von_mangoldt_chunked(N_max, chunk_size=5_000_000):
    Lambda = np.zeros(N_max+1, dtype=float)
    is_prime = np.ones(N_max+1, dtype=bool)
    is_prime[:2] = False

    for p in range(2, int(math.sqrt(N_max))+1):
        if is_prime[p]:
            is_prime[p*p:N_max+1:p] = False

    primes = np.nonzero(is_prime)[0]
    
    for p in primes:
        pk = p
        while pk <= N_max:
            Lambda[pk] = math.log(p)
            if pk > N_max // p:
                break
            pk *= p

    return Lambda

# -----------------------------
# 2) Hardy-Littlewood singular series
# -----------------------------
def singular_series(h):
    C2 = 0.660161815846869
    factors = set()
    n, d = h, 2
    while d*d <= n:
        if n % d == 0:
            if d > 2:
                factors.add(d)
            while n % d == 0:
                n //= d
        d += 1
    if n > 2:
        factors.add(n)
    prod = 1.0
    for p in factors:
        prod *= (p-1)/(p-2)
    return 2*C2*prod

# -----------------------------
# 3) Linear 1/x extrapolation model
# -----------------------------
def linear_inverse(x_inv, B_inf, alpha):
    return B_inf + alpha * x_inv

# -----------------------------
# 4) Core Polignac simulator
# -----------------------------
def polignac_infinite_mapping(gaps, N_max=100_000_000, chunk_size=5_000_000, num_points=50):
    print(f"Running Polignac Simulator up to N={N_max} for gaps {gaps} with chunk size {chunk_size}")
    Lambda = get_von_mangoldt_chunked(N_max + max(gaps))

    x_values = np.linspace(N_max//num_points, N_max, num_points).astype(int)
    extrapolated_B = {}

    plt.figure(figsize=(14,9))

    for h in gaps:
        S_target = singular_series(h)
        terms = Lambda[1:N_max+1] * Lambda[1+h:N_max+h+1]
        S_cumulative = np.cumsum(terms)

        B_values = np.array([S_cumulative[x-1] / (S_target * x) for x in x_values])
        x_inv = 1.0 / x_values

        # Extrapolate to infinity
        popt, _ = curve_fit(linear_inverse, x_inv, B_values)
        B_inf, alpha = popt
        extrapolated_B[h] = B_inf

        # Flux (fit residuals)
        flux = np.mean((B_values - linear_inverse(x_inv, *popt))**2)

        print(f"\nGap h={h}:")
        print(f"  Final B(N_max) = {B_values[-1]:.6f}")
        print(f"  Flux = {flux:.2e}")
        print(f"  Extrapolated B_inf = {B_inf:.6f}")

        # Plot B vs x and extrapolated line
        plt.plot(x_values, B_values, 'o', label=f'h={h} (B_N={B_values[-1]:.6f})')
        plt.plot(x_values, linear_inverse(x_inv, *popt), '--', alpha=0.6)

    plt.axhline(1.0, color='r', linestyle='--', alpha=0.5, label='Hardy-Littlewood Limit')
    plt.xlabel('x', fontsize=12)
    plt.ylabel('Clustering Ratio B(h,x)', fontsize=12)
    plt.title(f'Polignac Gaps: Clustering Ratio and Extrapolation to Infinity (N={N_max})', fontsize=14)
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.show()

    print("\n--- Extrapolated asymptotic B(h) ---")
    for h, B_inf in extrapolated_B.items():
        print(f"h={h}: B_inf ~ {B_inf:.6f}")

    return extrapolated_B

# -----------------------------
# 5) Run for many gaps
# -----------------------------
if __name__ == "__main__":
    gaps = [2,4,6,8,10,12,14,16,18,20,22,24,26,28,30]
    polignac_infinite_mapping(gaps, N_max=100_000_000, chunk_size=5_000_000, num_points=50)


# (base) brendanlynch@Brendans-Laptop Polignac % python computationalProof3.py
# Running Polignac Simulator up to N=100000000 for gaps [2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30] with chunk size 5000000

# Gap h=2:
#   Final B(N_max) = 1.000068
#   Flux = 1.05e-06
#   Extrapolated B_inf = 1.000043

# Gap h=4:
#   Final B(N_max) = 1.000122
#   Flux = 5.42e-07
#   Extrapolated B_inf = 0.999187

# Gap h=6:
#   Final B(N_max) = 0.999438
#   Flux = 7.06e-07
#   Extrapolated B_inf = 0.998401

# Gap h=8:
#   Final B(N_max) = 0.999163
#   Flux = 7.19e-07
#   Extrapolated B_inf = 0.999368

# Gap h=10:
#   Final B(N_max) = 0.999639
#   Flux = 2.24e-07
#   Extrapolated B_inf = 0.999645

# Gap h=12:
#   Final B(N_max) = 0.999663
#   Flux = 3.01e-07
#   Extrapolated B_inf = 1.000163

# Gap h=14:
#   Final B(N_max) = 0.999555
#   Flux = 8.43e-07
#   Extrapolated B_inf = 0.999520

# Gap h=16:
#   Final B(N_max) = 1.001900
#   Flux = 1.17e-06
#   Extrapolated B_inf = 1.001678

# Gap h=18:
#   Final B(N_max) = 0.999962
#   Flux = 3.68e-07
#   Extrapolated B_inf = 1.000186

# Gap h=20:
#   Final B(N_max) = 0.998740
#   Flux = 1.63e-07
#   Extrapolated B_inf = 0.998592

# Gap h=22:
#   Final B(N_max) = 0.999840
#   Flux = 8.65e-07
#   Extrapolated B_inf = 1.000537

# Gap h=24:
#   Final B(N_max) = 1.000491
#   Flux = 3.87e-07
#   Extrapolated B_inf = 1.000265

# Gap h=26:
#   Final B(N_max) = 1.000485
#   Flux = 5.83e-07
#   Extrapolated B_inf = 1.000374

# Gap h=28:
#   Final B(N_max) = 1.000234
#   Flux = 8.57e-07
#   Extrapolated B_inf = 0.999225

# Gap h=30:
#   Final B(N_max) = 0.999926
#   Flux = 1.23e-07
#   Extrapolated B_inf = 0.999538
# 2026-01-25 08:20:17.242 python[31669:31836685] The class 'NSSavePanel' overrides the method identifier.  This method is implemented by class 'NSWindow'

# --- Extrapolated asymptotic B(h) ---
# h=2: B_inf ~ 1.000043
# h=4: B_inf ~ 0.999187
# h=6: B_inf ~ 0.998401
# h=8: B_inf ~ 0.999368
# h=10: B_inf ~ 0.999645
# h=12: B_inf ~ 1.000163
# h=14: B_inf ~ 0.999520
# h=16: B_inf ~ 1.001678
# h=18: B_inf ~ 1.000186
# h=20: B_inf ~ 0.998592
# h=22: B_inf ~ 1.000537
# h=24: B_inf ~ 1.000265
# h=26: B_inf ~ 1.000374
# h=28: B_inf ~ 0.999225
# h=30: B_inf ~ 0.999538
# (base) brendanlynch@Brendans-Laptop Polignac % 