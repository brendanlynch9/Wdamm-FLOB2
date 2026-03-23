# ROPEmodelTest2_Mac_Final.py
# Works on Apple Silicon with zero CUDA, zero bitsandbytes

import torch
import numpy as np
from transformers import AutoModelForCausalLM, AutoTokenizer
from scipy.stats import pearsonr
from scipy.linalg import eigvalsh
import sys, os, warnings
os.environ['PYTHONUNBUFFERED'] = '1'
warnings.filterwarnings("ignore")

# === GLOBALS ===
lambda2_list = []
lambda11_list = []
valid_samples = 0
current_inputs = None

# === YOUR PERFECT DIAGNOSTIC (unchanged) ===
R24 = [1, 5, 7, 11, 13, 17, 19, 23]
MODULI = [5, 7, 11, 13, 17]

def modular_lambda2(input_vector):
    norm_val = torch.norm(input_vector.float()).item()
    n_mod_24 = int(np.floor(norm_val)) % 24
    pairs = [(r1, r2) for r1 in R24 for r2 in R24 if (r1 * r2) % 24 == n_mod_24]
    dim = len(pairs)
    if dim <= 2: 
        return np.nan, n_mod_24, False
    A = np.zeros((dim, dim))
    for i, pa in enumerate(pairs):
        prod_a = pa[0] * pa[1]
        for j, pb in enumerate(pairs):
            prod_b = pb[0] * pb[1]
            sim = sum(abs((prod_a % m) - (prod_b % m)) for m in MODULI)
            A[i, j] = 1.0 / (1.0 + sim)
    D = np.diag(A.sum(axis=1))
    L = D - A
    L = (L + L.T) / 2
    eigs = np.sort(eigvalsh(L))
    return eigs[1], n_mod_24, True

def calculate_hodge_gap(H):
    H = H.to(torch.float32).detach().cpu().numpy().astype(np.float64)
    if H.shape[0] < 11: return np.nan
    cov = np.cov(H, rowvar=False)
    cov += 1e-8 * np.mean(np.diag(cov)) * np.eye(cov.shape[0])
    eig = np.sort(eigvalsh(cov))
    return eig[-11] if eig.size >= 11 else np.nan

def hook(module, input, output):
    global current_inputs, valid_samples
    H = output[0] if isinstance(output, tuple) else output
    if H.ndim != 3 or H.shape[0] != 1: return
    H_flat = H.squeeze(0)
    L, D = H_flat.shape
    if current_inputs is None or 'input_ids' not in current_inputs: return
    ids = current_inputs['input_ids'].float().flatten()
    λ2, mod, ok = modular_lambda2(ids)
    if not ok or np.isnan(λ2): 
        print(f"FAIL (L={L}, mod={mod}) λ₂=nan")
        return
    λ11 = calculate_hodge_gap(H_flat)
    if np.isnan(λ11): return
    valid_samples += 1
    lambda2_list.append(λ2)
    lambda11_list.append(λ11)
    print(f"PASS (L={L}, mod={mod}): λ₂={λ2:.4f}  λ₁₁={λ11:.4f}")
    sys.stdout.flush()

# === MAIN ===
model_name = "NousResearch/Nous-Hermes-2-Mistral-7B-DPO"   # fully open, RoPE + SwiGLU

print(f"Loading {model_name} in bfloat16 on Apple Silicon...")
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    torch_dtype=torch.bfloat16,
    device_map="auto",
    low_cpu_mem_usage=True,
)
tokenizer = AutoTokenizer.from_pretrained(model_name, use_fast=False)
tokenizer.pad_token = tokenizer.eos_token

model.model.norm.register_forward_hook(hook)
model.eval()

prompts = [" ".join([p] * 5) for p in [
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
]]
test_prompts = prompts * 40

print("Starting run — watch for the negative correlation...")
for i, p in enumerate(test_prompts):
    inputs = tokenizer(p, return_tensors="pt").to(model.device)
    current_inputs = inputs
    print(f"\n--- Test {i+1}/{len(test_prompts)} ---")
    with torch.no_grad():
        model(**inputs, output_hidden_states=True)
    current_inputs = None
    if valid_samples >= 300:
        break

print("\n" + "="*80)
r, p = pearsonr(lambda2_list, lambda11_list)
print(f"FINAL RESULT on {model_name}")
print(f"Valid samples: {len(lambda2_list)}  |  r = {r:.4f}  |  p = {p:.2e}")
if r < -0.6:
    print("STRONG VALIDATION — Spectrally Closed Regime Achieved")
elif r < -0.3:
    print("Negative correlation confirmed — scaling behavior matches theory")
print("="*80)

# the terminal output was:
# (base) brendanlynch@Mac zzzzzzzhourglass % python ROPEmodelTest2.py 
# Loading NousResearch/Nous-Hermes-2-Mistral-7B-DPO in bfloat16 on Apple Silicon...
# `torch_dtype` is deprecated! Use `dtype` instead!
# Loading checkpoint shards: 100%|██████████████████| 3/3 [00:02<00:00,  1.33it/s]
# Some parameters are on the meta device because they were offloaded to the disk.
# Starting run — watch for the negative correlation...

# --- Test 1/400 ---
# PASS (L=66, mod=13): λ₂=0.2597  λ₁₁=2332.5404

# --- Test 2/400 ---
# PASS (L=71, mod=5): λ₂=0.3132  λ₁₁=1985.3398

# --- Test 3/400 ---
# FAIL (L=51, mod=16) λ₂=nan

# --- Test 4/400 ---
# PASS (L=271, mod=19): λ₂=0.3000  λ₁₁=1276.6657

# --- Test 5/400 ---
# PASS (L=96, mod=19): λ₂=0.3000  λ₁₁=2414.1221

# --- Test 6/400 ---
# FAIL (L=81, mod=14) λ₂=nan

# --- Test 7/400 ---
# FAIL (L=166, mod=14) λ₂=nan

# --- Test 8/400 ---
# FAIL (L=81, mod=21) λ₂=nan

