import torch
import torch.nn as nn
import torch.nn.utils as utils
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from tqdm import tqdm

# We use torch.func for high-performance Jacobian computation
try:
    from torch.func import vmap, jacrev
except ImportError:
    # Fallback for older torch versions
    vmap, jacrev = None, None

class AAES_Net(nn.Module):
    def __init__(self, d, hidden=64):
        super().__init__()
        # Geometry: 1-Lipschitz layers via Spectral Norm
        self.fc1 = utils.spectral_norm(nn.Linear(d, hidden))
        self.fc2 = utils.spectral_norm(nn.Linear(hidden, d))
        self.act = nn.LeakyReLU(0.1)

        # Energy: Initialize scale to signal energy (25.0) to allow effective shrinkage.
        # We use the Modularity Constant (0.003119) as a small additive bias 
        # to ensure a non-zero spectral floor.
        self.scale = nn.Parameter(torch.tensor(25.0))
        self.floor = 0.003119 

    def forward(self, x):
        out = self.fc2(self.act(self.fc1(x)))
        return torch.nn.functional.softplus(out) * (self.scale + self.floor)

def get_diag_jacobian(x, model):
    """Vectorized computation of the diagonal of the Jacobian."""
    if vmap and jacrev:
        # High-speed vectorized Jacobian diagonal
        def model_fn(x_in): return model(x_in)
        # We compute the diagonal by evaluating the derivative of each output i w.r.t input i
        jac = jacrev(model_fn)(x)
        return torch.diag(jac)
    else:
        # Optimized loop fallback
        x_in = x.detach().requires_grad_(True)
        c = model(x_in)
        diag = torch.zeros_like(x)
        for i in range(x.shape[0]):
            grad_i = torch.autograd.grad(c[i], x_in, retain_graph=True)[0]
            diag[i] = grad_i[i]
        return diag

def compute_sure_loss(x, model):
    c = model(x)
    d = x.shape[0]
    r = torch.norm(x) + 1e-8
    
    # Efficient Jacobian Diagonal
    diag_jac = get_diag_jacobian(x, model)
    
    phi = torch.exp(-c / r)
    t1 = torch.sum(x**2 * (phi - 1)**2)
    t2 = 2 * torch.sum(phi - 1)
    t3 = 2 * torch.sum(phi * ((c * x**2 / r**3) - (x * diag_jac / r)))
    
    return d + t1 + t2 + t3

def js_estimate(x):
    d = x.shape[0]
    norm_sq = torch.sum(x**2)
    return x * max(0.0, 1 - (d - 2) / norm_sq)

def run_single_trial(d=500, block_size=50, num_active_blocks=1, seed=44):
    torch.manual_seed(seed)
    np.random.seed(seed)
    
    theta = torch.zeros(d)
    block_starts = np.random.choice(range(0, d, block_size), num_active_blocks, replace=False)
    for start in block_starts:
        theta[start:start+block_size] = 25.0 / np.sqrt(block_size)
        
    x_obs = theta + torch.randn(d)
    
    model = AAES_Net(d)
    # Using a higher learning rate for the scale parameter to adapt quickly
    optimizer = torch.optim.Adam([
        {'params': [model.fc1.weight, model.fc1.bias, model.fc2.weight, model.fc2.bias], 'lr': 2e-3},
        {'params': [model.scale], 'lr': 1e-1} 
    ])
    
    for _ in range(401):
        optimizer.zero_grad()
        loss = compute_sure_loss(x_obs, model)
        loss.backward()
        optimizer.step()
        
    with torch.no_grad():
        c_final = model(x_obs)
        r = torch.norm(x_obs) + 1e-8
        aaes_res = x_obs * torch.exp(-c_final / r)
        js_res = js_estimate(x_obs)
        
        aaes_risk = torch.sum((aaes_res - theta)**2).item()
        js_risk = torch.sum((js_res - theta)**2).item()
        
    return js_risk, aaes_risk

# === Execution ===
N_TRIALS = 50
js_risks, aaes_risks = [], []

print("Running Table 1 (d=500, s=1) with Optimized Jacobian...")
for i in tqdm(range(N_TRIALS)):
    js_r, aaes_r = run_single_trial(num_active_blocks=1, seed=44+i)
    js_risks.append(js_r)
    aaes_risks.append(aaes_r)

print(f"\nFinal Results (d=500, s=1):")
print(f"James-Stein Mean Risk: {np.mean(js_risks):.2f} ± {np.std(js_risks):.2f}")
print(f"Neural AAES Mean Risk: {np.mean(aaes_risks):.2f} ± {np.std(aaes_risks):.2f}")

# === Figure 1 ===
sns.set_style("whitegrid")
s_values = [1, 2, 4]
js_means, aaes_means = [], []

print("\nGenerating Figure 1 (Risk vs. Sparsity)...")
for s in s_values:
    js_r_s, aaes_r_s = [], []
    for i in tqdm(range(20), desc=f"Sparsity s={s}"):
        jr, ar = run_single_trial(num_active_blocks=s, seed=100+i)
        js_r_s.append(jr)
        aaes_r_s.append(ar)
    js_means.append(np.mean(js_r_s))
    aaes_means.append(np.mean(aaes_r_s))

plt.figure(figsize=(7, 5))
plt.plot(s_values, js_means, 'o-', label='James-Stein')
plt.plot(s_values, aaes_means, 's-', label='Neural AAES (Stabilized)')
plt.xlabel('Number of active blocks s')
plt.ylabel('Mean Squared Error')
plt.legend()
plt.savefig('risk_vs_sparsity_vmap.pdf')
plt.show()


# (base) brendanlynch@Brendans-Laptop final2 % python simulation3.py
# Running Table 1 (d=500, s=1) with Optimized Jacobian...
# 100%|███████████████████████████████████████████| 50/50 [00:33<00:00,  1.48it/s]

# Final Results (d=500, s=1):
# James-Stein Mean Risk: 280.07 ± 17.10
# Neural AAES Mean Risk: 222.72 ± 20.81

# Generating Figure 1 (Risk vs. Sparsity)...
# Sparsity s=1: 100%|█████████████████████████████| 20/20 [00:14<00:00,  1.40it/s]
# Sparsity s=2: 100%|█████████████████████████████| 20/20 [00:13<00:00,  1.47it/s]
# Sparsity s=4: 100%|█████████████████████████████| 20/20 [00:13<00:00,  1.48it/s]
# (base) brendanlynch@Brendans-Laptop final2 % 