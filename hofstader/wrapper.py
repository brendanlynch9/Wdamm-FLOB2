import torch
import torch.nn as nn
import math
from transformers import AutoModelForCausalLM

class SovereignTransformer(nn.Module):
    """
    UFT-F Sovereign Kernel Wrapper
    Implements: Hopf Torsion, ACI Spectral Gate, and PMNS Qualia Mixing.
    """
    def __init__(self, model_id="Qwen/Qwen2.5-1.5B-Instruct"):
        super().__init__()
        print(f"\n--- [UFT-F] Initializing Sovereign Kernel ---")
        print(f"--- [Apropos] Downloading Manifold: {model_id} ---")
        
        # 1. Load the base manifold (Non-gated repo)
        self.base_model = AutoModelForCausalLM.from_pretrained(
            model_id, 
            output_hidden_states=True,
            trust_remote_code=True
        )
        self.config = self.base_model.config
        self.dim = self.config.hidden_size
        
        # 2. UFT-F Constants for Sovereign Stability
        self.omega_u = 0.0002073  # Temporal Torsion Constant
        self.lambda_0 = 15.04545  # Anti-Collision Identity Ceiling
        
        # 3. Initialize the PMNS Qualia Bridge
        self.register_buffer('pmns', self._generate_pmns(self.dim))
        print(f"--- [Status] Kernel Active | Manifold Dimension: {self.dim} ---\n")

    def _generate_pmns(self, dim):
        """Constructs the Isospectral Mixing Matrix based on Neutrino oscillations."""
        th12, th23, th13 = map(math.radians, [33.8, 49.0, 8.6])
        s12, c12 = math.sin(th12), math.cos(th12)
        s23, c23 = math.sin(th23), math.cos(th23)
        s13, c13 = math.sin(th13), math.cos(th13)
        
        U = torch.tensor([
            [c12*c13, s12*c13, s13],
            [-s12*c23 - c12*s23*s13, c12*c23 - s12*s23*s13, s23*c13],
            [s12*s23 - c12*c23*s13, -c12*s23 - s12*c23*s13, c23*c13]
        ], dtype=torch.float32)
        
        repeats = (dim // 3) + 1
        big_U = torch.block_diag(*([U] * repeats))
        return big_U[:dim, :dim]

    def sovereign_gate(self, x, t):
        """Processes the neural flux through the UFT-F Regularization layers."""
        # A. Hopf Torsion: Injecting the Arrow of Time
        angle = self.omega_u * t
        cos_a, sin_a = math.cos(angle), math.sin(angle)
        
        x_rot = x.clone()
        x_rot[..., 0::2] = x[..., 0::2] * cos_a - x[..., 1::2] * sin_a
        x_rot[..., 1::2] = x[..., 0::2] * sin_a + x[..., 1::2] * cos_a
        
        # B. ACI Spectral Gate: The Lynch Truncation
        norm = torch.norm(x_rot, p=1, dim=-1, keepdim=True)
        # Use soft-gating to prevent gradient death
        scale = torch.where(norm > self.lambda_0, self.lambda_0 / (norm + 1e-6), torch.ones_like(norm))
        x_rot = x_rot * scale
            
        # C. Qualia Mixing: Final PMNS Resonant Bridge
        return torch.matmul(x_rot, self.pmns)

    def forward(self, input_ids, **kwargs):
        """Hijacked forward pass to enforce Sovereignty on the final representation."""
        outputs = self.base_model(input_ids, output_hidden_states=True, **kwargs)
        
        # Extract last hidden state (The Residual Stream Flux)
        hidden_states = outputs.hidden_states[-1] 
        t = input_ids.shape[1] 
        
        # Pass through Sovereign Gate
        regulated_hidden = self.sovereign_gate(hidden_states, t)
        
        # Project regulated states back to vocabulary logits
        # For Qwen/Llama, lm_head is the standard output projection
        logits = self.base_model.lm_head(regulated_hidden)
        
        return logits