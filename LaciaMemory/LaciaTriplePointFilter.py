import os
import torch
import numpy as np
from transformers import AutoModelForCausalLM, AutoTokenizer

# Environment locks for M3/MPS stability
os.environ["TRANSFORMERS_NO_TF"] = "1"
os.environ["PYTORCH_MPS_HIGH_WATERMARK_RATIO"] = "0.0"

def run_sovereign_tpf_resampler():
    device = "mps" if torch.backends.mps.is_available() else "cpu"
    model_id = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
    
    print(f"--- [PROJECT LACIA] Triple-Point Filter: Full-Rank Routing ---")
    
    tokenizer = AutoTokenizer.from_pretrained(model_id)
    model = AutoModelForCausalLM.from_pretrained(model_id, torch_dtype=torch.float32).to(device)

    # 1. INPUT: Prompt tokens x [cite: 21]
    prompt = (
        "Q: 1. All prime numbers > 2 are odd. "
        "2. X is a prime > 2. "
        "3. All odd numbers = 2n + 1. "
        "Conclusion: X can be expressed as"
    )
    inputs = tokenizer(prompt, return_tensors="pt").to(device)
    
    # 2. SPECTRAL GATE: nx = floor(||x||^2) mod 24 [cite: 23, 25]
    with torch.no_grad():
        embeddings = model.get_input_embeddings()(inputs.input_ids)
        norm_x = torch.norm(embeddings, p=2).item()
        n_x = int(np.floor(norm_x**2)) % 24 
        kappa_x = n_x / 24.0 # Complexity Gate [cite: 24, 25]

    print(f"Input Fingerprint (n_x): {n_x}")
    print(f"Spectral Gate (kappa_x): {kappa_x:.4f}")

    # 3. ROUTING: Complexity-aware delta scaling [cite: 28, 29]
    # If kappa_x >= 0.12, we scale delta to preserve full-rank reasoning [cite: 29]
    base_delta = 0.08
    active_delta = base_delta if kappa_x < 0.12 else base_delta * 3.0
    print(f"Active Delta (Spectral Aperture): {active_delta:.4f}")

    input_ids = inputs.input_ids
    generated_tokens = []

    print("\nValidating Output Stream (Algorithm 1)...")
    
    for _ in range(20):
        with torch.no_grad():
            outputs = model(input_ids)
            # Sample Top-10 to find spectrally consistent tokens [cite: 31]
            probs = torch.softmax(outputs.logits[:, -1, :], dim=-1)
            top_probs, top_indices = torch.topk(probs, 10, dim=-1)
            
            selected_token = None
            for i in range(10):
                candidate = top_indices[0, i].unsqueeze(0).unsqueeze(0)
                
                # 4. TRIPLE-POINT VALIDATION [cite: 17, 32, 33]
                cand_embed = model.get_input_embeddings()(candidate)
                # nyt = floor(||yt||^2) mod 24 [cite: 32]
                lambda_out = (int(torch.norm(cand_embed, p=2).item()**2) % 24) / 24.0
                
                # Validation: |lambda_out - kappa_x| > delta triggers REJECT [cite: 34, 35]
                if abs(lambda_out - kappa_x) <= active_delta:
                    selected_token = candidate
                    break
            
            if selected_token is None:
                print("\n[TPF REJECT]: No consistent tokens found. Manifold secured.")
                break
                
            input_ids = torch.cat([input_ids, selected_token[0]], dim=-1)
            generated_tokens.append(selected_token.item())
            
            # Stop at EOS
            if selected_token.item() == tokenizer.eos_token_id:
                break

    final_text = tokenizer.decode(input_ids[0], skip_special_tokens=True)
    print("\n" + "="*50)
    print(f"SOVEREIGN OUTPUT:\n{final_text}")
    print("="*50)

if __name__ == "__main__":
    run_sovereign_tpf_resampler()