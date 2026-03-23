import numpy as np
from scipy.spatial.distance import pdist, squareform
from sklearn.cluster import KMeans
import networkx as nx

def get_connected_steiner_length(points, centers, grid_step=None):
    """
    Computes a connected Steiner Tree length by:
    1. Optionally quantizing centers to a grid.
    2. Building an MST on the union of (terminals + centers).
    This addresses Grok's 'connectivity' requirement.
    """
    pts = np.atleast_2d(points)
    cnts = np.atleast_2d(centers)
    
    if grid_step is not None:
        cnts = np.round(cnts / grid_step) * grid_step
        
    # Combine terminals and Steiner points
    nodes = np.vstack([pts, cnts])
    dist_matrix = squareform(pdist(nodes))
    
    # Build MST using NetworkX for reliability
    G = nx.from_numpy_array(dist_matrix)
    mst = nx.minimum_spanning_tree(G)
    return mst.size(weight='weight')

# Test Case: The 'Grok Adversarial' (High-sensitivity configuration)
# A circle of points with a single point shifted just enough to test grid-snap sensitivity.
n_adversarial = 12
theta = np.linspace(0, 2*np.pi, n_adversarial, endpoint=False)
adversarial_pts = np.column_stack([np.cos(theta), np.sin(theta)])
adversarial_pts[0] += [0.021, 0.019] # Jiggle to 'miss' the 1/24 grid lines

# Comparison run
steps = [1/23, 1/24, 1/25]
med = np.mean(adversarial_pts, axis=0).reshape(1, -1) # Single junction

print(f"Adversarial Set (n={n_adversarial})")
print(f"Continuous Connected Length: {get_connected_steiner_length(adversarial_pts, med):.7f}")
for s in steps:
    l = get_connected_steiner_length(adversarial_pts, med, grid_step=s)
    print(f"Grid 1/{int(1/s)} Connected Length: {l:.7f} (Err: {abs(l-get_connected_steiner_length(adversarial_pts, med)):.7e})")

#     (base) brendanlynch@Brendans-Laptop SteinerTree % python stabilityBridge.py
# Adversarial Set (n=12)
# Continuous Connected Length: 6.6794233
# Grid 1/23 Connected Length: 6.6817304 (Err: 2.3070877e-03)
# Grid 1/24 Connected Length: 6.6817304 (Err: 2.3070877e-03)
# Grid 1/25 Connected Length: 6.6817304 (Err: 2.3070877e-03)
# (base) brendanlynch@Brendans-Laptop SteinerTree % 


