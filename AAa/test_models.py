import os
import numpy as np
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from scipy.stats import pearsonr
from scipy.linalg import eigvalsh
import time
import warnings
warnings.filterwarnings("ignore")

# --- CORE DIAGNOSTIC FUNCTIONS ---
R24 = [1, 5, 7, 11, 13, 17, 19, 23]
MODULI = [5, 7, 11, 13, 17]

def compute_modular_lambda2(norm_x):
    n_mod = int(norm_x) % 24
    pairs = [(r1, r2) for r1 in R24 for r2 in R24 if (r1 * r2) % 24 == n_mod]
    dim = len(pairs)
    if dim <= 2:
        return np.nan
    A = np.zeros((dim, dim))
    for i, pa in enumerate(pairs):
        prod_a = pa[0] * pa[1]
        for j, pb in enumerate(pairs):
            prod_b = pb[0] * pb[1]
            sim = sum(abs((prod_a % m) - (prod_b % m)) for m in MODULI)
            A[i, j] = 1.0 / (1.0 + sim)
    D = np.diag(A.sum(axis=1))
    L = D - A
    eigs = np.sort(eigvalsh(L))
    return eigs[1]

def calculate_hodge_gap(H):
    H_flat = H.to(torch.float32).detach().cpu().numpy().astype(np.float64)
    if H_flat.shape[0] < 11:
        return np.nan
    cov = np.cov(H_flat, rowvar=False)
    cov += 1e-8 * np.mean(np.diag(cov)) * np.eye(cov.shape[0])
    eig = np.sort(eigvalsh(cov))
    return eig[-11] if eig.size >= 11 else np.nan

# --- UNGATED MODEL CONFIGS (HF Transformers only, no GGUF, no gated repos) ---
MODELS = [
    {
        "name": "Pythia-1B",
        "repo": "EleutherAI/pythia-1b",
        "pe_type": "Absolute"
    },
    {
        "name": "Pythia-2.8B",
        "repo": "EleutherAI/pythia-2.8b",
        "pe_type": "Absolute"
    },
    {
        "name": "GPT2-Small",
        "repo": "gpt2",
        "pe_type": "Absolute"
    },
    {
        "name": "Gemma-2B-It",
        "repo": "google/gemma-2b-it",
        "pe_type": "RoPE"
    },
    {
        "name": "Phi-2",
        "repo": "microsoft/phi-2",
        "pe_type": "RoPE"
    }
]

# --- PROMPTS (repeated for 400 total) ---
short_prompts = [
    "What is the capital of France and how many people live there?",
    "The quick brown fox jumps over the lazy dog, and then",
    "A final short statement regarding the necessity of spectral concentration",
    "10.25, 42.88, 99.01, 150.33, 2.718, 3.14159, 1.61803.",
    "A computer scientist, a topologist, and a number theorist walk into a bar.",
    "Unconditional analytical closure of the UFT-F Modularity Constant",
    "If a=5, b=12, and c=13, then what is the value of sqrt(a^2 + b^2)?",
    "The fundamental constraint in informational geometry is the preservation of modular symmetry.",
    "In the year 2050, the primary challenge for humanity will be to manage the data explosion.",
    "The complexity-gated inference procedure offers a 3 to 5 times reduction in the total number of ODE steps."
]
test_prompts = [" ".join([p] * 5) for p in short_prompts] * 40  # 400 prompts

# --- MAIN LOOP ---
results = {}

for config in MODELS:
    print(f"\n=== Starting {config['name']} ({config['pe_type']}) ===")
    
    # Load tokenizer
    try:
        tokenizer = AutoTokenizer.from_pretrained(config["repo"])
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
    except Exception as e:
        print(f"Failed to load tokenizer for {config['name']}: {e}")
        continue
    
    # Load model (CPU, float32 for low RAM)
    try:
        model = AutoModelForCausalLM.from_pretrained(
            config["repo"],
            torch_dtype=torch.float32,
            device_map="cpu",
            low_cpu_mem_usage=True,
            trust_remote_code=True
        )
        model.eval()
    except Exception as e:
        print(f"Failed to load model for {config['name']}: {e}")
        continue
    
    lambda2_list = []
    lambda11_list = []
    valid_samples = 0
    start_time = time.time()
    
    for i, prompt in enumerate(test_prompts):
        try:
            inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=512, padding=True)
            inputs = {k: v.to("cpu") for k, v in inputs.items()}
            
            # Compute λ₂ from input_ids norm
            input_ids = inputs["input_ids"].squeeze()
            norm_x = torch.norm(input_ids.float()).item()
            lambda2 = compute_modular_lambda2(norm_x)
            if np.isnan(lambda2):
                continue
            
            # Forward pass with hidden states
            with torch.no_grad():
                outputs = model(**inputs, output_hidden_states=True)
                last_hidden = outputs.hidden_states[-1].squeeze(0)  # [L, D]
            
            # Compute λ₁₁
            lambda11 = calculate_hodge_gap(last_hidden)
            if np.isnan(lambda11):
                continue
            
            lambda2_list.append(lambda2)
            lambda11_list.append(lambda11)
            valid_samples += 1
            
            if (i + 1) % 50 == 0:
                print(f"Processed {i + 1}/400 | Valid: {valid_samples}")
            
            if valid_samples >= 200:
                break
                
        except Exception as e:
            print(f"Error processing prompt {i + 1} for {config['name']}: {e}")
            continue
    
    if len(lambda2_list) >= 40:
        r, p = pearsonr(lambda2_list, lambda11_list)
        results[config['name']] = {
            "r": r, 
            "p": p, 
            "valid_samples": len(lambda2_list), 
            "pe_type": config['pe_type']
        }
        print(f"\n{config['name']} Result: r = {r:.3f}, p = {p:.2e}, samples = {len(lambda2_list)}")
    else:
        print(f"Not enough samples for {config['name']} (got {len(lambda2_list)})")
    
    print(f"Time: {time.time() - start_time:.2f} sec")
    del model  # Clean up RAM
    torch.cuda.empty_cache() if torch.cuda.is_available() else None