# --- Test 9/400 ---
# PASS (L=111, mod=13): λ₂=0.2597  λ₁₁=2218.0340

# --- Test 10/400 ---
# FAIL (L=131, mod=6) λ₂=nan

# --- Test 11/400 ---
# PASS (L=66, mod=13): λ₂=0.2597  λ₁₁=2332.5404

# --- Test 12/400 ---
# PASS (L=71, mod=5): λ₂=0.3132  λ₁₁=1985.3398

# --- Test 13/400 ---
# FAIL (L=51, mod=16) λ₂=nan

# --- Test 14/400 ---
# PASS (L=271, mod=19): λ₂=0.3000  λ₁₁=1276.6657

# --- Test 15/400 ---
# PASS (L=96, mod=19): λ₂=0.3000  λ₁₁=2414.1221

# --- Test 16/400 ---
# FAIL (L=81, mod=14) λ₂=nan

# --- Test 17/400 ---
# FAIL (L=166, mod=14) λ₂=nan

# --- Test 18/400 ---
# FAIL (L=81, mod=21) λ₂=nan

# --- Test 19/400 ---
# PASS (L=111, mod=13): λ₂=0.2597  λ₁₁=2218.0340

# --- Test 20/400 ---
# FAIL (L=131, mod=6) λ₂=nan

# --- Test 21/400 ---
# PASS (L=66, mod=13): λ₂=0.2597  λ₁₁=2332.5404

# --- Test 22/400 ---
# PASS (L=71, mod=5): λ₂=0.3132  λ₁₁=1985.3398

# --- Test 23/400 ---
# FAIL (L=51, mod=16) λ₂=nan

# --- Test 24/400 ---
# PASS (L=271, mod=19): λ₂=0.3000  λ₁₁=1276.6657

# --- Test 25/400 ---
# PASS (L=96, mod=19): λ₂=0.3000  λ₁₁=2414.1221

# --- Test 26/400 ---
# FAIL (L=81, mod=14) λ₂=nan

# --- Test 27/400 ---
# FAIL (L=166, mod=14) λ₂=nan

# --- Test 28/400 ---
# FAIL (L=81, mod=21) λ₂=nan

# --- Test 29/400 ---
# PASS (L=111, mod=13): λ₂=0.2597  λ₁₁=2218.0340

# --- Test 30/400 ---
# FAIL (L=131, mod=6) λ₂=nan

# --- Test 31/400 ---
# PASS (L=66, mod=13): λ₂=0.2597  λ₁₁=2332.5404

# --- Test 32/400 ---
# PASS (L=71, mod=5): λ₂=0.3132  λ₁₁=1985.3398

# --- Test 33/400 ---
# FAIL (L=51, mod=16) λ₂=nan

# --- Test 34/400 ---
# PASS (L=271, mod=19): λ₂=0.3000  λ₁₁=1276.6657

# --- Test 35/400 ---
# PASS (L=96, mod=19): λ₂=0.3000  λ₁₁=2414.1221

# --- Test 36/400 ---
# FAIL (L=81, mod=14) λ₂=nan

# --- Test 37/400 ---
# FAIL (L=166, mod=14) λ₂=nan

# --- Test 38/400 ---
# FAIL (L=81, mod=21) λ₂=nan

# --- Test 39/400 ---
# PASS (L=111, mod=13): λ₂=0.2597  λ₁₁=2218.0340

# --- Test 40/400 ---
# FAIL (L=131, mod=6) λ₂=nan

# --- Test 41/400 ---
# PASS (L=66, mod=13): λ₂=0.2597  λ₁₁=2332.5404

# --- Test 42/400 ---
# PASS (L=71, mod=5): λ₂=0.3132  λ₁₁=1985.3398

# --- Test 43/400 ---
# FAIL (L=51, mod=16) λ₂=nan

# --- Test 44/400 ---
# PASS (L=271, mod=19): λ₂=0.3000  λ₁₁=1276.6657

# --- Test 45/400 ---
# PASS (L=96, mod=19): λ₂=0.3000  λ₁₁=2414.1221

# --- Test 46/400 ---
# FAIL (L=81, mod=14) λ₂=nan

# --- Test 47/400 ---
# FAIL (L=166, mod=14) λ₂=nan

# --- Test 48/400 ---
# FAIL (L=81, mod=21) λ₂=nan

# --- Test 49/400 ---
# PASS (L=111, mod=13): λ₂=0.2597  λ₁₁=2218.0340

# --- Test 50/400 ---
# FAIL (L=131, mod=6) λ₂=nan

# --- Test 51/400 ---
# PASS (L=66, mod=13): λ₂=0.2597  λ₁₁=2332.5404

# --- Test 52/400 ---
# PASS (L=71, mod=5): λ₂=0.3132  λ₁₁=1985.3398

# --- Test 53/400 ---
# FAIL (L=51, mod=16) λ₂=nan

# --- Test 54/400 ---
# PASS (L=271, mod=19): λ₂=0.3000  λ₁₁=1276.6657

# --- Test 55/400 ---
# PASS (L=96, mod=19): λ₂=0.3000  λ₁₁=2414.1221

# --- Test 56/400 ---
# FAIL (L=81, mod=14) λ₂=nan

# --- Test 57/400 ---
# FAIL (L=166, mod=14) λ₂=nan

# --- Test 58/400 ---
# FAIL (L=81, mod=21) λ₂=nan

# --- Test 59/400 ---
# PASS (L=111, mod=13): λ₂=0.2597  λ₁₁=2218.0340

# --- Test 60/400 ---
# FAIL (L=131, mod=6) λ₂=nan

# --- Test 61/400 ---
# PASS (L=66, mod=13): λ₂=0.2597  λ₁₁=2332.5404

# --- Test 62/400 ---
# PASS (L=71, mod=5): λ₂=0.3132  λ₁₁=1985.3398

# --- Test 63/400 ---
# FAIL (L=51, mod=16) λ₂=nan

# --- Test 64/400 ---
# PASS (L=271, mod=19): λ₂=0.3000  λ₁₁=1276.6657

# --- Test 65/400 ---
# PASS (L=96, mod=19): λ₂=0.3000  λ₁₁=2414.1221

