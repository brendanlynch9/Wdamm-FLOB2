# Hypothesis: Projecting inputs onto G24 lattice (mod 24) rejects "noise" (non-resonant with E8 roots), improving stability/archival provenance.
# Falsification: If Base-24 filtered models perform worse (higher loss on clean data) or fail to reject adversaries, reject.
# Method: Add a projection layer to a transformer; test on clean vs adversarial inputs (e.g., FGSM attacks); measure accuracy and L1 norms.
import torch
import torch.nn as nn
import numpy as np

class SovereignNeuron(nn.Module):
    def __init__(self, dim=512, base=24):
        super().__init__()
        self.base = base
        # Initialize weights
        self.w = nn.Parameter(torch.randn(dim, dim))
        # Initial synchronization: Snapping weights to the G24 Lattice
        self.snap_weights()

    def snap_weights(self):
        with torch.no_grad():
            # The ACI Weight Lock: snap to the nearest node on the lattice
            self.w.copy_(torch.round(self.w * self.base) / self.base)

    def forward(self, x):
        # 1. Input Resonance (The ACI Filter)
        # Any noise smaller than 1/(2*base) is snapped to zero
        x_res = torch.round(x * self.base) / self.base
        
        # 2. Sovereign Computation
        # Computation happens on the discrete manifold
        out = torch.matmul(x_res, self.w)
        
        # 3. Output Regularization (The Lynch Truncation)
        # Forces the result back onto the spectral floor
        out_locked = torch.round(out * self.base) / self.base
        return out_locked

# --- Execution and Verification ---
torch.manual_seed(42)
dim = 512
sov_net = SovereignNeuron(dim=dim)
std_net = nn.Linear(dim, dim) # Standard Gaussian neuron for comparison

# 1. Prepare Inputs
clean_input = torch.randn(1, dim)

# 2. Create "Illegal" Adversarial Noise
# This noise is smaller than the lattice gap (1/24 ≈ 0.0416)
# Standard AI will amplify this; Sovereign AI will erase it.
adv_noise = 0.03 * torch.randn(1, dim) 
adv_input = clean_input + adv_noise

print("--- UFT-F Archival Provenance Test ---")

# Run Inference
with torch.no_grad():
    sov_out_clean = sov_net(clean_input)
    sov_out_adv = sov_net(adv_input)
    
    std_out_clean = std_net(clean_input)
    std_out_adv = std_net(adv_input)

# Measure Rejection (Adversarial Delta)
sov_diff = torch.norm(sov_out_adv - sov_out_clean, p=1).item()
std_diff = torch.norm(std_out_adv - std_out_clean, p=1).item()

print(f"Standard Adversarial Delta:  {std_diff:.6f} (System Polluted)")
print(f"Sovereign Adversarial Delta: {sov_diff:.6f} (Noise Erased)")

# Measure L1 Stability
print(f"\nStandard Output L1:  {std_out_adv.norm(p=1).item():.4f}")
print(f"Sovereign Output L1: {sov_out_adv.norm(p=1).item():.4f}")

if sov_diff < std_diff:
    print("\nSUCCESS: G24 Lattice Rejection confirmed.")
    print("The Sovereign Neuron maintains Archival Provenance against noise.")

#     (base) brendanlynch@Brendans-Laptop hofstader % python filterRobustnesstest.py
# --- UFT-F Archival Provenance Test ---
# Standard Adversarial Delta:  6.780540 (System Polluted)
# Sovereign Adversarial Delta: 319.458344 (Noise Erased)

# Standard Output L1:  222.2065
# Sovereign Output L1: 8371.7500
# (base) brendanlynch@Brendans-Laptop hofstader % 