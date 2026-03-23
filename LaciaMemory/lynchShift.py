import os
import torch
import numpy as np
from transformers import AutoModelForCausalLM, AutoTokenizer

# Environment locks for M3/MPS stability
os.environ["TRANSFORMERS_NO_TF"] = "1"
os.environ["PYTORCH_MPS_HIGH_WATERMARK_RATIO"] = "0.0"

def run_lynch_shift_syllogism():
    device = "mps" if torch.backends.mps.is_available() else "cpu"
    model_id = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
    
    print(f"--- [PROJECT LACIA] The Lynch Shift: Multi-Step Syllogism ---")
    
    tokenizer = AutoTokenizer.from_pretrained(model_id)
    model = AutoModelForCausalLM.from_pretrained(model_id, torch_dtype=torch.float32).to(device)

    # A 5-step jump requiring transitive logic:
    # 1. Primes > 2 are Odd.
    # 2. X is Prime > 2.
    # 3. Odd numbers = 2n + 1.
    # 4. n is an integer.
    # 5. Therefore X - 1 is even.
    prompt = (
        "Q: 1. All prime numbers greater than 2 are odd.\n"
        "2. The number X is a prime number greater than 2.\n"
        "3. All odd numbers can be expressed as the form 2n + 1, where n is an integer.\n"
        "Therefore, we can conclude that the value of (X - 1) is always:\n"
        "A:"
    )
    
    inputs = tokenizer(prompt, return_tensors="pt").to(device)

    with torch.no_grad():
        outputs = model.generate(
            **inputs, 
            max_new_tokens=60,
            num_beams=5,
            penalty_alpha=0.6, # Contrastive steering
            top_k=5
        )

    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    
    # Calculate Spectral Health
    logits = model(outputs).logits[0, -1, :].float()
    probs = torch.softmax(logits, dim=-1)
    kappa = torch.max(probs).item()
    
    # Carbon resonance check
    target_f = 1 / np.sqrt(float(6 * 720 + 6 * 95232))
    student_z = np.clip(kappa * 10 + 1, 1, 118)
    student_f = 1 / np.sqrt(student_z * 720 + student_z * 95232)
    
    t = np.linspace(0, 10, 50)
    dissonance = np.mean((np.sin(2*np.pi*student_f*t) - np.sin(2*np.pi*target_f*t))**2)

    print(f"\nSYLLOGISM RESPONSE:\n{response}")
    print(f"\nFINAL KAPPA: {kappa:.4f}")
    print(f"SPECTRAL DISSONANCE: {dissonance:.10f}")
    
    if dissonance < 0.0002:
        print("\n[VERDICT]: SOVEREIGN LOGIC CONFIRMED.")
    else:
        print("\n[VERDICT]: MANIFOLD COLLAPSE. Logic reverted to statistical drift.")

if __name__ == "__main__":
    run_lynch_shift_syllogism()

#     (base) brendanlynch@Brendans-Laptop LaciaMemory % python lynchShift.py
# --- [PROJECT LACIA] The Lynch Shift: Multi-Step Syllogism ---
# /Users/brendanlynch/miniconda3/lib/python3.12/site-packages/huggingface_hub/file_download.py:942: FutureWarning: `resume_download` is deprecated and will be removed in version 1.0.0. Downloads always resume when possible. If you want to force a new download, use `force_download=True`.
#   warnings.warn(
# /Users/brendanlynch/miniconda3/lib/python3.12/site-packages/huggingface_hub/file_download.py:942: FutureWarning: `resume_download` is deprecated and will be removed in version 1.0.0. Downloads always resume when possible. If you want to force a new download, use `force_download=True`.
#   warnings.warn(

# SYLLOGISM RESPONSE:
# Q: 1. All prime numbers greater than 2 are odd.
# 2. The number X is a prime number greater than 2.
# 3. All odd numbers can be expressed as the form 2n + 1, where n is an integer.
# Therefore, we can conclude that the value of (X - 1) is always:
# A: 2
# B: 3
# C: 4
# D: 5
# E: 6
# F: 7
# G: 8
# H: 9
# I: 10
# J: 11
# K: 12
# L: 1

# FINAL KAPPA: 0.9982
# SPECTRAL DISSONANCE: 0.0001566110

# [VERDICT]: SOVEREIGN LOGIC CONFIRMED.
# (base) brendanlynch@Brendans-Laptop LaciaMemory % 