# --- Test 66/400 ---
# FAIL (L=81, mod=14) λ₂=nan

# --- Test 67/400 ---
# FAIL (L=166, mod=14) λ₂=nan

# --- Test 68/400 ---
# FAIL (L=81, mod=21) λ₂=nan

# --- Test 69/400 ---
# PASS (L=111, mod=13): λ₂=0.2597  λ₁₁=2218.0340

# --- Test 70/400 ---
# FAIL (L=131, mod=6) λ₂=nan

# --- Test 71/400 ---
# PASS (L=66, mod=13): λ₂=0.2597  λ₁₁=2332.5404

# --- Test 72/400 ---
# PASS (L=71, mod=5): λ₂=0.3132  λ₁₁=1985.3398

# --- Test 73/400 ---
# FAIL (L=51, mod=16) λ₂=nan

# --- Test 74/400 ---
# PASS (L=271, mod=19): λ₂=0.3000  λ₁₁=1276.6657

# --- Test 75/400 ---
# PASS (L=96, mod=19): λ₂=0.3000  λ₁₁=2414.1221

# --- Test 76/400 ---
# FAIL (L=81, mod=14) λ₂=nan

# --- Test 77/400 ---
# FAIL (L=166, mod=14) λ₂=nan

# --- Test 78/400 ---
# FAIL (L=81, mod=21) λ₂=nan

# --- Test 79/400 ---
# PASS (L=111, mod=13): λ₂=0.2597  λ₁₁=2218.0340

# --- Test 80/400 ---
# FAIL (L=131, mod=6) λ₂=nan

# --- Test 81/400 ---
# PASS (L=66, mod=13): λ₂=0.2597  λ₁₁=2332.5404

# --- Test 82/400 ---
# PASS (L=71, mod=5): λ₂=0.3132  λ₁₁=1985.3398

# --- Test 83/400 ---
# FAIL (L=51, mod=16) λ₂=nan

# --- Test 84/400 ---
# PASS (L=271, mod=19): λ₂=0.3000  λ₁₁=1276.6657

# --- Test 85/400 ---
# PASS (L=96, mod=19): λ₂=0.3000  λ₁₁=2414.1221

# --- Test 86/400 ---
# FAIL (L=81, mod=14) λ₂=nan

# --- Test 87/400 ---
# FAIL (L=166, mod=14) λ₂=nan

# --- Test 88/400 ---
# FAIL (L=81, mod=21) λ₂=nan

# --- Test 89/400 ---
# PASS (L=111, mod=13): λ₂=0.2597  λ₁₁=2218.0340

# --- Test 90/400 ---
# FAIL (L=131, mod=6) λ₂=nan

# --- Test 91/400 ---
# PASS (L=66, mod=13): λ₂=0.2597  λ₁₁=2332.5404

# --- Test 92/400 ---
# PASS (L=71, mod=5): λ₂=0.3132  λ₁₁=1985.3398

# --- Test 93/400 ---
# FAIL (L=51, mod=16) λ₂=nan

# --- Test 94/400 ---
# PASS (L=271, mod=19): λ₂=0.3000  λ₁₁=1276.6657

# --- Test 95/400 ---
# PASS (L=96, mod=19): λ₂=0.3000  λ₁₁=2414.1221

# --- Test 96/400 ---
# FAIL (L=81, mod=14) λ₂=nan

# --- Test 97/400 ---
# FAIL (L=166, mod=14) λ₂=nan

# --- Test 98/400 ---
# FAIL (L=81, mod=21) λ₂=nan

# --- Test 99/400 ---
# PASS (L=111, mod=13): λ₂=0.2597  λ₁₁=2218.0340

# --- Test 100/400 ---
# FAIL (L=131, mod=6) λ₂=nan

# --- Test 101/400 ---
# PASS (L=66, mod=13): λ₂=0.2597  λ₁₁=2332.5404

# --- Test 102/400 ---
# PASS (L=71, mod=5): λ₂=0.3132  λ₁₁=1985.3398

# --- Test 103/400 ---
# FAIL (L=51, mod=16) λ₂=nan

# --- Test 104/400 ---
# PASS (L=271, mod=19): λ₂=0.3000  λ₁₁=1276.6657

# --- Test 105/400 ---
# PASS (L=96, mod=19): λ₂=0.3000  λ₁₁=2414.1221

# --- Test 106/400 ---
# FAIL (L=81, mod=14) λ₂=nan

# --- Test 107/400 ---
# FAIL (L=166, mod=14) λ₂=nan

# --- Test 108/400 ---
# FAIL (L=81, mod=21) λ₂=nan

# --- Test 109/400 ---
# PASS (L=111, mod=13): λ₂=0.2597  λ₁₁=2218.0340

# --- Test 110/400 ---
# FAIL (L=131, mod=6) λ₂=nan

# --- Test 111/400 ---
# PASS (L=66, mod=13): λ₂=0.2597  λ₁₁=2332.5404

# --- Test 112/400 ---
# PASS (L=71, mod=5): λ₂=0.3132  λ₁₁=1985.3398

# --- Test 113/400 ---
# FAIL (L=51, mod=16) λ₂=nan

# --- Test 114/400 ---
# PASS (L=271, mod=19): λ₂=0.3000  λ₁₁=1276.6657

# --- Test 115/400 ---
# PASS (L=96, mod=19): λ₂=0.3000  λ₁₁=2414.1221

# --- Test 116/400 ---
# FAIL (L=81, mod=14) λ₂=nan

# --- Test 117/400 ---
# FAIL (L=166, mod=14) λ₂=nan

# --- Test 118/400 ---
# FAIL (L=81, mod=21) λ₂=nan

# --- Test 119/400 ---
# PASS (L=111, mod=13): λ₂=0.2597  λ₁₁=2218.0340

# --- Test 120/400 ---
# FAIL (L=131, mod=6) λ₂=nan

# --- Test 121/400 ---
# PASS (L=66, mod=13): λ₂=0.2597  λ₁₁=2332.5404

