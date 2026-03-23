import networkx as nx
import matplotlib.pyplot as plt
from collections import Counter
import numpy as np

# Collatz next
def collatz_next(n):
    if n % 2 == 0:
        return n // 2
    else:
        return 3 * n + 1

# Build graph
def build_collatz_graph(max_n):
    G = nx.DiGraph()
    for n in range(1, max_n + 1):
        current = n
        path = [current]
        while current > 1:
            if current in G and G.has_edge(current, collatz_next(current)):
                break  # Avoid re-adding if already present
            next_val = collatz_next(current)
            G.add_edge(current, next_val)
            current = next_val
            path.append(current)
            if current > max_n * 10:  # Safety cap for potential explosions (though none in Collatz)
                break
    return G

# Mod-24 counts
def compute_mod24_counts(G):
    mods = [node % 24 for node in G.nodes() if node > 0]
    counter = Counter(mods)
    return counter

# Detect cycles (beyond known 4-2-1)
def detect_cycles(G):
    try:
        cycle = nx.find_cycle(G)
        return cycle
    except nx.NetworkXNoCycle:
        return None

# Simulate simple spectral potential V(x) ~ sum 1/log(steps) * delta(mod)
def simulate_spectral_potential(G, prime_residues):
    V = np.zeros(24)
    for node in G.nodes():
        if node == 1:
            continue
        steps = nx.shortest_path_length(G, node, 1) if nx.has_path(G, node, 1) else 0
        if steps > 0:
            mod = node % 24
            V[mod] += 1 / np.log(steps + 2)  # Avoid log1, proxy for info density
    norm_L1 = np.sum(np.abs(V))
    return V, norm_L1

# Main
max_n = 10000  # Larger for stats
G = build_collatz_graph(max_n)

print(f"Number of nodes: {G.number_of_nodes()}")
print(f"Number of edges: {G.number_of_edges()}")
components = list(nx.weakly_connected_components(G))
print(f"Number of weakly connected components: {len(components)}")
main_component = max(components, key=len)
print(f"Size of largest component: {len(main_component)}")

mod_counts = compute_mod24_counts(G)
print("Mod-24 distribution:")
for mod in sorted(mod_counts):
    print(f"{mod}: {mod_counts[mod]}")

prime_residues = {1,5,7,11,13,17,19,23}
prime_count = sum(mod_counts[mod] for mod in prime_residues)
total_nodes = G.number_of_nodes()
print(f"Nodes in prime residues: {prime_count} ({prime_count / total_nodes * 100:.2f}%)")

# Cycle check
cycle = detect_cycles(G)
print(f"Cycle detected: {cycle}" if cycle else "No cycles detected (expected)")

# Spectral sim
V, L1_norm = simulate_spectral_potential(G, prime_residues)
print(f"Simulated V(mod): {V}")
print(f"L1 norm (finite, per ACI): {L1_norm}")

# Bar for mods
labels = list(range(24))
values = [mod_counts.get(i, 0) for i in labels]
plt.bar(labels, values)
plt.xlabel('Mod 24')
plt.ylabel('Count')
plt.title(f'Node Distribution Mod 24 up to {max_n}')
plt.show()

# Potential plot
plt.bar(labels, V)
plt.xlabel('Mod 24')
plt.ylabel('V(x) contrib')
plt.title('Spectral Potential Proxy')
plt.show()

# (base) brendanlynch@Brendans-Laptop collatz % python collatz2.py
# Number of nodes: 19382
# Number of edges: 19212
# Number of weakly connected components: 170
# Size of largest component: 15824
# Mod-24 distribution:
# 0: 416
# 1: 493
# 2: 865
# 3: 417
# 4: 1780
# 5: 872
# 6: 417
# 7: 496
# 8: 865
# 9: 417
# 10: 1781
# 11: 870
# 12: 417
# 13: 493
# 14: 870
# 15: 417
# 16: 1781
# 17: 870
# 18: 416
# 19: 494
# 20: 874
# 21: 416
# 22: 1779
# 23: 866
# Nodes in prime residues: 5454 (28.14%)
# No cycles detected (expected)
# Simulated V(mod): [106.85842268 101.33598702 190.71654814  89.62347412 344.48414004
#  184.17525585  87.30394359  73.42678663 210.17285764  89.2153632
#  334.60244875 142.81568697  98.43843017 114.21871045 155.37004561
#   67.80659171 399.34653309 151.84726701  99.3812592  100.79944515
#  191.36768674  98.88344122 224.9439707   82.93148376]
# L1 norm (finite, per ACI): 3740.065779454258
# 2025-12-28 07:39:11.827 python[54981:51678509] The class 'NSSavePanel' overrides the method identifier.  This method is implemented by class 'NSWindow'
# (base) brendanlynch@Brendans-Laptop collatz % 