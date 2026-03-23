import numpy as np
import matplotlib.pyplot as plt

# Vectorized Gerver support function approximations
def gerver_support(theta):
    theta = np.mod(theta, np.pi)
    h = np.zeros_like(theta)
    
    # Piecewise conditions using np.where for array handling
    cond1 = (theta >= 0) & (theta < np.pi/4)
    cond2 = (theta >= np.pi/4) & (theta < np.pi/2)
    cond3 = (theta >= np.pi/2)
    
    h = np.where(cond1, 0.5 + 0.5 * np.cos(4*theta), h)
    h = np.where(cond2, 1.0 - 0.5 * np.sin(4*(theta - np.pi/4)), h)
    h = np.where(cond3, 0.5, h)
    return h

# Width constraint: h(theta) + h(theta + pi/2)
def width_constraint(theta):
    return gerver_support(theta) + gerver_support(theta + np.pi/2)

# Perturbed version: add a small bulge near critical theta = pi/4 to gain area
def perturbed_support(theta, epsilon=0.015):
    h = gerver_support(theta)
    # Gaussian bump represents the "extra area" attempt
    bump = epsilon * np.exp(-((theta - np.pi/4)/0.1)**2)
    return h + bump

# Clearance: 1 - total width
def clearance(theta, epsilon=0.0):
    if epsilon == 0:
        w = width_constraint(theta)
    else:
        w = perturbed_support(theta, epsilon) + perturbed_support(theta + np.pi/2, epsilon)
    return 1.0 - w

# Plotting the Geometric Limit
thetas = np.linspace(0, np.pi/2, 1000)

plt.figure(figsize=(10, 8))

# Subplot 1: Width Constraint
plt.subplot(2,1,1)
plt.plot(thetas, width_constraint(thetas), color='blue', label='Gerver Width (Ideal)')
plt.axhline(1.0, color='red', linestyle='--', label='Corridor Wall (Limit)')
plt.title('Rigid Width Constraint (Saturation at θ = π/4)')
plt.ylabel('h(θ) + h(θ + π/2)')
plt.legend()
plt.grid(alpha=0.3)

# Subplot 2: Clearance Violation (The "Pinch-off")
plt.subplot(2,1,2)
plt.plot(thetas, clearance(thetas, epsilon=0), 'g', label='Gerver Clearance (Stable)')
plt.plot(thetas, clearance(thetas, epsilon=0.01), 'r--', label='Super-Gerver Clearance (A + ε)')

# Shading the violation region
cl_perturbed = clearance(thetas, epsilon=0.01)
plt.fill_between(thetas, cl_perturbed, 0, where=(cl_perturbed < 0), color='red', alpha=0.3, label='Violation (Collision)')

plt.axhline(0, color='black', linewidth=1)
plt.title('Geometric Pinch-Off: Negative Clearance for A > A_Gerver')
plt.xlabel('Rotation Angle (θ)')
plt.ylabel('Clearance δ(θ)')
plt.legend()
plt.grid(alpha=0.3)

plt.tight_layout()
plt.show()