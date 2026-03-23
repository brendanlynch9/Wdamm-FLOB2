import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import minimize

class UFTFSteinerSolver:
    def __init__(self, terminals):
        """
        Initialize with arithmetic motives (terminals) M[cite: 150].
        """
        self.terminals = np.array(terminals)
        self.n_terminals = len(terminals)
        # Universal Constant derived from E8/K3 [cite: 42, 95]
        self.C_UFT_F = 331/22 
        # Base-24 Modulus for informational quantization [cite: 49, 130]
        self.base_24 = 24.0

    def spectral_potential(self, points):
        """
        Computes the Defect Potential V_M(x)[cite: 142].
        In this model, V is the L1-norm of distances, which must remain finite[cite: 40, 86].
        """
        total_potential = 0
        # Calculate potential between points (Simulating ACI/LIC) [cite: 154]
        for i in range(len(points)):
            for j in range(i + 1, len(points)):
                dist = np.linalg.norm(points[i] - points[j])
                total_potential += dist
        return total_potential

    def aci_constraint(self, s_points_flat):
        """
        Enforces the Anti-Collision Identity (ACI).
        Ensures Steiner points don't collapse (collide) into terminals[cite: 87, 125].
        """
        s_points = s_points_flat.reshape(-1, 2)
        min_dist = float('inf')
        for s in s_points:
            for t in self.terminals:
                dist = np.linalg.norm(s - t)
                if dist < min_dist:
                    min_dist = dist
        # Penalize if distance drops below spectral floor lambda_0 [cite: 94]
        return min_dist - (1.0 / self.C_UFT_F)

    def base_24_quantization(self, s_points):
        """
        Applies Base-24 Harmony to the coordinates to ensure 
        informational energy quantization E_I[cite: 101, 130].
        """
        return np.round(s_points * self.base_24) / self.base_24

    def solve(self):
        """
        Constructive Algorithm: Resolving Steiner Tree via Spectral Closure[cite: 170].
        """
        # Initial guess: Centroid of terminals
        initial_steiner = np.mean(self.terminals, axis=0).reshape(1, 2)
        
        # Optimize the Potential V subject to ACI constraints [cite: 168]
        res = minimize(
            lambda x: self.spectral_potential(np.vstack([self.terminals, x.reshape(-1, 2)])),
            initial_steiner.flatten(),
            constraints={'type': 'ineq', 'fun': self.aci_constraint}
        )
        
        # Apply Base-24 Quantization to the result [cite: 171]
        optimized_steiner = res.x.reshape(-1, 2)
        quantized_steiner = self.base_24_quantization(optimized_steiner)
        
        return quantized_steiner

def visualize_results(terminals, steiner_point):
    plt.figure(figsize=(8, 8))
    plt.scatter(terminals[:, 0], terminals[:, 1], color='blue', label='Terminals (Motive M)', s=100)
    plt.scatter(steiner_point[:, 0], steiner_point[:, 1], color='red', label='Steiner Point (ACI Node)', marker='X', s=200)
    
    for t in terminals:
        plt.plot([t[0], steiner_point[0, 0]], [t[1], steiner_point[0, 1]], 'g--', alpha=0.5)
        
    plt.title("UFT-F Steiner-Quantization: Spectral Closure")
    plt.legend()
    plt.grid(True, which='both', linestyle='--', alpha=0.5)
    plt.show()

# Execution
if __name__ == "__main__":
    # Define a set of "arithmetic" coordinates
    motive_points = [[0, 0], [1, 2], [2, 0]]
    
    solver = UFTFSteinerSolver(motive_points)
    s_point = solver.solve()
    
    print(f"Topological Constant (C_UFT-F): {solver.C_UFT_F}")
    print(f"Quantized Steiner Node (Base-24): {s_point}")
    
    visualize_results(solver.terminals, s_point)

#     (base) brendanlynch@Brendans-Laptop SteinerTree % python steinerQuantization.py
# Topological Constant (C_UFT-F): 15.045454545454545
# Quantized Steiner Node (Base-24): [[1.         0.58333333]]
# (base) brendanlynch@Brendans-Laptop SteinerTree % 