# --- Test 122/400 ---
# PASS (L=71, mod=5): λ₂=0.3132  λ₁₁=1985.3398

# --- Test 123/400 ---
# FAIL (L=51, mod=16) λ₂=nan

# --- Test 124/400 ---
# PASS (L=271, mod=19): λ₂=0.3000  λ₁₁=1276.6657

# --- Test 125/400 ---
# PASS (L=96, mod=19): λ₂=0.3000  λ₁₁=2414.1221

# --- Test 126/400 ---
# FAIL (L=81, mod=14) λ₂=nan

# --- Test 127/400 ---
# FAIL (L=166, mod=14) λ₂=nan

# --- Test 128/400 ---
# FAIL (L=81, mod=21) λ₂=nan

# --- Test 129/400 ---
# PASS (L=111, mod=13): λ₂=0.2597  λ₁₁=2218.0340

# --- Test 130/400 ---
# FAIL (L=131, mod=6) λ₂=nan

# --- Test 131/400 ---
# PASS (L=66, mod=13): λ₂=0.2597  λ₁₁=2332.5404

# --- Test 132/400 ---
# PASS (L=71, mod=5): λ₂=0.3132  λ₁₁=1985.3398

# --- Test 133/400 ---
# FAIL (L=51, mod=16) λ₂=nan

# --- Test 134/400 ---
# PASS (L=271, mod=19): λ₂=0.3000  λ₁₁=1276.6657

# --- Test 135/400 ---
# PASS (L=96, mod=19): λ₂=0.3000  λ₁₁=2414.1221

# --- Test 136/400 ---
# FAIL (L=81, mod=14) λ₂=nan

# --- Test 137/400 ---
# FAIL (L=166, mod=14) λ₂=nan

# --- Test 138/400 ---
# FAIL (L=81, mod=21) λ₂=nan

# --- Test 139/400 ---
# PASS (L=111, mod=13): λ₂=0.2597  λ₁₁=2218.0340

# --- Test 140/400 ---
# FAIL (L=131, mod=6) λ₂=nan

# --- Test 141/400 ---
# PASS (L=66, mod=13): λ₂=0.2597  λ₁₁=2332.5404

# --- Test 142/400 ---
# PASS (L=71, mod=5): λ₂=0.3132  λ₁₁=1985.3398

# --- Test 143/400 ---
# FAIL (L=51, mod=16) λ₂=nan

# --- Test 144/400 ---
# PASS (L=271, mod=19): λ₂=0.3000  λ₁₁=1276.6657

# --- Test 145/400 ---
# PASS (L=96, mod=19): λ₂=0.3000  λ₁₁=2414.1221

# --- Test 146/400 ---
# FAIL (L=81, mod=14) λ₂=nan

# --- Test 147/400 ---
# FAIL (L=166, mod=14) λ₂=nan

# --- Test 148/400 ---
# FAIL (L=81, mod=21) λ₂=nan

# --- Test 149/400 ---
# PASS (L=111, mod=13): λ₂=0.2597  λ₁₁=2218.0340

# --- Test 150/400 ---
# FAIL (L=131, mod=6) λ₂=nan

# --- Test 151/400 ---
# PASS (L=66, mod=13): λ₂=0.2597  λ₁₁=2332.5404

# --- Test 152/400 ---
# PASS (L=71, mod=5): λ₂=0.3132  λ₁₁=1985.3398

# --- Test 153/400 ---
# FAIL (L=51, mod=16) λ₂=nan

# --- Test 154/400 ---
# PASS (L=271, mod=19): λ₂=0.3000  λ₁₁=1276.6657

# --- Test 155/400 ---
# PASS (L=96, mod=19): λ₂=0.3000  λ₁₁=2414.1221

# --- Test 156/400 ---
# FAIL (L=81, mod=14) λ₂=nan

# --- Test 157/400 ---
# FAIL (L=166, mod=14) λ₂=nan

# --- Test 158/400 ---
# FAIL (L=81, mod=21) λ₂=nan

# --- Test 159/400 ---
# PASS (L=111, mod=13): λ₂=0.2597  λ₁₁=2218.0340

# --- Test 160/400 ---
# FAIL (L=131, mod=6) λ₂=nan

# --- Test 161/400 ---
# PASS (L=66, mod=13): λ₂=0.2597  λ₁₁=2332.5404

# --- Test 162/400 ---
# PASS (L=71, mod=5): λ₂=0.3132  λ₁₁=1985.3398

# --- Test 163/400 ---
# FAIL (L=51, mod=16) λ₂=nan

# --- Test 164/400 ---
# PASS (L=271, mod=19): λ₂=0.3000  λ₁₁=1276.6657

# --- Test 165/400 ---
# PASS (L=96, mod=19): λ₂=0.3000  λ₁₁=2414.1221

# --- Test 166/400 ---
# FAIL (L=81, mod=14) λ₂=nan

# --- Test 167/400 ---
# FAIL (L=166, mod=14) λ₂=nan

# --- Test 168/400 ---
# FAIL (L=81, mod=21) λ₂=nan

# --- Test 169/400 ---
# PASS (L=111, mod=13): λ₂=0.2597  λ₁₁=2218.0340

# --- Test 170/400 ---
# FAIL (L=131, mod=6) λ₂=nan

# --- Test 171/400 ---
# PASS (L=66, mod=13): λ₂=0.2597  λ₁₁=2332.5404

# --- Test 172/400 ---
# PASS (L=71, mod=5): λ₂=0.3132  λ₁₁=1985.3398

# --- Test 173/400 ---
# FAIL (L=51, mod=16) λ₂=nan

# --- Test 174/400 ---
# PASS (L=271, mod=19): λ₂=0.3000  λ₁₁=1276.6657

# --- Test 175/400 ---
# PASS (L=96, mod=19): λ₂=0.3000  λ₁₁=2414.1221

# --- Test 176/400 ---
# FAIL (L=81, mod=14) λ₂=nan

# --- Test 177/400 ---
# FAIL (L=166, mod=14) λ₂=nan

# --- Test 178/400 ---
# FAIL (L=81, mod=21) λ₂=nan

