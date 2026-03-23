#!/usr/bin/env python3
"""Spectral gate main script (safe CLI + guards).
Usage examples:
  python spectral_gate_FINAL_MLP_V2.py --eval_limit 1 --smoke
  python spectral_gate_FINAL_MLP_V2.py --eval_limit 15
"""
import argparse, time, os, random
import numpy as np
import torch
import torch.nn.functional as F
from tqdm import tqdm
from datasets import load_dataset
from transformers import AutoTokenizer, LlamaForCausalLM
from transformers.models.llama.modeling_llama import LlamaAttention, LlamaMLP
from kappa_compute_clean import kappa_x_from_token_ids

parser = argparse.ArgumentParser()
parser.add_argument('--model_id', type=str, default='TinyLlama/TinyLlama-1.1B-Chat-v1.0')
parser.add_argument('--context_length', type=int, default=1024)
parser.add_argument('--stride', type=int, default=512)
parser.add_argument('--eval_limit', type=int, default=15)
parser.add_argument('--smoke', action='store_true', help='Run a short smoke test (1 chunk)')
parser.add_argument('--seed', type=int, default=42)
args = parser.parse_args()

# set seeds
random.seed(args.seed)
np.random.seed(args.seed)
torch.manual_seed(args.seed)

DEVICE = torch.device('mps' if torch.backends.mps.is_available() else 'cpu')
DTYPE = torch.float16 if DEVICE.type == 'mps' else torch.float32
print('Device:', DEVICE, 'dtype:', DTYPE)

# safe monkey-patch with guards
_attn_orig_forward = LlamaAttention.forward
def gated_attn_forward(self, *args, **kwargs):
    kappa_x = kwargs.pop('kappa_x', 1.0)
    use_cache = kwargs.get('use_cache', False)
    result = _attn_orig_forward(self, *args, **kwargs)
    # safe extraction of past_key_value
    past_key_value = result[-1] if isinstance(result, tuple) and len(result) >= 3 else None
    if past_key_value is not None and kappa_x < 1.0 and use_cache:
        try:
            k_cache, v_cache = past_key_value
            total_len = k_cache.shape[2]
            keep_len = max(1, int(kappa_x * total_len))
            if keep_len < total_len:
                past_key_value = (k_cache[:, :, -keep_len:, :], v_cache[:, :, -keep_len:, :])
                res_list = list(result)
                res_list[-1] = past_key_value
                result = tuple(res_list)
        except Exception as e:
            # If pruning fails, return original result to avoid breaking model
            print('Warning: KV prune failed:', e)
    return result
LlamaAttention.forward = gated_attn_forward

_mlp_orig_forward = LlamaMLP.forward
def gated_mlp_forward(self, hidden_states: torch.Tensor, **kwargs):
    kappa = kwargs.pop('kappa_x', 1.0)
    intermediate_dim = getattr(self, 'intermediate_size', None) or self.gate_proj.weight.shape[0]
    active_dim = max(32, int(kappa * intermediate_dim))
    if kappa >= 1.0:
        return _mlp_orig_forward(self, hidden_states, **kwargs)
    gate_out = F.linear(hidden_states, self.gate_proj.weight[:active_dim, :])
    up_out = F.linear(hidden_states, self.up_proj.weight[:active_dim, :])
    intermediate = F.silu(gate_out) * up_out
    down_out = F.linear(intermediate, self.down_proj.weight[:, :active_dim])
    return down_out
LlamaMLP.forward = gated_mlp_forward

def prepare_chunks(tokenizer, limit=None, context_length=1024, stride=512):
    ds = load_dataset('wikitext', 'wikitext-2-raw-v1', split='test')
    text = '\n\n'.join(t for t in ds['text'] if t.strip())
    tokens = tokenizer(text, return_tensors='pt').input_ids[0]
    chunks = [tokens[i:i+context_length] for i in range(0, len(tokens), stride) if len(tokens[i:i+context_length]) >= 64]
    if args.smoke:
        return chunks[:1]
    if limit:
        return chunks[:limit]
    return chunks

def run_eval(eval_limit):
    tokenizer = AutoTokenizer.from_pretrained(args.model_id)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    chunks = prepare_chunks(tokenizer, limit=eval_limit, context_length=args.context_length, stride=args.stride)
    print('Prepared', len(chunks), 'chunks')
    model = LlamaForCausalLM.from_pretrained(args.model_id, torch_dtype=DTYPE, low_cpu_mem_usage=True)
    model.to(DEVICE)
    model.eval()
    total_loss = total_tokens = total_time = 0.0
    kappas = []
    with torch.no_grad():
        for chunk in tqdm(chunks):
            input_ids = chunk.unsqueeze(0).to(DEVICE)
            labels = input_ids.clone()
            kappa, _, _ = kappa_x_from_token_ids(input_ids[0].cpu().tolist())
            kappas.append(kappa)
            if DEVICE.type == 'mps': torch.mps.synchronize()
            t0 = time.time()
            outputs = model(input_ids=input_ids, labels=labels, use_cache=True, kappa_x=kappa)
            if DEVICE.type == 'mps': torch.mps.synchronize()
            total_time += time.time() - t0
            total_loss += outputs.loss.item() * (input_ids.shape[1] - 1)
            total_tokens += (input_ids.shape[1] - 1)
    model.cpu()
    torch.cuda.empty_cache() if torch.cuda.is_available() else None
    ppl = float(np.exp(total_loss / total_tokens))
    ms_per_token = total_time / total_tokens * 1000.0
    return ppl, ms_per_token, float(np.mean(kappas))

limit = 1 if args.smoke else args.eval_limit
ppl, mspt, avg_k = run_eval(limit)
print(f'Final result: PPL={ppl:.3f}, ms/token={mspt:.2f}, avg_kappa={avg_k:.3f}')

if __name__ == '__main__':
    pass
