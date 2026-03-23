import torch
import gc
import json
import os
import shutil
import transformers
from transformers import AutoModelForVision2Seq
from lm_eval import evaluator
from lm_eval.tasks import TaskManager

# Resolve the one-time migration issue automatically
try:
    transformers.utils.move_cache()
except Exception:
    pass

def deep_cleanup():
    print("🧹 NUCLEAR CLEANUP: Purging VRAM and Disk...")
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        torch.cuda.ipc_collect()
    gc.collect()
    cache_dir = os.path.expanduser("~/.cache/huggingface/hub")
    if os.path.exists(cache_dir):
        shutil.rmtree(cache_dir, ignore_errors=True)
    os.makedirs(cache_dir, exist_ok=True)

def apply_hopf_torsion(hidden_states, epsilon=1e-6):
    norm = torch.norm(hidden_states, p=2, dim=-1, keepdim=True)
    torsion_factor = torch.sin(norm / (norm.max() + epsilon))
    return hidden_states * torsion_factor

def patch_sovereign_kernel(model):
    print("🛡️ Injecting Sovereign Kernel...")
    for name, module in model.named_modules():
        if any(x in name for x in ["mm_projector", "multi_modal_projector"]):
            original_forward = module.forward
            def sovereign_bridge_forward(*args, **kwargs):
                return apply_hopf_torsion(original_forward(*args, **kwargs))
            module.forward = sovereign_bridge_forward
        elif "self_attn" in name and "vision" not in name:
            original_forward = module.forward
            def sovereign_attn_forward(*args, **kwargs):
                out = original_forward(*args, **kwargs)
                return (apply_hopf_torsion(out[0]),) + out[1:] if isinstance(out, tuple) else apply_hopf_torsion(out)
            module.forward = sovereign_attn_forward
    return model

def run_sovereign_ensemble():
    # TASK NAMES UPDATED TO MATCH YOUR REGISTRY: 'mmmu_val_art_theory'
    task_map = [
        {"task": "mmmu_val_art_theory", "model": "llava-hf/llava-1.5-7b-hf", "type": "hf-multimodal"},
        {"task": "gsm8k", "model": "mistralai/Mistral-7B-v0.1", "type": "hf"},
        {"task": "arc_challenge", "model": "mistralai/Mistral-7B-v0.1", "type": "hf"}
    ]
    
    final_results = {}
    tm = TaskManager()

    for entry in task_map:
        task = entry["task"]
        model_id = entry["model"]
        harness_type = entry["type"]
        
        deep_cleanup()
        print(f"\n🧠 Task: {task} | Route: {model_id}")

        model_args = f"pretrained={model_id},dtype=bfloat16,trust_remote_code=True,attn_implementation=eager"

        try:
            res = evaluator.simple_evaluate(
                model=harness_type,
                model_args=model_args,
                tasks=[task],
                limit=10, 
                batch_size=1,
                task_manager=tm
            )
            
            if task in res["results"]:
                score = res["results"][task].get("acc,none") or res["results"][task].get("acc") or res["results"][task].get("exact_match")
                final_results[task] = score
                print(f"✅ Result for {task}: {score}")
            else:
                # Group result handling
                for k, v in res["results"].items():
                    score = v.get("acc,none") or v.get("acc")
                    final_results[k] = score
                    print(f"✅ Result for {k}: {score}")

        except Exception as e:
            print(f"❌ Failure on {task}: {e}")

    with open("sovereign_agi_final_results2.json", "w") as f:
        json.dump(final_results, f, indent=4)
    print(f"\n🚀 CIRCUIT COMPLETE. Results saved to sovereign_agi_final_results.json")

if __name__ == "__main__":
    run_sovereign_ensemble()

#     root@07f58a95152b:/workspace# python3 sovereign_ensemble.py
# The cache for model files in Transformers v4.22.0 has been updated. Migrating your old cache. This is a one-time only operation. You can interrupt this and resume the migration later on by calling `transformers.utils.move_cache()`.
# 0it [00:00, ?it/s]
# 0it [00:00, ?it/s]
# 🧹 NUCLEAR CLEANUP: Purging VRAM and Disk...

