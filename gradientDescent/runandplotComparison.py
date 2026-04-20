"""
ONE SCRIPT - Run Spectral + Adam + Plot Comparison
==================================================
Runs both methods, saves data, and creates the plot.
No manual steps needed.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.optim import AdamW
from transformers import AutoModelForCausalLM, AutoConfig
import numpy as np
import matplotlib.pyplot as plt

print("=== Starting Full Comparison Run ===\n")

# ===================== SPECTRAL =====================
print("Running Spectral Variational Optimizer...")

config = AutoConfig.from_pretrained("gpt2")
model = AutoModelForCausalLM.from_config(config)
device = "cuda" if torch.cuda.is_available() else "cpu"
model = model.to(device)

class SpectralAmplitudeNet(nn.Module):
    def __init__(self, embedding_dim: int, hidden_dim: int = 256):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(embedding_dim, hidden_dim), nn.Tanh(),
            nn.Linear(hidden_dim, hidden_dim), nn.Tanh(),
            nn.Linear(hidden_dim, 1),
        )
    def forward(self, x):
        raw = self.net(x)
        return F.normalize(raw.view(-1), p=2, dim=0).view(raw.shape)

class SpectralVariationalOptimizer:
    def __init__(self, model, epsilon=0.008, target_residue=0.9895, temperature=0.16, device="cpu"):
        self.model = model.to(device)
        self.epsilon = epsilon
        self.target_residue = target_residue
        self.temperature = temperature
        self.device = device
        self.psi_net = SpectralAmplitudeNet(model.config.n_embd).to(device)
        self.opt_theta = AdamW(self.model.parameters(), lr=2e-5)
        self.opt_psi = AdamW(self.psi_net.parameters(), lr=8e-5)
        self.step_count = 0
        self.residue_history = []
        self.energy_history = []

    def _compute_energy(self, inputs, labels):
        outputs = self.model(inputs, labels=labels, output_hidden_states=True)
        logits = outputs.logits
        hidden = outputs.hidden_states[-1]
        shift_logits = logits[..., :-1, :].contiguous()
        shift_labels = labels[..., 1:].contiguous()
        v_theta = F.cross_entropy(shift_logits.view(-1, shift_logits.size(-1)), shift_labels.view(-1), reduction='none').view(shift_labels.shape)

        hidden.requires_grad_(True)
        psi_raw = self.psi_net(hidden)
        psi = F.normalize(psi_raw.view(-1), p=2, dim=0).view(psi_raw.shape)
        psi = psi[..., :-1, 0]

        kinetic = torch.tensor(0.0, device=self.device, requires_grad=True)
        if psi.requires_grad:
            grad_psi = torch.autograd.grad(psi.sum(), hidden, create_graph=True, retain_graph=True, allow_unused=True)[0]
            if grad_psi is not None:
                kinetic = self.epsilon * torch.sum(grad_psi ** 2)

        potential = torch.sum((psi ** 2) * v_theta)
        return kinetic + potential, v_theta.mean().item(), psi.detach()

    def step(self, inputs, labels):
        inputs, labels = inputs.to(self.device), labels.to(self.device)
        self.step_count += 1

        # Phase 1: Update ψ
        for p in self.model.parameters(): p.requires_grad = False
        self.opt_psi.zero_grad()
        energy_psi, _, _ = self._compute_energy(inputs, labels)
        energy_psi.backward()
        self.opt_psi.step()

        # Phase 2: Update θ
        for p in self.model.parameters(): p.requires_grad = True
        for p in self.psi_net.parameters(): p.requires_grad = False
        self.opt_theta.zero_grad()
        energy_theta, mean_v, psi = self._compute_energy(inputs, labels)
        energy_theta.backward()
        self.opt_theta.step()
        for p in self.psi_net.parameters(): p.requires_grad = True

        with torch.no_grad():
            normalized = energy_theta.item() / (mean_v + 1e-8)
            residue = np.exp(-normalized * self.temperature)
            self.residue_history.append(residue)
            self.energy_history.append(energy_theta.item())

            status = "STABLE SPECTRUM" if residue >= self.target_residue - 0.018 else f"DAMPING ({max(0.85, residue / self.target_residue):.3f})"
            print(f"Step {self.step_count:03d} | Energy {energy_theta.item():.4f} | Residue {residue:.5f} | Status: {status}")

        return energy_theta.item(), residue

optimizer = SpectralVariationalOptimizer(model, device=device)

batch_size, seq_len = 2, 64
dummy_input = torch.randint(0, config.vocab_size, (batch_size, seq_len), device=device)
dummy_labels = dummy_input.clone()

print("Running Spectral 350 steps...")
for i in range(350):
    optimizer.step(dummy_input, dummy_labels)

np.save('spectral_residue.npy', np.array(optimizer.residue_history))
np.save('spectral_energy.npy', np.array(optimizer.energy_history))
print("Spectral data saved.\n")

# ===================== ADAM =====================
print("Running AdamW Baseline 350 steps...")

model = AutoModelForCausalLM.from_config(config).to(device)
opt = AdamW(model.parameters(), lr=5e-5)
adam_loss = []

for step in range(350):
    model.train()
    opt.zero_grad()
    outputs = model(dummy_input, labels=dummy_labels)
    loss = outputs.loss
    loss.backward()
    opt.step()
    adam_loss.append(loss.item())

    if step % 50 == 0 or step < 10 or step > 340:
        print(f"Adam Step {step+1:03d} | Loss {loss.item():.4f}")

np.save('adam_loss.npy', np.array(adam_loss))
print("Adam data saved.\n")

# ===================== PLOT =====================
print("Generating comparison plot...")

spectral_residue = np.load('spectral_residue.npy')
spectral_energy  = np.load('spectral_energy.npy')
adam_loss        = np.load('adam_loss.npy')
steps = list(range(1, 351))

fig, ax1 = plt.subplots(figsize=(11, 6.8))

ax1.set_xlabel('Optimization Step', fontsize=12)
ax1.set_ylabel('Spectral Residue $\\mathcal{R}$', color='tab:blue', fontsize=12)
ax1.plot(steps, spectral_residue, color='tab:blue', linewidth=2.8, label='Spectral Residue $\\mathcal{R}$')
ax1.tick_params(axis='y', labelcolor='tab:blue')
ax1.set_ylim(0.80, 1.005)
ax1.axhline(y=0.9895, color='gray', linestyle='--', alpha=0.8, label='Target Attractor (0.9895)')

ax2 = ax1.twinx()
ax2.set_ylabel('Energy / Loss', color='tab:red', fontsize=12)
ax2.plot(steps, spectral_energy, color='tab:red', linewidth=2.3, label='Spectral Energy $\\mathcal{E}$')
ax2.plot(steps, adam_loss, color='tab:orange', linewidth=2.2, linestyle='--', label='AdamW Loss')
ax2.tick_params(axis='y', labelcolor='tab:red')

plt.title('Spectral Variational Optimizer vs Classical AdamW\n'
          'Residue Convergence to Attractor and Energy Descent (350 steps)', fontsize=14, pad=25)

ax1.grid(True, alpha=0.3)

lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, loc='lower right')

plt.tight_layout()
plt.savefig('spectral_vs_adam_comparison.png', dpi=300, bbox_inches='tight')
plt.show()

print("\n✅ DONE! Plot saved as 'spectral_vs_adam_comparison.png'")
print("   Use in LaTeX: \\includegraphics[width=0.95\\textwidth]{spectral_vs_adam_comparison.png}")



# (base) brendanlynch@Brendans-Laptop gradientDescent % python runandplotComparison.py
# === Starting Full Comparison Run ===

# Running Spectral Variational Optimizer...
# Running Spectral 350 steps...
# `loss_type=None` was set in the config but it is unrecognized. Using the default loss: `ForCausalLMLoss`.
# Step 001 | Energy 10.6913 | Residue 0.85473 | Status: DAMPING (0.864)
# Step 002 | Energy 10.3209 | Residue 0.85716 | Status: DAMPING (0.866)
# Step 003 | Energy 9.6923 | Residue 0.86382 | Status: DAMPING (0.873)
# Step 004 | Energy 9.7207 | Residue 0.86086 | Status: DAMPING (0.870)
# Step 005 | Energy 8.5691 | Residue 0.87619 | Status: DAMPING (0.885)
# Step 006 | Energy 8.0361 | Residue 0.88333 | Status: DAMPING (0.893)
# Step 007 | Energy 7.3868 | Residue 0.89185 | Status: DAMPING (0.901)
# Step 008 | Energy 5.6794 | Residue 0.91540 | Status: DAMPING (0.925)
# Step 009 | Energy 4.4882 | Residue 0.93222 | Status: DAMPING (0.942)
# Step 010 | Energy 4.4242 | Residue 0.93312 | Status: DAMPING (0.943)
# Step 011 | Energy 5.1464 | Residue 0.92247 | Status: DAMPING (0.932)
# Step 012 | Energy 3.4174 | Residue 0.94785 | Status: DAMPING (0.958)
# Step 013 | Energy 3.2811 | Residue 0.94980 | Status: DAMPING (0.960)
# Step 014 | Energy 1.9350 | Residue 0.97021 | Status: DAMPING (0.981)
# Step 015 | Energy 3.2702 | Residue 0.94979 | Status: DAMPING (0.960)
# Step 016 | Energy 1.2245 | Residue 0.98103 | Status: STABLE SPECTRUM
# Step 017 | Energy 1.6609 | Residue 0.97421 | Status: STABLE SPECTRUM
# Step 018 | Energy 1.1094 | Residue 0.98282 | Status: STABLE SPECTRUM
# Step 019 | Energy 1.7945 | Residue 0.97237 | Status: STABLE SPECTRUM
# Step 020 | Energy 0.7817 | Residue 0.98787 | Status: STABLE SPECTRUM
# Step 021 | Energy 0.5876 | Residue 0.99082 | Status: STABLE SPECTRUM
# Step 022 | Energy 0.4971 | Residue 0.99226 | Status: STABLE SPECTRUM
# Step 023 | Energy 0.6577 | Residue 0.98977 | Status: STABLE SPECTRUM
# Step 024 | Energy 0.5247 | Residue 0.99185 | Status: STABLE SPECTRUM
# Step 025 | Energy 0.6459 | Residue 0.99000 | Status: STABLE SPECTRUM
# Step 026 | Energy 0.3860 | Residue 0.99402 | Status: STABLE SPECTRUM
# Step 027 | Energy 0.4901 | Residue 0.99243 | Status: STABLE SPECTRUM
# Step 028 | Energy 0.6211 | Residue 0.99044 | Status: STABLE SPECTRUM
# Step 029 | Energy 0.5516 | Residue 0.99152 | Status: STABLE SPECTRUM
# Step 030 | Energy 0.7385 | Residue 0.98869 | Status: STABLE SPECTRUM
# Step 031 | Energy 1.3933 | Residue 0.97884 | Status: STABLE SPECTRUM
# Step 032 | Energy 1.1805 | Residue 0.98214 | Status: STABLE SPECTRUM
# Step 033 | Energy 1.9692 | Residue 0.97033 | Status: DAMPING (0.981)
# Step 034 | Energy 1.6533 | Residue 0.97517 | Status: STABLE SPECTRUM
# Step 035 | Energy 4.1334 | Residue 0.93923 | Status: DAMPING (0.949)
# Step 036 | Energy 1.6192 | Residue 0.97571 | Status: STABLE SPECTRUM
# Step 037 | Energy 3.2796 | Residue 0.95148 | Status: DAMPING (0.962)
# Step 038 | Energy 1.4530 | Residue 0.97828 | Status: STABLE SPECTRUM
# Step 039 | Energy 2.9795 | Residue 0.95599 | Status: DAMPING (0.966)
# Step 040 | Energy 1.7454 | Residue 0.97398 | Status: STABLE SPECTRUM
# Step 041 | Energy 2.8450 | Residue 0.95824 | Status: DAMPING (0.968)
# Step 042 | Energy 1.7105 | Residue 0.97463 | Status: STABLE SPECTRUM
# Step 043 | Energy 4.8054 | Residue 0.93058 | Status: DAMPING (0.940)
# Step 044 | Energy 1.6775 | Residue 0.97526 | Status: STABLE SPECTRUM
# Step 045 | Energy 3.2258 | Residue 0.95305 | Status: DAMPING (0.963)
# Step 046 | Energy 4.4230 | Residue 0.93612 | Status: DAMPING (0.946)
# Step 047 | Energy 1.4978 | Residue 0.97793 | Status: STABLE SPECTRUM
# Step 048 | Energy 1.8397 | Residue 0.97310 | Status: STABLE SPECTRUM
# Step 049 | Energy 1.7754 | Residue 0.97405 | Status: STABLE SPECTRUM
# Step 050 | Energy 1.1874 | Residue 0.98261 | Status: STABLE SPECTRUM
# Step 051 | Energy 2.3433 | Residue 0.96590 | Status: DAMPING (0.976)
# Step 052 | Energy 1.2526 | Residue 0.98163 | Status: STABLE SPECTRUM
# Step 053 | Energy 1.1761 | Residue 0.98277 | Status: STABLE SPECTRUM
# Step 054 | Energy 0.9801 | Residue 0.98564 | Status: STABLE SPECTRUM
# Step 055 | Energy 1.8491 | Residue 0.97308 | Status: STABLE SPECTRUM
# Step 056 | Energy 2.0004 | Residue 0.97087 | Status: DAMPING (0.981)
# Step 057 | Energy 0.8030 | Residue 0.98824 | Status: STABLE SPECTRUM
# Step 058 | Energy 2.7356 | Residue 0.96057 | Status: DAMPING (0.971)
# Step 059 | Energy 0.8527 | Residue 0.98752 | Status: STABLE SPECTRUM
# Step 060 | Energy 2.9832 | Residue 0.95713 | Status: DAMPING (0.967)
# Step 061 | Energy 2.9038 | Residue 0.95818 | Status: DAMPING (0.968)
# Step 062 | Energy 0.5483 | Residue 0.99201 | Status: STABLE SPECTRUM
# Step 063 | Energy 2.5054 | Residue 0.96404 | Status: DAMPING (0.974)
# Step 064 | Energy 0.8828 | Residue 0.98715 | Status: STABLE SPECTRUM
# Step 065 | Energy 1.9149 | Residue 0.97230 | Status: STABLE SPECTRUM
# Step 066 | Energy 1.6783 | Residue 0.97573 | Status: STABLE SPECTRUM
# Step 067 | Energy 1.3042 | Residue 0.98108 | Status: STABLE SPECTRUM
# Step 068 | Energy 0.6170 | Residue 0.99103 | Status: STABLE SPECTRUM
# Step 069 | Energy 0.8845 | Residue 0.98719 | Status: STABLE SPECTRUM
# Step 070 | Energy 1.0304 | Residue 0.98505 | Status: STABLE SPECTRUM
# Step 071 | Energy 1.7385 | Residue 0.97501 | Status: STABLE SPECTRUM
# Step 072 | Energy 1.5369 | Residue 0.97787 | Status: STABLE SPECTRUM
# Step 073 | Energy 1.2302 | Residue 0.98225 | Status: STABLE SPECTRUM
# Step 074 | Energy 1.2082 | Residue 0.98264 | Status: STABLE SPECTRUM
# Step 075 | Energy 1.0168 | Residue 0.98536 | Status: STABLE SPECTRUM
# Step 076 | Energy 2.0525 | Residue 0.97058 | Status: DAMPING (0.981)
# Step 077 | Energy 3.0551 | Residue 0.95658 | Status: DAMPING (0.967)
# Step 078 | Energy 1.5851 | Residue 0.97722 | Status: STABLE SPECTRUM
# Step 079 | Energy 3.8247 | Residue 0.94601 | Status: DAMPING (0.956)
# Step 080 | Energy 2.6762 | Residue 0.96184 | Status: DAMPING (0.972)
# Step 081 | Energy 1.3624 | Residue 0.98041 | Status: STABLE SPECTRUM
# Step 082 | Energy 3.4727 | Residue 0.95090 | Status: DAMPING (0.961)
# Step 083 | Energy 1.4922 | Residue 0.97859 | Status: STABLE SPECTRUM
# Step 084 | Energy 2.4422 | Residue 0.96520 | Status: DAMPING (0.975)
# Step 085 | Energy 0.9916 | Residue 0.98570 | Status: STABLE SPECTRUM
# Step 086 | Energy 0.4863 | Residue 0.99296 | Status: STABLE SPECTRUM
# Step 087 | Energy 0.9059 | Residue 0.98697 | Status: STABLE SPECTRUM
# Step 088 | Energy 1.1548 | Residue 0.98334 | Status: STABLE SPECTRUM
# Step 089 | Energy 0.5328 | Residue 0.99228 | Status: STABLE SPECTRUM
# Step 090 | Energy 0.7760 | Residue 0.98880 | Status: STABLE SPECTRUM
# Step 091 | Energy 0.6517 | Residue 0.99056 | Status: STABLE SPECTRUM
# Step 092 | Energy 0.6411 | Residue 0.99073 | Status: STABLE SPECTRUM
# Step 093 | Energy 1.6038 | Residue 0.97698 | Status: STABLE SPECTRUM
# Step 094 | Energy 1.2301 | Residue 0.98227 | Status: STABLE SPECTRUM
# Step 095 | Energy 2.5136 | Residue 0.96403 | Status: DAMPING (0.974)
# Step 096 | Energy 0.9007 | Residue 0.98700 | Status: STABLE SPECTRUM
# Step 097 | Energy 1.2180 | Residue 0.98245 | Status: STABLE SPECTRUM
# Step 098 | Energy 2.0834 | Residue 0.97018 | Status: DAMPING (0.980)
# Step 099 | Energy 1.4720 | Residue 0.97881 | Status: STABLE SPECTRUM
# Step 100 | Energy 2.3042 | Residue 0.96698 | Status: DAMPING (0.977)
# Step 101 | Energy 0.9614 | Residue 0.98611 | Status: STABLE SPECTRUM
# Step 102 | Energy 1.8831 | Residue 0.97292 | Status: STABLE SPECTRUM
# Step 103 | Energy 0.6550 | Residue 0.99052 | Status: STABLE SPECTRUM
# Step 104 | Energy 2.2896 | Residue 0.96714 | Status: DAMPING (0.977)
# Step 105 | Energy 1.4523 | Residue 0.97906 | Status: STABLE SPECTRUM
# Step 106 | Energy 1.8183 | Residue 0.97379 | Status: STABLE SPECTRUM
# Step 107 | Energy 1.4527 | Residue 0.97901 | Status: STABLE SPECTRUM
# Step 108 | Energy 0.8603 | Residue 0.98752 | Status: STABLE SPECTRUM
# Step 109 | Energy 1.0766 | Residue 0.98442 | Status: STABLE SPECTRUM
# Step 110 | Energy 0.9669 | Residue 0.98596 | Status: STABLE SPECTRUM
# Step 111 | Energy 1.2720 | Residue 0.98157 | Status: STABLE SPECTRUM
# Step 112 | Energy 1.2370 | Residue 0.98207 | Status: STABLE SPECTRUM
# Step 113 | Energy 3.4778 | Residue 0.95036 | Status: DAMPING (0.960)
# Step 114 | Energy 1.8417 | Residue 0.97340 | Status: STABLE SPECTRUM
# Step 115 | Energy 1.8765 | Residue 0.97288 | Status: STABLE SPECTRUM
# Step 116 | Energy 1.6545 | Residue 0.97604 | Status: STABLE SPECTRUM
# Step 117 | Energy 3.9168 | Residue 0.94431 | Status: DAMPING (0.954)
# Step 118 | Energy 2.8491 | Residue 0.95901 | Status: DAMPING (0.969)
# Step 119 | Energy 1.3646 | Residue 0.98016 | Status: STABLE SPECTRUM
# Step 120 | Energy 1.1877 | Residue 0.98268 | Status: STABLE SPECTRUM
# Step 121 | Energy 1.3907 | Residue 0.97979 | Status: STABLE SPECTRUM
# Step 122 | Energy 1.1602 | Residue 0.98308 | Status: STABLE SPECTRUM
# Step 123 | Energy 0.8254 | Residue 0.98791 | Status: STABLE SPECTRUM
# Step 124 | Energy 1.4583 | Residue 0.97873 | Status: STABLE SPECTRUM
# Step 125 | Energy 0.8801 | Residue 0.98707 | Status: STABLE SPECTRUM
# Step 126 | Energy 1.0918 | Residue 0.98400 | Status: STABLE SPECTRUM
# Step 127 | Energy 0.4562 | Residue 0.99330 | Status: STABLE SPECTRUM
# Step 128 | Energy 1.1467 | Residue 0.98321 | Status: STABLE SPECTRUM
# Step 129 | Energy 0.6216 | Residue 0.99087 | Status: STABLE SPECTRUM
# Step 130 | Energy 1.1932 | Residue 0.98252 | Status: STABLE SPECTRUM
# Step 131 | Energy 1.0079 | Residue 0.98518 | Status: STABLE SPECTRUM
# Step 132 | Energy 0.8808 | Residue 0.98708 | Status: STABLE SPECTRUM
# Step 133 | Energy 0.5334 | Residue 0.99213 | Status: STABLE SPECTRUM
# Step 134 | Energy 1.2357 | Residue 0.98192 | Status: STABLE SPECTRUM
# Step 135 | Energy 0.9493 | Residue 0.98605 | Status: STABLE SPECTRUM
# Step 136 | Energy 1.0447 | Residue 0.98464 | Status: STABLE SPECTRUM
# Step 137 | Energy 1.0700 | Residue 0.98423 | Status: STABLE SPECTRUM
# Step 138 | Energy 2.0045 | Residue 0.97076 | Status: DAMPING (0.981)
# Step 139 | Energy 1.1782 | Residue 0.98266 | Status: STABLE SPECTRUM
# Step 140 | Energy 1.5093 | Residue 0.97793 | Status: STABLE SPECTRUM
# Step 141 | Energy 0.9221 | Residue 0.98639 | Status: STABLE SPECTRUM
# Step 142 | Energy 1.6590 | Residue 0.97574 | Status: STABLE SPECTRUM
# Step 143 | Energy 0.7597 | Residue 0.98882 | Status: STABLE SPECTRUM
# Step 144 | Energy 0.9701 | Residue 0.98572 | Status: STABLE SPECTRUM
# Step 145 | Energy 1.6396 | Residue 0.97599 | Status: STABLE SPECTRUM
# Step 146 | Energy 2.0013 | Residue 0.97078 | Status: DAMPING (0.981)
# Step 147 | Energy 2.7256 | Residue 0.96040 | Status: DAMPING (0.971)
# Step 148 | Energy 1.5587 | Residue 0.97714 | Status: STABLE SPECTRUM
# Step 149 | Energy 1.4593 | Residue 0.97863 | Status: STABLE SPECTRUM
# Step 150 | Energy 1.4274 | Residue 0.97904 | Status: STABLE SPECTRUM
# Step 151 | Energy 1.0492 | Residue 0.98458 | Status: STABLE SPECTRUM
# Step 152 | Energy 1.4530 | Residue 0.97859 | Status: STABLE SPECTRUM
# Step 153 | Energy 1.7504 | Residue 0.97433 | Status: STABLE SPECTRUM
# Step 154 | Energy 1.8477 | Residue 0.97286 | Status: STABLE SPECTRUM
# Step 155 | Energy 1.0561 | Residue 0.98445 | Status: STABLE SPECTRUM
# Step 156 | Energy 1.3351 | Residue 0.98031 | Status: STABLE SPECTRUM
# Step 157 | Energy 1.9482 | Residue 0.97148 | Status: DAMPING (0.982)
# Step 158 | Energy 1.0028 | Residue 0.98524 | Status: STABLE SPECTRUM
# Step 159 | Energy 1.5473 | Residue 0.97725 | Status: STABLE SPECTRUM
# Step 160 | Energy 2.3992 | Residue 0.96502 | Status: DAMPING (0.975)
# Step 161 | Energy 2.8366 | Residue 0.95863 | Status: DAMPING (0.969)
# Step 162 | Energy 1.6262 | Residue 0.97608 | Status: STABLE SPECTRUM
# Step 163 | Energy 1.3737 | Residue 0.97980 | Status: STABLE SPECTRUM
# Step 164 | Energy 4.9314 | Residue 0.92925 | Status: DAMPING (0.939)
# Step 165 | Energy 1.8078 | Residue 0.97342 | Status: STABLE SPECTRUM
# Step 166 | Energy 2.2651 | Residue 0.96688 | Status: DAMPING (0.977)
# Step 167 | Energy 1.0101 | Residue 0.98508 | Status: STABLE SPECTRUM
# Step 168 | Energy 1.2697 | Residue 0.98130 | Status: STABLE SPECTRUM
# Step 169 | Energy 2.4519 | Residue 0.96419 | Status: DAMPING (0.974)
# Step 170 | Energy 1.2192 | Residue 0.98199 | Status: STABLE SPECTRUM
# Step 171 | Energy 4.3177 | Residue 0.93766 | Status: DAMPING (0.948)
# Step 172 | Energy 1.5309 | Residue 0.97740 | Status: STABLE SPECTRUM
# Step 173 | Energy 2.4156 | Residue 0.96462 | Status: DAMPING (0.975)
# Step 174 | Energy 1.0281 | Residue 0.98478 | Status: STABLE SPECTRUM
# Step 175 | Energy 4.0710 | Residue 0.94105 | Status: DAMPING (0.951)
# Step 176 | Energy 0.8933 | Residue 0.98674 | Status: STABLE SPECTRUM
# Step 177 | Energy 1.9066 | Residue 0.97193 | Status: STABLE SPECTRUM
# Step 178 | Energy 1.6527 | Residue 0.97554 | Status: STABLE SPECTRUM
# Step 179 | Energy 1.8463 | Residue 0.97277 | Status: STABLE SPECTRUM
# Step 180 | Energy 0.7939 | Residue 0.98818 | Status: STABLE SPECTRUM
# Step 181 | Energy 1.2824 | Residue 0.98096 | Status: STABLE SPECTRUM
# Step 182 | Energy 1.2714 | Residue 0.98111 | Status: STABLE SPECTRUM
# Step 183 | Energy 0.6464 | Residue 0.99038 | Status: STABLE SPECTRUM
# Step 184 | Energy 1.1535 | Residue 0.98283 | Status: STABLE SPECTRUM
# Step 185 | Energy 0.9536 | Residue 0.98575 | Status: STABLE SPECTRUM
# Step 186 | Energy 2.3253 | Residue 0.96573 | Status: DAMPING (0.976)
# Step 187 | Energy 1.0545 | Residue 0.98433 | Status: STABLE SPECTRUM
# Step 188 | Energy 1.3292 | Residue 0.98027 | Status: STABLE SPECTRUM
# Step 189 | Energy 1.8178 | Residue 0.97305 | Status: STABLE SPECTRUM
# Step 190 | Energy 1.2303 | Residue 0.98172 | Status: STABLE SPECTRUM
# Step 191 | Energy 1.6371 | Residue 0.97574 | Status: STABLE SPECTRUM
# Step 192 | Energy 0.9887 | Residue 0.98527 | Status: STABLE SPECTRUM
# Step 193 | Energy 0.7918 | Residue 0.98820 | Status: STABLE SPECTRUM
# Step 194 | Energy 0.6421 | Residue 0.99040 | Status: STABLE SPECTRUM
# Step 195 | Energy 0.7558 | Residue 0.98871 | Status: STABLE SPECTRUM
# Step 196 | Energy 1.4412 | Residue 0.97862 | Status: STABLE SPECTRUM
# Step 197 | Energy 1.1919 | Residue 0.98229 | Status: STABLE SPECTRUM
# Step 198 | Energy 2.4056 | Residue 0.96453 | Status: DAMPING (0.975)
# Step 199 | Energy 4.7722 | Residue 0.93067 | Status: DAMPING (0.941)
# Step 200 | Energy 5.3429 | Residue 0.92285 | Status: DAMPING (0.933)
# Step 201 | Energy 2.6987 | Residue 0.96030 | Status: DAMPING (0.970)
# Step 202 | Energy 3.6419 | Residue 0.94673 | Status: DAMPING (0.957)
# Step 203 | Energy 4.1917 | Residue 0.93912 | Status: DAMPING (0.949)
# Step 204 | Energy 1.6410 | Residue 0.97556 | Status: STABLE SPECTRUM
# Step 205 | Energy 2.9207 | Residue 0.95698 | Status: DAMPING (0.967)
# Step 206 | Energy 0.6775 | Residue 0.98985 | Status: STABLE SPECTRUM
# Step 207 | Energy 0.7899 | Residue 0.98813 | Status: STABLE SPECTRUM
# Step 208 | Energy 1.3233 | Residue 0.98024 | Status: STABLE SPECTRUM
# Step 209 | Energy 0.8271 | Residue 0.98756 | Status: STABLE SPECTRUM
# Step 210 | Energy 1.3285 | Residue 0.98009 | Status: STABLE SPECTRUM
# Step 211 | Energy 0.5653 | Residue 0.99147 | Status: STABLE SPECTRUM
# Step 212 | Energy 0.6569 | Residue 0.99010 | Status: STABLE SPECTRUM
# Step 213 | Energy 0.6060 | Residue 0.99084 | Status: STABLE SPECTRUM
# Step 214 | Energy 0.4052 | Residue 0.99387 | Status: STABLE SPECTRUM
# Step 215 | Energy 0.4904 | Residue 0.99259 | Status: STABLE SPECTRUM
# Step 216 | Energy 0.3423 | Residue 0.99482 | Status: STABLE SPECTRUM
# Step 217 | Energy 0.3726 | Residue 0.99434 | Status: STABLE SPECTRUM
# Step 218 | Energy 0.5340 | Residue 0.99194 | Status: STABLE SPECTRUM
# Step 219 | Energy 0.4766 | Residue 0.99280 | Status: STABLE SPECTRUM
# Step 220 | Energy 0.3487 | Residue 0.99473 | Status: STABLE SPECTRUM
# Step 221 | Energy 0.4548 | Residue 0.99312 | Status: STABLE SPECTRUM
# Step 222 | Energy 0.3256 | Residue 0.99507 | Status: STABLE SPECTRUM
# Step 223 | Energy 0.3941 | Residue 0.99404 | Status: STABLE SPECTRUM
# Step 224 | Energy 0.5271 | Residue 0.99204 | Status: STABLE SPECTRUM
# Step 225 | Energy 0.4452 | Residue 0.99329 | Status: STABLE SPECTRUM
# Step 226 | Energy 0.7127 | Residue 0.98927 | Status: STABLE SPECTRUM
# Step 227 | Energy 0.5470 | Residue 0.99176 | Status: STABLE SPECTRUM
# Step 228 | Energy 0.5470 | Residue 0.99176 | Status: STABLE SPECTRUM
# Step 229 | Energy 1.0180 | Residue 0.98468 | Status: STABLE SPECTRUM
# Step 230 | Energy 0.8143 | Residue 0.98779 | Status: STABLE SPECTRUM
# Step 231 | Energy 0.9104 | Residue 0.98632 | Status: STABLE SPECTRUM
# Step 232 | Energy 1.4927 | Residue 0.97776 | Status: STABLE SPECTRUM
# Step 233 | Energy 1.8551 | Residue 0.97247 | Status: STABLE SPECTRUM
# Step 234 | Energy 0.9077 | Residue 0.98641 | Status: STABLE SPECTRUM
# Step 235 | Energy 3.1405 | Residue 0.95378 | Status: DAMPING (0.964)
# Step 236 | Energy 1.5979 | Residue 0.97623 | Status: STABLE SPECTRUM
# Step 237 | Energy 4.1047 | Residue 0.94017 | Status: DAMPING (0.950)
# Step 238 | Energy 1.2005 | Residue 0.98213 | Status: STABLE SPECTRUM
# Step 239 | Energy 5.1244 | Residue 0.92562 | Status: DAMPING (0.935)
# Step 240 | Energy 5.5751 | Residue 0.91930 | Status: DAMPING (0.929)
# Step 241 | Energy 3.1022 | Residue 0.95440 | Status: DAMPING (0.965)
# Step 242 | Energy 2.1579 | Residue 0.96811 | Status: DAMPING (0.978)
# Step 243 | Energy 2.6964 | Residue 0.96022 | Status: DAMPING (0.970)
# Step 244 | Energy 0.8576 | Residue 0.98718 | Status: STABLE SPECTRUM
# Step 245 | Energy 2.5492 | Residue 0.96219 | Status: DAMPING (0.972)
# Step 246 | Energy 0.6739 | Residue 0.98987 | Status: STABLE SPECTRUM
# Step 247 | Energy 1.8798 | Residue 0.97197 | Status: STABLE SPECTRUM
# Step 248 | Energy 0.7453 | Residue 0.98880 | Status: STABLE SPECTRUM
# Step 249 | Energy 0.7574 | Residue 0.98860 | Status: STABLE SPECTRUM
# Step 250 | Energy 1.1063 | Residue 0.98336 | Status: STABLE SPECTRUM
# Step 251 | Energy 0.3162 | Residue 0.99522 | Status: STABLE SPECTRUM
# Step 252 | Energy 0.6466 | Residue 0.99028 | Status: STABLE SPECTRUM
# Step 253 | Energy 0.4170 | Residue 0.99368 | Status: STABLE SPECTRUM
# Step 254 | Energy 0.5405 | Residue 0.99181 | Status: STABLE SPECTRUM
# Step 255 | Energy 0.4776 | Residue 0.99277 | Status: STABLE SPECTRUM
# Step 256 | Energy 0.3681 | Residue 0.99443 | Status: STABLE SPECTRUM
# Step 257 | Energy 0.5757 | Residue 0.99130 | Status: STABLE SPECTRUM
# Step 258 | Energy 0.4060 | Residue 0.99386 | Status: STABLE SPECTRUM
# Step 259 | Energy 0.4354 | Residue 0.99343 | Status: STABLE SPECTRUM
# Step 260 | Energy 0.4315 | Residue 0.99345 | Status: STABLE SPECTRUM
# Step 261 | Energy 0.2826 | Residue 0.99572 | Status: STABLE SPECTRUM
# Step 262 | Energy 0.3714 | Residue 0.99437 | Status: STABLE SPECTRUM
# Step 263 | Energy 0.3446 | Residue 0.99480 | Status: STABLE SPECTRUM
# Step 264 | Energy 0.3885 | Residue 0.99412 | Status: STABLE SPECTRUM
# Step 265 | Energy 0.2958 | Residue 0.99553 | Status: STABLE SPECTRUM
# Step 266 | Energy 0.3925 | Residue 0.99406 | Status: STABLE SPECTRUM
# Step 267 | Energy 0.3443 | Residue 0.99481 | Status: STABLE SPECTRUM
# Step 268 | Energy 0.4358 | Residue 0.99342 | Status: STABLE SPECTRUM
# Step 269 | Energy 0.6629 | Residue 0.99005 | Status: STABLE SPECTRUM
# Step 270 | Energy 0.4993 | Residue 0.99249 | Status: STABLE SPECTRUM
# Step 271 | Energy 1.1387 | Residue 0.98302 | Status: STABLE SPECTRUM
# Step 272 | Energy 1.2454 | Residue 0.98138 | Status: STABLE SPECTRUM
# Step 273 | Energy 0.8332 | Residue 0.98756 | Status: STABLE SPECTRUM
# Step 274 | Energy 0.8142 | Residue 0.98784 | Status: STABLE SPECTRUM
# Step 275 | Energy 0.5373 | Residue 0.99195 | Status: STABLE SPECTRUM
# Step 276 | Energy 1.1425 | Residue 0.98303 | Status: STABLE SPECTRUM
# Step 277 | Energy 1.4075 | Residue 0.97913 | Status: STABLE SPECTRUM
# Step 278 | Energy 1.8494 | Residue 0.97268 | Status: STABLE SPECTRUM
# Step 279 | Energy 1.2311 | Residue 0.98174 | Status: STABLE SPECTRUM
# Step 280 | Energy 2.8065 | Residue 0.95905 | Status: DAMPING (0.969)
# Step 281 | Energy 2.3116 | Residue 0.96607 | Status: DAMPING (0.976)
# Step 282 | Energy 1.1080 | Residue 0.98357 | Status: STABLE SPECTRUM
# Step 283 | Energy 2.1603 | Residue 0.96830 | Status: DAMPING (0.979)
# Step 284 | Energy 1.3404 | Residue 0.98017 | Status: STABLE SPECTRUM
# Step 285 | Energy 1.0195 | Residue 0.98493 | Status: STABLE SPECTRUM
# Step 286 | Energy 1.9792 | Residue 0.97104 | Status: DAMPING (0.981)
# Step 287 | Energy 1.5473 | Residue 0.97725 | Status: STABLE SPECTRUM
# Step 288 | Energy 1.2456 | Residue 0.98165 | Status: STABLE SPECTRUM
# Step 289 | Energy 3.1191 | Residue 0.95476 | Status: DAMPING (0.965)
# Step 290 | Energy 2.1911 | Residue 0.96802 | Status: DAMPING (0.978)
# Step 291 | Energy 1.4394 | Residue 0.97895 | Status: STABLE SPECTRUM
# Step 292 | Energy 3.6516 | Residue 0.94721 | Status: DAMPING (0.957)
# Step 293 | Energy 1.0433 | Residue 0.98468 | Status: STABLE SPECTRUM
# Step 294 | Energy 2.8479 | Residue 0.95859 | Status: DAMPING (0.969)
# Step 295 | Energy 0.8298 | Residue 0.98773 | Status: STABLE SPECTRUM
# Step 296 | Energy 4.0355 | Residue 0.94194 | Status: DAMPING (0.952)
# Step 297 | Energy 1.3931 | Residue 0.97955 | Status: STABLE SPECTRUM
# Step 298 | Energy 1.7773 | Residue 0.97398 | Status: STABLE SPECTRUM
# Step 299 | Energy 2.3645 | Residue 0.96555 | Status: DAMPING (0.976)
# Step 300 | Energy 1.3644 | Residue 0.98004 | Status: STABLE SPECTRUM
# Step 301 | Energy 0.7862 | Residue 0.98841 | Status: STABLE SPECTRUM
# Step 302 | Energy 1.2186 | Residue 0.98211 | Status: STABLE SPECTRUM
# Step 303 | Energy 2.5201 | Residue 0.96325 | Status: DAMPING (0.973)
# Step 304 | Energy 0.9789 | Residue 0.98560 | Status: STABLE SPECTRUM
# Step 305 | Energy 1.1269 | Residue 0.98344 | Status: STABLE SPECTRUM
# Step 306 | Energy 0.8600 | Residue 0.98735 | Status: STABLE SPECTRUM
# Step 307 | Energy 1.5255 | Residue 0.97764 | Status: STABLE SPECTRUM
# Step 308 | Energy 1.3869 | Residue 0.97966 | Status: STABLE SPECTRUM
# Step 309 | Energy 1.5726 | Residue 0.97700 | Status: STABLE SPECTRUM
# Step 310 | Energy 1.7942 | Residue 0.97382 | Status: STABLE SPECTRUM
# Step 311 | Energy 3.4408 | Residue 0.95057 | Status: DAMPING (0.961)
# Step 312 | Energy 0.9201 | Residue 0.98651 | Status: STABLE SPECTRUM
# Step 313 | Energy 4.3645 | Residue 0.93753 | Status: DAMPING (0.947)
# Step 314 | Energy 1.2579 | Residue 0.98159 | Status: STABLE SPECTRUM
# Step 315 | Energy 4.6694 | Residue 0.93328 | Status: DAMPING (0.943)
# Step 316 | Energy 4.7227 | Residue 0.93248 | Status: DAMPING (0.942)
# Step 317 | Energy 1.3106 | Residue 0.98078 | Status: STABLE SPECTRUM
# Step 318 | Energy 5.4346 | Residue 0.92275 | Status: DAMPING (0.933)
# Step 319 | Energy 5.8522 | Residue 0.91703 | Status: DAMPING (0.927)
# Step 320 | Energy 1.8384 | Residue 0.97311 | Status: STABLE SPECTRUM
# Step 321 | Energy 3.7550 | Residue 0.94561 | Status: DAMPING (0.956)
# Step 322 | Energy 4.6999 | Residue 0.93245 | Status: DAMPING (0.942)
# Step 323 | Energy 4.2251 | Residue 0.93888 | Status: DAMPING (0.949)
# Step 324 | Energy 0.9231 | Residue 0.98626 | Status: STABLE SPECTRUM
# Step 325 | Energy 2.3605 | Residue 0.96529 | Status: DAMPING (0.976)
# Step 326 | Energy 3.0038 | Residue 0.95605 | Status: DAMPING (0.966)
# Step 327 | Energy 0.6524 | Residue 0.99024 | Status: STABLE SPECTRUM
# Step 328 | Energy 0.5672 | Residue 0.99152 | Status: STABLE SPECTRUM
# Step 329 | Energy 1.6334 | Residue 0.97576 | Status: STABLE SPECTRUM
# Step 330 | Energy 1.0997 | Residue 0.98354 | Status: STABLE SPECTRUM
# Step 331 | Energy 0.2285 | Residue 0.99655 | Status: STABLE SPECTRUM
# Step 332 | Energy 0.4195 | Residue 0.99370 | Status: STABLE SPECTRUM
# Step 333 | Energy 0.9338 | Residue 0.98600 | Status: STABLE SPECTRUM
# Step 334 | Energy 0.3478 | Residue 0.99475 | Status: STABLE SPECTRUM
# Step 335 | Energy 0.1667 | Residue 0.99748 | Status: STABLE SPECTRUM
# Step 336 | Energy 0.3540 | Residue 0.99465 | Status: STABLE SPECTRUM
# Step 337 | Energy 0.3798 | Residue 0.99427 | Status: STABLE SPECTRUM
# Step 338 | Energy 0.1242 | Residue 0.99811 | Status: STABLE SPECTRUM
# Step 339 | Energy 0.1377 | Residue 0.99791 | Status: STABLE SPECTRUM
# Step 340 | Energy 0.2923 | Residue 0.99558 | Status: STABLE SPECTRUM
# Step 341 | Energy 0.1697 | Residue 0.99742 | Status: STABLE SPECTRUM
# Step 342 | Energy 0.0971 | Residue 0.99852 | Status: STABLE SPECTRUM
# Step 343 | Energy 0.1336 | Residue 0.99797 | Status: STABLE SPECTRUM
# Step 344 | Energy 0.2010 | Residue 0.99694 | Status: STABLE SPECTRUM
# Step 345 | Energy 0.1141 | Residue 0.99826 | Status: STABLE SPECTRUM
# Step 346 | Energy 0.0867 | Residue 0.99868 | Status: STABLE SPECTRUM
# Step 347 | Energy 0.1031 | Residue 0.99843 | Status: STABLE SPECTRUM
# Step 348 | Energy 0.1348 | Residue 0.99794 | Status: STABLE SPECTRUM
# Step 349 | Energy 0.1110 | Residue 0.99831 | Status: STABLE SPECTRUM
# Step 350 | Energy 0.0873 | Residue 0.99867 | Status: STABLE SPECTRUM
# Spectral data saved.

# Running AdamW Baseline 350 steps...
# Adam Step 001 | Loss 10.9659
# Adam Step 002 | Loss 10.1424
# Adam Step 003 | Loss 9.6726
# Adam Step 004 | Loss 9.3175
# Adam Step 005 | Loss 8.9842
# Adam Step 006 | Loss 8.7274
# Adam Step 007 | Loss 8.4929
# Adam Step 008 | Loss 8.2057
# Adam Step 009 | Loss 8.0548
# Adam Step 010 | Loss 7.7959
# Adam Step 051 | Loss 0.9951
# Adam Step 101 | Loss 0.1215
# Adam Step 151 | Loss 0.0589
# Adam Step 201 | Loss 0.0407
# Adam Step 251 | Loss 0.0318
# Adam Step 301 | Loss 0.0239
# Adam Step 342 | Loss 0.0220
# Adam Step 343 | Loss 0.0209
# Adam Step 344 | Loss 0.0209
# Adam Step 345 | Loss 0.0215
# Adam Step 346 | Loss 0.0211
# Adam Step 347 | Loss 0.0209
# Adam Step 348 | Loss 0.0212
# Adam Step 349 | Loss 0.0203
# Adam Step 350 | Loss 0.0204
# Adam data saved.

# Generating comparison plot...

# ✅ DONE! Plot saved as 'spectral_vs_adam_comparison.png'
#    Use in LaTeX: \includegraphics[width=0.95\textwidth]{spectral_vs_adam_comparison.png}
# (base) brendanlynch@Brendans-Laptop gradientDescent % 