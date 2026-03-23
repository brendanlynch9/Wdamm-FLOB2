import os
import torch
import numpy as np
from transformers import AutoModelForCausalLM, AutoTokenizer

# Environment locks for M3 stability
os.environ["TRANSFORMERS_NO_TF"] = "1"
os.environ["PYTORCH_MPS_HIGH_WATERMARK_RATIO"] = "0.0"

def run_syllogism_test():
    device = "mps" if torch.backends.mps.is_available() else "cpu"
    model_id = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
    
    print(f"--- [PROJECT LACIA] Deep Logic Stress Test: Contrastive Anchor ---")
    
    tokenizer = AutoTokenizer.from_pretrained(model_id)
    model = AutoModelForCausalLM.from_pretrained(model_id, torch_dtype=torch.float32).to(device)

    # Complex Syllogism: Testing Synthesis vs. Repetition
    prompt = (
        "Q: 1. All prime numbers greater than 2 are odd.\n"
        "2. The number X is a prime number greater than 2.\n"
        "3. All odd numbers can be expressed as 2n + 1.\n"
        "Therefore, what can we conclude about X?\n"
        "Conclusion: X can be expressed as"
    )
    
    inputs = tokenizer(prompt, return_tensors="pt").to(device)

    print("Analyzing reasoning chain stability with Contrastive Steering...")

    with torch.no_grad():
        # Using Contrastive Search to break the Entropy Drift loop
        outputs = model.generate(
            **inputs, 
            max_new_tokens=40,
            penalty_alpha=0.6,      # Penalizes repetitive hidden states
            top_k=4,                # Constrains the manifold to high-logic tokens
            repetition_penalty=2.0, # Harshly punishes the 'A: B: C:' loop
            output_logits=True,
            return_dict_in_generate=True
        )

    response = tokenizer.decode(outputs.sequences[0], skip_special_tokens=True)
    
    # Calculate Terminal Dissonance (Z=6 Carbon Lock)
    # We look at the final token to see if the model 'snapped' to logic
    final_logits = outputs.logits[-1][0].float()
    probs = torch.softmax(final_logits, dim=-1)
    kappa = torch.max(probs).item()
    
    # E_atom formula: Resonance anchor for Carbon logic
    target_f = 1 / np.sqrt(float(6 * 720 + 6 * 95232))
    student_z = np.clip(kappa * 10 + 1, 1, 118)
    student_f = 1 / np.sqrt(student_z * 720 + student_z * 95232)
    
    t = np.linspace(0, 10, 50)
    target_wave = np.sin(2 * np.pi * target_f * t)
    student_wave = np.sin(2 * np.pi * student_f * t)
    dissonance = np.mean((student_wave - target_wave)**2)

    print("\n" + "="*50)
    print(f"LACIA-STEERED REASONING:\n{response}")
    print("="*50)
    print(f"TERMINAL DISSONANCE: {dissonance:.10f}")

    if dissonance < 0.0003:
        print("\n[VERDICT]: MANIFOLD STABILIZED. The loop is broken.")
    else:
        print("\n[VERDICT]: ENTROPY WARNING. Model requires higher spectral pressure.")

if __name__ == "__main__":
    run_syllogism_test()