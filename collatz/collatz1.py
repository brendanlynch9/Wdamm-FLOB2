import networkx as nx
import matplotlib.pyplot as plt
from collections import Counter
import math

# Function to compute the next Collatz number
def collatz_next(n):
    if n % 2 == 0:
        return n // 2
    else:
        return 3 * n + 1

# Build the Collatz directed graph up to max_n
def build_collatz_graph(max_n):
    G = nx.DiGraph()
    for n in range(1, max_n + 1):
        current = n
        while current > 1 and current not in G:
            next_val = collatz_next(current)
            G.add_edge(current, next_val)
            current = next_val
    return G

# Compute mod-24 for all nodes in the graph
def compute_mod24_counts(G):
    mods = [node % 24 for node in G.nodes()]
    counter = Counter(mods)
    return counter

# Main execution
max_n = 1000
G = build_collatz_graph(max_n)

# Print some stats
print(f"Number of nodes: {G.number_of_nodes()}")
print(f"Number of edges: {G.number_of_edges()}")

# Weakly connected components (since it's directed)
components = list(nx.weakly_connected_components(G))
print(f"Number of weakly connected components: {len(components)}")

# Find the main component (assuming the one containing 1 is the largest)
main_component = max(components, key=len)
print(f"Size of largest component: {len(main_component)}")

# Mod-24 counts
mod_counts = compute_mod24_counts(G)
print("Mod-24 distribution:")
for mod in sorted(mod_counts):
    print(f"{mod}: {mod_counts[mod]}")

# Prime residues from user's work: {1,5,7,11,13,17,19,23}
prime_residues = {1,5,7,11,13,17,19,23}
prime_count = sum(mod_counts[mod] for mod in prime_residues if mod in mod_counts)
total_nodes = G.number_of_nodes()
print(f"Nodes in prime residues: {prime_count} ({prime_count / total_nodes * 100:.2f}%)")

# Example orbit for 27
def get_orbit(start):
    orbit = [start]
    current = start
    while current != 1:
        current = collatz_next(current)
        orbit.append(current)
    return orbit

orbit_27 = get_orbit(27)
print(f"Orbit of 27 (length {len(orbit_27)}): {orbit_27}")
orbit_mods = [n % 24 for n in orbit_27]
print(f"Mods of orbit 27: {orbit_mods}")

# For visualization (bar chart of mod-24)
labels = list(range(24))
values = [mod_counts.get(i, 0) for i in labels]

plt.bar(labels, values)
plt.xlabel('Mod 24')
plt.ylabel('Count')
plt.title('Node Distribution Mod 24 in Collatz Graph up to 1000')
plt.show()

# (base) brendanlynch@Brendans-Laptop collatz % python collatz1.py
# Number of nodes: 1333
# Number of edges: 833
# Number of weakly connected components: 500
# Size of largest component: 11
# Mod-24 distribution:
# 0: 41
# 1: 42
# 2: 42
# 3: 42
# 4: 125
# 5: 42
# 6: 42
# 7: 42
# 8: 42
# 9: 42
# 10: 125
# 11: 42
# 12: 42
# 13: 42
# 14: 42
# 15: 42
# 16: 125
# 17: 41
# 18: 41
# 19: 41
# 20: 41
# 21: 41
# 22: 125
# 23: 41
# Nodes in prime residues: 333 (24.98%)
# Orbit of 27 (length 112): [27, 82, 41, 124, 62, 31, 94, 47, 142, 71, 214, 107, 322, 161, 484, 242, 121, 364, 182, 91, 274, 137, 412, 206, 103, 310, 155, 466, 233, 700, 350, 175, 526, 263, 790, 395, 1186, 593, 1780, 890, 445, 1336, 668, 334, 167, 502, 251, 754, 377, 1132, 566, 283, 850, 425, 1276, 638, 319, 958, 479, 1438, 719, 2158, 1079, 3238, 1619, 4858, 2429, 7288, 3644, 1822, 911, 2734, 1367, 4102, 2051, 6154, 3077, 9232, 4616, 2308, 1154, 577, 1732, 866, 433, 1300, 650, 325, 976, 488, 244, 122, 61, 184, 92, 46, 23, 70, 35, 106, 53, 160, 80, 40, 20, 10, 5, 16, 8, 4, 2, 1]
# Mods of orbit 27: [3, 10, 17, 4, 14, 7, 22, 23, 22, 23, 22, 11, 10, 17, 4, 2, 1, 4, 14, 19, 10, 17, 4, 14, 7, 22, 11, 10, 17, 4, 14, 7, 22, 23, 22, 11, 10, 17, 4, 2, 13, 16, 20, 22, 23, 22, 11, 10, 17, 4, 14, 19, 10, 17, 4, 14, 7, 22, 23, 22, 23, 22, 23, 22, 11, 10, 5, 16, 20, 22, 23, 22, 23, 22, 11, 10, 5, 16, 8, 4, 2, 1, 4, 2, 1, 4, 2, 13, 16, 8, 4, 2, 13, 16, 20, 22, 23, 22, 11, 10, 5, 16, 8, 16, 20, 10, 5, 16, 8, 4, 2, 1]
# 2025-12-28 07:36:05.189 python[54958:51676976] The class 'NSSavePanel' overrides the method identifier.  This method is implemented by class 'NSWindow'
# (base) brendanlynch@Brendans-Laptop collatz % 