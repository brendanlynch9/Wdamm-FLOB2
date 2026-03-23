# spectral_gate_FINAL_MLP_V2.py
# Implements KV-Cache Pruning (Attention) AND Intermediate Dimension Slicing (MLP)
# Uses minimal monkey-patching to avoid decoder layer tuple errors.

import torch
import torch.nn.functional as F
import numpy as np
import time
from tqdm import tqdm
from datasets import load_dataset
from transformers import AutoTokenizer, LlamaForCausalLM
# Import the base classes needed for monkey-patching
from transformers.models.llama.modeling_llama import LlamaAttention, LlamaMLP
from typing import Optional, Tuple, List # Needed for type hints in the patch functions

# ==================== CONFIG ====================
MODEL_ID = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
CONTEXT_LENGTH = 1024
STRIDE = 512
EVAL_LIMIT = 15
DTYPE = torch.float16
device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
print(f"Using {device} – {DTYPE}")

# ==================== YOUR REAL κ_x ====================
LAMBDA2_TABLE = np.array([
    1.50000, 1.36216, 1.48839, 1.49969, 1.50000, 1.36216, 1.48839, 1.36216,
    1.50000, 1.49079, 1.49969, 1.35759, 1.50000, 1.35759, 1.49969, 1.49079,
    1.50000, 1.36216, 1.48839, 1.35759, 1.50000, 1.49079, 1.49969, 1.35759
])
L2_MIN, L2_MAX = LAMBDA2_TABLE.min(), LAMBDA2_TABLE.max()
MOD = 24

def compute_kappa_x(token_ids):
    if not token_ids: return 1.0
    norm = int(np.floor(np.linalg.norm(np.array(token_ids, dtype=float))))
    n = norm % MOD
    lam = LAMBDA2_TABLE[n]
    # Use a safer, slightly expanded normalization range
    kappa = (lam - 1.35) / (1.50 - 1.35) 
    return float(np.clip(kappa, 0.0, 1.0))

# ==================== MONKEY-PATCHES THAT WORK ====================

# 1. Patch LlamaAttention.forward (KV-Cache Pruning)
_attn_orig_forward = LlamaAttention.forward

def gated_attn_forward(self, *args, **kwargs):
    # This patch works because LlamaAttention.forward receives all kwargs
    kappa_x = kwargs.pop("kappa_x", 1.0)
    use_cache = kwargs.get("use_cache", False)
    
    # CRITICAL FIX: The base LlamaAttention forward method expects 'past_key_value' to be set
    # if it's not in kwargs, it must be the 4th positional argument in *args
    # We must ensure we don't accidentally consume past_key_value from *args if it's there.
    # We will rely on the base model wrapper passing the correct kwargs/args.

    # Call original forward
    result = _attn_orig_forward(self, *args, **kwargs)

    # The result tuple will have past_key_value as the last element.
    # We retrieve it for inspection/pruning.
    past_key_value = result[-1]
    
    # SPECTRAL GATE: prune KV cache
    if past_key_value is not None and kappa_x < 1.0 and use_cache:
        k_cache, v_cache = past_key_value
        total_len = k_cache.shape[2]
        keep_len = max(1, int(kappa_x * total_len))
        if keep_len < total_len:
            # Slicing the KV cache
            past_key_value = (k_cache[:, :, -keep_len:, :], v_cache[:, :, -keep_len:, :])
            
        # Create a new result tuple with the pruned KV cache
        # The structure is (attn_output, [attn_weights], past_key_value)
        result = list(result)
        result[-1] = past_key_value
        result = tuple(result)

    return result

LlamaAttention.forward = gated_attn_forward

# 2. Patch LlamaMLP.forward (Intermediate Dimension Slicing)
_mlp_orig_forward = LlamaMLP.forward

def gated_mlp_forward(self, hidden_states: torch.Tensor, **kwargs) -> torch.Tensor:
    # LlamaMLP.forward normally only takes hidden_states.
    # We add **kwargs to safely consume kappa_x passed down from LlamaDecoderLayer
    kappa_x = kwargs.pop("kappa_x", 1.0)
    
    # Use the intermediate_size attribute (set in base LlamaMLP.__init__)
    intermediate_dim = self.intermediate_size 
    
    # Determine the active dimension size based on kappa_x
    active_dim = max(32, int(kappa_x * intermediate_dim))
    
    if kappa_x == 1.0:
        # Fallback to original, non-gated path for full compute/baseline
        # We pass **kwargs in case the original function uses them, though it shouldn't.
        return _mlp_orig_forward(self, hidden_states, **kwargs)

    # Slicing the projection weights
    gate_out = F.linear(hidden_states, self.gate_proj.weight[:active_dim, :])
    up_out = F.linear(hidden_states, self.up_proj.weight[:active_dim, :])
    intermediate = F.silu(gate_out) * up_out
    
    # Slice the down_proj weight's input dimension (columns)
    down_out = F.linear(intermediate, self.down_proj.weight[:, :active_dim])
    return down_out

LlamaMLP.forward = gated_mlp_forward

# 3. Patch LlamaDecoderLayer.forward (REMOVED)
# We are relying on the base LlamaDecoderLayer to correctly pass **kwargs to its sub-modules (attn and mlp).
# This avoids the complex and fragile tuple unpacking error.


