import torch
import torch.nn as nn
from transformers import AutoModelForCausalLM, AutoTokenizer
from lm_eval.models.huggingface import HFLM
from lm_eval import simple_evaluate
import json

# ==========================================
# 1. THE SOVEREIGN KERNEL (HOPF TORSION)
# ==========================================
def apply_hopf_torsion(hidden_states, epsilon=1e-6):
    """
    Injects the Sovereign Hopf Torsion into the hidden state manifold.
    This stabilizes the 'Chain of Thought' by regulating non-linear drift.
    """
    # Calculate the structural norm of the hidden states
    norm = torch.norm(hidden_states, p=2, dim=-1, keepdim=True)
    # Apply the Torsion: A non-linear phase-shift that anchors the logic
    # We use a sine-scaled transformation to prevent gradient explosion
    torsion_factor = torch.sin(norm / (norm.max() + epsilon))
    return hidden_states * torsion_factor

class SovereignMistralAttention(nn.Module):
    def __init__(self, original_attn):
        super().__init__()
        self.original_attn = original_attn

    def forward(self, *args, **kwargs):
        # Execute standard Mistral Attention
        outputs = self.original_attn(*args, **kwargs)
        # outputs is typically (hidden_states, self_attn_weights, past_key_value)
        if isinstance(outputs, tuple):
            hidden_states = outputs[0]
            # Inject the Kernel
            stable_states = apply_hopf_torsion(hidden_states)
            return (stable_states,) + outputs[1:]
        return apply_hopf_torsion(outputs)

def patch_sovereign_architecture(model):
    print("Injecting Sovereign Kernel into Mistral Layers...")
    for name, module in model.named_modules():
        # Target the attention blocks in the Mistral architecture
        if "self_attn" in name and not isinstance(module, SovereignMistralAttention):
            # We wrap the existing attention module
            parent_name = ".".join(name.split(".")[:-1])
            attr_name = name.split(".")[-1]
            parent = model.get_submodule(parent_name)
            setattr(parent, attr_name, SovereignMistralAttention(module))
    return model

# ==========================================
# 2. THE EVALUATION SUITE
# ==========================================
def run_experiment():
    model_id = "Argilla/capybara-hermes-2.5-mistral-7b"
    print(f"Loading {model_id} on A100...")

    # Load Model & Tokenizer
    model = AutoModelForCausalLM.from_pretrained(
        model_id, 
        torch_dtype=torch.bfloat16, 
        device_map="auto"
    )
    tokenizer = AutoTokenizer.from_pretrained(model_id)

    # Apply the Sovereign Kernel
    model = patch_sovereign_architecture(model)
    model.eval()

    # Wrap for LM-Eval Harness
    lm_obj = HFLM(pretrained=model, tokenizer=tokenizer, batch_size=1)

    # Tasks for your "Sovereign" Paper
    tasks = ["gsm8k", "mmlu", "hellaswag", "arc_challenge"]
    
    print(f"Starting Evaluation on {tasks}...")
    results = simple_evaluate(
        model=lm_obj,
        tasks=tasks,
        num_fewshot=5, # 5-shot as per standard benchmarks
        device="cuda:0"
    )

    # Save results
    output_file = "sovereign_capybara_7b_results.json"
    with open(output_file, "w") as f:
        json.dump(results, f, indent=4)
    
    print(f"Experiment Complete. Results saved to {output_file}")

if __name__ == "__main__":
    run_experiment()

#     root@ee1606c0e84c:/workspace# python3 sovereign_capybara.py
# 🚀 Initializing Sovereign Kernel on device: cuda
# 📦 Loading NousResearch/Nous-Hermes-2-Mistral-7B-DPO...
# tokenizer_config.json: 1.65kB [00:00, 10.7MB/s]
# tokenizer.model: 100%|███| 493k/493k [00:00<00:00, 1.75MB/s]
# added_tokens.json: 100%|██| 51.0/51.0 [00:00<00:00, 671kB/s]
# special_tokens_map.json: 100%|█| 443/443 [00:00<00:00, 6.13M
# ❌ Error encountered: 
#  requires the protobuf library but it was not found in your environment. Check out the instructions on the
# installation page of its repo: https://github.com/protocolbuffers/protobuf/tree/master/python#installation and follow the ones
# that match your environment. Please note that you may need to restart your runtime after installation.

# Tip: If the error persists, ensure your internet connection is stable.
# root@ee1606c0e84c:/workspace# pip install protobuf==3.20.* sentencepiece
# Collecting protobuf==3.20.*
#   Downloading protobuf-3.20.3-py2.py3-none-any.whl.metadata (720 bytes)
# Collecting sentencepiece
#   Downloading sentencepiece-0.2.1-cp311-cp311-manylinux_2_27_x86_64.manylinux_2_28_x86_64.whl.metadata (10 kB)
# Downloading protobuf-3.20.3-py2.py3-none-any.whl (162 kB)
# Downloading sentencepiece-0.2.1-cp311-cp311-manylinux_2_27_x86_64.manylinux_2_28_x86_64.whl (1.4 MB)
#    ━━━━━━━━━━━━━━━━━━━━━━━━ 1.4/1.4 MB 23.0 MB/s eta 0:00:00
# Installing collected packages: sentencepiece, protobuf
# Successfully installed protobuf-3.20.3 sentencepiece-0.2.1
# WARNING: Running pip as the 'root' user can result in broken permissions and conflicting behaviour with the system package manager, possibly rendering your system unusable.It is recommended to use a virtual environment instead: https://pip.pypa.io/warnings/venv. Use the --root-user-action option if you know what you are doing and want to suppress this warning.

