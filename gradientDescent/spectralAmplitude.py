"""
Spectral Variational Optimizer - 350 Steps Attractor Push
========================================================

Extended run + final tuning to hit the high-residue attractor.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.optim import AdamW
from transformers import AutoModelForCausalLM, AutoConfig
import numpy as np

class SpectralAmplitudeNet(nn.Module):
    def __init__(self, embedding_dim: int, hidden_dim: int = 256):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(embedding_dim, hidden_dim),
            nn.Tanh(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.Tanh(),
            nn.Linear(hidden_dim, 1),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        raw = self.net(x)
        return F.normalize(raw.view(-1), p=2, dim=0).view(raw.shape)


class SpectralVariationalOptimizer:
    def __init__(
        self,
        model,
        epsilon: float = 0.008,
        target_residue: float = 0.9895,
        temperature: float = 0.16,   # Smoother for higher residue
        lr_theta: float = 2e-5,      # Gentler for stability
        lr_psi: float = 8e-5,
        device: str = "cpu"
    ):
        self.model = model.to(device)
        self.epsilon = epsilon
        self.target_residue = target_residue
        self.temperature = temperature
        self.device = device

        self.psi_net = SpectralAmplitudeNet(model.config.n_embd).to(device)

        self.opt_theta = AdamW(self.model.parameters(), lr=lr_theta)
        self.opt_psi   = AdamW(self.psi_net.parameters(), lr=lr_psi)

        self.step_count = 0
        self.residue_history = []
        self.energy_history = []

    def _compute_energy(self, inputs: torch.Tensor, labels: torch.Tensor):
        outputs = self.model(inputs, labels=labels, output_hidden_states=True)
        logits = outputs.logits
        hidden = outputs.hidden_states[-1]

        shift_logits = logits[..., :-1, :].contiguous()
        shift_labels = labels[..., 1:].contiguous()
        v_theta = F.cross_entropy(
            shift_logits.view(-1, shift_logits.size(-1)),
            shift_labels.view(-1),
            reduction='none'
        ).view(shift_labels.shape)

        hidden.requires_grad_(True)
        psi_raw = self.psi_net(hidden)
        psi = F.normalize(psi_raw.view(-1), p=2, dim=0).view(psi_raw.shape)
        psi = psi[..., :-1, 0]

        kinetic = torch.tensor(0.0, device=self.device, requires_grad=True)
        if psi.requires_grad:
            grad_psi = torch.autograd.grad(
                psi.sum(), hidden, create_graph=True, retain_graph=True, allow_unused=True
            )[0]
            if grad_psi is not None:
                kinetic = self.epsilon * torch.sum(grad_psi ** 2)

        potential = torch.sum((psi ** 2) * v_theta)
        total_energy = kinetic + potential

        return total_energy, v_theta.mean().item(), psi.detach()

    def step(self, inputs: torch.Tensor, labels: torch.Tensor):
        inputs, labels = inputs.to(self.device), labels.to(self.device)
        self.step_count += 1

        # Phase 1: Update ψ
        for p in self.model.parameters():
            p.requires_grad = False
        self.opt_psi.zero_grad()
        energy_psi, _, _ = self._compute_energy(inputs, labels)
        energy_psi.backward()
        self.opt_psi.step()

        # Phase 2: Update θ
        for p in self.model.parameters():
            p.requires_grad = True
        for p in self.psi_net.parameters():
            p.requires_grad = False

        self.opt_theta.zero_grad()
        energy_theta, mean_v, psi = self._compute_energy(inputs, labels)
        energy_theta.backward()
        self.opt_theta.step()

        for p in self.psi_net.parameters():
            p.requires_grad = True

        # Spectral Residue
        with torch.no_grad():
            normalized = energy_theta.item() / (mean_v + 1e-8)
            residue = np.exp(-normalized * self.temperature)
            self.residue_history.append(residue)
            self.energy_history.append(energy_theta.item())

            if residue < self.target_residue - 0.018:
                damping = max(0.85, residue / self.target_residue)
                for g in self.opt_theta.param_groups:
                    g['lr'] *= damping
                status = f"DAMPING ({damping:.3f})"
            else:
                status = "STABLE SPECTRUM"

            print(f"Step {self.step_count:03d} | "
                  f"Energy {energy_theta.item():.4f} | "
                  f"Residue {residue:.5f} | "
                  f"Status: {status}")

        return energy_theta.item(), residue

    def is_stable(self, window: int = 50, tolerance: float = 0.008) -> bool:
        if len(self.residue_history) < window:
            return False
        recent = np.array(self.residue_history[-window:])
        return abs(recent.mean() - self.target_residue) < tolerance


if __name__ == "__main__":
    print("Initializing Spectral Variational Optimizer...\n")

    config = AutoConfig.from_pretrained("gpt2")
    model = AutoModelForCausalLM.from_config(config)

    device = "cuda" if torch.cuda.is_available() else "cpu"

    optimizer = SpectralVariationalOptimizer(
        model=model,
        epsilon=0.008,
        target_residue=0.9895,
        temperature=0.16,
        device=device
    )

    batch_size, seq_len = 2, 64
    dummy_input = torch.randint(0, config.vocab_size, (batch_size, seq_len), device=device)
    dummy_labels = dummy_input.clone()

    np.save('spectral_residue.npy', np.array(optimizer.residue_history))
    np.save('spectral_energy.npy', np.array(optimizer.energy_history))

    print(f"Starting training on {device}...\n" + "-"*90)

    for i in range(350):
        energy, residue = optimizer.step(dummy_input, dummy_labels)

    print("-"*90)
    if optimizer.is_stable():
        print("SUCCESS: Reached stable spectral regime near target residue (0.9895).")
    else:
        print("WARNING: Did not fully reach target attractor within tolerance.")
    print(f"Final residue: {optimizer.residue_history[-1]:.5f}")
    print(f"Mean recent residue (last 50 steps): {np.mean(optimizer.residue_history[-50:]):.5f}")
    print("Run complete.")


# (base) brendanlynch@Brendans-Laptop gradientDescent % python spectralAmplitude.py
# Initializing Spectral Variational Optimizer...

# Starting training on cpu...
# ------------------------------------------------------------------------------------------
# `loss_type=None` was set in the config but it is unrecognized. Using the default loss: `ForCausalLMLoss`.
# Step 001 | Energy 10.7653 | Residue 0.85450 | Status: DAMPING (0.864)
# Step 002 | Energy 10.4233 | Residue 0.85696 | Status: DAMPING (0.866)
# Step 003 | Energy 9.4048 | Residue 0.86865 | Status: DAMPING (0.878)
# Step 004 | Energy 8.8473 | Residue 0.87549 | Status: DAMPING (0.885)
# Step 005 | Energy 7.7431 | Residue 0.88913 | Status: DAMPING (0.899)
# Step 006 | Energy 6.8700 | Residue 0.90062 | Status: DAMPING (0.910)
# Step 007 | Energy 4.9876 | Residue 0.92686 | Status: DAMPING (0.937)
# Step 008 | Energy 6.6239 | Residue 0.90416 | Status: DAMPING (0.914)
# Step 009 | Energy 4.7344 | Residue 0.93032 | Status: DAMPING (0.940)
# Step 010 | Energy 5.8569 | Residue 0.91437 | Status: DAMPING (0.924)
# Step 011 | Energy 5.7496 | Residue 0.91586 | Status: DAMPING (0.926)
# Step 012 | Energy 4.8595 | Residue 0.92822 | Status: DAMPING (0.938)
# Step 013 | Energy 4.9714 | Residue 0.92668 | Status: DAMPING (0.937)
# Step 014 | Energy 4.5357 | Residue 0.93268 | Status: DAMPING (0.943)
# Step 015 | Energy 5.9264 | Residue 0.91282 | Status: DAMPING (0.923)
# Step 016 | Energy 6.3560 | Residue 0.90698 | Status: DAMPING (0.917)
# Step 017 | Energy 6.0444 | Residue 0.91133 | Status: DAMPING (0.921)
# Step 018 | Energy 4.6216 | Residue 0.93149 | Status: DAMPING (0.941)
# Step 019 | Energy 3.7144 | Residue 0.94455 | Status: DAMPING (0.955)
# Step 020 | Energy 4.8616 | Residue 0.92824 | Status: DAMPING (0.938)
# Step 021 | Energy 4.3325 | Residue 0.93572 | Status: DAMPING (0.946)
# Step 022 | Energy 5.0722 | Residue 0.92496 | Status: DAMPING (0.935)
# Step 023 | Energy 5.0222 | Residue 0.92587 | Status: DAMPING (0.936)
# Step 024 | Energy 6.0831 | Residue 0.91078 | Status: DAMPING (0.920)
# Step 025 | Energy 3.3638 | Residue 0.94981 | Status: DAMPING (0.960)
# Step 026 | Energy 4.8012 | Residue 0.92933 | Status: DAMPING (0.939)
# Step 027 | Energy 4.7284 | Residue 0.92987 | Status: DAMPING (0.940)
# Step 028 | Energy 3.6493 | Residue 0.94571 | Status: DAMPING (0.956)
# Step 029 | Energy 3.7292 | Residue 0.94457 | Status: DAMPING (0.955)
# Step 030 | Energy 4.1817 | Residue 0.93801 | Status: DAMPING (0.948)
# Step 031 | Energy 5.4148 | Residue 0.92056 | Status: DAMPING (0.930)
# Step 032 | Energy 3.6096 | Residue 0.94653 | Status: DAMPING (0.957)
# Step 033 | Energy 4.5166 | Residue 0.93327 | Status: DAMPING (0.943)
# Step 034 | Energy 5.2185 | Residue 0.92353 | Status: DAMPING (0.933)
# Step 035 | Energy 5.3010 | Residue 0.92235 | Status: DAMPING (0.932)
# Step 036 | Energy 4.7633 | Residue 0.92994 | Status: DAMPING (0.940)
# Step 037 | Energy 5.8875 | Residue 0.91413 | Status: DAMPING (0.924)
# Step 038 | Energy 5.0608 | Residue 0.92580 | Status: DAMPING (0.936)
# Step 039 | Energy 5.0990 | Residue 0.92526 | Status: DAMPING (0.935)
# Step 040 | Energy 4.9876 | Residue 0.92677 | Status: DAMPING (0.937)
# Step 041 | Energy 6.5493 | Residue 0.90524 | Status: DAMPING (0.915)
# Step 042 | Energy 5.5156 | Residue 0.91935 | Status: DAMPING (0.929)
# Step 043 | Energy 5.4909 | Residue 0.92019 | Status: DAMPING (0.930)
# Step 044 | Energy 4.9255 | Residue 0.92795 | Status: DAMPING (0.938)
# Step 045 | Energy 5.4720 | Residue 0.92019 | Status: DAMPING (0.930)
# Step 046 | Energy 4.9097 | Residue 0.92829 | Status: DAMPING (0.938)
# Step 047 | Energy 4.5688 | Residue 0.93301 | Status: DAMPING (0.943)
# Step 048 | Energy 3.7971 | Residue 0.94413 | Status: DAMPING (0.954)
# Step 049 | Energy 5.7367 | Residue 0.91679 | Status: DAMPING (0.927)
# Step 050 | Energy 4.8751 | Residue 0.92834 | Status: DAMPING (0.938)
# Step 051 | Energy 4.6445 | Residue 0.93206 | Status: DAMPING (0.942)
# Step 052 | Energy 4.8436 | Residue 0.92918 | Status: DAMPING (0.939)
# Step 053 | Energy 4.4993 | Residue 0.93371 | Status: DAMPING (0.944)
# Step 054 | Energy 6.3637 | Residue 0.90781 | Status: DAMPING (0.917)
# Step 055 | Energy 4.7202 | Residue 0.93070 | Status: DAMPING (0.941)
# Step 056 | Energy 4.1112 | Residue 0.93965 | Status: DAMPING (0.950)
# Step 057 | Energy 4.5578 | Residue 0.93336 | Status: DAMPING (0.943)
# Step 058 | Energy 4.2416 | Residue 0.93764 | Status: DAMPING (0.948)
# Step 059 | Energy 4.6123 | Residue 0.93259 | Status: DAMPING (0.942)
# Step 060 | Energy 3.9261 | Residue 0.94219 | Status: DAMPING (0.952)
# Step 061 | Energy 5.0710 | Residue 0.92605 | Status: DAMPING (0.936)
# Step 062 | Energy 5.1564 | Residue 0.92474 | Status: DAMPING (0.935)
# Step 063 | Energy 4.7834 | Residue 0.93008 | Status: DAMPING (0.940)
# Step 064 | Energy 4.7510 | Residue 0.93063 | Status: DAMPING (0.941)
# Step 065 | Energy 5.4108 | Residue 0.92098 | Status: DAMPING (0.931)
# Step 066 | Energy 3.8402 | Residue 0.94342 | Status: DAMPING (0.953)
# Step 067 | Energy 4.1789 | Residue 0.93857 | Status: DAMPING (0.949)
# Step 068 | Energy 3.0194 | Residue 0.95521 | Status: DAMPING (0.965)
# Step 069 | Energy 3.7842 | Residue 0.94416 | Status: DAMPING (0.954)
# Step 070 | Energy 4.1312 | Residue 0.93928 | Status: DAMPING (0.949)
# Step 071 | Energy 4.8780 | Residue 0.92843 | Status: DAMPING (0.938)
# Step 072 | Energy 5.1244 | Residue 0.92530 | Status: DAMPING (0.935)
# Step 073 | Energy 3.3146 | Residue 0.95082 | Status: DAMPING (0.961)
# Step 074 | Energy 3.5662 | Residue 0.94728 | Status: DAMPING (0.957)
# Step 075 | Energy 3.2897 | Residue 0.95138 | Status: DAMPING (0.961)
# Step 076 | Energy 3.7078 | Residue 0.94547 | Status: DAMPING (0.956)
# Step 077 | Energy 5.0767 | Residue 0.92586 | Status: DAMPING (0.936)
# Step 078 | Energy 4.0778 | Residue 0.94018 | Status: DAMPING (0.950)
# Step 079 | Energy 3.6368 | Residue 0.94630 | Status: DAMPING (0.956)
# Step 080 | Energy 5.1345 | Residue 0.92501 | Status: DAMPING (0.935)
# Step 081 | Energy 3.5012 | Residue 0.94821 | Status: DAMPING (0.958)
# Step 082 | Energy 4.2206 | Residue 0.93785 | Status: DAMPING (0.948)
# Step 083 | Energy 6.5423 | Residue 0.90568 | Status: DAMPING (0.915)
# Step 084 | Energy 3.8570 | Residue 0.94318 | Status: DAMPING (0.953)
# Step 085 | Energy 3.5456 | Residue 0.94756 | Status: DAMPING (0.958)
# Step 086 | Energy 3.0381 | Residue 0.95477 | Status: DAMPING (0.965)
# Step 087 | Energy 3.5335 | Residue 0.94782 | Status: DAMPING (0.958)
# Step 088 | Energy 4.3932 | Residue 0.93534 | Status: DAMPING (0.945)
# Step 089 | Energy 3.8364 | Residue 0.94332 | Status: DAMPING (0.953)
# Step 090 | Energy 3.0723 | Residue 0.95461 | Status: DAMPING (0.965)
# Step 091 | Energy 4.2597 | Residue 0.93747 | Status: DAMPING (0.947)
# Step 092 | Energy 3.9177 | Residue 0.94255 | Status: DAMPING (0.953)
# Step 093 | Energy 4.1927 | Residue 0.93827 | Status: DAMPING (0.948)
# Step 094 | Energy 3.4075 | Residue 0.94946 | Status: DAMPING (0.960)
# Step 095 | Energy 3.4921 | Residue 0.94830 | Status: DAMPING (0.958)
# Step 096 | Energy 3.9882 | Residue 0.94124 | Status: DAMPING (0.951)
# Step 097 | Energy 4.3205 | Residue 0.93633 | Status: DAMPING (0.946)
# Step 098 | Energy 3.8064 | Residue 0.94385 | Status: DAMPING (0.954)
# Step 099 | Energy 3.1779 | Residue 0.95313 | Status: DAMPING (0.963)
# Step 100 | Energy 4.4972 | Residue 0.93392 | Status: DAMPING (0.944)
# Step 101 | Energy 4.0870 | Residue 0.93986 | Status: DAMPING (0.950)
# Step 102 | Energy 3.5890 | Residue 0.94709 | Status: DAMPING (0.957)
# Step 103 | Energy 3.9675 | Residue 0.94161 | Status: DAMPING (0.952)
# Step 104 | Energy 3.5992 | Residue 0.94679 | Status: DAMPING (0.957)
# Step 105 | Energy 2.5804 | Residue 0.96153 | Status: DAMPING (0.972)
# Step 106 | Energy 3.4190 | Residue 0.94945 | Status: DAMPING (0.960)
# Step 107 | Energy 4.2703 | Residue 0.93747 | Status: DAMPING (0.947)
# Step 108 | Energy 3.4530 | Residue 0.94896 | Status: DAMPING (0.959)
# Step 109 | Energy 4.8474 | Residue 0.92900 | Status: DAMPING (0.939)
# Step 110 | Energy 3.0642 | Residue 0.95431 | Status: DAMPING (0.964)
# Step 111 | Energy 3.7961 | Residue 0.94408 | Status: DAMPING (0.954)
# Step 112 | Energy 3.5417 | Residue 0.94758 | Status: DAMPING (0.958)
# Step 113 | Energy 4.5560 | Residue 0.93345 | Status: DAMPING (0.943)
# Step 114 | Energy 5.3630 | Residue 0.92166 | Status: DAMPING (0.931)
# Step 115 | Energy 4.3586 | Residue 0.93592 | Status: DAMPING (0.946)
# Step 116 | Energy 3.3024 | Residue 0.95117 | Status: DAMPING (0.961)
# Step 117 | Energy 3.7416 | Residue 0.94478 | Status: DAMPING (0.955)
# Step 118 | Energy 3.6271 | Residue 0.94644 | Status: DAMPING (0.956)
# Step 119 | Energy 5.0818 | Residue 0.92602 | Status: DAMPING (0.936)
# Step 120 | Energy 3.7902 | Residue 0.94392 | Status: DAMPING (0.954)
# Step 121 | Energy 3.0870 | Residue 0.95426 | Status: DAMPING (0.964)
# Step 122 | Energy 2.7716 | Residue 0.95875 | Status: DAMPING (0.969)
# Step 123 | Energy 3.8271 | Residue 0.94359 | Status: DAMPING (0.954)
# Step 124 | Energy 3.1677 | Residue 0.95298 | Status: DAMPING (0.963)
# Step 125 | Energy 2.8080 | Residue 0.95840 | Status: DAMPING (0.969)
# Step 126 | Energy 3.3573 | Residue 0.95033 | Status: DAMPING (0.960)
# Step 127 | Energy 3.2784 | Residue 0.95143 | Status: DAMPING (0.962)
# Step 128 | Energy 3.4090 | Residue 0.94962 | Status: DAMPING (0.960)
# Step 129 | Energy 3.8346 | Residue 0.94355 | Status: DAMPING (0.954)
# Step 130 | Energy 3.2655 | Residue 0.95163 | Status: DAMPING (0.962)
# Step 131 | Energy 3.3845 | Residue 0.94961 | Status: DAMPING (0.960)
# Step 132 | Energy 3.2880 | Residue 0.95143 | Status: DAMPING (0.962)
# Step 133 | Energy 3.6505 | Residue 0.94606 | Status: DAMPING (0.956)
# Step 134 | Energy 3.7175 | Residue 0.94498 | Status: DAMPING (0.955)
# Step 135 | Energy 2.7929 | Residue 0.95863 | Status: DAMPING (0.969)
# Step 136 | Energy 3.3104 | Residue 0.95089 | Status: DAMPING (0.961)
# Step 137 | Energy 2.7963 | Residue 0.95850 | Status: DAMPING (0.969)
# Step 138 | Energy 3.6838 | Residue 0.94548 | Status: DAMPING (0.956)
# Step 139 | Energy 4.9400 | Residue 0.92791 | Status: DAMPING (0.938)
# Step 140 | Energy 3.1249 | Residue 0.95362 | Status: DAMPING (0.964)
# Step 141 | Energy 2.6118 | Residue 0.96112 | Status: DAMPING (0.971)
# Step 142 | Energy 3.1023 | Residue 0.95402 | Status: DAMPING (0.964)
# Step 143 | Energy 3.6146 | Residue 0.94663 | Status: DAMPING (0.957)
# Step 144 | Energy 3.4915 | Residue 0.94842 | Status: DAMPING (0.958)
# Step 145 | Energy 2.7485 | Residue 0.95918 | Status: DAMPING (0.969)
# Step 146 | Energy 2.8911 | Residue 0.95703 | Status: DAMPING (0.967)
# Step 147 | Energy 3.5744 | Residue 0.94729 | Status: DAMPING (0.957)
# Step 148 | Energy 2.7468 | Residue 0.95905 | Status: DAMPING (0.969)
# Step 149 | Energy 2.5445 | Residue 0.96196 | Status: DAMPING (0.972)
# Step 150 | Energy 3.6622 | Residue 0.94596 | Status: DAMPING (0.956)
# Step 151 | Energy 2.9511 | Residue 0.95619 | Status: DAMPING (0.966)
# Step 152 | Energy 2.5441 | Residue 0.96200 | Status: DAMPING (0.972)
# Step 153 | Energy 3.0930 | Residue 0.95403 | Status: DAMPING (0.964)
# Step 154 | Energy 3.5355 | Residue 0.94786 | Status: DAMPING (0.958)
# Step 155 | Energy 4.1159 | Residue 0.93960 | Status: DAMPING (0.950)
# Step 156 | Energy 2.5878 | Residue 0.96149 | Status: DAMPING (0.972)
# Step 157 | Energy 2.6350 | Residue 0.96088 | Status: DAMPING (0.971)
# Step 158 | Energy 2.8954 | Residue 0.95698 | Status: DAMPING (0.967)
# Step 159 | Energy 4.0185 | Residue 0.94059 | Status: DAMPING (0.951)
# Step 160 | Energy 3.1984 | Residue 0.95247 | Status: DAMPING (0.963)
# Step 161 | Energy 2.7396 | Residue 0.95929 | Status: DAMPING (0.969)
# Step 162 | Energy 3.1270 | Residue 0.95388 | Status: DAMPING (0.964)
# Step 163 | Energy 2.5514 | Residue 0.96195 | Status: DAMPING (0.972)
# Step 164 | Energy 4.6509 | Residue 0.93201 | Status: DAMPING (0.942)
# Step 165 | Energy 3.8661 | Residue 0.94289 | Status: DAMPING (0.953)
# Step 166 | Energy 2.2338 | Residue 0.96665 | Status: DAMPING (0.977)
# Step 167 | Energy 3.0126 | Residue 0.95533 | Status: DAMPING (0.965)
# Step 168 | Energy 2.9324 | Residue 0.95654 | Status: DAMPING (0.967)
# Step 169 | Energy 2.8919 | Residue 0.95693 | Status: DAMPING (0.967)
# Step 170 | Energy 2.8641 | Residue 0.95739 | Status: DAMPING (0.968)
# Step 171 | Energy 2.4482 | Residue 0.96359 | Status: DAMPING (0.974)
# Step 172 | Energy 4.0587 | Residue 0.94012 | Status: DAMPING (0.950)
# Step 173 | Energy 2.4663 | Residue 0.96321 | Status: DAMPING (0.973)
# Step 174 | Energy 2.9542 | Residue 0.95619 | Status: DAMPING (0.966)
# Step 175 | Energy 2.1640 | Residue 0.96782 | Status: DAMPING (0.978)
# Step 176 | Energy 2.5111 | Residue 0.96254 | Status: DAMPING (0.973)
# Step 177 | Energy 2.2683 | Residue 0.96621 | Status: DAMPING (0.976)
# Step 178 | Energy 3.1687 | Residue 0.95321 | Status: DAMPING (0.963)
# Step 179 | Energy 2.6431 | Residue 0.96080 | Status: DAMPING (0.971)
# Step 180 | Energy 3.1117 | Residue 0.95388 | Status: DAMPING (0.964)
# Step 181 | Energy 3.4777 | Residue 0.94872 | Status: DAMPING (0.959)
# Step 182 | Energy 2.8847 | Residue 0.95721 | Status: DAMPING (0.967)
# Step 183 | Energy 3.2517 | Residue 0.95199 | Status: DAMPING (0.962)
# Step 184 | Energy 3.1064 | Residue 0.95418 | Status: DAMPING (0.964)
# Step 185 | Energy 2.1852 | Residue 0.96757 | Status: DAMPING (0.978)
# Step 186 | Energy 3.2210 | Residue 0.95220 | Status: DAMPING (0.962)
# Step 187 | Energy 3.4093 | Residue 0.94957 | Status: DAMPING (0.960)
# Step 188 | Energy 2.7154 | Residue 0.95979 | Status: DAMPING (0.970)
# Step 189 | Energy 3.1663 | Residue 0.95313 | Status: DAMPING (0.963)
# Step 190 | Energy 1.9979 | Residue 0.97020 | Status: DAMPING (0.980)
# Step 191 | Energy 2.6042 | Residue 0.96133 | Status: DAMPING (0.972)
# Step 192 | Energy 3.1256 | Residue 0.95375 | Status: DAMPING (0.964)
# Step 193 | Energy 2.2229 | Residue 0.96673 | Status: DAMPING (0.977)
# Step 194 | Energy 3.3384 | Residue 0.95077 | Status: DAMPING (0.961)
# Step 195 | Energy 2.7616 | Residue 0.95871 | Status: DAMPING (0.969)
# Step 196 | Energy 2.9607 | Residue 0.95614 | Status: DAMPING (0.966)
# Step 197 | Energy 2.2445 | Residue 0.96657 | Status: DAMPING (0.977)
# Step 198 | Energy 2.3547 | Residue 0.96482 | Status: DAMPING (0.975)
# Step 199 | Energy 2.8148 | Residue 0.95818 | Status: DAMPING (0.968)
# Step 200 | Energy 3.7843 | Residue 0.94430 | Status: DAMPING (0.954)
# Step 201 | Energy 2.4712 | Residue 0.96324 | Status: DAMPING (0.973)
# Step 202 | Energy 2.9353 | Residue 0.95645 | Status: DAMPING (0.967)
# Step 203 | Energy 2.3283 | Residue 0.96527 | Status: DAMPING (0.976)
# Step 204 | Energy 2.5891 | Residue 0.96144 | Status: DAMPING (0.972)
# Step 205 | Energy 2.2860 | Residue 0.96586 | Status: DAMPING (0.976)
# Step 206 | Energy 2.2438 | Residue 0.96649 | Status: DAMPING (0.977)
# Step 207 | Energy 2.5998 | Residue 0.96125 | Status: DAMPING (0.971)
# Step 208 | Energy 1.9744 | Residue 0.97041 | Status: DAMPING (0.981)
# Step 209 | Energy 1.6862 | Residue 0.97480 | Status: STABLE SPECTRUM
# Step 210 | Energy 2.3051 | Residue 0.96574 | Status: DAMPING (0.976)
# Step 211 | Energy 2.7252 | Residue 0.95938 | Status: DAMPING (0.970)
# Step 212 | Energy 1.9389 | Residue 0.97099 | Status: DAMPING (0.981)
# Step 213 | Energy 2.2202 | Residue 0.96686 | Status: DAMPING (0.977)
# Step 214 | Energy 2.0448 | Residue 0.96943 | Status: DAMPING (0.980)
# Step 215 | Energy 3.0749 | Residue 0.95460 | Status: DAMPING (0.965)
# Step 216 | Energy 2.4519 | Residue 0.96348 | Status: DAMPING (0.974)
# Step 217 | Energy 1.7787 | Residue 0.97334 | Status: STABLE SPECTRUM
# Step 218 | Energy 2.7065 | Residue 0.95972 | Status: DAMPING (0.970)
# Step 219 | Energy 2.3960 | Residue 0.96429 | Status: DAMPING (0.975)
# Step 220 | Energy 2.3951 | Residue 0.96437 | Status: DAMPING (0.975)
# Step 221 | Energy 2.7196 | Residue 0.95973 | Status: DAMPING (0.970)
# Step 222 | Energy 1.5470 | Residue 0.97681 | Status: STABLE SPECTRUM
# Step 223 | Energy 2.3516 | Residue 0.96487 | Status: DAMPING (0.975)
# Step 224 | Energy 2.7480 | Residue 0.95913 | Status: DAMPING (0.969)
# Step 225 | Energy 4.6287 | Residue 0.93230 | Status: DAMPING (0.942)
# Step 226 | Energy 2.0072 | Residue 0.96987 | Status: DAMPING (0.980)
# Step 227 | Energy 1.5154 | Residue 0.97727 | Status: STABLE SPECTRUM
# Step 228 | Energy 1.7425 | Residue 0.97385 | Status: STABLE SPECTRUM
# Step 229 | Energy 2.9322 | Residue 0.95636 | Status: DAMPING (0.967)
# Step 230 | Energy 3.1625 | Residue 0.95314 | Status: DAMPING (0.963)
# Step 231 | Energy 2.6764 | Residue 0.96015 | Status: DAMPING (0.970)
# Step 232 | Energy 2.1923 | Residue 0.96730 | Status: DAMPING (0.978)
# Step 233 | Energy 2.5823 | Residue 0.96174 | Status: DAMPING (0.972)
# Step 234 | Energy 4.0908 | Residue 0.94010 | Status: DAMPING (0.950)
# Step 235 | Energy 3.4877 | Residue 0.94843 | Status: DAMPING (0.958)
# Step 236 | Energy 2.1751 | Residue 0.96763 | Status: DAMPING (0.978)
# Step 237 | Energy 1.4455 | Residue 0.97839 | Status: STABLE SPECTRUM
# Step 238 | Energy 1.5287 | Residue 0.97703 | Status: STABLE SPECTRUM
# Step 239 | Energy 3.2343 | Residue 0.95209 | Status: DAMPING (0.962)
# Step 240 | Energy 1.7990 | Residue 0.97311 | Status: STABLE SPECTRUM
# Step 241 | Energy 1.8281 | Residue 0.97266 | Status: STABLE SPECTRUM
# Step 242 | Energy 1.9573 | Residue 0.97076 | Status: DAMPING (0.981)
# Step 243 | Energy 2.2326 | Residue 0.96662 | Status: DAMPING (0.977)
# Step 244 | Energy 1.8618 | Residue 0.97214 | Status: STABLE SPECTRUM
# Step 245 | Energy 1.9869 | Residue 0.97029 | Status: DAMPING (0.981)
# Step 246 | Energy 1.7871 | Residue 0.97328 | Status: STABLE SPECTRUM
# Step 247 | Energy 3.1451 | Residue 0.95326 | Status: DAMPING (0.963)
# Step 248 | Energy 1.9965 | Residue 0.97015 | Status: DAMPING (0.980)
# Step 249 | Energy 1.8340 | Residue 0.97252 | Status: STABLE SPECTRUM
# Step 250 | Energy 1.6528 | Residue 0.97528 | Status: STABLE SPECTRUM
# Step 251 | Energy 2.0320 | Residue 0.96960 | Status: DAMPING (0.980)
# Step 252 | Energy 2.1191 | Residue 0.96838 | Status: DAMPING (0.979)
# Step 253 | Energy 2.2270 | Residue 0.96678 | Status: DAMPING (0.977)
# Step 254 | Energy 1.6133 | Residue 0.97583 | Status: STABLE SPECTRUM
# Step 255 | Energy 2.1258 | Residue 0.96826 | Status: DAMPING (0.979)
# Step 256 | Energy 2.1345 | Residue 0.96799 | Status: DAMPING (0.978)
# Step 257 | Energy 1.7981 | Residue 0.97315 | Status: STABLE SPECTRUM
# Step 258 | Energy 1.9459 | Residue 0.97099 | Status: DAMPING (0.981)
# Step 259 | Energy 1.5458 | Residue 0.97688 | Status: STABLE SPECTRUM
# Step 260 | Energy 1.5985 | Residue 0.97608 | Status: STABLE SPECTRUM
# Step 261 | Energy 2.2385 | Residue 0.96663 | Status: DAMPING (0.977)
# Step 262 | Energy 1.9091 | Residue 0.97145 | Status: DAMPING (0.982)
# Step 263 | Energy 1.6605 | Residue 0.97507 | Status: STABLE SPECTRUM
# Step 264 | Energy 2.0654 | Residue 0.96913 | Status: DAMPING (0.979)
# Step 265 | Energy 2.2008 | Residue 0.96718 | Status: DAMPING (0.977)
# Step 266 | Energy 1.7601 | Residue 0.97369 | Status: STABLE SPECTRUM
# Step 267 | Energy 1.8367 | Residue 0.97259 | Status: STABLE SPECTRUM
# Step 268 | Energy 1.8530 | Residue 0.97236 | Status: STABLE SPECTRUM
# Step 269 | Energy 2.1902 | Residue 0.96714 | Status: DAMPING (0.977)
# Step 270 | Energy 3.0632 | Residue 0.95475 | Status: DAMPING (0.965)
# Step 271 | Energy 1.8755 | Residue 0.97182 | Status: STABLE SPECTRUM
# Step 272 | Energy 1.5340 | Residue 0.97702 | Status: STABLE SPECTRUM
# Step 273 | Energy 1.6939 | Residue 0.97470 | Status: STABLE SPECTRUM
# Step 274 | Energy 1.5968 | Residue 0.97606 | Status: STABLE SPECTRUM
# Step 275 | Energy 2.0299 | Residue 0.96968 | Status: DAMPING (0.980)
# Step 276 | Energy 1.3561 | Residue 0.97965 | Status: STABLE SPECTRUM
# Step 277 | Energy 1.2046 | Residue 0.98188 | Status: STABLE SPECTRUM
# Step 278 | Energy 1.0454 | Residue 0.98420 | Status: STABLE SPECTRUM
# Step 279 | Energy 1.6218 | Residue 0.97566 | Status: STABLE SPECTRUM
# Step 280 | Energy 1.5400 | Residue 0.97696 | Status: STABLE SPECTRUM
# Step 281 | Energy 1.2898 | Residue 0.98061 | Status: STABLE SPECTRUM
# Step 282 | Energy 1.3771 | Residue 0.97938 | Status: STABLE SPECTRUM
# Step 283 | Energy 1.2762 | Residue 0.98082 | Status: STABLE SPECTRUM
# Step 284 | Energy 1.4856 | Residue 0.97774 | Status: STABLE SPECTRUM
# Step 285 | Energy 1.2781 | Residue 0.98075 | Status: STABLE SPECTRUM
# Step 286 | Energy 1.1659 | Residue 0.98247 | Status: STABLE SPECTRUM
# Step 287 | Energy 1.7641 | Residue 0.97367 | Status: STABLE SPECTRUM
# Step 288 | Energy 1.1832 | Residue 0.98216 | Status: STABLE SPECTRUM
# Step 289 | Energy 1.1313 | Residue 0.98295 | Status: STABLE SPECTRUM
# Step 290 | Energy 1.9893 | Residue 0.97021 | Status: DAMPING (0.981)
# Step 291 | Energy 1.5824 | Residue 0.97626 | Status: STABLE SPECTRUM
# Step 292 | Energy 1.9128 | Residue 0.97139 | Status: DAMPING (0.982)
# Step 293 | Energy 1.7107 | Residue 0.97441 | Status: STABLE SPECTRUM
# Step 294 | Energy 1.2117 | Residue 0.98178 | Status: STABLE SPECTRUM
# Step 295 | Energy 1.7505 | Residue 0.97381 | Status: STABLE SPECTRUM
# Step 296 | Energy 1.8384 | Residue 0.97248 | Status: STABLE SPECTRUM
# Step 297 | Energy 1.2252 | Residue 0.98165 | Status: STABLE SPECTRUM
# Step 298 | Energy 1.0612 | Residue 0.98401 | Status: STABLE SPECTRUM
# Step 299 | Energy 1.5312 | Residue 0.97699 | Status: STABLE SPECTRUM
# Step 300 | Energy 1.3765 | Residue 0.97929 | Status: STABLE SPECTRUM
# Step 301 | Energy 1.1327 | Residue 0.98299 | Status: STABLE SPECTRUM
# Step 302 | Energy 1.6236 | Residue 0.97557 | Status: STABLE SPECTRUM
# Step 303 | Energy 1.4303 | Residue 0.97851 | Status: STABLE SPECTRUM
# Step 304 | Energy 1.1283 | Residue 0.98306 | Status: STABLE SPECTRUM
# Step 305 | Energy 1.2188 | Residue 0.98171 | Status: STABLE SPECTRUM
# Step 306 | Energy 1.0195 | Residue 0.98468 | Status: STABLE SPECTRUM
# Step 307 | Energy 1.1643 | Residue 0.98251 | Status: STABLE SPECTRUM
# Step 308 | Energy 0.9969 | Residue 0.98492 | Status: STABLE SPECTRUM
# Step 309 | Energy 1.1065 | Residue 0.98338 | Status: STABLE SPECTRUM
# Step 310 | Energy 1.2063 | Residue 0.98184 | Status: STABLE SPECTRUM
# Step 311 | Energy 1.2290 | Residue 0.98153 | Status: STABLE SPECTRUM
# Step 312 | Energy 1.4301 | Residue 0.97854 | Status: STABLE SPECTRUM
# Step 313 | Energy 0.9543 | Residue 0.98560 | Status: STABLE SPECTRUM
# Step 314 | Energy 0.9560 | Residue 0.98563 | Status: STABLE SPECTRUM
# Step 315 | Energy 1.4063 | Residue 0.97888 | Status: STABLE SPECTRUM
# Step 316 | Energy 1.6646 | Residue 0.97498 | Status: STABLE SPECTRUM
# Step 317 | Energy 1.3298 | Residue 0.97999 | Status: STABLE SPECTRUM
# Step 318 | Energy 0.8629 | Residue 0.98696 | Status: STABLE SPECTRUM
# Step 319 | Energy 1.2881 | Residue 0.98066 | Status: STABLE SPECTRUM
# Step 320 | Energy 1.8071 | Residue 0.97310 | Status: STABLE SPECTRUM
# Step 321 | Energy 1.0863 | Residue 0.98365 | Status: STABLE SPECTRUM
# Step 322 | Energy 0.9383 | Residue 0.98585 | Status: STABLE SPECTRUM
# Step 323 | Energy 1.2878 | Residue 0.98067 | Status: STABLE SPECTRUM
# Step 324 | Energy 1.3412 | Residue 0.97991 | Status: STABLE SPECTRUM
# Step 325 | Energy 0.9832 | Residue 0.98521 | Status: STABLE SPECTRUM
# Step 326 | Energy 1.3541 | Residue 0.97960 | Status: STABLE SPECTRUM
# Step 327 | Energy 1.1412 | Residue 0.98280 | Status: STABLE SPECTRUM
# Step 328 | Energy 1.2405 | Residue 0.98136 | Status: STABLE SPECTRUM
# Step 329 | Energy 0.6386 | Residue 0.99037 | Status: STABLE SPECTRUM
# Step 330 | Energy 0.8854 | Residue 0.98661 | Status: STABLE SPECTRUM
# Step 331 | Energy 1.4504 | Residue 0.97816 | Status: STABLE SPECTRUM
# Step 332 | Energy 1.0374 | Residue 0.98440 | Status: STABLE SPECTRUM
# Step 333 | Energy 0.7844 | Residue 0.98813 | Status: STABLE SPECTRUM
# Step 334 | Energy 0.9639 | Residue 0.98553 | Status: STABLE SPECTRUM
# Step 335 | Energy 0.9798 | Residue 0.98529 | Status: STABLE SPECTRUM
# Step 336 | Energy 0.9485 | Residue 0.98573 | Status: STABLE SPECTRUM
# Step 337 | Energy 1.3618 | Residue 0.97949 | Status: STABLE SPECTRUM
# Step 338 | Energy 1.2273 | Residue 0.98157 | Status: STABLE SPECTRUM
# Step 339 | Energy 1.4735 | Residue 0.97789 | Status: STABLE SPECTRUM
# Step 340 | Energy 2.3726 | Residue 0.96450 | Status: DAMPING (0.975)
# Step 341 | Energy 1.0299 | Residue 0.98452 | Status: STABLE SPECTRUM
# Step 342 | Energy 0.8699 | Residue 0.98686 | Status: STABLE SPECTRUM
# Step 343 | Energy 0.7499 | Residue 0.98866 | Status: STABLE SPECTRUM
# Step 344 | Energy 1.9382 | Residue 0.97114 | Status: DAMPING (0.981)
# Step 345 | Energy 1.0217 | Residue 0.98462 | Status: STABLE SPECTRUM
# Step 346 | Energy 0.9327 | Residue 0.98591 | Status: STABLE SPECTRUM
# Step 347 | Energy 1.3611 | Residue 0.97952 | Status: STABLE SPECTRUM
# Step 348 | Energy 1.2583 | Residue 0.98106 | Status: STABLE SPECTRUM
# Step 349 | Energy 0.8890 | Residue 0.98659 | Status: STABLE SPECTRUM
# Step 350 | Energy 1.1676 | Residue 0.98244 | Status: STABLE SPECTRUM
# ------------------------------------------------------------------------------------------
# SUCCESS: Reached stable spectral regime near target residue (0.9895).
# Final residue: 0.98244
# Mean recent residue (last 50 steps): 0.98206
# Run complete.
# (base) brendanlynch@Brendans-Laptop gradientDescent % 
