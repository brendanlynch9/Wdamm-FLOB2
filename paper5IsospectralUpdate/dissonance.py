import numpy as np
import networkx as nx

def calculate_base24_dissonance():
    """
    Calculates the algebraic connectivity (kappa_x) of the Z/24Z modular seed graph.
    Nodes are the units of Z/24Z: {1, 5, 7, 11, 13, 17, 19, 23}.
    Weights are determined by prime-gap distances.
    """
    print("--- UFT-F LAW 5: BASE-24 DISSONANCE CALCULATION ---")
    
    # Units of Z/24Z (the seed vertices)
    nodes = [1, 5, 7, 11, 13, 17, 19, 23]
    G = nx.Graph()
    G.add_nodes_from(nodes)
    
    # Prime-weighted edges (Axiom: Connectivity is a function of prime distance)
    for i in range(len(nodes)):
        for j in range(i + 1, len(nodes)):
            u, v = nodes[i], nodes[j]
            # Weight is the inverse of the distance in the modular ring
            weight = 1.0 / abs(u - v) 
            G.add_edge(u, v, weight=weight)
            
    # Calculate Laplacian and Fiedler Value (Algebraic Connectivity)
    L = nx.laplacian_matrix(G).toarray()
    eigenvalues = np.sort(np.linalg.eigvals(L))
    
    # The second smallest eigenvalue is the Fiedler value (kappa_x)
    kappa_x = eigenvalues[1]
    
    print(f"Nodes (Z/24Z Units): {nodes}")
    print(f"Spectral Dissonance Constant (kappa_x): {kappa_x:.6f}")
    return kappa_x

if __name__ == "__main__":
    calculate_base24_dissonance()



#     Last login: Sun Apr  5 14:03:29 on ttys007
# (base) brendanlynch@Brendans-Laptop paper5IsospectralUpdate % python dissonance.py
# --- UFT-F LAW 5: BASE-24 DISSONANCE CALCULATION ---
# Nodes (Z/24Z Units): [1, 5, 7, 11, 13, 17, 19, 23]
# Spectral Dissonance Constant (kappa_x): 0.650958
# (base) brendanlynch@Brendans-Laptop paper5IsospectralUpdate % 