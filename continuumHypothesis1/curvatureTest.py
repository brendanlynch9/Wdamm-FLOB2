import numpy as np
import pandas as pd
from scipy.linalg import eigvalsh

def uftf_curvature_test():
    """
    UFT-F Curvature Test: 
    Finding the 'Inflection Point' of the Spectral Gap.
    If the curvature peaks near 599, the 'Arbitrary Parameter' argument is dead.
    """
    primes = []
    n = 2
    while len(primes) < 500:
        if all(n % i != 0 for i in range(2, int(n**0.5) + 1)):
            primes.append(n)
        n += 1
    
    # Sweep C from 100 to 2000
    C_values = np.linspace(100, 2000, 20)
    gaps = []

    for C in C_values:
        N = len(primes)
        M = np.zeros((N, N))
        for i in range(N):
            for j in range(N):
                inf_i = 360 / primes[i]
                inf_j = 360 / primes[j]
                gap = abs(primes[i] - primes[j])
                M[i, j] = ((inf_i * inf_j) / 120) * np.exp(-gap / C)
        
        evs = eigvalsh(M)
        gaps.append(evs[-1] - evs[-2])

    # Calculate First and Second Derivatives (Curvature)
    d1 = np.gradient(gaps, C_values)
    d2 = np.gradient(d1, C_values)
    
    results = pd.DataFrame({
        'C': C_values,
        'Gap': gaps,
        'Curvature': np.abs(d2)
    })
    
    print("--- UFT-F CURVATURE RESULTS ---")
    # Find where the Curvature is highest
    peak_curvature = results.loc[results['Curvature'].idxmax()]
    print(results)
    print(f"\nPEAK INFLECTION DETECTED AT C = {peak_curvature['C']}")
    return results

if __name__ == "__main__":
    uftf_curvature_test()


#     (base) brendanlynch@Brendans-Laptop continuumHypothesis % python curvatureTest.py
# --- UFT-F CURVATURE RESULTS ---
#          C         Gap     Curvature
# 0    100.0  466.406920  2.834080e-04
# 1    200.0  475.679007  3.246149e-04
# 2    300.0  479.282933  2.420324e-04
# 3    400.0  481.238584  8.651576e-05
# 4    500.0  482.477652  4.252578e-05
# 5    600.0  483.337531  2.443635e-05
# 6    700.0  483.971339  1.546148e-05
# 7    800.0  484.459024  1.045401e-05
# 8    900.0  484.846567  7.422273e-06
# 9   1000.0  485.162356  5.471962e-06
# 10  1100.0  485.424903  4.156908e-06
# 11  1200.0  485.646810  3.236165e-06
# 12  1300.0  485.836964  2.571273e-06
# 13  1400.0  486.001818  2.078568e-06
# 14  1500.0  486.146174  1.705354e-06
# 15  1600.0  486.273682  1.417258e-06
# 16  1700.0  486.387169  1.191178e-06
# 17  1800.0  486.488857  1.011181e-06
# 18  1900.0  486.580518  6.803996e-07
# 19  2000.0  486.663584  4.297347e-07

# PEAK INFLECTION DETECTED AT C = 200.0
# (base) brendanlynch@Brendans-Laptop continuumHypothesis % 
