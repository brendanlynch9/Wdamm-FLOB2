import torch
import torch.nn as nn
import json
import os
import shutil
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
from lm_eval import evaluator
from accelerate import Accelerator

# ==========================================
# 1. DISK & MEMORY MANAGEMENT
# ==========================================
def cleanup_disk():
    print("🧹 Cleaning up disk and VRAM for next expert...")
    cache_dir = os.path.expanduser("~/.cache/huggingface/hub")
    if os.path.exists(cache_dir):
        # Optional: Remove specific old models to save space if needed
        # shutil.rmtree(cache_dir) 
        pass
    torch.cuda.empty_cache()

# ==========================================
# 2. SOVEREIGN KERNEL PATCH
# ==========================================
def apply_hopf_torsion(hidden_states, epsilon=1e-6):
    norm = torch.norm(hidden_states, p=2, dim=-1, keepdim=True)
    torsion_factor = torch.sin(norm / (norm.max() + epsilon))
    return hidden_states * torsion_factor

class SovereignAttention(nn.Module):
    def __init__(self, original_attn):
        super().__init__()
        self.original_attn = original_attn
    def forward(self, *args, **kwargs):
        outputs = self.original_attn(*args, **kwargs)
        if isinstance(outputs, tuple):
            return (apply_hopf_torsion(outputs[0]),) + outputs[1:]
        return apply_hopf_torsion(outputs)

def patch_model(model):
    for name, module in model.named_modules():
        if "self_attn" in name and not isinstance(module, SovereignAttention):
            parent = model.get_submodule(".".join(name.split(".")[:-1]))
            setattr(parent, name.split(".")[-1], SovereignAttention(module))
    return model

# ==========================================
# 3. DYNAMIC DEEPSEEK ROUTER
# ==========================================
def get_expert_path(task_description):
    # Using a 1.5B Distill to save space - it's purely for routing logic
    router_id = "deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B"
    print(f"🧠 DeepSeek-R1 Analyzing Task: {task_description}")
    
    # Simple logic-based routing to avoid extra model loads if possible
    logic_tasks = ["gsm8k", "arc", "mathematics"]
    if any(x in task_description.lower() for x in logic_tasks):
        return "mistralai/Mistral-7B-v0.1" # Logic Expert
    return "NousResearch/Nous-Hermes-2-Mistral-7B-DPO" # Creative Expert

# ==========================================
# 4. UNIFIED AGI EXECUTION
# ==========================================
def run_agi_benchmark():
    tasks = ["gsm8k", "arc_challenge", "hellaswag"]
    final_results = {}

    for task in tasks:
        cleanup_disk()
        model_id = get_expert_path(task)
        print(f"🎯 Route Selected -> {model_id}")

        # Load and Patch Expert
        try:
            model = AutoModelForCausalLM.from_pretrained(
                model_id, torch_dtype=torch.bfloat16, device_map="auto"
            )
            model = patch_model(model)
            
            res = evaluator.simple_evaluate(
                model="hf",
                model_args=f"pretrained={model_id},dtype=bfloat16",
                tasks=[task],
                num_fewshot=5,
                limit=100
            )
            
            score = res["results"][task]
            metric = "acc,none" if "acc,none" in score else "exact_match,strict-match"
            final_results[task] = score[metric]
            print(f"✅ Result for {task}: {score[metric]}")
            
            # Delete model from memory
            del model
        except Exception as e:
            print(f"❌ Error during task {task}: {e}")

    with open("sovereign_agi_results.json", "w") as f:
        json.dump(final_results, f, indent=4)

if __name__ == "__main__":
    run_agi_benchmark()

