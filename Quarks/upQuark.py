import numpy as np
from scipy.linalg import eigh
from scipy.optimize import minimize

def compute_up_quark(j_params, scale_to_mt=173.0):
    J = np.array([[j_params[0], j_params[3], j_params[5]],
                  [j_params[3], j_params[1], j_params[4]],
                  [j_params[5], j_params[4], j_params[2]]])
    eigvals, eigvecs = eigh(J)
    idx = eigvals.argsort()
    m_sq = np.abs(eigvals[idx])
    U = eigvecs[:, idx]
    scale = scale_to_mt / np.sqrt(m_sq[2])
    m_phys = np.sqrt(m_sq) * scale
    theta12 = np.degrees(np.arctan2(np.abs(U[0, 1]), np.abs(U[0, 0])))
    theta23 = np.degrees(np.arctan2(np.abs(U[1, 2]), np.abs(U[2, 2])))
    theta13 = np.degrees(np.arcsin(np.abs(U[0, 2])))
    return m_phys, [theta12, theta23, theta13]

def objective(j_params):
    _, angles = compute_up_quark(j_params)
    targets = [13.03, 2.39, 0.214]
    return np.sum((np.array(angles) - targets)**2)

# Optimal initial for up-type (light u requires tiny diag/off-diag)
init = [1e-10, 5e-4, 0.134, 1e-9, 0.01, 8e-4]  # From E8 duality scaling
opt = minimize(objective, init, method='Nelder-Mead', tol=1e-15, options={'maxiter': 100000, 'adaptive': True})

m_up, ang_up = compute_up_quark(opt.x)
print("UFT-F Up-Quark Closure:")
print(f"Angles: θ12={ang_up[0]:.4f}° | θ23={ang_up[1]:.4f}° | θ13={ang_up[2]:.4f}°")
print(f"Masses: mu={m_up[0]:.6f} GeV | mc={m_up[1]:.4f} GeV | mt={m_up[2]:.1f} GeV")
print(f"Residual: {opt.fun:.2e} (Converged: {opt.success})")

# (base) brendanlynch@Brendans-Laptop Quarks % python upQuark.py          
# UFT-F Up-Quark Closure:
# Angles: θ12=13.0300° | θ23=2.3900° | θ13=0.2140°
# Masses: mu=1.223587 GeV | mc=4.4432 GeV | mt=173.0 GeV
# Residual: 9.43e-27 (Converged: True)
# (base) brendanlynch@Brendans-Laptop