# 🧠 Task: mmmu_val_art_theory | Route: llava-hf/llava-1.5-7b-hf
# 2026-01-18:04:19:00,879 INFO     [evaluator.py:164] Setting random seed to 0 | Setting numpy seed to 1234 | Setting torch manual seed to 1234 | Setting fewshot manual seed to 1234
# 2026-01-18:04:19:00,879 INFO     [evaluator.py:201] Initializing hf-multimodal model, with arguments: {'pretrained': 'llava-hf/llava-1.5-7b-hf', 'dtype': 'bfloat16', 'trust_remote_code': True, 'attn_implementation': 'eager'}
# 2026-01-18:04:19:00,918 INFO     [huggingface.py:129] Using device 'cuda'
# config.json: 100%|███████████████████████████████████████████████████████████████████████| 950/950 [00:00<00:00, 3.15MB/s]
# 2026-01-18:04:19:01,137 INFO     [huggingface.py:492] Model type cannot be determined. Using default model type 'default'
# processor_config.json: 100%|██████████████████████████████████████████████████████████████| 173/173 [00:00<00:00, 550kB/s]
# chat_template.json: 100%|████████████████████████████████████████████████████████████████| 701/701 [00:00<00:00, 3.52MB/s]
# preprocessor_config.json: 100%|██████████████████████████████████████████████████████████| 505/505 [00:00<00:00, 2.42MB/s]
# tokenizer_config.json: 1.45kB [00:00, 2.32MB/s]
# tokenizer.model: 100%|██████████████████████████████████████████████████████████████████| 500k/500k [00:00<00:00, 792kB/s]
# tokenizer.json: 3.62MB [00:00, 71.9MB/s]
# added_tokens.json: 100%|████████████████████████████████████████████████████████████████| 41.0/41.0 [00:00<00:00, 145kB/s]
# special_tokens_map.json: 100%|███████████████████████████████████████████████████████████| 552/552 [00:00<00:00, 2.56MB/s]
# Some kwargs in processor config are unused and will not have any effect: num_additional_image_tokens. 
# 2026-01-18:04:19:04,165 INFO     [huggingface.py:365] Model parallel was set to False, max memory was not set, and device map was set to {'': 'cuda'}
# model.safetensors.index.json: 70.1kB [00:00, 75.4MB/s]
# model-00001-of-00003.safetensors: 100%|███████████████████████████████████████████████| 4.99G/4.99G [00:05<00:00, 854MB/s]
# model-00002-of-00003.safetensors: 100%|███████████████████████████████████████████████| 4.96G/4.96G [00:05<00:00, 877MB/s]
# model-00003-of-00003.safetensors: 100%|███████████████████████████████████████████████| 4.18G/4.18G [00:04<00:00, 918MB/s]
# Downloading shards: 100%|███████████████████████████████████████████████████████████████████| 3/3 [00:17<00:00,  5.77s/it]
# Loading checkpoint shards: 100%|████████████████████████████████████████████████████████████| 3/3 [00:14<00:00,  4.78s/it]
# generation_config.json: 100%|████████████████████████████████████████████████████████████| 141/141 [00:00<00:00, 1.39MB/s]
# README.md: 42.3kB [00:00, 60.3MB/s]
# Art_Theory/dev-00000-of-00001.parquet: 100%|█████████████████████████████████████████| 6.39M/6.39M [00:01<00:00, 4.30MB/s]
# Art_Theory/validation-00000-of-00001.par(…): 100%|███████████████████████████████████| 29.8M/29.8M [00:00<00:00, 52.9MB/s]
# Art_Theory/test-00000-of-00002.parquet: 100%|██████████████████████████████████████████| 206M/206M [00:03<00:00, 57.2MB/s]
# Art_Theory/test-00001-of-00002.parquet: 100%|██████████████████████████████████████████| 199M/199M [00:03<00:00, 55.4MB/s]
# Generating dev split: 100%|█████████████████████████████████████████████████████████| 5/5 [00:00<00:00, 145.41 examples/s]
# Generating validation split: 100%|████████████████████████████████████████████████| 30/30 [00:00<00:00, 206.24 examples/s]
# Generating test split: 100%|████████████████████████████████████████████████████| 429/429 [00:01<00:00, 243.72 examples/s]
# 2026-01-18:04:19:52,729 INFO     [task.py:415] Building contexts for mmmu_val_art_theory on rank 0...
# 100%|██████████████████████████████████████████████████████████████████████████████████| 10/10 [00:00<00:00, 14857.61it/s]
# 2026-01-18:04:19:53,014 INFO     [evaluator.py:489] Running generate_until requests
# Running generate_until requests with text+image input:   0%|                                       | 0/10 [00:00<?, ?it/s]Starting from v4.46, the `logits` model output will have the same type as the model (except at train time, where it will always be FP32)
# Running generate_until requests with text+image input: 100%|██████████████████████████████| 10/10 [00:04<00:00,  2.20it/s]
# fatal: not a git repository (or any parent up to mount point /)
# Stopping at filesystem boundary (GIT_DISCOVERY_ACROSS_FILESYSTEM not set).
# ✅ Result for mmmu_val_art_theory: 0.4
# 🧹 NUCLEAR CLEANUP: Purging VRAM and Disk...