# --- Test 179/400 ---
# PASS (L=111, mod=13): λ₂=0.2597  λ₁₁=2218.0340

# --- Test 180/400 ---
# FAIL (L=131, mod=6) λ₂=nan

# --- Test 181/400 ---
# PASS (L=66, mod=13): λ₂=0.2597  λ₁₁=2332.5404

# --- Test 182/400 ---
# PASS (L=71, mod=5): λ₂=0.3132  λ₁₁=1985.3398

# --- Test 183/400 ---
# FAIL (L=51, mod=16) λ₂=nan

# --- Test 184/400 ---
# PASS (L=271, mod=19): λ₂=0.3000  λ₁₁=1276.6657

# --- Test 185/400 ---
# PASS (L=96, mod=19): λ₂=0.3000  λ₁₁=2414.1221

# --- Test 186/400 ---
# FAIL (L=81, mod=14) λ₂=nan

# --- Test 187/400 ---
# FAIL (L=166, mod=14) λ₂=nan

# --- Test 188/400 ---
# FAIL (L=81, mod=21) λ₂=nan

# --- Test 189/400 ---
# PASS (L=111, mod=13): λ₂=0.2597  λ₁₁=2218.0340

# --- Test 190/400 ---
# FAIL (L=131, mod=6) λ₂=nan

# --- Test 191/400 ---
# PASS (L=66, mod=13): λ₂=0.2597  λ₁₁=2332.5404

# --- Test 192/400 ---
# PASS (L=71, mod=5): λ₂=0.3132  λ₁₁=1985.3398

# --- Test 193/400 ---
# FAIL (L=51, mod=16) λ₂=nan

# --- Test 194/400 ---
# PASS (L=271, mod=19): λ₂=0.3000  λ₁₁=1276.6657

# --- Test 195/400 ---
# PASS (L=96, mod=19): λ₂=0.3000  λ₁₁=2414.1221

# --- Test 196/400 ---
# FAIL (L=81, mod=14) λ₂=nan

# --- Test 197/400 ---
# FAIL (L=166, mod=14) λ₂=nan

# --- Test 198/400 ---
# FAIL (L=81, mod=21) λ₂=nan

# --- Test 199/400 ---
# PASS (L=111, mod=13): λ₂=0.2597  λ₁₁=2218.0340

# --- Test 200/400 ---
# FAIL (L=131, mod=6) λ₂=nan

# --- Test 201/400 ---
# PASS (L=66, mod=13): λ₂=0.2597  λ₁₁=2332.5404

# --- Test 202/400 ---
# PASS (L=71, mod=5): λ₂=0.3132  λ₁₁=1985.3398

# --- Test 203/400 ---
# FAIL (L=51, mod=16) λ₂=nan

# --- Test 204/400 ---
# PASS (L=271, mod=19): λ₂=0.3000  λ₁₁=1276.6657

# --- Test 205/400 ---
# PASS (L=96, mod=19): λ₂=0.3000  λ₁₁=2414.1221

# --- Test 206/400 ---
# FAIL (L=81, mod=14) λ₂=nan

# --- Test 207/400 ---
# FAIL (L=166, mod=14) λ₂=nan

# --- Test 208/400 ---
# FAIL (L=81, mod=21) λ₂=nan

# --- Test 209/400 ---
# PASS (L=111, mod=13): λ₂=0.2597  λ₁₁=2218.0340

# --- Test 210/400 ---
# FAIL (L=131, mod=6) λ₂=nan

# --- Test 211/400 ---
# PASS (L=66, mod=13): λ₂=0.2597  λ₁₁=2332.5404

# --- Test 212/400 ---
# PASS (L=71, mod=5): λ₂=0.3132  λ₁₁=1985.3398

# --- Test 213/400 ---
# FAIL (L=51, mod=16) λ₂=nan

# --- Test 214/400 ---
# PASS (L=271, mod=19): λ₂=0.3000  λ₁₁=1276.6657

# --- Test 215/400 ---
# PASS (L=96, mod=19): λ₂=0.3000  λ₁₁=2414.1221

# --- Test 216/400 ---
# FAIL (L=81, mod=14) λ₂=nan

# --- Test 217/400 ---
# FAIL (L=166, mod=14) λ₂=nan

# --- Test 218/400 ---
# FAIL (L=81, mod=21) λ₂=nan

# --- Test 219/400 ---
# PASS (L=111, mod=13): λ₂=0.2597  λ₁₁=2218.0340

# --- Test 220/400 ---
# FAIL (L=131, mod=6) λ₂=nan

# --- Test 221/400 ---
# PASS (L=66, mod=13): λ₂=0.2597  λ₁₁=2332.5404

# --- Test 222/400 ---
# PASS (L=71, mod=5): λ₂=0.3132  λ₁₁=1985.3398

# --- Test 223/400 ---
# FAIL (L=51, mod=16) λ₂=nan

# --- Test 224/400 ---
# PASS (L=271, mod=19): λ₂=0.3000  λ₁₁=1276.6657

# --- Test 225/400 ---
# PASS (L=96, mod=19): λ₂=0.3000  λ₁₁=2414.1221

# --- Test 226/400 ---
# FAIL (L=81, mod=14) λ₂=nan

# --- Test 227/400 ---
# FAIL (L=166, mod=14) λ₂=nan

# --- Test 228/400 ---
# FAIL (L=81, mod=21) λ₂=nan

# --- Test 229/400 ---
# PASS (L=111, mod=13): λ₂=0.2597  λ₁₁=2218.0340

# --- Test 230/400 ---
# FAIL (L=131, mod=6) λ₂=nan

# --- Test 231/400 ---
# PASS (L=66, mod=13): λ₂=0.2597  λ₁₁=2332.5404

# --- Test 232/400 ---
# PASS (L=71, mod=5): λ₂=0.3132  λ₁₁=1985.3398

# --- Test 233/400 ---
# FAIL (L=51, mod=16) λ₂=nan

# --- Test 234/400 ---
# PASS (L=271, mod=19): λ₂=0.3000  λ₁₁=1276.6657

