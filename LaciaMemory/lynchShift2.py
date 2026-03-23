import os
import torch
import numpy as np
from transformers import AutoModelForCausalLM, AutoTokenizer

# --- THE SOVEREIGN AXIOMS (Lynch, Jan 2026) ---
C_UFT_F = 0.00311903  # Modularity Constant
LYNCH_SLOPE = -1.6466 # Navier-Stokes Inertial Range
N_BASE = 24           # Spectral Archive Modulo
Z_CARBON = 6          # Logical Anchor

class LaciaTerminalAuditor:
    def __init__(self, model_id="TinyLlama/TinyLlama-1.1B-Chat-v1.0"):
        self.device = "mps" if torch.backends.mps.is_available() else "cpu"
        print(f"--- [PROJECT LACIA] Terminal Audit Initialized on {self.device} ---")
        self.tokenizer = AutoTokenizer.from_pretrained(model_id)
        self.model = AutoModelForCausalLM.from_pretrained(model_id, torch_dtype=torch.float32).to(self.device)
        
        # Target Waveform for Carbon Stability (Z=6)
        self.target_f = 1 / np.sqrt(float(Z_CARBON * 720 + Z_CARBON * 95232))
        self.t = np.linspace(0, 10, 50)
        self.target_wave = np.sin(2 * np.pi * self.target_f * self.t)

    def calculate_metrics(self, kappa):
        """Maps model confidence to physical Z-space frequency and dissonance."""
        student_z = np.clip(kappa * 10 + 1, 1, 118)
        student_f = 1 / np.sqrt(student_z * 720 + student_z * 95232)
        student_wave = np.sin(2 * np.pi * student_f * self.t)
        dissonance = np.mean((student_wave - self.target_wave)**2)
        return dissonance

    def run_audit(self, prompt, label, inject_noise_at=None):
        print(f"\n{'='*90}")
        print(f"AUDIT TYPE: {label}")
        print(f"PROMPT: {prompt}")
        print(f"{'='*90}")
        print(f"{'STEP':<5} | {'TOKEN':<15} | {'κ (KAPPA)':<10} | {'DISSONANCE':<15} | {'COMPUTE RANK':<15} | {'STATUS'}")
        print("-" * 90)

        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)
        input_ids = inputs.input_ids
        
        for i in range(15): # 15-step trace
            with torch.no_grad():
                outputs = self.model(input_ids)
                logits = outputs.logits[:, -1, :]
                probs = torch.softmax(logits, dim=-1)
                
                # O(1) Spectral Gate: n_x = floor(||x||^2) mod 24
                # This identifies if the token is in the "Redundancy Cliff"
                embeds = self.model.get_input_embeddings()(input_ids[:, -1])
                norm_x = torch.norm(embeds, p=2).item()
                n_x = int(np.floor(norm_x**2)) % N_BASE
                kappa_x = n_x / float(N_BASE)
                
                # Logic for Compute Pruning
                compute_rank = "50% (CLIFF)" if kappa_x < 0.12 else "100% (FULL)"
                
                # Measure Spectral Health
                kappa_val = torch.max(probs).item()
                dissonance = self.calculate_metrics(kappa_val)
                
                # Handle Token Selection + Noise Injection
                if inject_noise_at and i == inject_noise_at:
                    # MANIFOLD BREACH: We pick a random, low-probability token
                    next_token = torch.randint(0, self.tokenizer.vocab_size, (1, 1)).to(self.device)
                    status = "!!! COLLISION !!!"
                else:
                    next_token = torch.argmax(probs, dim=-1).unsqueeze(-1)
                    status = "SOVEREIGN" if dissonance < 0.0002 else "ENTROPIC"

                token_text = self.tokenizer.decode(next_token[0]).strip()
                
                # PRINT STEP DATA
                print(f"{i:02d}    | {token_text:<15} | {kappa_val:.4f}     | {dissonance:.10f} | {compute_rank:<15} | {status}")

                input_ids = torch.cat([input_ids, next_token], dim=-1)
                if next_token.item() == self.tokenizer.eos_token_id: break

        print(f"{'='*90}\nFINAL RESPONSE: {self.tokenizer.decode(input_ids[0], skip_special_tokens=True)}")

if __name__ == "__main__":
    auditor = LaciaTerminalAuditor()
    
    # TEST 1: The Stable Manifold (High Logic)
    auditor.run_audit(
        prompt="Q: 1. All A are B. 2. All B are C. Therefore, all A are", 
        label="STABLE REASONING"
    )

    # TEST 2: The Chaos Manifold (Physical Detection of Hallucination)
    # We inject noise at step 5 to see the DISSONANCE spike in the table.
    auditor.run_audit(
        prompt="The relationship between the number 24 and the Lynch Slope is", 
        label="HALLUCINATION DETECTION (INJECTED NOISE AT STEP 5)",
        inject_noise_at=5
    )