# 🧠 Task: gsm8k | Route: mistralai/Mistral-7B-v0.1
# 2026-01-18:04:20:00,941 INFO     [evaluator.py:164] Setting random seed to 0 | Setting numpy seed to 1234 | Setting torch manual seed to 1234 | Setting fewshot manual seed to 1234
# 2026-01-18:04:20:00,941 INFO     [evaluator.py:201] Initializing hf model, with arguments: {'pretrained': 'mistralai/Mistral-7B-v0.1', 'dtype': 'bfloat16', 'trust_remote_code': True, 'attn_implementation': 'eager'}
# 2026-01-18:04:20:00,943 INFO     [huggingface.py:129] Using device 'cuda'
# config.json: 100%|███████████████████████████████████████████████████████████████████████| 571/571 [00:00<00:00, 4.05MB/s]
# 2026-01-18:04:20:01,166 INFO     [huggingface.py:481] Using model type 'default'
# tokenizer_config.json: 100%|█████████████████████████████████████████████████████████████| 996/996 [00:00<00:00, 6.38MB/s]
# tokenizer.model: 100%|█████████████████████████████████████████████████████████████████| 493k/493k [00:00<00:00, 1.84MB/s]
# tokenizer.json: 1.80MB [00:00, 188MB/s]
# special_tokens_map.json: 100%|███████████████████████████████████████████████████████████| 414/414 [00:00<00:00, 2.87MB/s]
# 2026-01-18:04:20:02,514 INFO     [huggingface.py:365] Model parallel was set to False, max memory was not set, and device map was set to {'': 'cuda'}
# model.safetensors.index.json: 25.1kB [00:00, 112MB/s]
# model-00001-of-00002.safetensors: 100%|██████████████████████████████████████████████| 9.94G/9.94G [00:08<00:00, 1.17GB/s]
# model-00002-of-00002.safetensors: 100%|██████████████████████████████████████████████| 4.54G/4.54G [00:04<00:00, 1.06GB/s]
# Downloading shards: 100%|███████████████████████████████████████████████████████████████████| 2/2 [00:13<00:00,  6.71s/it]
# Loading checkpoint shards: 100%|████████████████████████████████████████████████████████████| 2/2 [00:03<00:00,  1.53s/it]
# generation_config.json: 100%|████████████████████████████████████████████████████████████| 116/116 [00:00<00:00, 1.01MB/s]
# README.md: 7.93kB [00:00, 37.8MB/s]
# 2026-01-18:04:20:24,208 INFO     [task.py:415] Building contexts for gsm8k on rank 0...
# 100%|████████████████████████████████████████████████████████████████████████████████████| 10/10 [00:00<00:00, 372.79it/s]
# 2026-01-18:04:20:24,236 INFO     [evaluator.py:489] Running generate_until requests
# Running generate_until requests:   0%|                                                             | 0/10 [00:00<?, ?it/s]Starting from v4.46, the `logits` model output will have the same type as the model (except at train time, where it will always be FP32)
# Running generate_until requests: 100%|████████████████████████████████████████████████████| 10/10 [00:52<00:00,  5.25s/it]
# fatal: not a git repository (or any parent up to mount point /)
# Stopping at filesystem boundary (GIT_DISCOVERY_ACROSS_FILESYSTEM not set).
# ✅ Result for gsm8k: None
# 🧹 NUCLEAR CLEANUP: Purging VRAM and Disk...