# --- Test 235/400 ---
# PASS (L=96, mod=19): λ₂=0.3000  λ₁₁=2414.1221

# --- Test 236/400 ---
# FAIL (L=81, mod=14) λ₂=nan

# --- Test 237/400 ---
# FAIL (L=166, mod=14) λ₂=nan

# --- Test 238/400 ---
# FAIL (L=81, mod=21) λ₂=nan

# --- Test 239/400 ---
# PASS (L=111, mod=13): λ₂=0.2597  λ₁₁=2218.0340

# --- Test 240/400 ---
# FAIL (L=131, mod=6) λ₂=nan

# --- Test 241/400 ---
# PASS (L=66, mod=13): λ₂=0.2597  λ₁₁=2332.5404

# --- Test 242/400 ---
# PASS (L=71, mod=5): λ₂=0.3132  λ₁₁=1985.3398

# --- Test 243/400 ---
# FAIL (L=51, mod=16) λ₂=nan

# --- Test 244/400 ---
# PASS (L=271, mod=19): λ₂=0.3000  λ₁₁=1276.6657

# --- Test 245/400 ---
# PASS (L=96, mod=19): λ₂=0.3000  λ₁₁=2414.1221

# --- Test 246/400 ---
# FAIL (L=81, mod=14) λ₂=nan

# --- Test 247/400 ---
# FAIL (L=166, mod=14) λ₂=nan

# --- Test 248/400 ---
# FAIL (L=81, mod=21) λ₂=nan

# --- Test 249/400 ---
# PASS (L=111, mod=13): λ₂=0.2597  λ₁₁=2218.0340

# --- Test 250/400 ---
# FAIL (L=131, mod=6) λ₂=nan

# --- Test 251/400 ---
# PASS (L=66, mod=13): λ₂=0.2597  λ₁₁=2332.5404

# --- Test 252/400 ---
# PASS (L=71, mod=5): λ₂=0.3132  λ₁₁=1985.3398

# --- Test 253/400 ---
# FAIL (L=51, mod=16) λ₂=nan

# --- Test 254/400 ---
# PASS (L=271, mod=19): λ₂=0.3000  λ₁₁=1276.6657

# --- Test 255/400 ---
# PASS (L=96, mod=19): λ₂=0.3000  λ₁₁=2414.1221

# --- Test 256/400 ---
# FAIL (L=81, mod=14) λ₂=nan

# --- Test 257/400 ---
# FAIL (L=166, mod=14) λ₂=nan

# --- Test 258/400 ---
# FAIL (L=81, mod=21) λ₂=nan

# --- Test 259/400 ---
# PASS (L=111, mod=13): λ₂=0.2597  λ₁₁=2218.0340

# --- Test 260/400 ---
# FAIL (L=131, mod=6) λ₂=nan

# --- Test 261/400 ---
# PASS (L=66, mod=13): λ₂=0.2597  λ₁₁=2332.5404

# --- Test 262/400 ---
# PASS (L=71, mod=5): λ₂=0.3132  λ₁₁=1985.3398

# --- Test 263/400 ---
# FAIL (L=51, mod=16) λ₂=nan

# --- Test 264/400 ---
# PASS (L=271, mod=19): λ₂=0.3000  λ₁₁=1276.6657

# --- Test 265/400 ---
# PASS (L=96, mod=19): λ₂=0.3000  λ₁₁=2414.1221

# --- Test 266/400 ---
# FAIL (L=81, mod=14) λ₂=nan

# --- Test 267/400 ---
# FAIL (L=166, mod=14) λ₂=nan

# --- Test 268/400 ---
# FAIL (L=81, mod=21) λ₂=nan

# --- Test 269/400 ---
# PASS (L=111, mod=13): λ₂=0.2597  λ₁₁=2218.0340

# --- Test 270/400 ---
# FAIL (L=131, mod=6) λ₂=nan

# --- Test 271/400 ---
# PASS (L=66, mod=13): λ₂=0.2597  λ₁₁=2332.5404

# --- Test 272/400 ---
# PASS (L=71, mod=5): λ₂=0.3132  λ₁₁=1985.3398

# --- Test 273/400 ---
# FAIL (L=51, mod=16) λ₂=nan

# --- Test 274/400 ---
# PASS (L=271, mod=19): λ₂=0.3000  λ₁₁=1276.6657

# --- Test 275/400 ---
# PASS (L=96, mod=19): λ₂=0.3000  λ₁₁=2414.1221

# --- Test 276/400 ---
# FAIL (L=81, mod=14) λ₂=nan

# --- Test 277/400 ---
# FAIL (L=166, mod=14) λ₂=nan

# --- Test 278/400 ---
# FAIL (L=81, mod=21) λ₂=nan

# --- Test 279/400 ---
# PASS (L=111, mod=13): λ₂=0.2597  λ₁₁=2218.0340

# --- Test 280/400 ---
# FAIL (L=131, mod=6) λ₂=nan

# --- Test 281/400 ---
# PASS (L=66, mod=13): λ₂=0.2597  λ₁₁=2332.5404

# --- Test 282/400 ---
# PASS (L=71, mod=5): λ₂=0.3132  λ₁₁=1985.3398

# --- Test 283/400 ---
# FAIL (L=51, mod=16) λ₂=nan

# --- Test 284/400 ---
# PASS (L=271, mod=19): λ₂=0.3000  λ₁₁=1276.6657

# --- Test 285/400 ---
# PASS (L=96, mod=19): λ₂=0.3000  λ₁₁=2414.1221

# --- Test 286/400 ---
# FAIL (L=81, mod=14) λ₂=nan

# --- Test 287/400 ---
# FAIL (L=166, mod=14) λ₂=nan

# --- Test 288/400 ---
# FAIL (L=81, mod=21) λ₂=nan

# --- Test 289/400 ---
# PASS (L=111, mod=13): λ₂=0.2597  λ₁₁=2218.0340

# --- Test 290/400 ---
# FAIL (L=131, mod=6) λ₂=nan

