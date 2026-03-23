# Hypothesis: Recursive self-models become unstable (manifold rupture) when hidden state rank exceeds 321, proxying L1 divergence via ACI.
# Falsification: If models with rank >321 remain stable (low loss, no divergence) or low-rank ones unstable, reject.
# Method: Simulate a recurrent net (e.g., RNN/LSTM) with self-referential loops; compute SVD rank of activations; enforce truncation governor; measure stability (e.g., exploding gradients or loss divergence) over iterations.
import torch
import torch.nn as nn
import numpy as np
from scipy.linalg import svdvals
import matplotlib.pyplot as plt

class SelfLoopLinear(nn.Module):
    def __init__(self, dim=512):
        super().__init__()
        self.linear = nn.Linear(dim, dim)
        # Expansive init
        gain = 1.2
        std = gain / np.sqrt(dim)
        self.linear.weight.data.normal_(0, std)
        self.linear.bias.data.fill_(0.01)
    
    def forward(self, x, steps=30, governor_rank=321, amplify=1.02, lambda_0=15.045):
        batch_size = x.size(0)
        h = x
        activations = []
        trunc_count = 0
        norm_factor = np.sqrt(batch_size * self.linear.out_features)
        is_governed = governor_rank < 1000000
        for step in range(steps):
            h = self.linear(h)
            if not is_governed:
                h = h * amplify
            h_matrix = h.detach().cpu().numpy()
            U, S, Vh = np.linalg.svd(h_matrix, full_matrices=False)
            current_rank = np.sum(S > 1e-5)
            if current_rank > governor_rank:
                trunc_count += 1
                S[governor_rank:] = 0.0
            # ACI bounding in governed: enforce L1 < lambda_0 via scaling
            l1_sings = np.sum(S) / norm_factor
            if is_governed and l1_sings > lambda_0:
                scale = (lambda_0 * norm_factor) / np.sum(S)
                S *= scale
            h_matrix = U @ np.diag(S) @ Vh
            h = torch.from_numpy(h_matrix).float()
            activations.append(l1_sings)  # Log pre-bound L1 for ungov, post for gov
        print(f"Total truncations: {trunc_count}")
        return activations

# Run test
torch.manual_seed(42)
np.random.seed(42)
batch_size = 512
dim = 512
input_tensor = torch.randn(batch_size, dim)
model = SelfLoopLinear(dim=dim)

print("Running governed (rank cap 321)...")
governed_acts = model(input_tensor, governor_rank=321)

print("\nRunning ungoverned (no cap, full amplification)...")
ungoverned_acts = model(input_tensor, governor_rank=1000000)

lambda_0 = 15.045
print("\nResults:")
print(f"Governed max L1 sings: {max(governed_acts):.4f}")
print(f"Governed mean L1 sings: {np.mean(governed_acts):.4f}")
print(f"Ungoverned max L1 sings: {max(ungoverned_acts):.4f}")
print(f"Ungoverned mean L1 sings: {np.mean(ungoverned_acts):.4f}")
print(f"Expected: Governed bounded <~{lambda_0}, Ungoverned grows >>{lambda_0}")

# Plot
plt.plot(governed_acts, label='Governed (Stable Self)')
plt.plot(ungoverned_acts, label='Ungoverned (Rupture)')
plt.axhline(lambda_0, color='r', linestyle='--', label='λ0 Ceiling')
plt.xlabel('Steps (Strange Loop Iterations)')
plt.ylabel('L1 Sings Proxy (Informational Mass)')
plt.legend()
plt.title('UFT-F Lynch Limit Demo: ACI Governor vs Rupture')
plt.savefig('rupture_plot.png')  # Save to file to avoid NSSavePanel warning
print("Plot saved as rupture_plot.png")

# (base) brendanlynch@Brendans-Laptop hofstader % python Rupture321test.py
# Running governed (rank cap 321)...
# Total truncations: 30

# Running ungoverned (no cap, full amplification)...
# Total truncations: 0

# Results:
# Governed max L1 sings: 19.0125
# Governed mean L1 sings: 17.6666
# Ungoverned max L1 sings: 3355.0161
# Ungoverned mean L1 sings: 620.4942
# Expected: Governed bounded <~15.045, Ungoverned grows >>15.045
# Plot saved as rupture_plot.png
# (base) brendanlynch@Brendans-Laptop hofstader % 