# 🧠 Task: arc_challenge | Route: mistralai/Mistral-7B-v0.1
# 2026-01-18:04:21:19,813 INFO     [evaluator.py:164] Setting random seed to 0 | Setting numpy seed to 1234 | Setting torch manual seed to 1234 | Setting fewshot manual seed to 1234
# 2026-01-18:04:21:19,813 INFO     [evaluator.py:201] Initializing hf model, with arguments: {'pretrained': 'mistralai/Mistral-7B-v0.1', 'dtype': 'bfloat16', 'trust_remote_code': True, 'attn_implementation': 'eager'}
# 2026-01-18:04:21:19,814 INFO     [huggingface.py:129] Using device 'cuda'
# config.json: 100%|███████████████████████████████████████████████████████████████████████| 571/571 [00:00<00:00, 1.91MB/s]
# 2026-01-18:04:21:19,995 INFO     [huggingface.py:481] Using model type 'default'
# tokenizer_config.json: 100%|█████████████████████████████████████████████████████████████| 996/996 [00:00<00:00, 6.08MB/s]
# tokenizer.model: 100%|██████████████████████████████████████████████████████████████████| 493k/493k [00:00<00:00, 950kB/s]
# tokenizer.json: 1.80MB [00:00, 97.1MB/s]
# special_tokens_map.json: 100%|███████████████████████████████████████████████████████████| 414/414 [00:00<00:00, 1.49MB/s]
# 2026-01-18:04:21:21,611 INFO     [huggingface.py:365] Model parallel was set to False, max memory was not set, and device map was set to {'': 'cuda'}
# model.safetensors.index.json: 25.1kB [00:00, 108MB/s]
# model-00001-of-00002.safetensors: 100%|██████████████████████████████████████████████| 9.94G/9.94G [00:08<00:00, 1.13GB/s]
# model-00002-of-00002.safetensors: 100%|███████████████████████████████████████████████| 4.54G/4.54G [00:04<00:00, 989MB/s]
# Downloading shards: 100%|███████████████████████████████████████████████████████████████████| 2/2 [00:14<00:00,  7.00s/it]
# Loading checkpoint shards: 100%|████████████████████████████████████████████████████████████| 2/2 [00:03<00:00,  1.53s/it]
# generation_config.json: 100%|████████████████████████████████████████████████████████████| 116/116 [00:00<00:00, 1.03MB/s]
# README.md: 9.00kB [00:00, 20.4MB/s]
# 2026-01-18:04:21:41,420 INFO     [task.py:415] Building contexts for arc_challenge on rank 0...
# 100%|███████████████████████████████████████████████████████████████████████████████████| 10/10 [00:00<00:00, 1621.99it/s]
# 2026-01-18:04:21:41,427 INFO     [evaluator.py:489] Running loglikelihood requests
# Running loglikelihood requests: 100%|█████████████████████████████████████████████████████| 40/40 [00:01<00:00, 29.62it/s]
# fatal: not a git repository (or any parent up to mount point /)
# Stopping at filesystem boundary (GIT_DISCOVERY_ACROSS_FILESYSTEM not set).
# ✅ Result for arc_challenge: 0.4

# 🚀 CIRCUIT COMPLETE. Results saved to sovereign_agi_final_results.json
# root@07f58a95152b:/workspace# 