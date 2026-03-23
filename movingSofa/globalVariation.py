import numpy as np

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

def run_global_variation_test(n_samples=2000, max_harmonics=12, amp=0.015):
    thetas = np.linspace(0, 2*np.pi, 4000)
    h_g = gerver_support(thetas)
    area_g = compute_area(h_g, thetas)  # Baseline Gerver area

    admissible = []
    for _ in range(n_samples):
        coeffs = (np.random.rand(max_harmonics) - 0.5) * amp
        variation = np.zeros_like(thetas)
        for n in range(1, max_harmonics + 1):
            variation += coeffs[n-1] * np.sin(n * thetas)

        h_test = h_g + variation

        # Convexity check (h'' + h >= 0)
        h_pp = np.gradient(np.gradient(h_test, thetas), thetas)
        is_convex = np.all(h_pp + h_test >= -1e-6)

        # Width check
        w_test = h_test + gerver_support(thetas + np.pi/2)
        is_admissible_width = np.all(w_test <= 1.0000001)

        if is_convex and is_admissible_width:
            area_test = compute_area(h_test, thetas)
            if area_test > area_g + 1e-8:  # Only count if area actually increases
                admissible.append(area_test)

    print(f"Tested {n_samples} global Fourier perturbations")
    print(f"Admissible & convex & larger area found: {len(admissible)}")
    if len(admissible) > 0:
        print(f"Max area gain found: {max(admissible) - area_g:.6e}")
    else:
        print("No larger admissible variations found.")

if __name__ == "__main__":
    run_global_variation_test()

#     (base) brendanlynch@Brendans-Laptop movingSofa % python globalVariation.py
# Tested 2000 global Fourier perturbations
# Admissible & convex & larger area found: 0
# No larger admissible variations found.
# (base) brendanlynch@Brendans-Laptop movingSofa % 