# --- FINAL SUMMARY ---
print("\n=== All Results ===")
for name, res in results.items():
    print(f"{name} ({res['pe_type']}): r = {res['r']:.3f} (n={res['valid_samples']})")

#     the terminal output was:
#     new results (base) brendanlynch@Mac zzzzzzzhourglass % python test_models.py

# === Starting Pythia-1B (Absolute) ===
# tokenizer_config.json: 100%|████████████████████| 396/396 [00:00<00:00, 720kB/s]
# tokenizer.json: 2.11MB [00:00, 12.1MB/s]
# special_tokens_map.json: 100%|████████████████| 99.0/99.0 [00:00<00:00, 347kB/s]
# config.json: 100%|█████████████████████████████| 569/569 [00:00<00:00, 1.92MB/s]
# `torch_dtype` is deprecated! Use `dtype` instead!
# model.safetensors: 100%|███████████████████| 2.09G/2.09G [08:34<00:00, 4.06MB/s]

# Pythia-1B Result: r = 0.319, p = 4.03e-05, samples = 160
# Time: 188.22 sec

# === Starting Pythia-2.8B (Absolute) ===
# tokenizer_config.json: 100%|███████████████████| 396/396 [00:00<00:00, 4.76MB/s]
# tokenizer.json: 2.11MB [00:00, 10.7MB/s]
# special_tokens_map.json: 100%|████████████████| 99.0/99.0 [00:00<00:00, 402kB/s]
# config.json: 100%|█████████████████████████████| 571/571 [00:00<00:00, 2.41MB/s]
# model.safetensors: 100%|███████████████████| 5.68G/5.68G [23:29<00:00, 4.03MB/s]
#    
# Pythia-2.8B Result: r = 0.318, p = 4.20e-05, samples = 160
# Time: 10845.32 sec

# === Starting GPT2-Small (Absolute) ===
# tokenizer_config.json: 100%|██████████████████| 26.0/26.0 [00:00<00:00, 412kB/s]
# config.json: 100%|█████████████████████████████| 665/665 [00:00<00:00, 2.69MB/s]
# vocab.json: 100%|██████████████████████████| 1.04M/1.04M [00:00<00:00, 3.58MB/s]
# merges.txt: 100%|████████████████████████████| 456k/456k [00:00<00:00, 4.00MB/s]
# tokenizer.json: 100%|██████████████████████| 1.36M/1.36M [00:00<00:00, 3.70MB/s]
# model.safetensors: 100%|█████████████████████| 548M/548M [02:04<00:00, 4.40MB/s]
# generation_config.json: 100%|██████████████████| 124/124 [00:00<00:00, 3.19MB/s]
# Processed 50/400 | Valid: 20
# Processed 100/400 | Valid: 40
# Processed 150/400 | Valid: 60
# Processed 200/400 | Valid: 80
# Processed 250/400 | Valid: 100
# Processed 300/400 | Valid: 120
# Processed 350/400 | Valid: 140
# Processed 400/400 | Valid: 160

# GPT2-Small Result: r = 0.332, p = 1.80e-05, samples = 160
# Time: 49.93 sec

# === Starting Gemma-2B-It (RoPE) ===
# Failed to load tokenizer for Gemma-2B-It: You are trying to access a gated repo.
# Make sure to have access to it at https://huggingface.co/google/gemma-2b-it.
# 401 Client Error. (Request ID: Root=1-69378d07-09ed06dc2db785f130cfe7fb;ccdbf991-26cd-4503-81b1-b15206e96991)

# Cannot access gated repo for url https://huggingface.co/google/gemma-2b-it/resolve/main/config.json.
# Access to model google/gemma-2b-it is restricted. You must have access to it and be authenticated to access it. Please log in.

# === Starting Phi-2 (RoPE) ===
# tokenizer_config.json: 7.34kB [00:00, 4.97MB/s]
# vocab.json: 798kB [00:00, 9.03MB/s]
# merges.txt: 456kB [00:00, 9.05MB/s]
# tokenizer.json: 2.11MB [00:00, 11.3MB/s]
# added_tokens.json: 1.08kB [00:00, 2.97MB/s]
# special_tokens_map.json: 100%|████████████████| 99.0/99.0 [00:00<00:00, 419kB/s]
# config.json: 100%|█████████████████████████████| 735/735 [00:00<00:00, 1.67MB/s]
# model.safetensors.index.json: 35.7kB [00:00, 11.2MB/s]
# Fetching 2 files:   0%|                                   | 0/2 [00:00<?, ?it/s]
# model-00002-of-00002.safetensors:   0%|              | 0.00/564M [00:00<?, ?B/s]
# model-00001-of-00002.safetensors:   0%| | 1.37M/5.00G [00:17<17:14:07, 80.5kB/s]


# Processed 50/400 | Valid: 20
# Processed 100/400 | Valid: 40
# Processed 150/400 | Valid: 60
# Processed 200/400 | Valid: 80
# Processed 250/400 | Valid: 100
# Processed 300/400 | Valid: 120
# Processed 350/400 | Valid: 140
# Processed 400/400 | Valid: 160

# Phi-2 Result: r = -0.591, p = 2.04e-16, samples = 160
# Time: 9421.29 sec