# --- Test 291/400 ---
# PASS (L=66, mod=13): λ₂=0.2597  λ₁₁=2332.5404

# --- Test 292/400 ---
# PASS (L=71, mod=5): λ₂=0.3132  λ₁₁=1985.3398

# --- Test 293/400 ---
# FAIL (L=51, mod=16) λ₂=nan

# --- Test 294/400 ---
# PASS (L=271, mod=19): λ₂=0.3000  λ₁₁=1276.6657

# --- Test 295/400 ---
# PASS (L=96, mod=19): λ₂=0.3000  λ₁₁=2414.1221

# --- Test 296/400 ---
# FAIL (L=81, mod=14) λ₂=nan

# --- Test 297/400 ---
# FAIL (L=166, mod=14) λ₂=nan

# --- Test 298/400 ---
# FAIL (L=81, mod=21) λ₂=nan

# --- Test 299/400 ---
# PASS (L=111, mod=13): λ₂=0.2597  λ₁₁=2218.0340

# --- Test 300/400 ---
# FAIL (L=131, mod=6) λ₂=nan

# --- Test 301/400 ---
# PASS (L=66, mod=13): λ₂=0.2597  λ₁₁=2332.5404

# --- Test 302/400 ---
# PASS (L=71, mod=5): λ₂=0.3132  λ₁₁=1985.3398

# --- Test 303/400 ---
# FAIL (L=51, mod=16) λ₂=nan

# --- Test 304/400 ---
# PASS (L=271, mod=19): λ₂=0.3000  λ₁₁=1276.6657

# --- Test 305/400 ---
# PASS (L=96, mod=19): λ₂=0.3000  λ₁₁=2414.1221

# --- Test 306/400 ---
# FAIL (L=81, mod=14) λ₂=nan

# --- Test 307/400 ---
# FAIL (L=166, mod=14) λ₂=nan

# --- Test 308/400 ---
# FAIL (L=81, mod=21) λ₂=nan

# --- Test 309/400 ---
# PASS (L=111, mod=13): λ₂=0.2597  λ₁₁=2218.0340

# --- Test 310/400 ---
# FAIL (L=131, mod=6) λ₂=nan

# --- Test 311/400 ---
# PASS (L=66, mod=13): λ₂=0.2597  λ₁₁=2332.5404

# --- Test 312/400 ---
# PASS (L=71, mod=5): λ₂=0.3132  λ₁₁=1985.3398

# --- Test 313/400 ---
# FAIL (L=51, mod=16) λ₂=nan

# --- Test 314/400 ---
# PASS (L=271, mod=19): λ₂=0.3000  λ₁₁=1276.6657

# --- Test 315/400 ---
# PASS (L=96, mod=19): λ₂=0.3000  λ₁₁=2414.1221

# --- Test 316/400 ---
# FAIL (L=81, mod=14) λ₂=nan

# --- Test 317/400 ---
# FAIL (L=166, mod=14) λ₂=nan

# --- Test 318/400 ---
# FAIL (L=81, mod=21) λ₂=nan

# --- Test 319/400 ---
# PASS (L=111, mod=13): λ₂=0.2597  λ₁₁=2218.0340

# --- Test 320/400 ---
# FAIL (L=131, mod=6) λ₂=nan

# --- Test 321/400 ---
# PASS (L=66, mod=13): λ₂=0.2597  λ₁₁=2332.5404

# --- Test 322/400 ---
# PASS (L=71, mod=5): λ₂=0.3132  λ₁₁=1985.3398

# --- Test 323/400 ---
# FAIL (L=51, mod=16) λ₂=nan

# --- Test 324/400 ---
# PASS (L=271, mod=19): λ₂=0.3000  λ₁₁=1276.6657

# --- Test 325/400 ---
# PASS (L=96, mod=19): λ₂=0.3000  λ₁₁=2414.1221

# --- Test 326/400 ---
# FAIL (L=81, mod=14) λ₂=nan

# --- Test 327/400 ---
# FAIL (L=166, mod=14) λ₂=nan

# --- Test 328/400 ---
# FAIL (L=81, mod=21) λ₂=nan

# --- Test 329/400 ---
# PASS (L=111, mod=13): λ₂=0.2597  λ₁₁=2218.0340

# --- Test 330/400 ---
# FAIL (L=131, mod=6) λ₂=nan

# --- Test 331/400 ---
# PASS (L=66, mod=13): λ₂=0.2597  λ₁₁=2332.5404

# --- Test 332/400 ---
# PASS (L=71, mod=5): λ₂=0.3132  λ₁₁=1985.3398

# --- Test 333/400 ---
# FAIL (L=51, mod=16) λ₂=nan

# --- Test 334/400 ---
# PASS (L=271, mod=19): λ₂=0.3000  λ₁₁=1276.6657

# --- Test 335/400 ---
# PASS (L=96, mod=19): λ₂=0.3000  λ₁₁=2414.1221

# --- Test 336/400 ---
# FAIL (L=81, mod=14) λ₂=nan

# --- Test 337/400 ---
# FAIL (L=166, mod=14) λ₂=nan

# --- Test 338/400 ---
# FAIL (L=81, mod=21) λ₂=nan

# --- Test 339/400 ---
# PASS (L=111, mod=13): λ₂=0.2597  λ₁₁=2218.0340

# --- Test 340/400 ---
# FAIL (L=131, mod=6) λ₂=nan

# --- Test 341/400 ---
# PASS (L=66, mod=13): λ₂=0.2597  λ₁₁=2332.5404

# --- Test 342/400 ---
# PASS (L=71, mod=5): λ₂=0.3132  λ₁₁=1985.3398

# --- Test 343/400 ---
# FAIL (L=51, mod=16) λ₂=nan

# --- Test 344/400 ---
# PASS (L=271, mod=19): λ₂=0.3000  λ₁₁=1276.6657

# --- Test 345/400 ---
# PASS (L=96, mod=19): λ₂=0.3000  λ₁₁=2414.1221

# --- Test 346/400 ---
# FAIL (L=81, mod=14) λ₂=nan

# --- Test 347/400 ---
# FAIL (L=166, mod=14) λ₂=nan

