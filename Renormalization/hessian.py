import numpy as np

def terminal_hessian_analysis(kappa_values, x_range=(-2.5, 2.5), resolution=1000):
    """
    Analyzes the interaction-induced convexity of a non-convex double-well potential
    in the terminal without plots.
    """
    x = np.linspace(x_range[0], x_range[1], resolution)
    
    # Define Base Potential V''(x) = 12x^2 - 4
    # The local non-convexity constant L is the max magnitude of the negative eigenvalue.
    v_hessian = 12 * x**2 - 4
    L = np.abs(np.min(v_hessian))
    
    print("="*65)
    print(f"{'INTERACTION-INDUCED CONVEXITY ANALYSIS':^65}")
    print("="*65)
    print(f"Base Potential: V(x) = x^4 - 2x^2")
    print(f"Non-convexity limit (L): {L:.4f}")
    print("-"*65)
    print(f"{'Interaction (kappa)':<20} | {'Min Eigenvalue':<15} | {'Status':<15}")
    print("-"*65)
    
    for kappa in kappa_values:
        # Total Hessian = V''(x) + kappa
        total_hessian = v_hessian + kappa
        min_eig = np.min(total_hessian)
        
        status = "CONVEX" if min_eig > 0 else "NON-CONVEX"
        
        # Color coding markers (using plain text)
        indicator = "[*]" if min_eig > 0 else "[ ]"
        
        print(f"{kappa:<20.2f} | {min_eig:<15.4f} | {status:<15} {indicator}")
        
    print("-"*65)
    print("Interpretation:")
    print(f"1. If kappa > L ({L:.2f}), the system achieves Global Displacement Convexity.")
    print("2. A positive Min Eigenvalue indicates a uniform spectral gap (lambda).")
    print("3. When lambda > 0, the optimizer converges at exponential rate e^(-2*lambda*T).")
    print("="*65)

if __name__ == "__main__":
    # Test values: 0 (No interaction), 2 (Partial), 4 (Critical threshold L), 6+ (Global)
    test_kappas = [0.0, 2.0, 4.0, 6.0, 10.0, 20.0]
    terminal_hessian_analysis(test_kappas)


#     Last login: Mon Apr 20 08:07:08 on console
# (base) brendanlynch@Brendans-Laptop universalOptimizer % python hessian.py
# =================================================================
#              INTERACTION-INDUCED CONVEXITY ANALYSIS              
# =================================================================
# Base Potential: V(x) = x^4 - 2x^2
# Non-convexity limit (L): 3.9999
# -----------------------------------------------------------------
# Interaction (kappa)  | Min Eigenvalue  | Status         
# -----------------------------------------------------------------
# 0.00                 | -3.9999         | NON-CONVEX      [ ]
# 2.00                 | -1.9999         | NON-CONVEX      [ ]
# 4.00                 | 0.0001          | CONVEX          [*]
# 6.00                 | 2.0001          | CONVEX          [*]
# 10.00                | 6.0001          | CONVEX          [*]
# 20.00                | 16.0001         | CONVEX          [*]
# -----------------------------------------------------------------
# Interpretation:
# 1. If kappa > L (4.00), the system achieves Global Displacement Convexity.
# 2. A positive Min Eigenvalue indicates a uniform spectral gap (lambda).
# 3. When lambda > 0, the optimizer converges at exponential rate e^(-2*lambda*T).
# =================================================================
# (base) brendanlynch@Brendans-Laptop universalOptimizer % 