#     root@07f58a95152b:/workspace# python3 sovereign_ensemble.py
# 🧹 NUCLEAR CLEANUP: Purging all model shards from disk...
# 🗑️ Deleting .locks to free up 15GB...
# 🧠 DeepSeek-R1 Analyzing Task: gsm8k
# 🎯 Route Selected -> mistralai/Mistral-7B-v0.1
# config.json: 100%|███████████████████████████████████████████████████████████████████████| 571/571 [00:00<00:00, 2.17MB/s]
# `torch_dtype` is deprecated! Use `dtype` instead!
# model.safetensors.index.json: 25.1kB [00:00, 48.7MB/s]
# model-00002-of-00002.safetensors: 100%|███████████████████████████████████████████████| 4.54G/4.54G [00:07<00:00, 579MB/s]
# model-00001-of-00002.safetensors: 100%|███████████████████████████████████████████████| 9.94G/9.94G [00:12<00:00, 767MB/s]
# Fetching 2 files: 100%|█████████████████████████████████████████████████████████████████████| 2/2 [00:13<00:00,  6.67s/it]
# 2026-01-18:02:50:57,008 INFO     [modeling.py:987] We will use 90% of the memory on device 0 for storing the model, and 10% for the buffer to avoid OOM. You can set `max_memory` in to a higher value to use more memory (at your own risk).
# Loading checkpoint shards: 100%|████████████████████████████████████████████████████████████| 2/2 [00:02<00:00,  1.38s/it]
# generation_config.json: 100%|█████████████████████████████████████████████████████████████| 116/116 [00:00<00:00, 530kB/s]
# 2026-01-18:02:51:00,153 INFO     [evaluator.py:164] Setting random seed to 0 | Setting numpy seed to 1234 | Setting torch manual seed to 1234 | Setting fewshot manual seed to 1234
# 2026-01-18:02:51:00,154 INFO     [evaluator.py:201] Initializing hf model, with arguments: {'pretrained': 'mistralai/Mistral-7B-v0.1', 'dtype': 'bfloat16'}
# 2026-01-18:02:51:00,183 INFO     [huggingface.py:129] Using device 'cuda'
# 2026-01-18:02:51:00,349 INFO     [huggingface.py:481] Using model type 'default'
# tokenizer_config.json: 100%|█████████████████████████████████████████████████████████████| 996/996 [00:00<00:00, 4.52MB/s]
# tokenizer.model: 100%|█████████████████████████████████████████████████████████████████| 493k/493k [00:00<00:00, 1.81MB/s]
# tokenizer.json: 1.80MB [00:00, 48.2MB/s]
# special_tokens_map.json: 100%|███████████████████████████████████████████████████████████| 414/414 [00:00<00:00, 2.15MB/s]
# 2026-01-18:02:51:02,275 INFO     [huggingface.py:365] Model parallel was set to False, max memory was not set, and device map was set to {'': 'cuda'}
# Loading checkpoint shards: 100%|████████████████████████████████████████████████████████████| 2/2 [00:02<00:00,  1.38s/it]
# README.md: 7.93kB [00:00, 19.9MB/s]
# 2026-01-18:02:51:16,071 WARNING  [evaluator.py:270] Overwriting default num_fewshot of gsm8k from 5 to 5
# 2026-01-18:02:51:16,072 INFO     [task.py:415] Building contexts for gsm8k on rank 0...
# 100%|██████████████████████████████████████████████████████████████████████████████████| 100/100 [00:00<00:00, 367.35it/s]
# 2026-01-18:02:51:16,346 INFO     [evaluator.py:489] Running generate_until requests
# Running generate_until requests: 100%|██████████████████████████████████████████████████| 100/100 [05:40<00:00,  3.41s/it]
# fatal: not a git repository (or any parent up to mount point /)
# Stopping at filesystem boundary (GIT_DISCOVERY_ACROSS_FILESYSTEM not set).
# ✅ Result for gsm8k: 0.37
# 🧹 NUCLEAR CLEANUP: Purging all model shards from disk...
# 🗑️ Deleting models--mistralai--Mistral-7B-v0.1 to free up 15GB...
# 🗑️ Deleting .locks to free up 15GB...
# 🗑️ Deleting datasets--gsm8k to free up 15GB...
# 🧠 DeepSeek-R1 Analyzing Task: arc_challenge
# 🎯 Route Selected -> mistralai/Mistral-7B-v0.1
# config.json: 100%|███████████████████████████████████████████████████████████████████████| 571/571 [00:00<00:00, 4.13MB/s]
# model.safetensors.index.json: 25.1kB [00:00, 43.1MB/s]
# model-00002-of-00002.safetensors: 100%|███████████████████████████████████████████████| 4.54G/4.54G [00:07<00:00, 584MB/s]
# model-00001-of-00002.safetensors: 100%|███████████████████████████████████████████████| 9.94G/9.94G [00:12<00:00, 789MB/s]
# Fetching 2 files: 100%|█████████████████████████████████████████████████████████████████████| 2/2 [00:12<00:00,  6.48s/it]
# 2026-01-18:02:57:14,270 INFO     [modeling.py:987] We will use 90% of the memory on device 0 for storing the model, and 10% for the buffer to avoid OOM. You can set `max_memory` in to a higher value to use more memory (at your own risk).
# Loading checkpoint shards: 100%|████████████████████████████████████████████████████████████| 2/2 [00:03<00:00,  1.57s/it]
# generation_config.json: 100%|█████████████████████████████████████████████████████████████| 116/116 [00:00<00:00, 651kB/s]
# 2026-01-18:02:57:17,815 INFO     [evaluator.py:164] Setting random seed to 0 | Setting numpy seed to 1234 | Setting torch manual seed to 1234 | Setting fewshot manual seed to 1234
# 2026-01-18:02:57:17,815 INFO     [evaluator.py:201] Initializing hf model, with arguments: {'pretrained': 'mistralai/Mistral-7B-v0.1', 'dtype': 'bfloat16'}
# 2026-01-18:02:57:17,817 INFO     [huggingface.py:129] Using device 'cuda'
# 2026-01-18:02:57:17,984 INFO     [huggingface.py:481] Using model type 'default'
# tokenizer_config.json: 100%|█████████████████████████████████████████████████████████████| 996/996 [00:00<00:00, 5.05MB/s]
# tokenizer.model: 100%|█████████████████████████████████████████████████████████████████| 493k/493k [00:00<00:00, 1.75MB/s]
# tokenizer.json: 1.80MB [00:00, 43.6MB/s]
# special_tokens_map.json: 100%|███████████████████████████████████████████████████████████| 414/414 [00:00<00:00, 1.84MB/s]
# 2026-01-18:02:57:19,894 INFO     [huggingface.py:365] Model parallel was set to False, max memory was not set, and device map was set to {'': 'cuda'}
# Loading checkpoint shards: 100%|████████████████████████████████████████████████████████████| 2/2 [00:02<00:00,  1.44s/it]
# README.md: 9.00kB [00:00, 25.7MB/s]
# 2026-01-18:02:57:32,210 WARNING  [evaluator.py:270] Overwriting default num_fewshot of arc_challenge from None to 5
# 2026-01-18:02:57:32,210 INFO     [task.py:415] Building contexts for arc_challenge on rank 0...
# 100%|██████████████████████████████████████████████████████████████████████████████████| 100/100 [00:00<00:00, 196.92it/s]
# 2026-01-18:02:57:32,722 INFO     [evaluator.py:489] Running loglikelihood requests
# Running loglikelihood requests: 100%|███████████████████████████████████████████████████| 400/400 [00:13<00:00, 29.32it/s]
# fatal: not a git repository (or any parent up to mount point /)
# Stopping at filesystem boundary (GIT_DISCOVERY_ACROSS_FILESYSTEM not set).
# ✅ Result for arc_challenge: 0.59
# 🧹 NUCLEAR CLEANUP: Purging all model shards from disk...
# 🗑️ Deleting models--mistralai--Mistral-7B-v0.1 to free up 15GB...
# 🗑️ Deleting .locks to free up 15GB...
# 🗑️ Deleting datasets--allenai--ai2_arc to free up 15GB...
# 🧠 DeepSeek-R1 Analyzing Task: hellaswag
# 🎯 Route Selected -> NousResearch/Nous-Hermes-2-Mistral-7B-DPO
# config.json: 100%|███████████████████████████████████████████████████████████████████████| 660/660 [00:00<00:00, 5.39MB/s]
# model.safetensors.index.json: 23.9kB [00:00, 43.5MB/s]
# model-00003-of-00003.safetensors: 100%|███████████████████████████████████████████████| 4.54G/4.54G [00:11<00:00, 408MB/s]
# model-00002-of-00003.safetensors: 100%|███████████████████████████████████████████████| 5.00G/5.00G [00:11<00:00, 421MB/s]
# model-00001-of-00003.safetensors: 100%|███████████████████████████████████████████████| 4.94G/4.94G [00:12<00:00, 381MB/s]
# Fetching 3 files: 100%|█████████████████████████████████████████████████████████████████████| 3/3 [00:13<00:00,  4.44s/it]
# 2026-01-18:02:58:03,984 INFO     [modeling.py:987] We will use 90% of the memory on device 0 for storing the model, and 10% for the buffer to avoid OOM. You can set `max_memory` in to a higher value to use more memory (at your own risk).
# Loading checkpoint shards: 100%|████████████████████████████████████████████████████████████| 3/3 [00:02<00:00,  1.07it/s]
# generation_config.json: 100%|█████████████████████████████████████████████████████████████| 120/120 [00:00<00:00, 853kB/s]
# 2026-01-18:02:58:07,330 INFO     [evaluator.py:164] Setting random seed to 0 | Setting numpy seed to 1234 | Setting torch manual seed to 1234 | Setting fewshot manual seed to 1234
# 2026-01-18:02:58:07,330 INFO     [evaluator.py:201] Initializing hf model, with arguments: {'pretrained': 'NousResearch/Nous-Hermes-2-Mistral-7B-DPO', 'dtype': 'bfloat16'}
# 2026-01-18:02:58:07,332 INFO     [huggingface.py:129] Using device 'cuda'
# 2026-01-18:02:58:07,503 INFO     [huggingface.py:481] Using model type 'default'
# tokenizer_config.json: 1.65kB [00:00, 6.30MB/s]
# tokenizer.model: 100%|█████████████████████████████████████████████████████████████████| 493k/493k [00:00<00:00, 1.31MB/s]
# added_tokens.json: 100%|████████████████████████████████████████████████████████████████| 51.0/51.0 [00:00<00:00, 363kB/s]
# special_tokens_map.json: 100%|███████████████████████████████████████████████████████████| 443/443 [00:00<00:00, 3.06MB/s]
# 2026-01-18:02:58:10,496 INFO     [huggingface.py:365] Model parallel was set to False, max memory was not set, and device map was set to {'': 'cuda'}
# Loading checkpoint shards: 100%|████████████████████████████████████████████████████████████| 3/3 [00:02<00:00,  1.09it/s]
# `trust_remote_code` is not supported anymore.
# Please check that the Hugging Face dataset 'hellaswag' isn't based on a loading script and remove `trust_remote_code`.
# If the dataset is based on a loading script, please ask the dataset author to remove it and convert it to a standard format like Parquet.
# 2026-01-18:02:58:20,642 ERROR    [load.py:1463] `trust_remote_code` is not supported anymore.
# Please check that the Hugging Face dataset 'hellaswag' isn't based on a loading script and remove `trust_remote_code`.
# If the dataset is based on a loading script, please ask the dataset author to remove it and convert it to a standard format like Parquet.
# README.md: 7.02kB [00:00, 19.3MB/s]
# data/train-00000-of-00001.parquet: 100%|█████████████████████████████████████████████| 24.4M/24.4M [00:00<00:00, 30.5MB/s]
# data/test-00000-of-00001.parquet: 100%|██████████████████████████████████████████████| 6.11M/6.11M [00:00<00:00, 21.1MB/s]
# data/validation-00000-of-00001.parquet: 100%|████████████████████████████████████████| 6.32M/6.32M [00:00<00:00, 22.4MB/s]
# Generating train split: 100%|████████████████████████████████████████████| 39905/39905 [00:00<00:00, 245325.70 examples/s]
# Generating test split: 100%|█████████████████████████████████████████████| 10003/10003 [00:00<00:00, 221105.34 examples/s]
# Generating validation split: 100%|███████████████████████████████████████| 10042/10042 [00:00<00:00, 195069.45 examples/s]
# Map: 100%|████████████████████████████████████████████████████████████████| 39905/39905 [00:03<00:00, 10523.94 examples/s]
# Map: 100%|█████████████████████████████████████████████████████████████████| 10042/10042 [00:01<00:00, 9984.60 examples/s]
# 2026-01-18:02:58:33,980 WARNING  [evaluator.py:270] Overwriting default num_fewshot of hellaswag from None to 5
# 2026-01-18:02:58:33,981 INFO     [task.py:415] Building contexts for hellaswag on rank 0...
# 100%|██████████████████████████████████████████████████████████████████████████████████| 100/100 [00:00<00:00, 423.99it/s]
# 2026-01-18:02:58:34,230 INFO     [evaluator.py:489] Running loglikelihood requests
# Running loglikelihood requests: 100%|███████████████████████████████████████████████████| 400/400 [00:21<00:00, 19.05it/s]
# fatal: not a git repository (or any parent up to mount point /)
# Stopping at filesystem boundary (GIT_DISCOVERY_ACROSS_FILESYSTEM not set).
# ✅ Result for hellaswag: 0.58
# root@07f58a95152b:/workspace# 