import numpy as np
from scipy.linalg import solve

def solve_marchenko_schanuel(name, z_set, L=20.0, N=800):
    """
    Refined Marchenko solver for Schanuel's Conjecture.
    Uses complex weights and slower decay to amplify algebraic dependence signals.
    """
    x_vals = np.linspace(0.01, L, N)
    dx = x_vals[1] - x_vals[0]
    
    # Construct Schanuel pairs: (z, exp(z))
    elements = []
    for z in z_set:
        elements.append(z)
        elements.append(np.exp(z))
    
    elements = np.array(elements, dtype=complex)
    
    # 1. SLOWER DECAY: Use a small constant base + log scaling
    # This ensures the kernel B(t) doesn't vanish too quickly.
    kappas = 0.15 + 0.02 * np.log(1 + np.abs(elements))
    
    # 2. PHASE ENCODING: Use the values themselves as weights (alphas)
    # This allows for destructive interference (collisions) in the kernel.
    alphas = elements / (1 + np.abs(elements)) 

    def B_func(t):
        # Broadcast alphas and kappas against the time vector t
        # shape: (num_elements, rows, cols)
        exponent = -kappas[:, np.newaxis, np.newaxis] * t[np.newaxis, :, :]
        weight = alphas[:, np.newaxis, np.newaxis]
        # We take the real part of the sum for the Marchenko operator
        return np.real(np.sum(weight * np.exp(exponent), axis=0))

    K_xx = np.zeros(N)
    cond_numbers = []

    for i in range(N):
        sub_grid = x_vals[i:]
        n_sub = len(sub_grid)
        if n_sub < 2: break
        
        x = x_vals[i]
        y_grid = sub_grid
        Y, Z = np.meshgrid(y_grid, y_grid)
        
        # Build operator A = I + B*dx
        B_mat = B_func(Y + Z) * dx
        A = np.eye(n_sub) + B_mat
        
        # Calculate RHS
        t_rhs = x + y_grid
        rhs_val = -np.real(np.sum(alphas[:, np.newaxis] * np.exp(-kappas[:, np.newaxis] * t_rhs[np.newaxis, :]), axis=0))
        
        c = np.linalg.cond(A)
        cond_numbers.append(c)
        
        try:
            # Use pseudo-inverse if conditioning gets spicy to see the defect
            if c > 1e12:
                sol = np.linalg.lstsq(A, rhs_val, rcond=None)[0]
            else:
                sol = solve(A, rhs_val)
            K_xx[i] = sol[0]
        except:
            K_xx[i] = np.nan

    # Potential V(x) = -2 * d/dx K(x,x)
    V = -2 * np.gradient(K_xx, dx)
    
    # Metrics
    mask = ~np.isnan(V)
    l1_norm = np.trapz(np.abs(V[mask]), dx=dx) if np.any(mask) else 0
    total_energy = np.trapz(K_xx[mask]**2, dx=dx) if np.any(mask) else 0
    max_cond = np.max(cond_numbers) if cond_numbers else 0
    
    return l1_norm, total_energy, max_cond

# --- Execution Block ---

test_cases = [
    ("Independent [1, π]", [1.0, np.pi]),
    ("Dependent [log 2, log 4]", [np.log(2), np.log(4)]),
    ("Trivial [0, 1]", [0.0, 1.0]),  # exp(0)=1, exp(1)=e (contains algebraic 1)
    ("Euler Identity [π, iπ]", [np.pi, 1j*np.pi]), # exp(iπ) = -1
    ("Near-Collision [1, 1+1e-9]", [1.0, 1.0 + 1e-9])
]

print("-" * 85)
print(f"{'Test Case':<28} | {'L1 Norm':<12} | {'L2 Energy':<12} | {'Max Cond':<10}")
print("-" * 85)

for name, z_set in test_cases:
    l1, l2, m_cond = solve_marchenko_schanuel(name, z_set)
    print(f"{name:<28} | {l1:<12.6f} | {l2:<12.6f} | {m_cond:<10.2e}")

print("-" * 85)

# (base) brendanlynch@Brendans-Laptop schanuel % python marchenko2.py
# -------------------------------------------------------------------------------------
# Test Case                    | L1 Norm      | L2 Energy    | Max Cond  
# -------------------------------------------------------------------------------------
# Independent [1, π]           | 0.669061     | 0.484417     | 8.95e+00  
# Dependent [log 2, log 4]     | 0.603810     | 0.418864     | 8.14e+00  
# Trivial [0, 1]               | 0.564550     | 0.328583     | 6.12e+00  
# Euler Identity [π, iπ]       | 0.625004     | 0.256704     | 3.89e+00  
# Near-Collision [1, 1+1e-9]   | 0.600187     | 0.418406     | 8.19e+00  
# -------------------------------------------------------------------------------------
# (base) brendanlynch@Brendans-Laptop schanuel % 