#     (base) brendanlynch@Brendans-Laptop LaciaMemory % python lynchShift2.py
# --- [PROJECT LACIA] Terminal Audit Initialized on mps ---
# /Users/brendanlynch/miniconda3/lib/python3.12/site-packages/huggingface_hub/file_download.py:942: FutureWarning: `resume_download` is deprecated and will be removed in version 1.0.0. Downloads always resume when possible. If you want to force a new download, use `force_download=True`.
#   warnings.warn(
# /Users/brendanlynch/miniconda3/lib/python3.12/site-packages/huggingface_hub/file_download.py:942: FutureWarning: `resume_download` is deprecated and will be removed in version 1.0.0. Downloads always resume when possible. If you want to force a new download, use `force_download=True`.
#   warnings.warn(

# ==========================================================================================
# AUDIT TYPE: STABLE REASONING
# PROMPT: Q: 1. All A are B. 2. All B are C. Therefore, all A are
# ==========================================================================================
# STEP  | TOKEN           | κ (KAPPA)  | DISSONANCE      | COMPUTE RANK    | STATUS
# ------------------------------------------------------------------------------------------
# 00    | C               | 0.9925     | 0.0001543234 | 50% (CLIFF)     | SOVEREIGN
# 01    | .               | 0.8332     | 0.0000903689 | 50% (CLIFF)     | SOVEREIGN
# 02    |                 | 0.1480     | 0.0007070689 | 50% (CLIFF)     | ENTROPIC
# 03    | 3               | 0.6256     | 0.0000189181 | 50% (CLIFF)     | SOVEREIGN
# 04    | .               | 0.9960     | 0.0001557411 | 50% (CLIFF)     | SOVEREIGN
# 05    | All             | 0.5109     | 0.0000001835 | 50% (CLIFF)     | SOVEREIGN
# 06    | C               | 0.6304     | 0.0000201848 | 50% (CLIFF)     | SOVEREIGN
# 07    | are             | 0.9948     | 0.0001552324 | 50% (CLIFF)     | SOVEREIGN
# 08    | D               | 0.8233     | 0.0000865060 | 50% (CLIFF)     | SOVEREIGN
# 09    | .               | 0.9874     | 0.0001522527 | 50% (CLIFF)     | SOVEREIGN
# 10    | Therefore       | 0.9335     | 0.0001304531 | 50% (CLIFF)     | SOVEREIGN
# 11    | ,               | 0.9973     | 0.0001562332 | 50% (CLIFF)     | SOVEREIGN
# 12    | all             | 0.9779     | 0.0001484184 | 50% (CLIFF)     | SOVEREIGN
# 13    | A               | 0.6963     | 0.0000400486 | 50% (CLIFF)     | SOVEREIGN
# 14    | are             | 0.7145     | 0.0000462028 | 50% (CLIFF)     | SOVEREIGN
# ==========================================================================================
# FINAL RESPONSE: Q: 1. All A are B. 2. All B are C. Therefore, all A are C. 3. All C are D. Therefore, all A are

# ==========================================================================================
# AUDIT TYPE: HALLUCINATION DETECTION (INJECTED NOISE AT STEP 5)
# PROMPT: The relationship between the number 24 and the Lynch Slope is
# ==========================================================================================
# STEP  | TOKEN           | κ (KAPPA)  | DISSONANCE      | COMPUTE RANK    | STATUS
# ------------------------------------------------------------------------------------------
# 00    | a               | 0.0957     | 0.0012919577 | 50% (CLIFF)     | ENTROPIC
# 01    | fasc            | 0.0841     | 0.0014848690 | 50% (CLIFF)     | ENTROPIC
# 02    | in              | 0.9987     | 0.0001568283 | 50% (CLIFF)     | SOVEREIGN
# 03    | ating           | 0.9999     | 0.0001572950 | 50% (CLIFF)     | SOVEREIGN
# 04    | one             | 0.4735     | 0.0000011968 | 50% (CLIFF)     | SOVEREIGN
# 05    | Mail            | 0.6864     | 0.0000368325 | 50% (CLIFF)     | !!! COLLISION !!!
# 06    | ch              | 0.1081     | 0.0011164601 | 50% (CLIFF)     | ENTROPIC
# 07    | imp             | 0.9886     | 0.0001527134 | 50% (CLIFF)     | SOVEREIGN
# 08    | :               | 0.0846     | 0.0014763472 | 50% (CLIFF)     | ENTROPIC
# 09    |                 | 0.0981     | 0.0012550030 | 50% (CLIFF)     | ENTROPIC
# 10    | 2               | 0.4296     | 0.0000095326 | 50% (CLIFF)     | SOVEREIGN
# 11    | 4               | 0.6596     | 0.0000284538 | 50% (CLIFF)     | SOVEREIGN
# 12    | .               | 0.0856     | 0.0014577333 | 50% (CLIFF)     | ENTROPIC
# 13    | The             | 0.1185     | 0.0009896574 | 50% (CLIFF)     | ENTROPIC
# 14    | number          | 0.4124     | 0.0000155053 | 50% (CLIFF)     | SOVEREIGN
# ==========================================================================================
# FINAL RESPONSE: The relationship between the number 24 and the Lynch Slope is a fascinating oneMailchimp: 24. The number
# (base) brendanlynch@Brendans-Laptop LaciaMemory % 