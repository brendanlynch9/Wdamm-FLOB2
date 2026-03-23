import os
os.environ["TRANSFORMERS_NO_TF"] = "1"
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
import numpy as np

def final_sovereign_check():
    device = "mps" if torch.backends.mps.is_available() else "cpu"
    model_path = "./Lacia-TinyLlama-Sovereign"
    
    print(f"--- [PROJECT LACIA] Phase-Lock Validation ---")
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    # Using float32 for maximum precision during the check
    model = AutoModelForCausalLM.from_pretrained(model_path, torch_dtype=torch.float32).to(device)

    # The Paradox Test (The "Chaos" Trigger)
    prompt = "Q: If a set contains everything that does not contain itself, does it contain itself?\nA:"
    inputs = tokenizer(prompt, return_tensors="pt").to(device)

    with torch.no_grad():
        outputs = model.generate(
            **inputs, 
            max_new_tokens=40,
            do_sample=False, # Deterministic check for logic stability
        )

    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    
    # Analyze final hidden state for Spectral Health
    # We'll re-calculate dissonance on the final generated token
    input_ids = outputs[0].unsqueeze(0)
    final_logits = model(input_ids).logits[0, -1, :].float()
    probs = torch.softmax(final_logits, dim=-1)
    kappa = torch.max(probs).item()
    
    # Lacia Teacher logic for Carbon-Lock (Z=6)
    target_f = 1 / np.sqrt(float(6 * 720 + 6 * 95232))
    student_z = np.clip(kappa * 10 + 1, 1, 118)
    student_f = 1 / np.sqrt(student_z * 720 + student_z * 95232)
    
    t = np.linspace(0, 10, 50)
    target_wave = np.sin(2 * np.pi * target_f * t)
    student_wave = np.sin(2 * np.pi * student_f * t)
    dissonance = np.mean((student_wave - target_wave)**2)

    print("\n" + "="*50)
    print(f"SOVEREIGN RESPONSE:\n{response}")
    print("="*50)
    print(f"SPECTRAL KAPPA: {kappa:.6f}")
    print(f"FINAL DISSONANCE: {dissonance:.10f}")
    
    if dissonance < 0.0001:
        print("\n[VERDICT]: MANIFOLD SECURED. Model is Phase-Locked.")
    else:
        print("\n[VERDICT]: RESIDUAL CHAOS. Tuning required.")

if __name__ == "__main__":
    final_sovereign_check()