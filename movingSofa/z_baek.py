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
    return 0.5 * np.trapz(h**2 - h_prime**2, thetas)

def run_ultimate_refutation(n_samples=5000, max_harmonics=15, amp=0.012):
    thetas = np.linspace(0, 2*np.pi, 8000)
    h_g = gerver_support(thetas)
    area_g = compute_area(h_g, thetas)

    admissible = []
    violation_examples = []

    for i in range(n_samples):
        coeffs_sin = (np.random.rand(max_harmonics) - 0.5) * amp
        coeffs_cos = (np.random.rand(max_harmonics) - 0.5) * amp
        variation = np.zeros_like(thetas)
        for n in range(1, max_harmonics + 1):
            variation += coeffs_sin[n-1] * np.sin(n * thetas) + coeffs_cos[n-1] * np.cos(n * thetas)

        h_test = h_g + variation

        # Convexity
        h_pp = np.gradient(np.gradient(h_test, thetas), thetas)
        is_convex = np.all(h_pp + h_test >= -1e-6)

        # Width
        w_test = h_test + gerver_support(thetas + np.pi/2)
        is_admissible_width = np.all(w_test <= 1.0000001)

        area_test = compute_area(h_test, thetas)

        if is_convex and is_admissible_width and area_test > area_g + 1e-8:
            admissible.append(area_test)
        else:
            if i < 5 and not is_admissible_width:  # Save width violators
                violation_examples.append((thetas, w_test))

    print(f"Tested {n_samples} full Fourier perturbations")
    print(f"Admissible, convex, larger area found: {len(admissible)} / {n_samples}")
    if len(admissible) > 0:
        print(f"Max area gain: {max(admissible) - area_g:.6e}")
    else:
        print("Zero admissible larger variations found.")

    # Plot clearance violation (local bump example)
    epsilon = 0.01
    bump = epsilon * np.exp(-((thetas - np.pi/4)/0.1)**2)
    h_pert = gerver_support(thetas) + bump
    cl_pert = 1.0 - (h_pert + gerver_support(thetas + np.pi/2))

    plt.figure(figsize=(12, 8))
    plt.subplot(2,1,1)
    plt.plot(thetas, cl_pert, 'r--', label='Perturbed Clearance')
    plt.fill_between(thetas, cl_pert, 0, where=cl_pert < 0, color='red', alpha=0.3)
    plt.axhline(0, color='k', label='Zero Clearance')
    plt.title('Local Perturbation: Negative Clearance')
    plt.xlabel('θ')
    plt.ylabel('δ(θ)')
    plt.legend()
    plt.grid(True)

    # Plot one width violation
    if violation_examples:
        plt.subplot(2,1,2)
        thetas_ex, w_ex = violation_examples[0]
        plt.plot(thetas_ex, w_ex, 'r--', label='Rejected Width')
        plt.axhline(1.0, color='k', label='Limit')
        plt.fill_between(thetas_ex, w_ex, 1.0, where=w_ex > 1.0, color='red', alpha=0.3)
        plt.title('Example Rejected Global Perturbation')
        plt.xlabel('θ')
        plt.ylabel('Width')
        plt.legend()
        plt.grid(True)

    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    run_ultimate_refutation()

#     (base) brendanlynch@Brendans-Laptop movingSofa % python baek.py
# Tested 5000 full Fourier perturbations
# Admissible, convex, larger area found: 0 / 5000
# Zero admissible larger variations found.
# (base) brendanlynch@Brendans-Laptop movingSofa % 