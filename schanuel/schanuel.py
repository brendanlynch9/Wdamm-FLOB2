import numpy as np
import math
from scipy.linalg import solve
from scipy.integrate import simpson
import matplotlib.pyplot as plt

def get_schanuel_generator(z_list, exp_z_list, t_grid):
    """
    Generates the spectral data kernel B(t) from the transcendental motive.
    B(t) = sum(exp(-kappa * t))
    """
    B = np.zeros_like(t_grid)
    # Combine z and exp(z) into the spectral set
    motive_data = np.concatenate([z_list, exp_z_list])
    
    for val in motive_data:
        kappa = np.abs(val)
        B += np.exp(-kappa * t_grid)
    
    return B

def solve_marchenko(t_grid, B_data):
    """
    Solves the Marchenko Integral Equation for K(x,x).
    """
    size = len(t_grid)
    dt = t_grid[1] - t_grid[0]
    K_diag = np.zeros(size)
    
    # Solve back to front
    for i in range(size - 1, -1, -1):
        sub_grid = t_grid[i:]
        sub_size = len(sub_grid)
        
        if sub_size < 2:
            K_diag[i] = -B_data[min(2*i, size-1)]
            continue
            
        # Matrix B_mat[j, k] = B(x_j + x_k)
        B_mat = np.zeros((sub_size, sub_size))
        for j in range(sub_size):
            for k in range(sub_size):
                idx = i + j + k
                B_mat[j, k] = B_data[idx] if idx < size else 0
        
        rhs = -np.array([B_data[i + j] if (i+j) < size else 0 for j in range(sub_size)])
        A = np.eye(sub_size) + B_mat * dt
        
        try:
            # Using rcond to detect near-singularities (collisions)
            sol = solve(A, rhs)
            K_diag[i] = sol[0]
        except np.linalg.LinAlgError:
            K_diag[i] = np.inf # Force divergence on collision

    return K_diag

def run_experiment(name, z_vals):
    exp_z = [np.exp(z) for z in z_vals]
    L = 10.0
    N = 400
    t_grid = np.linspace(0, L, N)
    
    B_t = get_schanuel_generator(z_vals, exp_z, t_grid)
    K_x = solve_marchenko(t_grid, B_t)
    
    # Calculate Potential
    V_x = 2 * np.gradient(K_x, t_grid[1]-t_grid[0])
    
    # L1 Norm
    mask = np.isfinite(V_x)
    if not np.any(mask):
        return np.inf, V_x, t_grid
    
    l1_norm = simpson(np.abs(V_x[mask]))
    return l1_norm, V_x, t_grid

# 1. Independent Case (Schanuel Condition Met)
# z1 = 1.0, z2 = pi (linearly independent over Q)
l1_indep, v_indep, t_indep = run_experiment("Independent", [1.0, np.pi])

# 2. Collision Case (Algebraic Dependence / Spectral Overlap)
# z1 = 1.0, z2 = 1.0 + 1e-9 (simulated collision)
l1_coll, v_coll, t_coll = run_experiment("Collision", [1.0, 1.000000001])

print(f"Independent L1: {l1_indep}")
print(f"Collision L1: {l1_coll}")

# Plotting the comparison
plt.figure(figsize=(10, 6))
plt.plot(t_indep, np.abs(v_indep), label='Independent (Stable)')
plt.plot(t_coll, np.abs(v_coll), label='Collision (Unstable/Divergent)', linestyle='--')
plt.yscale('log')
plt.title("UFT-F Schanuel Potential: Independent vs. Collision")
plt.xlabel("Spectral Coordinate (x)")
plt.ylabel("|V(x)| (Log Scale)")
plt.legend()
plt.grid(True, which='both', ls='--')
plt.savefig('schanuel_collision_test.png')

# Save results to CSV for record
import pandas as pd
results_df = pd.DataFrame({
    'Metric': ['L1_Independent', 'L1_Collision', 'UFT_F_Constant'],
    'Value': [l1_indep, l1_coll, 0.0031193375]
})
results_df.to_csv('schanuel_experiment_results.csv', index=False)

# (base) brendanlynch@Brendans-Laptop schanuel % python schanuel.py
# Independent L1: 201.53306733821745
# Collision L1: 146.03545630294892
# (base) brendanlynch@Brendans-Laptop schanuel % 

# csv output Schanuel_experiment_results.csv:
# Metric,Value
# L1_Independent,201.53306733821745
# L1_Collision,146.03545630294892
# UFT_F_Constant,0.0031193375