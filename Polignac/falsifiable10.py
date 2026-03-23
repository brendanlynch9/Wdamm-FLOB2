import numpy as np
import math
import matplotlib.pyplot as plt

def get_von_mangoldt(N):
    """Compute Lambda(n) up to N using a sieve."""
    ln = np.zeros(N+1)
    is_prime = np.ones(N+1, dtype=bool)
    is_prime[:2] = False
    for p in range(2, N+1):
        if is_prime[p]:
            logp = math.log(p)
            # Mark multiples as non-prime
            is_prime[p*p:N+1:p] = False
            # Assign log(p) to prime powers
            pk = p
            while pk <= N:
                ln[pk] = logp
                if pk > N // p: break
                pk *= p
    return ln

def singular_series(h):
    """Compute Hardy-Littlewood singular series for gap h."""
    C2 = 0.660161815846869
    factors = set()
    n, d = h, 2
    while d*d <= n:
        if n % d == 0:
            if d > 2: factors.add(d)
            while n % d == 0: n //= d
        d += 1
    if n > 2: factors.add(n)
    prod = 1.0
    for p in factors:
        prod *= (p-1)/(p-2)
    return 2*C2*prod

def maynard_weights(N, k=2):
    """
    Construct simple Maynard-type weights for prime tuples of length k.
    Here we use uniform weights as a naive first approximation.
    """
    w = np.ones(N+1)
    # Optional: weight primes more heavily or sieve small factors
    return w

def polignac_simulator(gaps=[2,4,6,8,10,12,30], N_max=10_000_000, steps=20):
    print(f"Running Polignac Simulator up to N={N_max} for gaps {gaps}\n")
    ln = get_von_mangoldt(N_max + max(gaps))
    x_axis = np.linspace(N_max//steps, N_max, steps).astype(int)

    plt.figure(figsize=(14,8))
    
    for h in gaps:
        S_target = singular_series(h)
        terms = ln[1:N_max+1] * ln[1+h:N_max+h+1]
        S_h_cumulative = np.cumsum(terms)
        # Compute B(h,x) and residual flux
        B_values = []
        flux_values = []
        for x in x_axis:
            Sx = S_h_cumulative[x-1]
            B = Sx / (S_target * x)
            flux = ((Sx - S_target * x)**2) / (x**2)
            B_values.append(B)
            flux_values.append(flux)
        
        plt.plot(x_axis, B_values, marker='o', markersize=3, label=f"Gap h={h} (B={B_values[-1]:.4f})")
        print(f"Gap h={h}: Final B(h,N_max) = {B_values[-1]:.6f}, Final flux = {flux_values[-1]:.6e}")
    
    plt.axhline(1.0, color='r', linestyle='--', alpha=0.6, label='Hardy-Littlewood Limit')
    plt.title(f"Polignac Simulator: Clustering Ratio B(h,x) up to N={N_max}", fontsize=14)
    plt.xlabel("x", fontsize=12)
    plt.ylabel("Clustering Ratio B(h,x)", fontsize=12)
    plt.ylim(0.95, 1.05)
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.legend()
    plt.show()

    print("\nInterpretation:")
    print("- If B(h,x) ~ 1 and flux decays to 0, S_h(x) grows linearly.")
    print("- This numerically supports positive asymptotic density for prime pairs of gap h.")
    print("- Any collapse of B or growth of flux would be a falsifiable signal against the conjecture.")

if __name__ == "__main__":
    polignac_simulator(gaps=[2,4,6,8,10,12,30], N_max=10_000_000, steps=20)


# (base) brendanlynch@Brendans-Laptop Polignac % python falsifiable10.py
# Running Polignac Simulator up to N=10000000 for gaps [2, 4, 6, 8, 10, 12, 30]

# Gap h=2: Final B(h,N_max) = 1.005183, Final flux = 4.683512e-05
# Gap h=4: Final B(h,N_max) = 0.998689, Final flux = 2.995843e-06
# Gap h=6: Final B(h,N_max) = 0.998315, Final flux = 1.979609e-05
# Gap h=8: Final B(h,N_max) = 0.997710, Final flux = 9.142533e-06
# Gap h=10: Final B(h,N_max) = 0.999334, Final flux = 1.374764e-06
# Gap h=12: Final B(h,N_max) = 1.001193, Final flux = 9.931237e-06
# Gap h=30: Final B(h,N_max) = 0.999584, Final flux = 2.142294e-06
# 2026-01-25 08:01:06.274 python[31371:31824185] The class 'NSSavePanel' overrides the method identifier.  This method is implemented by class 'NSWindow'

# Interpretation:
# - If B(h,x) ~ 1 and flux decays to 0, S_h(x) grows linearly.
# - This numerically supports positive asymptotic density for prime pairs of gap h.
# - Any collapse of B or growth of flux would be a falsifiable signal against the conjecture.
# (base) brendanlynch@Brendans-Laptop Polignac % 