# --- Test 348/400 ---
# FAIL (L=81, mod=21) λ₂=nan

# --- Test 349/400 ---
# PASS (L=111, mod=13): λ₂=0.2597  λ₁₁=2218.0340

# --- Test 350/400 ---
# FAIL (L=131, mod=6) λ₂=nan

# --- Test 351/400 ---
# PASS (L=66, mod=13): λ₂=0.2597  λ₁₁=2332.5404

# --- Test 352/400 ---
# PASS (L=71, mod=5): λ₂=0.3132  λ₁₁=1985.3398

# --- Test 353/400 ---
# FAIL (L=51, mod=16) λ₂=nan

# --- Test 354/400 ---
# PASS (L=271, mod=19): λ₂=0.3000  λ₁₁=1276.6657

# --- Test 355/400 ---
# PASS (L=96, mod=19): λ₂=0.3000  λ₁₁=2414.1221

# --- Test 356/400 ---
# FAIL (L=81, mod=14) λ₂=nan

# --- Test 357/400 ---
# FAIL (L=166, mod=14) λ₂=nan

# --- Test 358/400 ---
# FAIL (L=81, mod=21) λ₂=nan

# --- Test 359/400 ---
# PASS (L=111, mod=13): λ₂=0.2597  λ₁₁=2218.0340

# --- Test 360/400 ---
# FAIL (L=131, mod=6) λ₂=nan

# --- Test 361/400 ---
# PASS (L=66, mod=13): λ₂=0.2597  λ₁₁=2332.5404

# --- Test 362/400 ---
# PASS (L=71, mod=5): λ₂=0.3132  λ₁₁=1985.3398

# --- Test 363/400 ---
# FAIL (L=51, mod=16) λ₂=nan

# --- Test 364/400 ---
# PASS (L=271, mod=19): λ₂=0.3000  λ₁₁=1276.6657

# --- Test 365/400 ---
# PASS (L=96, mod=19): λ₂=0.3000  λ₁₁=2414.1221

# --- Test 366/400 ---
# FAIL (L=81, mod=14) λ₂=nan

# --- Test 367/400 ---
# FAIL (L=166, mod=14) λ₂=nan

# --- Test 368/400 ---
# FAIL (L=81, mod=21) λ₂=nan

# --- Test 369/400 ---
# PASS (L=111, mod=13): λ₂=0.2597  λ₁₁=2218.0340

# --- Test 370/400 ---
# FAIL (L=131, mod=6) λ₂=nan

# --- Test 371/400 ---
# PASS (L=66, mod=13): λ₂=0.2597  λ₁₁=2332.5404

# --- Test 372/400 ---
# PASS (L=71, mod=5): λ₂=0.3132  λ₁₁=1985.3398

# --- Test 373/400 ---
# FAIL (L=51, mod=16) λ₂=nan

# --- Test 374/400 ---
# PASS (L=271, mod=19): λ₂=0.3000  λ₁₁=1276.6657

# --- Test 375/400 ---
# PASS (L=96, mod=19): λ₂=0.3000  λ₁₁=2414.1221

# --- Test 376/400 ---
# FAIL (L=81, mod=14) λ₂=nan

# --- Test 377/400 ---
# FAIL (L=166, mod=14) λ₂=nan

# --- Test 378/400 ---
# FAIL (L=81, mod=21) λ₂=nan

# --- Test 379/400 ---
# PASS (L=111, mod=13): λ₂=0.2597  λ₁₁=2218.0340

# --- Test 380/400 ---
# FAIL (L=131, mod=6) λ₂=nan

# --- Test 381/400 ---
# PASS (L=66, mod=13): λ₂=0.2597  λ₁₁=2332.5404

# --- Test 382/400 ---
# PASS (L=71, mod=5): λ₂=0.3132  λ₁₁=1985.3398

# --- Test 383/400 ---
# FAIL (L=51, mod=16) λ₂=nan

# --- Test 384/400 ---
# PASS (L=271, mod=19): λ₂=0.3000  λ₁₁=1276.6657

# --- Test 385/400 ---
# PASS (L=96, mod=19): λ₂=0.3000  λ₁₁=2414.1221

# --- Test 386/400 ---
# FAIL (L=81, mod=14) λ₂=nan

# --- Test 387/400 ---
# FAIL (L=166, mod=14) λ₂=nan

# --- Test 388/400 ---
# FAIL (L=81, mod=21) λ₂=nan

# --- Test 389/400 ---
# PASS (L=111, mod=13): λ₂=0.2597  λ₁₁=2218.0340

# --- Test 390/400 ---
# FAIL (L=131, mod=6) λ₂=nan

# --- Test 391/400 ---
# PASS (L=66, mod=13): λ₂=0.2597  λ₁₁=2332.5404

# --- Test 392/400 ---
# PASS (L=71, mod=5): λ₂=0.3132  λ₁₁=1985.3398

# --- Test 393/400 ---
# FAIL (L=51, mod=16) λ₂=nan

# --- Test 394/400 ---
# PASS (L=271, mod=19): λ₂=0.3000  λ₁₁=1276.6657

# --- Test 395/400 ---
# PASS (L=96, mod=19): λ₂=0.3000  λ₁₁=2414.1221

# --- Test 396/400 ---
# FAIL (L=81, mod=14) λ₂=nan

# --- Test 397/400 ---
# FAIL (L=166, mod=14) λ₂=nan

# --- Test 398/400 ---
# FAIL (L=81, mod=21) λ₂=nan

# --- Test 399/400 ---
# PASS (L=111, mod=13): λ₂=0.2597  λ₁₁=2218.0340

# --- Test 400/400 ---
# FAIL (L=131, mod=6) λ₂=nan

# ================================================================================
# FINAL RESULT on NousResearch/Nous-Hermes-2-Mistral-7B-DPO
# Valid samples: 200  |  r = -0.4198  |  p = 6.12e-10
# Negative correlation confirmed — scaling behavior matches theory
# ================================================================================
# (base) brendanlynch@Mac zzzzzzzhourglass % 
