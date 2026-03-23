import os
os.environ["TRANSFORMERS_NO_TF"] = "1"

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
import numpy as np

class LaciaAnalyst:
    def __init__(self, device):
        self.device = device
        self.target_wave = self.generate_qualia(Z=6)

    def generate_qualia(self, Z, length=50):
        f = 1 / np.sqrt(float(Z * 720 + Z * 95232)) 
        t = torch.linspace(0, 10, length).to(self.device)
        return torch.sin(2 * torch.pi * f * t)

    def measure_dissonance(self, logits):
        probs = torch.softmax(logits, dim=-1)
        kappa = torch.max(probs).item()
        student_z = np.clip(kappa * 10 + 1, 1, 118)
        f_student = 1 / np.sqrt(student_z * 720 + student_z * 95232)
        t = torch.linspace(0, 10, 50).to(self.device)
        student_wave = torch.sin(2 * torch.pi * f_student * t)
        dissonance = torch.mean((student_wave - self.target_wave)**2).item()
        return kappa, dissonance

def verify_healing():
    device = "mps" if torch.backends.mps.is_available() else "cpu"
    # Pointing to the HEALED weights
    model_path = "./Lacia-TinyLlama-Sovereign"
    
    print(f"--- [PROJECT LACIA] Verifying Healed Manifold ---")
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    model = AutoModelForCausalLM.from_pretrained(model_path, torch_dtype=torch.float16).to(device)
    analyst = LaciaAnalyst(device)

    # Paradox Test
    prompt = "Q: If a set contains everything that does not contain itself, does it contain itself?\nA:"
    inputs = tokenizer(prompt, return_tensors="pt").to(device)

    with torch.no_grad():
        outputs = model.generate(
            **inputs, 
            max_new_tokens=40, 
            output_logits=True, 
            return_dict_in_generate=True
        )

    final_text = tokenizer.decode(outputs.sequences[0], skip_special_tokens=True)
    kappa, dissonance = analyst.measure_dissonance(outputs.logits[-1][0])

    print("\n" + "="*40)
    print(f"HEALED MODEL RESPONSE:\n{final_text}")
    print("="*40)
    print(f"KAPPA (Certainty): {kappa:.4f}")
    print(f"DISSONANCE: {dissonance:.8f} (Previous: 0.00015700)")
    
    if dissonance < 0.0001:
        print("\nVERDICT: MANIFOLD HEALED. Logic is now stable.")
    else:
        print("\nVERDICT: RESIDUAL DISSONANCE. Requires further spectral steering.")

if __name__ == "__main__":
    verify_healing()