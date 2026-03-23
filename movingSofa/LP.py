import numpy as np
from scipy.optimize import linprog

def dual_lp_area_bound(N=360):
    """
    Dual LP Approximation for Maximum Area under Unit-Width Constraint.
    Discretizes support function h(θ) at N points.
    Maximizes linear surrogate of area (sum h_i * dθ) subject to:
    - h(θ) + h(θ + π/2) ≤ 1 for all θ
    - h ≥ 0 (support function non-negative)
    
    This gives a strict upper bound on possible area.
    If bound ≤ A_Gerver, it would prove optimality (but it won't be).
    """
    print("--- DUAL LP UPPER BOUND ON AREA ---")
    
    thetas = np.linspace(0, 2*np.pi, N, endpoint=False)
    dtheta = thetas[1] - thetas[0]
    shift = N // 4  # π/2 = 90 degrees for N=360

    # Objective: Maximize sum h_i * dtheta (linear proxy for area)
    c = -np.ones(N) * dtheta  # linprog minimizes c @ x, so negative for max

    # Width constraints: h[i] + h[(i + shift) % N] <= 1
    A_ub = np.zeros((N, N))
    b_ub = np.ones(N)
    for i in range(N):
        A_ub[i, i] = 1
        A_ub[i, (i + shift) % N] = 1

    # Bounds: h ≥ 0 (support function non-negative)
    bounds = [(0, None) for _ in range(N)]

    # Solve the LP
    res = linprog(c, A_ub=A_ub, b_ub=b_ub, bounds=bounds, method='highs')

    if res.success:
        h_opt = res.x
        max_area_bound = -res.fun  # Convert back to maximization
        print(f"LP success: Optimal value (upper bound on area): {max_area_bound:.6f}")
        print(f"Gerver area for comparison: {np.pi/2 + 2/np.pi:.6f}")
        if max_area_bound <= np.pi/2 + 2/np.pi + 1e-6:
            print("LP bound ≤ Gerver area → strong evidence of optimality (unlikely)")
        else:
            print("LP bound > Gerver area → does not rule out larger areas (expected, since linear surrogate is loose)")
        print(f"Max h value: {np.max(h_opt):.4f}")
        print(f"Number of active constraints: {np.sum(np.isclose(A_ub @ h_opt, b_ub, atol=1e-6))}")
    else:
        print("LP failed:", res.message)

if __name__ == "__main__":
    dual_lp_area_bound(N=360)

#     (base) brendanlynch@Brendans-Laptop movingSofa % python LP.py              
# --- DUAL LP UPPER BOUND ON AREA ---
# LP success: Optimal value (upper bound on area): 3.141593
# Gerver area for comparison: 2.207416
# LP bound > Gerver area → does not rule out larger areas (expected, since linear surrogate is loose)
# Max h value: 1.0000
# Number of active constraints: 360
# (base) brendanlynch@Brendans-Laptop movingSofa % 

