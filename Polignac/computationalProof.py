import numpy as np
import math
import matplotlib.pyplot as plt

# --- Von Mangoldt Function ---
def get_von_mangoldt(N):
    ln = np.zeros(N+1, dtype=float)
    is_prime = np.ones(N+1, dtype=bool)
    is_prime[:2] = False
    for p in range(2, N+1):
        if is_prime[p]:
            # mark multiples as non-prime
            is_prime[p*p:N+1:p] = False
            pk = p
            while pk <= N:
                ln[pk] = math.log(p)
                if pk > N // p:
                    break
                pk *= p
    return ln

# --- Hardy-Littlewood Singular Series ---
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

# --- Polignac Simulator ---
def polignac_simulator(N_max=10_000_000, gaps=[2,4,6,8,10,12,14,16,18,20,22,24,26,28,30]):
    print(f"Running Polignac Simulator up to N={N_max} for gaps {gaps}\n")
    
    ln = get_von_mangoldt(N_max + max(gaps) + 1)
    
    results = {}
    
    for h in gaps:
        length = N_max - h + 1  # ensure arrays align
        S_target = singular_series(h)
        
        # cumulative sum for gap h
        S_h_cumulative = np.cumsum(ln[1:1+length] * ln[1+h:1+h+length])
        
        # evaluation points
        x_axis = np.linspace(length//10, length, 20).astype(int)
        
        B_values = []
        flux_values = []
        for x in x_axis:
            S_obs = S_h_cumulative[x-1]
            B = S_obs / (S_target * x)
            flux = ((S_obs - S_target*x)/x)**2
            B_values.append(B)
            flux_values.append(flux)
        
        results[h] = (x_axis, B_values, flux_values)
        
        print(f"Gap h={h}: Final B(h,N_max) = {B_values[-1]:.6f}, Final flux = {flux_values[-1]:.6e}")
    
    # --- Visualization ---
    plt.figure(figsize=(12, 8))
    for h, (x_axis, B_vals, _) in results.items():
        plt.plot(x_axis, B_vals, label=f'Gap h={h} (B={B_vals[-1]:.4f})', marker='o', markersize=4)
    
    plt.axhline(y=1.0, color='r', linestyle='--', alpha=0.5, label='Hardy-Littlewood Limit')
    plt.title(f"Polignac Clustering Stability up to N={N_max}", fontsize=14)
    plt.xlabel("x", fontsize=12)
    plt.ylabel("Clustering Ratio B(h,x)", fontsize=12)
    plt.ylim(0.95, 1.05)
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.legend()
    plt.show()
    
    return results

# --- Run Simulator ---
if __name__ == "__main__":
    polignac_simulator()



# (base) brendanlynch@Brendans-Laptop Polignac % python computationalProof.py
# Running Polignac Simulator up to N=10000000 for gaps [2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30]

# Gap h=2: Final B(h,N_max) = 1.005183, Final flux = 4.683693e-05
# Gap h=4: Final B(h,N_max) = 0.998689, Final flux = 2.994474e-06
# Gap h=6: Final B(h,N_max) = 0.998316, Final flux = 1.978436e-05
# Gap h=8: Final B(h,N_max) = 0.997711, Final flux = 9.136958e-06
# Gap h=10: Final B(h,N_max) = 0.999335, Final flux = 1.371054e-06
# Gap h=12: Final B(h,N_max) = 1.001195, Final flux = 9.949575e-06
# Gap h=14: Final B(h,N_max) = 1.000150, Final flux = 5.638446e-08
# Gap h=16: Final B(h,N_max) = 0.998138, Final flux = 6.046996e-06
# Gap h=18: Final B(h,N_max) = 1.000713, Final flux = 3.547425e-06
# Gap h=20: Final B(h,N_max) = 0.999241, Final flux = 1.786924e-06
# Gap h=22: Final B(h,N_max) = 1.002092, Final flux = 9.415717e-06
# Gap h=24: Final B(h,N_max) = 0.999314, Final flux = 3.284847e-06
# Gap h=26: Final B(h,N_max) = 1.002249, Final flux = 1.049704e-05
# Gap h=28: Final B(h,N_max) = 1.000644, Final flux = 1.040076e-06
# Gap h=30: Final B(h,N_max) = 0.999587, Final flux = 2.112522e-06
# 2026-01-25 08:07:25.539 python[31452:31827950] The class 'NSSavePanel' overrides the method identifier.  This method is implemented by class 'NSWindow'
# (base) brendanlynch@Brendans-Laptop Polignac % 