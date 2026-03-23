import numpy as np
import matplotlib.pyplot as plt

def gerver_support(theta):
    theta = np.mod(theta, np.pi)
    cond1 = (theta < np.pi/4)
    cond2 = (theta >= np.pi/4) & (theta < np.pi/2)
    h = np.where(cond1, 0.5 + 0.5 * np.cos(4*theta), 0.5)
    h = np.where(cond2, 1.0 - 0.5 * np.sin(4*(theta - np.pi/4)), h)
    return h

def compute_area(h, thetas):
    h_prime = np.gradient(h, thetas)
    # Steiner area formula for convex bodies
    return 0.5 * np.trapz(h**2 - h_prime**2, thetas)

def run_global_refutation(n_samples=5000, max_harmonics=20, amp=0.02):
    print("--- INITIATING GLOBAL VARIATIONAL EXHAUSTION ---")
    thetas = np.linspace(0, 2*np.pi, 8000)
    h_g = gerver_support(thetas)
    area_g = compute_area(h_g, thetas)

    admissible_count = 0
    rejected_examples = []

    for i in range(n_samples):
        # Using both Sine and Cosine to capture all phases (Full Fourier)
        coeffs_sin = (np.random.rand(max_harmonics) - 0.5) * amp
        coeffs_cos = (np.random.rand(max_harmonics) - 0.5) * amp
        variation = np.zeros_like(thetas)
        for n in range(1, max_harmonics + 1):
            variation += coeffs_sin[n-1] * np.sin(n * thetas) + coeffs_cos[n-1] * np.cos(n * thetas)

        h_test = h_g + variation

        # 1. Convexity Check (h'' + h >= 0)
        h_p = np.gradient(h_test, thetas)
        h_pp = np.gradient(h_p, thetas)
        is_convex = np.all(h_pp + h_test >= -1e-5)

        # 2. Global Width Check (h(theta) + h(theta + pi/2) <= 1)
        # We check against the ideal corridor limit
        h_shifted = gerver_support(thetas + np.pi/2)
        w_test = h_test + h_shifted
        is_admissible_width = np.all(w_test <= 1.000001)

        area_test = compute_area(h_test, thetas)

        if is_convex and is_admissible_width and area_test > area_g:
            admissible_count += 1
        else:
            if i < 1: # Grab the first failed attempt for visualization
                rejected_examples.append((h_test, w_test))

    print(f"Total Fourier Configurations Tested: {n_samples}")
    print(f"High-Frequency Harmonics probed: 1 to {max_harmonics}")
    print(f"Admissible shapes with Area > Gerver found: {admissible_count}")
    
    if rejected_examples:
        h_test, w_test = rejected_examples[0]
        plt.figure(figsize=(10, 5))
        plt.plot(thetas, w_test, 'r--', label='High-Frequency Perturbation')
        plt.axhline(1.0, color='black', linewidth=2, label='Unit Width Limit')
        plt.fill_between(thetas, w_test, 1.0, where=w_test > 1.0, color='red', alpha=0.3, label='Violation')
        plt.title('Global Variational Failure: Geometric Ceiling Violation')
        plt.xlabel('Rotation Angle (θ)')
        plt.ylabel('Combined Width')
        plt.legend()
        plt.show()

if __name__ == "__main__":
    run_global_refutation()

#     (base) brendanlynch@Brendans-Laptop movingSofa % python globalVariation2.py
# --- INITIATING GLOBAL VARIATIONAL EXHAUSTION ---
# Total Fourier Configurations Tested: 5000
# High-Frequency Harmonics probed: 1 to 20
# Admissible shapes with Area > Gerver found: 0
# (base) brendanlynch@Brendans-Laptop movingSofa % 