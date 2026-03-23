import numpy as np
import math
import matplotlib.pyplot as plt

def get_von_mangoldt(N):
    ln = np.zeros(N+1, dtype=float)
    is_prime = np.ones(N+1, dtype=bool)
    is_prime[:2] = False
    for p in range(2, N+1):
        if is_prime[p]:
            is_prime[p*p:N+1:p] = False
            pk = p
            while pk <= N:
                ln[pk] = math.log(p)
                if pk > N // p: break
                pk *= p
    return ln

def singular_series(h):
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
    for p in factors: prod *= (p-1)/(p-2)
    return 2*C2*prod

def visualize_polignac_stability(gaps=[2, 4, 6, 10, 30], N_max=1000000):
    ln = get_von_mangoldt(N_max + max(gaps))
    x_axis = np.linspace(N_max//10, N_max, 20).astype(int)
    
    plt.figure(figsize=(12, 8))
    
    for h in gaps:
        S_target = singular_series(h)
        # Vectorized correlation calculation
        terms = ln[1:N_max+1] * ln[1+h:N_max+h+1]
        S_h_cumulative = np.cumsum(terms)
        
        B_values = [S_h_cumulative[x-1] / (S_target * x) for x in x_axis]
        plt.plot(x_axis, B_values, label=f'Gap h={h} (B={B_values[-1]:.4f})', marker='o', markersize=4)

    plt.axhline(y=1.0, color='r', linestyle='--', alpha=0.5, label='Hardy-Littlewood Limit')
    plt.title(f"Universal Clustering Stability (N={N_max})", fontsize=14)
    plt.xlabel("Search Range (x)", fontsize=12)
    plt.ylabel("Clustering Ratio B(h,x)", fontsize=12)
    plt.ylim(0.8, 1.2) # Zooming in on the convergence zone
    plt.legend()
    plt.grid(True, which='both', linestyle='--', alpha=0.5)
    
    print("\n[Visualizing Convergence... Close plot window to continue]")
    plt.show()

if __name__ == "__main__":
    visualize_polignac_stability(gaps=[2, 4, 6, 8, 10, 12, 30])