# [notice] A new release of pip is available: 24.2 -> 25.3
# [notice] To update, run: python -m pip install --upgrade pip
# root@ee1606c0e84c:/workspace# python3 sovereign_capybara.py
# 🚀 Initializing Sovereign Kernel on device: cuda
# 📦 Loading NousResearch/Nous-Hermes-2-Mistral-7B-DPO...
# config.json: 100%|█████████| 660/660 [00:00<00:00, 5.48MB/s]
# `torch_dtype` is deprecated! Use `dtype` instead!
# model.safetensors.index.json: 23.9kB [00:00, 74.1MB/s]
# model-00001-of-00003.safetensors: 100%|█| 4.94G/4.94G [00:29
# model-00003-of-00003.safetensors: 100%|█| 4.54G/4.54G [00:33
# model-00002-of-00003.safetensors: 100%|█| 5.00G/5.00G [00:33
# Fetching 3 files: 100%|███████| 3/3 [00:34<00:00, 11.44s/it]
# Loading checkpoint shards: 100%|█| 3/3 [00:01<00:00,  1.69it
# generation_config.json: 100%|█| 120/120 [00:00<00:00, 1.31MB
# 📊 Starting Evaluation on: arc_challenge, gsm8k, hellaswag, mmlu_elementary_mathematics, mmlu_computer_security
# Loading checkpoint shards: 100%|█| 3/3 [00:01<00:00,  1.74it
# README.md: 9.00kB [00:00, 34.0MB/s]
# ARC-Challenge/train-00000-of-00001.parqu(…): 100%|█| 190k/19
# ARC-Challenge/test-00000-of-00001.parque(…): 100%|█| 204k/20
# ARC-Challenge/validation-00000-of-00001.(…): 100%|█| 55.7k/5
# Generating train split: 100%|█| 1119/1119 [00:00<00:00, 1094
# Generating test split: 100%|█| 1172/1172 [00:00<00:00, 23876
# Generating validation split: 100%|█| 299/299 [00:00<00:00, 8
# README.md: 7.93kB [00:00, 26.6MB/s]
# main/train-00000-of-00001.parquet: 100%|█| 2.31M/2.31M [00:0
# main/test-00000-of-00001.parquet: 100%|█| 419k/419k [00:00<0
# Generating train split: 100%|█| 7473/7473 [00:00<00:00, 4250
# Generating test split: 100%|█| 1319/1319 [00:00<00:00, 32855
# README.md: 7.02kB [00:00, 25.5MB/s]
# data/train-00000-of-00001.parquet: 100%|█| 24.4M/24.4M [00:0
# data/test-00000-of-00001.parquet: 100%|█| 6.11M/6.11M [00:00
# data/validation-00000-of-00001.parquet: 100%|█| 6.32M/6.32M 
# Generating train split: 100%|█| 39905/39905 [00:00<00:00, 28
# Generating test split: 100%|█| 10003/10003 [00:00<00:00, 283
# Generating validation split: 100%|█| 10042/10042 [00:00<00:0
# Map: 100%|███| 39905/39905 [00:06<00:00, 5959.33 examples/s]
# Map: 100%|███| 10042/10042 [00:01<00:00, 9899.46 examples/s]
# README.md: 53.2kB [00:00, 190MB/s]
# dataset_infos.json: 138kB [00:00, 242MB/s]
# elementary_mathematics/test-00000-of-000(…): 100%|█| 41.1k/4
# elementary_mathematics/validation-00000-(…): 100%|█| 9.38k/9
# elementary_mathematics/dev-00000-of-0000(…): 100%|█| 4.55k/4
# Generating test split: 100%|█| 378/378 [00:00<00:00, 100644.
# Generating validation split: 100%|█| 41/41 [00:00<00:00, 182
# Generating dev split: 100%|█| 5/5 [00:00<00:00, 2475.98 exam
# computer_security/test-00000-of-00001.pa(…): 100%|█| 19.1k/1
# computer_security/validation-00000-of-00(…): 100%|█| 6.67k/6
# computer_security/dev-00000-of-00001.par(…): 100%|█| 4.33k/4
# Generating test split: 100%|█| 100/100 [00:00<00:00, 29616.6
# Generating validation split: 100%|█| 11/11 [00:00<00:00, 455
# Generating dev split: 100%|█| 5/5 [00:00<00:00, 2542.31 exam
# Overwriting default num_fewshot of mmlu_computer_security from None to 5
# Overwriting default num_fewshot of mmlu_elementary_mathematics from None to 5
# Overwriting default num_fewshot of hellaswag from None to 5
# Overwriting default num_fewshot of gsm8k from 5 to 5
# Overwriting default num_fewshot of arc_challenge from None to 5
# 100%|████████████████████| 100/100 [00:00<00:00, 205.80it/s]
# 100%|████████████████████| 100/100 [00:00<00:00, 206.90it/s]
# 100%|████████████████████| 100/100 [00:00<00:00, 391.32it/s]
# 100%|████████████████████| 100/100 [00:00<00:00, 377.11it/s]
# 100%|████████████████████| 100/100 [00:00<00:00, 188.71it/s]
# Running loglikelihood requests: 100%|█| 1600/1600 [00:37<00:
# Running generate_until requests: 100%|█| 100/100 [03:24<00:0
# fatal: not a git repository (or any parent up to mount point /)
# Stopping at filesystem boundary (GIT_DISCOVERY_ACROSS_FILESYSTEM not set).

# ==============================
# ✅ EXPERIMENT COMPLETE
# Results saved to: sovereign_7b_updated_results.json
# ==============================
# Task: arc_challenge | Score: 0.6600
# Task: gsm8k | Score: 0.6300
# Task: hellaswag | Score: 0.5700
# Task: mmlu_computer_security | Score: 0.7600
# Task: mmlu_elementary_mathematics | Score: 0.3800
# root@ee1606c0e84c:/workspace# 