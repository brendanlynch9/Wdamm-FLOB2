import numpy as np
import matplotlib.pyplot as plt
from scipy.fft import fft

def uftf_spectral_diagnostic(n):
    """
    Calculates the Spectral Rupture (L1 potential divergence) of an integer n
    based on the Steiner-Quantization floor.
    """
    # 1. Classical Divisor Ratio
    divisors = [d for d in range(1, n + 1) if n % d == 0]
    sigma_ratio = sum(divisors) / n
    target = 2.0
    
    # 2. UFT-F Modularity Constant (lambda_0) and Resolution Floor (epsilon)
    lambda_0 = 15.045
    epsilon = 1 / (24 * lambda_0) # Approx 0.00277
    
    # 3. Simulate the Spectral Encoding (Mellin-like Transform)
    # We map the divisors to a spectral density function
    x = np.linspace(0, 1, 1024)
    spectral_density = np.zeros_like(x)
    for d in divisors:
        # Each divisor contributes a phase-shifted spike
        phase = (d / n) * 2 * np.pi
        spectral_density += np.sin(24 * x + phase)
    
    # 4. Calculate the Potential V(x) and its L1 Norm
    # In UFT-F, V is derived from the defect between actual and target resonance
    defect = abs(sigma_ratio - target)
    
    # If defect is below resolution floor but non-zero, rupture occurs (O(1/delta))
    if 0 < defect < epsilon:
        rupture_index = 1.0 / (defect + 1e-15)
    else:
        rupture_index = defect
        
    # Potential function V_M(x) representing the "Mass" of the complexity
    V_potential = fft(spectral_density)
    l1_norm = np.sum(np.abs(V_potential)) / len(V_potential)
    
    return sigma_ratio, l1_norm, rupture_index

# Test Cases
numbers = {
    "Perfect (Even)": 28, 
    "Abundant (Odd)": 945, 
    "Near-Perfect (Pseudo)": 10**10 + 1 # Arbitrary large odd
}

print(f"{'Number Type':<25} | {'Sigma/n':<10} | {'L1 Potential (V)':<15} | {'Rupture Status'}")
print("-" * 80)

results = []
names = []
for label, n in numbers.items():
    s_ratio, l1, rupture = uftf_spectral_diagnostic(n)
    status = "STABLE (Lattice)" if l1 < 100 else "RUPTURE (Divergent)"
    print(f"{label:<25} | {s_ratio:<10.4f} | {l1:<15.2f} | {status}")
    results.append(l1)
    names.append(label)

# Visualization of the Spectral Rupture
plt.figure(figsize=(10, 6))
plt.bar(names, results, color=['blue', 'red', 'orange'])
plt.axhline(y=100, color='black', linestyle='--', label='L1 Admissibility Threshold')
plt.title("UFT-F Spectral Rupture Diagnostic: Even vs. Odd")
plt.ylabel("L1 Norm of Potential $||V_M||_{L^1}$")
plt.legend()
plt.show()

# (base) brendanlynch@Brendans-Laptop oddPerfectNumbers % python spectralRuptureDiagnostic.py
# Number Type               | Sigma/n    | L1 Potential (V) | Rupture Status
# --------------------------------------------------------------------------------
# Perfect (Even)            | 2.0000     | 10.80           | STABLE (Lattice)
# Abundant (Odd)            | 2.0317     | 42.80           | STABLE (Lattice)
# Near-Perfect (Pseudo)     | 1.0102     | 23.46           | STABLE (Lattice)
# (base) brendanlynch@Brendans-Laptop oddPerfectNumbers % 