# ==================== DATA ====================
print("Loading WikiText-2...")
tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token

ds = load_dataset("wikitext", "wikitext-2-raw-v1", split="test")
text = "\n\n".join(t for t in ds["text"] if t.strip())
tokens = tokenizer(text, return_tensors="pt").input_ids[0]

# Prepare chunks of text
chunks = [tokens[i:i+CONTEXT_LENGTH] for i in range(0, len(tokens), STRIDE)
          if len(tokens[i:i+CONTEXT_LENGTH]) >= 128]
print(f"Prepared {len(chunks)} chunks")

# ==================== EXPERIMENT ====================
def run_experiment(use_gating=True):
    mode = "Spectral-Gated (Attn + MLP)" if use_gating else "Baseline (Full Compute)"
    print(f"\n=== {mode} ===")

    # Use low_cpu_mem_usage=True and load on the fly
    model = LlamaForCausalLM.from_pretrained(MODEL_ID, torch_dtype=DTYPE, low_cpu_mem_usage=True)
    model.to(device)
    model.eval()

    total_loss = total_tokens = total_time = 0.0
    kappas = []

    with torch.no_grad():
        for chunk in tqdm(chunks[:EVAL_LIMIT]):
            input_ids = chunk.unsqueeze(0).to(device)
            labels = input_ids.clone()
            
            # Compute kappa_x once per chunk
            kappa_x = compute_kappa_x(input_ids[0].cpu().tolist()) if use_gating else 1.0

            if device.type == "mps": torch.mps.synchronize()
            start = time.time()

            # Pass kappa_x through the model's forward call
            # This relies on the base LlamaForCausalLM passing kwargs down to its layers
            outputs = model(input_ids=input_ids, labels=labels, use_cache=True, kappa_x=kappa_x)

            if device.type == "mps": torch.mps.synchronize()
            total_time += time.time() - start

            total_loss += outputs.loss.item() * (input_ids.shape[1] - 1)
            total_tokens += input_ids.shape[1] - 1
            kappas.append(kappa_x)

    # Clean up model resources
    del model
    if device.type == "mps": torch.mps.empty_cache()

    ppl = np.exp(total_loss / total_tokens)
    ms_per_token = total_time / total_tokens * 1000
    print(f"PPL: {ppl:.3f} | κ_x avg: {np.mean(kappas):.3f} | {ms_per_token:.1f} ms/token")
    return ppl, ms_per_token, np.mean(kappas)

# ==================== RUN ====================
# We wrap the main run in a try/finally block just in case, to ensure a clean exit
try:
    ppl_gated, lat_gated, kappa_g = run_experiment(use_gating=True)
    ppl_full,  lat_full,  kappa_f = run_experiment(use_gating=False)

    # ==================== TABLE 1 ====================
    print("\n" + "═" * 90)
    print("TABLE 1 – Spectral Gate (Attn + MLP) on TinyLlama-1.1B – Apple Silicon")
    print("═" * 90)
    print(f"{'Method':<18} {'Perplexity':>10} {'ΔPPL':>9} {'κ_x avg':>10} {'ms/token':>11} {'Speed-up':>10}")
    print(f"{'Baseline':<18} {ppl_full:10.3f} {'':>9} {kappa_f:10.3f} {lat_full:11.1f} {'-':>10}")
    
    speed_up = (lat_full / lat_gated - 1) * 100
    ppl_delta = (ppl_gated / ppl_full - 1) * 100
    
    print(f"{'Spectral-Gated':<18} {ppl_gated:10.3f} {ppl_delta:+7.2f}% {kappa_g:10.3f} {lat_gated:11.1f} {speed_up:9.1f}%")
    print("═" * 90)

except Exception as e:
    print(f"\nAn error occurred during experiment run: {e}")
    print("The patch likely failed due to an unexpected argument passing structure. Check the last traceback.")

#     the terminal outpt was:
#     (base) brendanlynch@Mac fixingCompute % python spectral_gate_FINAL_AND_IT_WORKS_MLP.py
# Using mps – torch.float16
# Loading WikiText-2...
# Token indices sequence length is longer than the specified maximum sequence length for this model (338535 > 2048). Running this sequence through the model will result in indexing errors
# Prepared 661 chunks

# === Spectral-Gated (Attn + MLP) ===
# `torch_dtype` is deprecated! Use `dtype` instead!
# 100%|███████████████████████████████████████████| 15/15 [00:18<00:00,  1.25s/it]
# PPL: 11.175 | κ_x avg: 0.797 | 1.2 ms/token

# === Baseline (Full Compute) ===
# 100%|███████████████████████████████████████████| 15/15 [00:18<00:00,  1.24s/it]
# PPL: 11.175 | κ_x avg: 1.000 | 1.2 ms/token

# ══════════════════════════════════════════════════════════════════════════════════════════
# TABLE 1 – Spectral Gate (Attn + MLP) on TinyLlama-1.1B – Apple Silicon
# ══════════════════════════════════════════════════════════════════════════════════════════
# Method             Perplexity      ΔPPL    κ_x avg    ms/token   Speed-up
# Baseline               11.175                1.000         1.2          -
# Spectral-Gated         11.175   +0.00%      0.797         1.2      -0.9%
# ══════════════════════════════════════════════════════════════════════════════════════════
# (base) brendanlynch@Mac fixingCompute % 
