import torch
import torch.nn.functional as F
from transformers import AutoModelForCausalLM, AutoTokenizer
import argparse
import subprocess
import time
import json
import numpy as np
import sys

# --- 1. Power Sampling Class for macOS (Final Robust Version) ---

class PowerSamplerMac:
    """
    Measures chip energy on Apple Silicon Macs using a single, short powermetrics sample.
    The script must be run with sudo privileges.
    """
    def __init__(self, device: str = 'mps'):
        self.device = device
        self.total_energy_kwh = 0.0
        self.start_time = None

    def start(self):
        """Starts timing the operation."""
        if self.device != 'mps':
            print("Warning: PowerSamplerMac is intended for 'mps' device.")
        self.start_time = time.time()
        print("Power measurement timing started.")

    def stop(self):
        """Stops the operation, takes a single powermetrics sample, and calculates energy."""
        end_time = time.time()
        duration = end_time - self.start_time
        
        # FINAL COMMAND: 'sudo' is included here to guarantee permission, and '-q' is removed.
        cmd = ['sudo', 'powermetrics', '--samplers', 'cpu_power,gpu_power', '-i', '1000', '-n', '1']

        try:
            # Note: Running powermetrics as a subprocess requires care. 
            # We explicitly pass the command as a list of arguments.
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                check=True,
                timeout=5
            )
            
            raw_output = result.stdout
            
            # --- DEBUGGING OUTPUT ---
            print(f"\n--- RAW POWERMETRICS OUTPUT (START) ---\n{raw_output}\n--- RAW POWERMETRICS OUTPUT (END) ---\n")
            # --- DEBUGGING OUTPUT ---

            # CALLING THE CORRECT PARSER FUNCTION
            avg_power_w = self._parse_powermetrics_output(raw_output)
            
            # Energy (kWh) = Power (kW) * Time (h)
            power_kw = avg_power_w / 1000.0
            time_hours = duration / 3600.0
            
            total_energy_kwh = power_kw * time_hours
            
            print(f"Power measurement stopped. Duration: {duration:.2f}s, Avg Power (W): {avg_power_w:.2f}")

            return total_energy_kwh, duration

        except subprocess.CalledProcessError as e:
            # This should not happen if the script is run with sudo
            print(f"\n🚨 ERROR: powermetrics command failed. Exit Code: {e.returncode}")
            print(f"Stdout: {e.stdout}", file=sys.stderr)
            print(f"Stderr: {e.stderr}", file=sys.stderr)
            return 0.0, duration
        except subprocess.TimeoutExpired:
            print("\n🚨 ERROR: powermetrics timed out.", file=sys.stderr)
            return 0.0, duration
        except FileNotFoundError:
            print("\n🚨 ERROR: powermetrics command not found. Is it in your system PATH?", file=sys.stderr)
            return 0.0, duration

    def _parse_powermetrics_output(self, output: str) -> float:
        """Parses the single power output for total power in Watts (W) using the Combined Power line."""
        
        for line in output.splitlines():
            line = line.strip()
            
            # The format is 'Combined Power (CPU + GPU + ANE): XXX mW'
            if 'Combined Power' in line and 'mW' in line:
                try:
                    # Split by colon, take the value part, strip 'mW', and convert to float
                    power_str = line.split(':')[1].strip().split('mW')[0].strip()
                    total_power_mw = float(power_str)
                    
                    # Convert mW to W
                    return total_power_mw / 1000.0
                except Exception as e:
                    print(f"Error parsing combined power line: {e}", file=sys.stderr)
                    pass

        # Fallback if the combined power line isn't found or parsed
        print("Warning: Could not parse Combined Power from powermetrics output.")
        return 0.0

# --- 2. Gating and Measurement Logic (Remains the same) ---

def get_input_norm(tokenizer, prompt: str, device: torch.device) -> float:
    """Calculates the L2 norm of the input vector x for the prompt."""
    input_ids = tokenizer.encode(prompt, return_tensors="pt").to(device)
    if input_ids.shape[1] == 0:
        return 0.0
    x = input_ids.squeeze(0).float()
    norm_l2 = torch.linalg.norm(x).item()
    return norm_l2

def calculate_lambda2(tokenizer, prompt: str, device: torch.device) -> float:
    """Calculates the O(1) diagnostic lambda_2 based on the L2 norm of the input token vector x."""
    norm_l2 = get_input_norm(tokenizer, prompt, device)
    if norm_l2 == 0.0:
        return np.nan
    K = 24.0
    lambda_2 = (norm_l2 % K) / K
    return lambda_2

def generate(model, tok, prompt: str, device: torch.device, max_new_tokens: int):
    """Generates tokens for a single prompt."""
    input_ids = tok.encode(prompt, return_tensors="pt").to(device)
    
    with torch.no_grad():
        out = model.generate(
            input_ids,
            max_new_tokens=max_new_tokens,
            do_sample=True,
            top_k=50,
            top_p=0.95,
            num_return_sequences=1,
            pad_token_id=tok.eos_token_id
        )
    
    new_tokens = out.shape[1] - input_ids.shape[1]
    return tok.decode(out[0], skip_special_tokens=True), new_tokens

def run_batch(FULL_MODEL_NAME, FULL_TOKENIZER_NAME, prompts: list, device: torch.device, max_new_tokens: int):
    """Measures total energy and tokens generated for a batch of prompts (baseline or gated)."""
    
    # --- MODEL LOADING MOVED HERE TO REDUCE PEAK MEMORY ---
    print(f"Loading {FULL_MODEL_NAME} for Baseline...")
    try:
        full_tok = AutoTokenizer.from_pretrained(FULL_TOKENIZER_NAME)
        full_model = AutoModelForCausalLM.from_pretrained(FULL_MODEL_NAME, torch_dtype=torch.float16).to(device)
    except Exception as e:
        print(f"Error loading model in run_batch: {e}", file=sys.stderr)
        return {"tokens": 0, "energy_kwh": 0.0, "cost_usd": 0.0, "co2_kg": 0.0, "energy_per_token_Wh": 0.0}
        
    sampler = PowerSamplerMac(device)
    total_tokens = 0
    
    # 1. START MEASUREMENT
    sampler.start()
    
    # 2. RUN INFERENCE
    for i, p in enumerate(prompts):
        try:
            _, n = generate(full_model, full_tok, p, device, max_new_tokens=max_new_tokens)
            total_tokens += n
        except Exception as e:
            print(f"Error generating for prompt {i+1}: {e}", file=sys.stderr)
            
    # 3. STOP MEASUREMENT
    energy_kwh, duration = sampler.stop()

    # Clear model and tokenizer from memory
    del full_model
    del full_tok
    if device.type == 'mps':
        torch.mps.empty_cache()

    results = {
        "tokens": total_tokens,
        "energy_kwh": energy_kwh,
        "cost_usd": energy_kwh * 0.15,
        "co2_kg": energy_kwh * 0.38
    }
    results["energy_per_token_Wh"] = (results["energy_kwh"] * 1000.0 / total_tokens) if total_tokens > 0 else 0.0

    return results

def run_gated_batch(FULL_MODEL_NAME, FULL_TOKENIZER_NAME, SMALL_MODEL_NAME, SMALL_TOKENIZER_NAME, prompts: list, device: torch.device, lambda_threshold: float, max_new_tokens: int):
    """Runs the gated architecture, routing based on lambda_2."""

    # --- MODEL LOADING MOVED HERE TO REDUCE PEAK MEMORY ---
    print(f"Loading {FULL_MODEL_NAME} and {SMALL_MODEL_NAME} for Gated Run...")
    try:
        full_tok = AutoTokenizer.from_pretrained(FULL_TOKENIZER_NAME)
        full_model = AutoModelForCausalLM.from_pretrained(FULL_MODEL_NAME, torch_dtype=torch.float16).to(device)
        small_tok = AutoTokenizer.from_pretrained(SMALL_TOKENIZER_NAME)
        small_model = AutoModelForCausalLM.from_pretrained(SMALL_MODEL_NAME, torch_dtype=torch.float16).to(device)
    except Exception as e:
        print(f"Error loading models in run_gated_batch: {e}", file=sys.stderr)
        return {"tokens": 0, "energy_kwh": 0.0, "cost_usd": 0.0, "co2_kg": 0.0, "routing": [], "energy_per_token_Wh": 0.0}

    sampler = PowerSamplerMac(device)
    total_tokens = 0
    routing_data = []

    # 1. START MEASUREMENT
    sampler.start()
    
    # 2. RUN INFERENCE
    for i, p in enumerate(prompts):
        lambda2 = calculate_lambda2(full_tok, p, device)
        used_small = False
        new_tokens = 0
        
        if not np.isnan(lambda2) and lambda2 >= lambda_threshold:
            model_to_use = small_model
            tokenizer_to_use = small_tok
            used_small = True
            print(f"Prompt {i+1}: Routed to SMALL model (lambda_2: {lambda2:.4f})")
        else:
            model_to_use = full_model
            tokenizer_to_use = full_tok
            print(f"Prompt {i+1}: Routed to FULL model (lambda_2: {lambda2:.4f} or NaN)")

        try:
            _, new_tokens = generate(model_to_use, tokenizer_to_use, p, device, max_new_tokens=max_new_tokens)
            total_tokens += new_tokens
        except Exception as e:
            print(f"Error generating for prompt {i+1}: {e}", file=sys.stderr)

        routing_data.append({
            "prompt": p,
            "lambda2": lambda2,
            "used_small": used_small,
            "new_tokens": new_tokens
        })
            
    # 3. STOP MEASUREMENT
    energy_kwh, duration = sampler.stop()

    # Clear models and tokenizers from memory
    del full_model, small_model
    del full_tok, small_tok
    if device.type == 'mps':
        torch.mps.empty_cache()

    results = {
        "tokens": total_tokens,
        "energy_kwh": energy_kwh,
        "cost_usd": energy_kwh * 0.15,
        "co2_kg": energy_kwh * 0.38,
        "routing": routing_data
    }
    results["energy_per_token_Wh"] = (results["energy_kwh"] * 1000.0 / total_tokens) if total_tokens > 0 else 0.0

    return results

# --- 3. Main Execution ---

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Measure energy and performance of a gated LLM on Apple Silicon (MPS).")
    parser.add_argument("--prompts", type=str, required=True, help="Path to the prompts.txt file.")
    parser.add_argument("--lambda_threshold", type=float, default=0.3, help="Lambda_2 threshold for routing.")
    parser.add_argument("--max_new_tokens", type=int, default=128, help="Maximum number of tokens to generate per prompt.")
    parser.add_argument("--num_prompts", type=int, default=50, help="Number of prompts to use from the file.")
    
    args = parser.parse_args()

    # Model configuration
    FULL_MODEL_NAME = "TinyLlama/TinyLlama-1.1B-Chat-v0.3"
    SMALL_MODEL_NAME = "EleutherAI/pythia-70m"
    
    # --- Setup Device ---
    if torch.backends.mps.is_available():
        device = torch.device("mps")
        print("Loading models to mps...")
    else:
        print("MPS not available. Falling back to CPU. Energy measurement may not work as expected.")
        device = torch.device("cpu")

    # --- Load Prompts ---
    try:
        with open(args.prompts, 'r') as f:
            prompts = [line.strip() for line in f if line.strip()][:args.num_prompts]
        if not prompts:
            print("Error: Prompts file is empty or prompts not found.", file=sys.stderr)
            exit(1)
    except FileNotFoundError:
        print(f"Error: Prompts file '{args.prompts}' not found.", file=sys.stderr)
        exit(1)

    # --- Run Experiment ---
    experiment_results = {
        "config": {
            "full_model": FULL_MODEL_NAME,
            "small_model": SMALL_MODEL_NAME,
            "lambda_threshold": args.lambda_threshold,
            "max_new_tokens": args.max_new_tokens
        }
    }

    # 1. Baseline Run (All prompts to Full Model)
    print(f"\n=== BASELINE RUN ({FULL_MODEL_NAME}) ===")
    experiment_results["baseline"] = run_batch(
        FULL_MODEL_NAME, FULL_MODEL_NAME, 
        prompts, device, 
        max_new_tokens=5
    )

    # 2. Gated Run
    print(f"\n=== GATED RUN (Threshold: {args.lambda_threshold}) ===")
    experiment_results["gated"] = run_gated_batch(
        FULL_MODEL_NAME, FULL_MODEL_NAME, 
        SMALL_MODEL_NAME, SMALL_MODEL_NAME,
        prompts, 
        device, 
        lambda_threshold=args.lambda_threshold, 
        max_new_tokens=5
    )

    # --- Output Results ---
    output_filename = "mac_o1_results_final.json"
    with open(output_filename, 'w') as f:
        json_output = json.dumps(experiment_results, indent=4, allow_nan=True)
        f.write(json_output)

    print(f"\n=== RESULTS WRITTEN TO {output_filename} ===")
    print(json_output)


#     first output run isolated with Metric,Value
# Model Tested,EleutherAI/pythia-70m
# Total Tokens Generated,52 tokens
# Total Energy Consumed (kWh),4.72×10−8 kWh
# Energy Per Token (Wh/token),9.08×10−7 Wh/token:
#      (base) brendanlynch@Mac zzzzzzzhourglass % sudo /Users/brendanlynch/miniconda3/bin/python measure_mac_isolated_test.py --prompts simple_prompts.txt --num_prompts 50
# Password:
# Loading models to mps...

# === BASELINE RUN (EleutherAI/pythia-70m) ===
# Loading EleutherAI/pythia-70m for Baseline...
# `torch_dtype` is deprecated! Use `dtype` instead!
# Warning: PowerSamplerMac is intended for 'mps' device.
# Power measurement timing started.
# /Users/brendanlynch/miniconda3/lib/python3.12/site-packages/transformers/pytorch_utils.py:339: UserWarning: To copy construct from a tensor, it is recommended to use sourceTensor.clone().detach() or sourceTensor.clone().detach().requires_grad_(True), rather than torch.tensor(sourceTensor).
#   test_elements = torch.tensor(test_elements)
# The attention mask is not set and cannot be inferred from input because pad token is same as eos token. As a consequence, you may observe unexpected behavior. Please pass your input's `attention_mask` to obtain reliable results.
# huggingface/tokenizers: The current process just got forked, after parallelism has already been used. Disabling parallelism to avoid deadlocks...
# To disable this warning, you can either:
# 	- Avoid using `tokenizers` before the fork if possible
# 	- Explicitly set the environment variable TOKENIZERS_PARALLELISM=(true | false)

# --- RAW POWERMETRICS OUTPUT (START) ---
# Machine model: Mac15,12
# OS version: 24F74
# Boot arguments: 
# Boot time: Mon Dec  8 21:22:00 2025



# *** Sampled system activity (Tue Dec  9 13:28:01 2025 -0600) (1003.37ms elapsed) ***


# **** Processor usage ****

# E-Cluster HW active frequency: 0 MHz
# E-Cluster HW active residency:   0.00% (744 MHz:   0% 1044 MHz: 100% 1476 MHz:   0% 2004 MHz:   0% 2268 MHz:   0% 2556 MHz:   0% 2748 MHz:   0%)
# E-Cluster idle residency: 100.00%
# CPU 0 frequency: 1044 MHz
# CPU 0 active residency:   2.44% (744 MHz:   0% 1044 MHz: 2.4% 1476 MHz:   0% 2004 MHz:   0% 2268 MHz:   0% 2556 MHz:   0% 2748 MHz:   0%)
# CPU 0 idle residency:  97.56%
# CPU 1 frequency: 1044 MHz
# CPU 1 active residency:   1.87% (744 MHz:   0% 1044 MHz: 1.9% 1476 MHz:   0% 2004 MHz:   0% 2268 MHz:   0% 2556 MHz:   0% 2748 MHz:   0%)
# CPU 1 idle residency:  98.13%
# CPU 2 frequency: 1044 MHz
# CPU 2 active residency:   0.78% (744 MHz:   0% 1044 MHz: .78% 1476 MHz:   0% 2004 MHz:   0% 2268 MHz:   0% 2556 MHz:   0% 2748 MHz:   0%)
# CPU 2 idle residency:  99.22%
# CPU 3 frequency: 1044 MHz
# CPU 3 active residency:   0.26% (744 MHz:   0% 1044 MHz: .26% 1476 MHz:   0% 2004 MHz:   0% 2268 MHz:   0% 2556 MHz:   0% 2748 MHz:   0%)
# CPU 3 idle residency:  99.74%

# P-Cluster HW active frequency: 0 MHz
# P-Cluster HW active residency:   0.00% (816 MHz:  98% 1092 MHz:   0% 1356 MHz:   0% 1596 MHz:   0% 1884 MHz:   0% 2172 MHz:   0% 2424 MHz:   0% 2616 MHz:   0% 2808 MHz:   0% 2988 MHz:   0% 3144 MHz:   0% 3288 MHz:   0% 3420 MHz:   0% 3540 MHz:   0% 3636 MHz: 1.8% 3720 MHz:   0% 3780 MHz:   0% 3864 MHz:   0% 3960 MHz:   0% 4056 MHz:   0%)
# P-Cluster idle residency: 100.00%
# CPU 4 frequency: 3907 MHz
# CPU 4 active residency:   0.37% (816 MHz: .02% 1092 MHz:   0% 1356 MHz:   0% 1596 MHz:   0% 1884 MHz:   0% 2172 MHz:   0% 2424 MHz:   0% 2616 MHz:   0% 2808 MHz:   0% 2988 MHz:   0% 3144 MHz:   0% 3288 MHz:   0% 3420 MHz:   0% 3540 MHz:   0% 3636 MHz:   0% 3720 MHz:   0% 3780 MHz:   0% 3864 MHz:   0% 3960 MHz:   0% 4056 MHz: .35%)
# CPU 4 idle residency:  99.63%
# CPU 5 frequency: 3921 MHz
# CPU 5 active residency:   1.41% (816 MHz: .06% 1092 MHz:   0% 1356 MHz:   0% 1596 MHz:   0% 1884 MHz:   0% 2172 MHz:   0% 2424 MHz:   0% 2616 MHz:   0% 2808 MHz:   0% 2988 MHz:   0% 3144 MHz:   0% 3288 MHz:   0% 3420 MHz:   0% 3540 MHz:   0% 3636 MHz:   0% 3720 MHz:   0% 3780 MHz:   0% 3864 MHz:   0% 3960 MHz:   0% 4056 MHz: 1.4%)
# CPU 5 idle residency:  98.59%
# CPU 6 frequency: 2123 MHz
# CPU 6 active residency:   0.23% (816 MHz: .13% 1092 MHz:   0% 1356 MHz:   0% 1596 MHz:   0% 1884 MHz:   0% 2172 MHz:   0% 2424 MHz:   0% 2616 MHz:   0% 2808 MHz:   0% 2988 MHz:   0% 3144 MHz:   0% 3288 MHz:   0% 3420 MHz:   0% 3540 MHz:   0% 3636 MHz:   0% 3720 MHz:   0% 3780 MHz:   0% 3864 MHz:   0% 3960 MHz:   0% 4056 MHz: .09%)
# CPU 6 idle residency:  99.77%
# CPU 7 frequency: 1993 MHz
# CPU 7 active residency:   0.01% (816 MHz: .01% 1092 MHz:   0% 1356 MHz:   0% 1596 MHz:   0% 1884 MHz:   0% 2172 MHz:   0% 2424 MHz:   0% 2616 MHz:   0% 2808 MHz:   0% 2988 MHz:   0% 3144 MHz:   0% 3288 MHz:   0% 3420 MHz:   0% 3540 MHz:   0% 3636 MHz:   0% 3720 MHz:   0% 3780 MHz:   0% 3864 MHz:   0% 3960 MHz:   0% 4056 MHz: .01%)
# CPU 7 idle residency:  99.99%

# CPU Power: 80 mW
# GPU Power: 0 mW
# ANE Power: 0 mW
# Combined Power (CPU + GPU + ANE): 80 mW

# **** GPU usage ****

# GPU HW active frequency: 338 MHz
# GPU HW active residency:   0.35% (338 MHz: .35% 618 MHz:   0% 796 MHz:   0% 836 MHz:   0% 928 MHz:   0% 952 MHz:   0% 1056 MHz:   0% 1053 MHz:   0% 1170 MHz:   0% 1152 MHz:   0% 1278 MHz:   0% 1204 MHz:   0% 1338 MHz:   0%)
# GPU SW requested state: (P1 : 100% P2 :   0% P3 :   0% P4 :   0% P5 :   0% P6 :   0% P7 :   0% P8 :   0% P9 :   0% P10 :   0% P11 :   0% P12 :   0% P13 :   0%)
# GPU SW state: (SW_P1 : .35% SW_P2 :   0% SW_P3 :   0% SW_P4 :   0% SW_P5 :   0% SW_P6 :   0% SW_P7 :   0% SW_P8 :   0% SW_P9 :   0% SW_P10 :   0% SW_P11 :   0% SW_P12 :   0% SW_P13 :   0%)
# GPU idle residency:  99.65%
# GPU Power: 0 mW


# --- RAW POWERMETRICS OUTPUT (END) ---

# Power measurement stopped. Duration: 2.12s, Avg Power (W): 0.08

# === GATED RUN (Threshold: 0.3) ===
# Loading EleutherAI/pythia-70m and EleutherAI/pythia-70m for Gated Run...
# Warning: PowerSamplerMac is intended for 'mps' device.
# Power measurement timing started.
# Prompt 1: Routed to FULL model (lambda_2: 0.2531 or NaN)
# /Users/brendanlynch/miniconda3/lib/python3.12/site-packages/transformers/pytorch_utils.py:339: UserWarning: To copy construct from a tensor, it is recommended to use sourceTensor.clone().detach() or sourceTensor.clone().detach().requires_grad_(True), rather than torch.tensor(sourceTensor).
#   test_elements = torch.tensor(test_elements)
# Prompt 2: Routed to SMALL model (lambda_2: 0.6521)
# Prompt 3: Routed to SMALL model (lambda_2: 0.3032)
# Prompt 4: Routed to SMALL model (lambda_2: 0.4290)
# Prompt 5: Routed to SMALL model (lambda_2: 0.6221)
# Prompt 6: Routed to FULL model (lambda_2: 0.0386 or NaN)
# Prompt 7: Routed to SMALL model (lambda_2: 0.7109)
# Prompt 8: Routed to FULL model (lambda_2: 0.0804 or NaN)
# Prompt 9: Routed to SMALL model (lambda_2: 0.3527)
# Prompt 10: Routed to SMALL model (lambda_2: 0.9189)
# Prompt 11: Routed to SMALL model (lambda_2: 0.7100)
# Prompt 12: Routed to SMALL model (lambda_2: 0.9007)
# Prompt 13: Routed to SMALL model (lambda_2: 0.5319)
# Prompt 14: Routed to SMALL model (lambda_2: 0.6296)
# Prompt 15: Routed to SMALL model (lambda_2: 0.7812)
# Prompt 16: Routed to SMALL model (lambda_2: 0.7355)
# Prompt 17: Routed to SMALL model (lambda_2: 0.4041)
# Prompt 18: Routed to SMALL model (lambda_2: 0.9045)
# Prompt 19: Routed to SMALL model (lambda_2: 0.4744)
# Prompt 20: Routed to SMALL model (lambda_2: 0.4592)
# Prompt 21: Routed to FULL model (lambda_2: 0.0700 or NaN)
# Prompt 22: Routed to SMALL model (lambda_2: 0.4010)
# Prompt 23: Routed to FULL model (lambda_2: 0.1445 or NaN)
# Prompt 24: Routed to FULL model (lambda_2: 0.0031 or NaN)
# Prompt 25: Routed to SMALL model (lambda_2: 0.9448)
# Prompt 26: Routed to SMALL model (lambda_2: 0.4924)
# Prompt 27: Routed to FULL model (lambda_2: 0.2058 or NaN)
# Prompt 28: Routed to SMALL model (lambda_2: 0.7390)
# Prompt 29: Routed to SMALL model (lambda_2: 0.4668)
# Prompt 30: Routed to FULL model (lambda_2: 0.2022 or NaN)
# Prompt 31: Routed to SMALL model (lambda_2: 0.6043)
# Prompt 32: Routed to SMALL model (lambda_2: 0.7194)
# Prompt 33: Routed to SMALL model (lambda_2: 0.5916)
# Prompt 34: Routed to SMALL model (lambda_2: 1.0000)
# Prompt 35: Routed to SMALL model (lambda_2: 0.3451)
# Prompt 36: Routed to SMALL model (lambda_2: 0.8812)
# Prompt 37: Routed to SMALL model (lambda_2: 0.3210)
# Prompt 38: Routed to SMALL model (lambda_2: 0.8611)
# Prompt 39: Routed to SMALL model (lambda_2: 0.8899)
# Prompt 40: Routed to SMALL model (lambda_2: 0.9004)
# Prompt 41: Routed to SMALL model (lambda_2: 0.7100)
# Prompt 42: Routed to SMALL model (lambda_2: 0.5988)
# Prompt 43: Routed to SMALL model (lambda_2: 0.8970)
# Prompt 44: Routed to FULL model (lambda_2: 0.0070 or NaN)
# Prompt 45: Routed to FULL model (lambda_2: 0.1871 or NaN)
# Prompt 46: Routed to SMALL model (lambda_2: 0.7866)
# Prompt 47: Routed to SMALL model (lambda_2: 0.7136)
# Prompt 48: Routed to FULL model (lambda_2: 0.0575 or NaN)
# Prompt 49: Routed to FULL model (lambda_2: 0.2467 or NaN)
# Prompt 50: Routed to SMALL model (lambda_2: 0.9615)
# huggingface/tokenizers: The current process just got forked, after parallelism has already been used. Disabling parallelism to avoid deadlocks...
# To disable this warning, you can either:
# 	- Avoid using `tokenizers` before the fork if possible
# 	- Explicitly set the environment variable TOKENIZERS_PARALLELISM=(true | false)

# --- RAW POWERMETRICS OUTPUT (START) ---
# Machine model: Mac15,12
# OS version: 24F74
# Boot arguments: 
# Boot time: Mon Dec  8 21:22:00 2025



# *** Sampled system activity (Tue Dec  9 13:28:05 2025 -0600) (1003.43ms elapsed) ***


# **** Processor usage ****

# E-Cluster HW active frequency: 0 MHz
# E-Cluster HW active residency:   0.00% (744 MHz:   0% 1044 MHz:  98% 1476 MHz:   0% 2004 MHz: 1.1% 2268 MHz:   0% 2556 MHz:   0% 2748 MHz: .45%)
# E-Cluster idle residency: 100.00%
# CPU 0 frequency: 1074 MHz
# CPU 0 active residency:   1.78% (744 MHz:   0% 1044 MHz: 1.7% 1476 MHz:   0% 2004 MHz: .02% 2268 MHz:   0% 2556 MHz:   0% 2748 MHz: .02%)
# CPU 0 idle residency:  98.22%
# CPU 1 frequency: 1067 MHz
# CPU 1 active residency:   1.34% (744 MHz:   0% 1044 MHz: 1.3% 1476 MHz:   0% 2004 MHz: .03% 2268 MHz:   0% 2556 MHz:   0% 2748 MHz: .00%)
# CPU 1 idle residency:  98.66%
# CPU 2 frequency: 1045 MHz
# CPU 2 active residency:   0.94% (744 MHz:   0% 1044 MHz: .94% 1476 MHz:   0% 2004 MHz: .00% 2268 MHz:   0% 2556 MHz:   0% 2748 MHz:   0%)
# CPU 2 idle residency:  99.06%
# CPU 3 frequency: 1117 MHz
# CPU 3 active residency:   0.23% (744 MHz:   0% 1044 MHz: .21% 1476 MHz:   0% 2004 MHz: .02% 2268 MHz:   0% 2556 MHz:   0% 2748 MHz:   0%)
# CPU 3 idle residency:  99.77%

# P-Cluster HW active frequency: 0 MHz
# P-Cluster HW active residency:   0.00% (816 MHz:  98% 1092 MHz:   0% 1356 MHz:   0% 1596 MHz:   0% 1884 MHz:   0% 2172 MHz:   0% 2424 MHz:   0% 2616 MHz:   0% 2808 MHz:   0% 2988 MHz:   0% 3144 MHz:   0% 3288 MHz:   0% 3420 MHz:   0% 3540 MHz:   0% 3636 MHz: 2.3% 3720 MHz:   0% 3780 MHz:   0% 3864 MHz:   0% 3960 MHz:   0% 4056 MHz:   0%)
# P-Cluster idle residency: 100.00%
# CPU 4 frequency: 3893 MHz
# CPU 4 active residency:   1.26% (816 MHz: .06% 1092 MHz:   0% 1356 MHz:   0% 1596 MHz:   0% 1884 MHz:   0% 2172 MHz:   0% 2424 MHz:   0% 2616 MHz:   0% 2808 MHz:   0% 2988 MHz:   0% 3144 MHz:   0% 3288 MHz:   0% 3420 MHz:   0% 3540 MHz:   0% 3636 MHz:   0% 3720 MHz:   0% 3780 MHz:   0% 3864 MHz:   0% 3960 MHz:   0% 4056 MHz: 1.2%)
# CPU 4 idle residency:  98.74%
# CPU 5 frequency: 3328 MHz
# CPU 5 active residency:   0.32% (816 MHz: .07% 1092 MHz:   0% 1356 MHz:   0% 1596 MHz:   0% 1884 MHz:   0% 2172 MHz:   0% 2424 MHz:   0% 2616 MHz:   0% 2808 MHz:   0% 2988 MHz:   0% 3144 MHz:   0% 3288 MHz:   0% 3420 MHz:   0% 3540 MHz:   0% 3636 MHz:   0% 3720 MHz:   0% 3780 MHz:   0% 3864 MHz:   0% 3960 MHz:   0% 4056 MHz: .25%)
# CPU 5 idle residency:  99.68%
# CPU 6 frequency: 3078 MHz
# CPU 6 active residency:   0.23% (816 MHz: .07% 1092 MHz:   0% 1356 MHz:   0% 1596 MHz:   0% 1884 MHz:   0% 2172 MHz:   0% 2424 MHz:   0% 2616 MHz:   0% 2808 MHz:   0% 2988 MHz:   0% 3144 MHz:   0% 3288 MHz:   0% 3420 MHz:   0% 3540 MHz:   0% 3636 MHz:   0% 3720 MHz:   0% 3780 MHz:   0% 3864 MHz:   0% 3960 MHz:   0% 4056 MHz: .16%)
# CPU 6 idle residency:  99.77%
# CPU 7 frequency: 2239 MHz
# CPU 7 active residency:   0.06% (816 MHz: .04% 1092 MHz:   0% 1356 MHz:   0% 1596 MHz:   0% 1884 MHz:   0% 2172 MHz:   0% 2424 MHz:   0% 2616 MHz:   0% 2808 MHz:   0% 2988 MHz:   0% 3144 MHz:   0% 3288 MHz:   0% 3420 MHz:   0% 3540 MHz:   0% 3636 MHz:   0% 3720 MHz:   0% 3780 MHz:   0% 3864 MHz:   0% 3960 MHz:   0% 4056 MHz: .03%)
# CPU 7 idle residency:  99.94%

# CPU Power: 72 mW
# GPU Power: 0 mW
# ANE Power: 0 mW
# Combined Power (CPU + GPU + ANE): 72 mW

# **** GPU usage ****

# GPU HW active frequency: 338 MHz
# GPU HW active residency:   0.16% (338 MHz: .16% 618 MHz:   0% 796 MHz:   0% 836 MHz:   0% 928 MHz:   0% 952 MHz:   0% 1056 MHz:   0% 1053 MHz:   0% 1170 MHz:   0% 1152 MHz:   0% 1278 MHz:   0% 1204 MHz:   0% 1338 MHz:   0%)
# GPU SW requested state: (P1 : 100% P2 :   0% P3 :   0% P4 :   0% P5 :   0% P6 :   0% P7 :   0% P8 :   0% P9 :   0% P10 :   0% P11 :   0% P12 :   0% P13 :   0%)
# GPU SW state: (SW_P1 : .16% SW_P2 :   0% SW_P3 :   0% SW_P4 :   0% SW_P5 :   0% SW_P6 :   0% SW_P7 :   0% SW_P8 :   0% SW_P9 :   0% SW_P10 :   0% SW_P11 :   0% SW_P12 :   0% SW_P13 :   0%)
# GPU idle residency:  99.84%
# GPU Power: 0 mW


# --- RAW POWERMETRICS OUTPUT (END) ---

# Power measurement stopped. Duration: 0.81s, Avg Power (W): 0.07

# === RESULTS WRITTEN TO mac_o1_results_final.json ===
# {
#     "config": {
#         "full_model": "EleutherAI/pythia-70m",
#         "small_model": "EleutherAI/pythia-70m",
#         "lambda_threshold": 0.3,
#         "max_new_tokens": 128
#     },
#     "baseline": {
#         "tokens": 52,
#         "energy_kwh": 4.720406532287598e-08,
#         "cost_usd": 7.080609798431396e-09,
#         "co2_kg": 1.793754482269287e-08,
#         "energy_per_token_Wh": 9.077704869783841e-07
#     },
#     "gated": {
#         "tokens": 52,
#         "energy_kwh": 1.612692356109619e-08,
#         "cost_usd": 2.419038534164428e-09,
#         "co2_kg": 6.128230953216552e-09,
#         "routing": [
#             {
#                 "prompt": "What is the capital of France?",
#                 "lambda2": 0.2530517578125,
#                 "used_small": false,
#                 "new_tokens": 1
#             },
#             {
#                 "prompt": "What planet is closest to the sun?",
#                 "lambda2": 0.6520589192708334,
#                 "used_small": true,
#                 "new_tokens": 1
#             },
#             {
#                 "prompt": "Name a large red star.",
#                 "lambda2": 0.3032023111979167,
#                 "used_small": true,
#                 "new_tokens": 1
#             },
#             {
#                 "prompt": "What does CPU stand for?",
#                 "lambda2": 0.4289957682291667,
#                 "used_small": true,
#                 "new_tokens": 1
#             },
#             {
#                 "prompt": "List two primary colors.",
#                 "lambda2": 0.6221110026041666,
#                 "used_small": true,
#                 "new_tokens": 2
#             },
#             {
#                 "prompt": "Write the number after 10.",
#                 "lambda2": 0.03857421875,
#                 "used_small": false,
#                 "new_tokens": 1
#             },
#             {
#                 "prompt": "What is the chemical symbol for gold?",
#                 "lambda2": 0.7108968098958334,
#                 "used_small": true,
#                 "new_tokens": 1
#             },
#             {
#                 "prompt": "Who invented the light bulb?",
#                 "lambda2": 0.08040364583333333,
#                 "used_small": false,
#                 "new_tokens": 1
#             },
#             {
#                 "prompt": "What is the freezing point of water in Celsius?",
#                 "lambda2": 0.3527018229166667,
#                 "used_small": true,
#                 "new_tokens": 1
#             },
#             {
#                 "prompt": "Name the fastest land animal.",
#                 "lambda2": 0.9188639322916666,
#                 "used_small": true,
#                 "new_tokens": 2
#             },
#             {
#                 "prompt": "What is the largest ocean on Earth?",
#                 "lambda2": 0.7099609375,
#                 "used_small": true,
#                 "new_tokens": 1
#             },
#             {
#                 "prompt": "What language is spoken in Brazil?",
#                 "lambda2": 0.9007161458333334,
#                 "used_small": true,
#                 "new_tokens": 1
#             },
#             {
#                 "prompt": "What is the value of $\\pi$ (to one decimal place)?",
#                 "lambda2": 0.5319010416666666,
#                 "used_small": true,
#                 "new_tokens": 1
#             },
#             {
#                 "prompt": "How many legs does an insect have?",
#                 "lambda2": 0.6295572916666666,
#                 "used_small": true,
#                 "new_tokens": 1
#             },
#             {
#                 "prompt": "What year did the Titanic sink?",
#                 "lambda2": 0.78125,
#                 "used_small": true,
#                 "new_tokens": 1
#             },
#             {
#                 "prompt": "Name a famous German composer.",
#                 "lambda2": 0.7355143229166666,
#                 "used_small": true,
#                 "new_tokens": 1
#             },
#             {
#                 "prompt": "What is the main ingredient in bread?",
#                 "lambda2": 0.4041341145833333,
#                 "used_small": true,
#                 "new_tokens": 1
#             },
#             {
#                 "prompt": "What does WWW stand for?",
#                 "lambda2": 0.904541015625,
#                 "used_small": true,
#                 "new_tokens": 1
#             },
#             {
#                 "prompt": "Which gas do humans primarily exhale?",
#                 "lambda2": 0.4744466145833333,
#                 "used_small": true,
#                 "new_tokens": 1
#             },
#             {
#                 "prompt": "What is the largest country by land area?",
#                 "lambda2": 0.4591878255208333,
#                 "used_small": true,
#                 "new_tokens": 1
#             },
#             {
#                 "prompt": "What is the currency of Japan?",
#                 "lambda2": 0.06998697916666667,
#                 "used_small": false,
#                 "new_tokens": 1
#             },
#             {
#                 "prompt": "Who wrote Romeo and Juliet?",
#                 "lambda2": 0.4010416666666667,
#                 "used_small": true,
#                 "new_tokens": 1
#             },
#             {
#                 "prompt": "What is the unit of electric resistance?",
#                 "lambda2": 0.14453125,
#                 "used_small": false,
#                 "new_tokens": 1
#             },
#             {
#                 "prompt": "What color is chlorophyll?",
#                 "lambda2": 0.0030924479166666665,
#                 "used_small": false,
#                 "new_tokens": 1
#             },
#             {
#                 "prompt": "How many sides does a hexagon have?",
#                 "lambda2": 0.94482421875,
#                 "used_small": true,
#                 "new_tokens": 1
#             },
#             {
#                 "prompt": "What is the name of our galaxy?",
#                 "lambda2": 0.4923502604166667,
#                 "used_small": true,
#                 "new_tokens": 1
#             },
#             {
#                 "prompt": "Name the highest mountain in Africa.",
#                 "lambda2": 0.205810546875,
#                 "used_small": false,
#                 "new_tokens": 1
#             },
#             {
#                 "prompt": "What is the chemical symbol for water?",
#                 "lambda2": 0.7389729817708334,
#                 "used_small": true,
#                 "new_tokens": 1
#             },
#             {
#                 "prompt": "Who was the first U.S. President?",
#                 "lambda2": 0.466796875,
#                 "used_small": true,
#                 "new_tokens": 1
#             },
#             {
#                 "prompt": "What is the square root of 9?",
#                 "lambda2": 0.20218912760416666,
#                 "used_small": false,
#                 "new_tokens": 1
#             },
#             {
#                 "prompt": "What animal is known as the 'King of the Jungle'?",
#                 "lambda2": 0.6043294270833334,
#                 "used_small": true,
#                 "new_tokens": 1
#             },
#             {
#                 "prompt": "What metal is liquid at room temperature?",
#                 "lambda2": 0.7194010416666666,
#                 "used_small": true,
#                 "new_tokens": 1
#             },
#             {
#                 "prompt": "How many days are in a leap year?",
#                 "lambda2": 0.5916341145833334,
#                 "used_small": true,
#                 "new_tokens": 1
#             },
#             {
#                 "prompt": "What is the official language of China?",
#                 "lambda2": 0.9999796549479166,
#                 "used_small": true,
#                 "new_tokens": 1
#             },
#             {
#                 "prompt": "Name a type of pasta.",
#                 "lambda2": 0.3451334635416667,
#                 "used_small": true,
#                 "new_tokens": 1
#             },
#             {
#                 "prompt": "What is the capital of Italy?",
#                 "lambda2": 0.8812255859375,
#                 "used_small": true,
#                 "new_tokens": 1
#             },
#             {
#                 "prompt": "What is the closest star to Earth (besides the sun)?",
#                 "lambda2": 0.3209635416666667,
#                 "used_small": true,
#                 "new_tokens": 1
#             },
#             {
#                 "prompt": "What is the chemical symbol for oxygen?",
#                 "lambda2": 0.8611246744791666,
#                 "used_small": true,
#                 "new_tokens": 1
#             },
#             {
#                 "prompt": "Who painted the Mona Lisa?",
#                 "lambda2": 0.889892578125,
#                 "used_small": true,
#                 "new_tokens": 1
#             },
#             {
#                 "prompt": "What is the boiling point of water in Fahrenheit?",
#                 "lambda2": 0.900390625,
#                 "used_small": true,
#                 "new_tokens": 1
#             },
#             {
#                 "prompt": "What is the main component of Earth's atmosphere?",
#                 "lambda2": 0.7100016276041666,
#                 "used_small": true,
#                 "new_tokens": 1
#             },
#             {
#                 "prompt": "What is the definition of a desert?",
#                 "lambda2": 0.5987955729166666,
#                 "used_small": true,
#                 "new_tokens": 1
#             },
#             {
#                 "prompt": "How many strings does a standard guitar have?",
#                 "lambda2": 0.89697265625,
#                 "used_small": true,
#                 "new_tokens": 1
#             },
#             {
#                 "prompt": "Name a South American country.",
#                 "lambda2": 0.006978352864583333,
#                 "used_small": false,
#                 "new_tokens": 1
#             },
#             {
#                 "prompt": "What is the largest organ in the human body?",
#                 "lambda2": 0.18711344401041666,
#                 "used_small": false,
#                 "new_tokens": 1
#             },
#             {
#                 "prompt": "What does the acronym 'URL' stand for?",
#                 "lambda2": 0.7865804036458334,
#                 "used_small": true,
#                 "new_tokens": 1
#             },
#             {
#                 "prompt": "Which element has the atomic number 1?",
#                 "lambda2": 0.713623046875,
#                 "used_small": true,
#                 "new_tokens": 1
#             },
#             {
#                 "prompt": "What is the currency of the UK?",
#                 "lambda2": 0.0574951171875,
#                 "used_small": false,
#                 "new_tokens": 1
#             },
#             {
#                 "prompt": "Who directed the film Jaws?",
#                 "lambda2": 0.24666341145833334,
#                 "used_small": false,
#                 "new_tokens": 1
#             },
#             {
#                 "prompt": "What is the next prime number after 7?",
#                 "lambda2": 0.9614664713541666,
#                 "used_small": true,
#                 "new_tokens": 1
#             }
#         ],
#         "energy_per_token_Wh": 3.101331454056959e-07
#     }
# }














# second run:

# (base) brendanlynch@Mac zzzzzzzhourglass % 
# Baseline Run (TinyLlama/TinyLlama-1.1B-Chat-v0.3)
#     second output run Metric,Value
# Total New Tokens,250
# Total Energy (kWh),3.33×10−7
# Energy per Token (Wh),1.33×10−6
# Estimated Cost (USD),4.99×10−8
# Estimated CO2​ (kg),1.27×10−7

# Gated Run (TinyLlama/TinyLlama-1.1B-Chat-v0.3 & EleutherAI/pythia-70m)
# Metric,Value
# Total New Tokens,107
# Total Energy (kWh),1.57×10−7
# Energy per Token (Wh),1.46×10−6
# Estimated Cost (USD),2.35×10−8
# Estimated CO2​ (kg),5.96×10−8
# Routing Threshold (λ2​),0.3:

# (base) brendanlynch@Mac zzzzzzzhourglass % sudo /Users/brendanlynch/miniconda3/bin/python measure_mac_isolated_test.py --prompts simple_prompts.txt --num_prompts 50
# Loading models to mps...

# === BASELINE RUN (TinyLlama/TinyLlama-1.1B-Chat-v0.3) ===
# Loading TinyLlama/TinyLlama-1.1B-Chat-v0.3 for Baseline...
# `torch_dtype` is deprecated! Use `dtype` instead!
# Warning: PowerSamplerMac is intended for 'mps' device.
# Power measurement timing started.
# /Users/brendanlynch/miniconda3/lib/python3.12/site-packages/transformers/pytorch_utils.py:339: UserWarning: To copy construct from a tensor, it is recommended to use sourceTensor.clone().detach() or sourceTensor.clone().detach().requires_grad_(True), rather than torch.tensor(sourceTensor).
#   test_elements = torch.tensor(test_elements)
# huggingface/tokenizers: The current process just got forked, after parallelism has already been used. Disabling parallelism to avoid deadlocks...
# To disable this warning, you can either:
# 	- Avoid using `tokenizers` before the fork if possible
# 	- Explicitly set the environment variable TOKENIZERS_PARALLELISM=(true | false)

# --- RAW POWERMETRICS OUTPUT (START) ---
# Machine model: Mac15,12
# OS version: 24F74
# Boot arguments: 
# Boot time: Mon Dec  8 21:22:00 2025



# *** Sampled system activity (Tue Dec  9 13:31:03 2025 -0600) (1003.41ms elapsed) ***


# **** Processor usage ****

# E-Cluster HW active frequency: 0 MHz
# E-Cluster HW active residency:   0.00% (744 MHz:   0% 1044 MHz:  94% 1476 MHz: .46% 2004 MHz: 5.0% 2268 MHz:   0% 2556 MHz:   0% 2748 MHz: .95%)
# E-Cluster idle residency: 100.00%
# CPU 0 frequency: 1155 MHz
# CPU 0 active residency:   3.58% (744 MHz:   0% 1044 MHz: 3.2% 1476 MHz: .00% 2004 MHz: .32% 2268 MHz:   0% 2556 MHz:   0% 2748 MHz: .06%)
# CPU 0 idle residency:  96.42%
# CPU 1 frequency: 1114 MHz
# CPU 1 active residency:   3.31% (744 MHz:   0% 1044 MHz: 3.0% 1476 MHz: .04% 2004 MHz: .22% 2268 MHz:   0% 2556 MHz:   0% 2748 MHz: .00%)
# CPU 1 idle residency:  96.69%
# CPU 2 frequency: 1210 MHz
# CPU 2 active residency:   1.58% (744 MHz:   0% 1044 MHz: 1.3% 1476 MHz: .01% 2004 MHz: .26% 2268 MHz:   0% 2556 MHz:   0% 2748 MHz: .01%)
# CPU 2 idle residency:  98.42%
# CPU 3 frequency: 1118 MHz
# CPU 3 active residency:   0.49% (744 MHz:   0% 1044 MHz: .45% 1476 MHz: .00% 2004 MHz: .04% 2268 MHz:   0% 2556 MHz:   0% 2748 MHz:   0%)
# CPU 3 idle residency:  99.51%

# P-Cluster HW active frequency: 0 MHz
# P-Cluster HW active residency:   0.00% (816 MHz:  98% 1092 MHz:   0% 1356 MHz:   0% 1596 MHz:   0% 1884 MHz:   0% 2172 MHz:   0% 2424 MHz:   0% 2616 MHz:   0% 2808 MHz:   0% 2988 MHz:   0% 3144 MHz:   0% 3288 MHz:   0% 3420 MHz:   0% 3540 MHz:   0% 3636 MHz: 1.6% 3720 MHz:   0% 3780 MHz:   0% 3864 MHz:   0% 3960 MHz:   0% 4056 MHz:   0%)
# P-Cluster idle residency: 100.00%
# CPU 4 frequency: 3024 MHz
# CPU 4 active residency:   0.13% (816 MHz: .04% 1092 MHz:   0% 1356 MHz:   0% 1596 MHz:   0% 1884 MHz:   0% 2172 MHz:   0% 2424 MHz:   0% 2616 MHz:   0% 2808 MHz:   0% 2988 MHz:   0% 3144 MHz:   0% 3288 MHz:   0% 3420 MHz:   0% 3540 MHz:   0% 3636 MHz:   0% 3720 MHz:   0% 3780 MHz:   0% 3864 MHz:   0% 3960 MHz:   0% 4056 MHz: .09%)
# CPU 4 idle residency:  99.87%
# CPU 5 frequency: 3526 MHz
# CPU 5 active residency:   0.38% (816 MHz: .06% 1092 MHz:   0% 1356 MHz:   0% 1596 MHz:   0% 1884 MHz:   0% 2172 MHz:   0% 2424 MHz:   0% 2616 MHz:   0% 2808 MHz:   0% 2988 MHz:   0% 3144 MHz:   0% 3288 MHz:   0% 3420 MHz:   0% 3540 MHz:   0% 3636 MHz:   0% 3720 MHz:   0% 3780 MHz:   0% 3864 MHz:   0% 3960 MHz:   0% 4056 MHz: .32%)
# CPU 5 idle residency:  99.62%
# CPU 6 frequency: 3945 MHz
# CPU 6 active residency:   2.40% (816 MHz: .08% 1092 MHz:   0% 1356 MHz:   0% 1596 MHz:   0% 1884 MHz:   0% 2172 MHz:   0% 2424 MHz:   0% 2616 MHz:   0% 2808 MHz:   0% 2988 MHz:   0% 3144 MHz:   0% 3288 MHz:   0% 3420 MHz:   0% 3540 MHz:   0% 3636 MHz:   0% 3720 MHz:   0% 3780 MHz:   0% 3864 MHz:   0% 3960 MHz:   0% 4056 MHz: 2.3%)
# CPU 6 idle residency:  97.60%
# CPU 7 frequency: 2452 MHz
# CPU 7 active residency:   0.14% (816 MHz: .07% 1092 MHz:   0% 1356 MHz:   0% 1596 MHz:   0% 1884 MHz:   0% 2172 MHz:   0% 2424 MHz:   0% 2616 MHz:   0% 2808 MHz:   0% 2988 MHz:   0% 3144 MHz:   0% 3288 MHz:   0% 3420 MHz:   0% 3540 MHz:   0% 3636 MHz:   0% 3720 MHz:   0% 3780 MHz:   0% 3864 MHz:   0% 3960 MHz:   0% 4056 MHz: .07%)
# CPU 7 idle residency:  99.86%

# CPU Power: 125 mW
# GPU Power: 0 mW
# ANE Power: 0 mW
# Combined Power (CPU + GPU + ANE): 125 mW

# **** GPU usage ****

# GPU HW active frequency: 338 MHz
# GPU HW active residency:   0.15% (338 MHz: .15% 618 MHz:   0% 796 MHz:   0% 836 MHz:   0% 928 MHz:   0% 952 MHz:   0% 1056 MHz:   0% 1053 MHz:   0% 1170 MHz:   0% 1152 MHz:   0% 1278 MHz:   0% 1204 MHz:   0% 1338 MHz:   0%)
# GPU SW requested state: (P1 : 100% P2 :   0% P3 :   0% P4 :   0% P5 :   0% P6 :   0% P7 :   0% P8 :   0% P9 :   0% P10 :   0% P11 :   0% P12 :   0% P13 :   0%)
# GPU SW state: (SW_P1 : .15% SW_P2 :   0% SW_P3 :   0% SW_P4 :   0% SW_P5 :   0% SW_P6 :   0% SW_P7 :   0% SW_P8 :   0% SW_P9 :   0% SW_P10 :   0% SW_P11 :   0% SW_P12 :   0% SW_P13 :   0%)
# GPU idle residency:  99.85%
# GPU Power: 0 mW


# --- RAW POWERMETRICS OUTPUT (END) ---

# Power measurement stopped. Duration: 9.59s, Avg Power (W): 0.12

# === GATED RUN (Threshold: 0.3) ===
# Loading TinyLlama/TinyLlama-1.1B-Chat-v0.3 and EleutherAI/pythia-70m for Gated Run...
# Warning: PowerSamplerMac is intended for 'mps' device.
# Power measurement timing started.
# Prompt 1: Routed to SMALL model (lambda_2: 0.3645)
# /Users/brendanlynch/miniconda3/lib/python3.12/site-packages/transformers/pytorch_utils.py:339: UserWarning: To copy construct from a tensor, it is recommended to use sourceTensor.clone().detach() or sourceTensor.clone().detach().requires_grad_(True), rather than torch.tensor(sourceTensor).
#   test_elements = torch.tensor(test_elements)
# The attention mask is not set and cannot be inferred from input because pad token is same as eos token. As a consequence, you may observe unexpected behavior. Please pass your input's `attention_mask` to obtain reliable results.
# Prompt 2: Routed to SMALL model (lambda_2: 0.8634)
# Prompt 3: Routed to SMALL model (lambda_2: 0.4543)
# Prompt 4: Routed to SMALL model (lambda_2: 0.6997)
# Prompt 5: Routed to SMALL model (lambda_2: 0.4375)
# Prompt 6: Routed to SMALL model (lambda_2: 0.6107)
# Prompt 7: Routed to SMALL model (lambda_2: 0.8171)
# Prompt 8: Routed to SMALL model (lambda_2: 0.9533)
# Prompt 9: Routed to SMALL model (lambda_2: 0.7585)
# Prompt 10: Routed to FULL model (lambda_2: 0.2583 or NaN)
# Prompt 11: Routed to SMALL model (lambda_2: 0.6154)
# Prompt 12: Routed to SMALL model (lambda_2: 0.6123)
# Prompt 13: Routed to SMALL model (lambda_2: 0.8267)
# Prompt 14: Routed to SMALL model (lambda_2: 0.6479)
# Prompt 15: Routed to SMALL model (lambda_2: 0.4622)
# Prompt 16: Routed to SMALL model (lambda_2: 0.6278)
# Prompt 17: Routed to FULL model (lambda_2: 0.0744 or NaN)
# Prompt 18: Routed to FULL model (lambda_2: 0.1190 or NaN)
# Prompt 19: Routed to FULL model (lambda_2: 0.0701 or NaN)
# Prompt 20: Routed to SMALL model (lambda_2: 0.8245)
# Prompt 21: Routed to SMALL model (lambda_2: 0.6104)
# Prompt 22: Routed to SMALL model (lambda_2: 0.6699)
# Prompt 23: Routed to FULL model (lambda_2: 0.2358 or NaN)
# Prompt 24: Routed to SMALL model (lambda_2: 0.5467)
# Prompt 25: Routed to FULL model (lambda_2: 0.1799 or NaN)
# Prompt 26: Routed to FULL model (lambda_2: 0.2612 or NaN)
# Prompt 27: Routed to SMALL model (lambda_2: 0.4966)
# Prompt 28: Routed to SMALL model (lambda_2: 0.8242)
# Prompt 29: Routed to SMALL model (lambda_2: 0.6035)
# Prompt 30: Routed to SMALL model (lambda_2: 0.7225)
# Prompt 31: Routed to SMALL model (lambda_2: 0.8534)
# Prompt 32: Routed to FULL model (lambda_2: 0.2837 or NaN)
# Prompt 33: Routed to SMALL model (lambda_2: 0.5776)
# Prompt 34: Routed to SMALL model (lambda_2: 0.8425)
# Prompt 35: Routed to SMALL model (lambda_2: 0.9699)
# Prompt 36: Routed to FULL model (lambda_2: 0.2396 or NaN)
# Prompt 37: Routed to SMALL model (lambda_2: 0.6281)
# Prompt 38: Routed to SMALL model (lambda_2: 0.4456)
# Prompt 39: Routed to SMALL model (lambda_2: 0.9373)
# Prompt 40: Routed to FULL model (lambda_2: 0.0868 or NaN)
# Prompt 41: Routed to SMALL model (lambda_2: 0.8677)
# Prompt 42: Routed to SMALL model (lambda_2: 0.8874)
# Prompt 43: Routed to FULL model (lambda_2: 0.2218 or NaN)
# Prompt 44: Routed to FULL model (lambda_2: 0.0212 or NaN)
# Prompt 45: Routed to FULL model (lambda_2: 0.0198 or NaN)
# Prompt 46: Routed to SMALL model (lambda_2: 0.4754)
# Prompt 47: Routed to FULL model (lambda_2: 0.0632 or NaN)
# Prompt 48: Routed to SMALL model (lambda_2: 0.9959)
# Prompt 49: Routed to SMALL model (lambda_2: 0.3540)
# Prompt 50: Routed to SMALL model (lambda_2: 0.6491)
# huggingface/tokenizers: The current process just got forked, after parallelism has already been used. Disabling parallelism to avoid deadlocks...
# To disable this warning, you can either:
# 	- Avoid using `tokenizers` before the fork if possible
# 	- Explicitly set the environment variable TOKENIZERS_PARALLELISM=(true | false)

# --- RAW POWERMETRICS OUTPUT (START) ---
# Machine model: Mac15,12
# OS version: 24F74
# Boot arguments: 
# Boot time: Mon Dec  8 21:22:00 2025



# *** Sampled system activity (Tue Dec  9 13:31:15 2025 -0600) (1003.49ms elapsed) ***


# **** Processor usage ****

# E-Cluster HW active frequency: 0 MHz
# E-Cluster HW active residency:   0.00% (744 MHz:   0% 1044 MHz:  90% 1476 MHz:   0% 2004 MHz: 4.2% 2268 MHz: 2.8% 2556 MHz: 1.4% 2748 MHz: 1.7%)
# E-Cluster idle residency: 100.00%
# CPU 0 frequency: 1218 MHz
# CPU 0 active residency:   4.80% (744 MHz:   0% 1044 MHz: 4.1% 1476 MHz:   0% 2004 MHz: .24% 2268 MHz: .26% 2556 MHz: .10% 2748 MHz: .08%)
# CPU 0 idle residency:  95.20%
# CPU 1 frequency: 1295 MHz
# CPU 1 active residency:   3.53% (744 MHz:   0% 1044 MHz: 2.8% 1476 MHz:   0% 2004 MHz: .34% 2268 MHz: .23% 2556 MHz: .12% 2748 MHz: .05%)
# CPU 1 idle residency:  96.47%
# CPU 2 frequency: 1286 MHz
# CPU 2 active residency:   1.32% (744 MHz:   0% 1044 MHz: 1.0% 1476 MHz:   0% 2004 MHz: .19% 2268 MHz: .07% 2556 MHz: .03% 2748 MHz: .01%)
# CPU 2 idle residency:  98.68%
# CPU 3 frequency: 1101 MHz
# CPU 3 active residency:   0.77% (744 MHz:   0% 1044 MHz: .74% 1476 MHz:   0% 2004 MHz: .00% 2268 MHz: .01% 2556 MHz:   0% 2748 MHz: .01%)
# CPU 3 idle residency:  99.23%

# P-Cluster HW active frequency: 0 MHz
# P-Cluster HW active residency:   0.00% (816 MHz:  94% 1092 MHz:   0% 1356 MHz: 2.7% 1596 MHz: 2.1% 1884 MHz:   0% 2172 MHz:   0% 2424 MHz:   0% 2616 MHz:   0% 2808 MHz:   0% 2988 MHz:   0% 3144 MHz:   0% 3288 MHz:   0% 3420 MHz:   0% 3540 MHz:   0% 3636 MHz: .83% 3720 MHz:   0% 3780 MHz:   0% 3864 MHz:   0% 3960 MHz:   0% 4056 MHz:   0%)
# P-Cluster idle residency: 100.00%
# CPU 4 frequency: 3783 MHz
# CPU 4 active residency:   2.79% (816 MHz: .08% 1092 MHz:   0% 1356 MHz: .10% 1596 MHz: .10% 1884 MHz:   0% 2172 MHz:   0% 2424 MHz:   0% 2616 MHz:   0% 2808 MHz:   0% 2988 MHz:   0% 3144 MHz:   0% 3288 MHz:   0% 3420 MHz:   0% 3540 MHz:   0% 3636 MHz:   0% 3720 MHz:   0% 3780 MHz:   0% 3864 MHz:   0% 3960 MHz:   0% 4056 MHz: 2.5%)
# CPU 4 idle residency:  97.21%
# CPU 5 frequency: 3267 MHz
# CPU 5 active residency:   0.49% (816 MHz: .07% 1092 MHz:   0% 1356 MHz: .06% 1596 MHz: .00% 1884 MHz:   0% 2172 MHz:   0% 2424 MHz:   0% 2616 MHz:   0% 2808 MHz:   0% 2988 MHz:   0% 3144 MHz:   0% 3288 MHz:   0% 3420 MHz:   0% 3540 MHz:   0% 3636 MHz:   0% 3720 MHz:   0% 3780 MHz:   0% 3864 MHz:   0% 3960 MHz:   0% 4056 MHz: .36%)
# CPU 5 idle residency:  99.51%
# CPU 6 frequency: 3744 MHz
# CPU 6 active residency:   1.33% (816 MHz: .10% 1092 MHz:   0% 1356 MHz: .04% 1596 MHz: .00% 1884 MHz:   0% 2172 MHz:   0% 2424 MHz:   0% 2616 MHz:   0% 2808 MHz:   0% 2988 MHz:   0% 3144 MHz:   0% 3288 MHz:   0% 3420 MHz:   0% 3540 MHz:   0% 3636 MHz:   0% 3720 MHz:   0% 3780 MHz:   0% 3864 MHz:   0% 3960 MHz:   0% 4056 MHz: 1.2%)
# CPU 6 idle residency:  98.67%
# CPU 7 frequency: 2006 MHz
# CPU 7 active residency:   0.06% (816 MHz: .01% 1092 MHz:   0% 1356 MHz: .01% 1596 MHz: .03% 1884 MHz:   0% 2172 MHz:   0% 2424 MHz:   0% 2616 MHz:   0% 2808 MHz:   0% 2988 MHz:   0% 3144 MHz:   0% 3288 MHz:   0% 3420 MHz:   0% 3540 MHz:   0% 3636 MHz:   0% 3720 MHz:   0% 3780 MHz:   0% 3864 MHz:   0% 3960 MHz:   0% 4056 MHz: .01%)
# CPU 7 idle residency:  99.94%

# CPU Power: 167 mW
# GPU Power: 0 mW
# ANE Power: 0 mW
# Combined Power (CPU + GPU + ANE): 167 mW

# **** GPU usage ****

# GPU HW active frequency: 338 MHz
# GPU HW active residency:   0.15% (338 MHz: .15% 618 MHz:   0% 796 MHz:   0% 836 MHz:   0% 928 MHz:   0% 952 MHz:   0% 1056 MHz:   0% 1053 MHz:   0% 1170 MHz:   0% 1152 MHz:   0% 1278 MHz:   0% 1204 MHz:   0% 1338 MHz:   0%)
# GPU SW requested state: (P1 : 100% P2 :   0% P3 :   0% P4 :   0% P5 :   0% P6 :   0% P7 :   0% P8 :   0% P9 :   0% P10 :   0% P11 :   0% P12 :   0% P13 :   0%)
# GPU SW state: (SW_P1 : .15% SW_P2 :   0% SW_P3 :   0% SW_P4 :   0% SW_P5 :   0% SW_P6 :   0% SW_P7 :   0% SW_P8 :   0% SW_P9 :   0% SW_P10 :   0% SW_P11 :   0% SW_P12 :   0% SW_P13 :   0%)
# GPU idle residency:  99.85%
# GPU Power: 0 mW


# --- RAW POWERMETRICS OUTPUT (END) ---

# Power measurement stopped. Duration: 3.38s, Avg Power (W): 0.17

# === RESULTS WRITTEN TO mac_o1_results_final.json ===
# {
#     "config": {
#         "full_model": "TinyLlama/TinyLlama-1.1B-Chat-v0.3",
#         "small_model": "EleutherAI/pythia-70m",
#         "lambda_threshold": 0.3,
#         "max_new_tokens": 128
#     },
#     "baseline": {
#         "tokens": 250,
#         "energy_kwh": 3.3311823176013096e-07,
#         "cost_usd": 4.9967734764019644e-08,
#         "co2_kg": 1.2658492806884977e-07,
#         "energy_per_token_Wh": 1.3324729270405239e-06
#     },
#     "gated": {
#         "tokens": 107,
#         "energy_kwh": 1.567271829975976e-07,
#         "cost_usd": 2.350907744963964e-08,
#         "co2_kg": 5.955632953908709e-08,
#         "routing": [
#             {
#                 "prompt": "What is the capital of France?",
#                 "lambda2": 0.364501953125,
#                 "used_small": true,
#                 "new_tokens": 1
#             },
#             {
#                 "prompt": "What planet is closest to the sun?",
#                 "lambda2": 0.8634440104166666,
#                 "used_small": true,
#                 "new_tokens": 1
#             },
#             {
#                 "prompt": "Name a large red star.",
#                 "lambda2": 0.4542643229166667,
#                 "used_small": true,
#                 "new_tokens": 1
#             },
#             {
#                 "prompt": "What does CPU stand for?",
#                 "lambda2": 0.69970703125,
#                 "used_small": true,
#                 "new_tokens": 1
#             },
#             {
#                 "prompt": "List two primary colors.",
#                 "lambda2": 0.4375,
#                 "used_small": true,
#                 "new_tokens": 2
#             },
#             {
#                 "prompt": "Write the number after 10.",
#                 "lambda2": 0.6106770833333334,
#                 "used_small": true,
#                 "new_tokens": 1
#             },
#             {
#                 "prompt": "What is the chemical symbol for gold?",
#                 "lambda2": 0.8170572916666666,
#                 "used_small": true,
#                 "new_tokens": 1
#             },
#             {
#                 "prompt": "Who invented the light bulb?",
#                 "lambda2": 0.9532877604166666,
#                 "used_small": true,
#                 "new_tokens": 1
#             },
#             {
#                 "prompt": "What is the freezing point of water in Celsius?",
#                 "lambda2": 0.7584635416666666,
#                 "used_small": true,
#                 "new_tokens": 1
#             },
#             {
#                 "prompt": "Name the fastest land animal.",
#                 "lambda2": 0.25830078125,
#                 "used_small": false,
#                 "new_tokens": 5
#             },
#             {
#                 "prompt": "What is the largest ocean on Earth?",
#                 "lambda2": 0.6153971354166666,
#                 "used_small": true,
#                 "new_tokens": 1
#             },
#             {
#                 "prompt": "What language is spoken in Brazil?",
#                 "lambda2": 0.6123046875,
#                 "used_small": true,
#                 "new_tokens": 1
#             },
#             {
#                 "prompt": "What is the value of $\\pi$ (to one decimal place)?",
#                 "lambda2": 0.82666015625,
#                 "used_small": true,
#                 "new_tokens": 1
#             },
#             {
#                 "prompt": "How many legs does an insect have?",
#                 "lambda2": 0.64794921875,
#                 "used_small": true,
#                 "new_tokens": 1
#             },
#             {
#                 "prompt": "What year did the Titanic sink?",
#                 "lambda2": 0.4622395833333333,
#                 "used_small": true,
#                 "new_tokens": 1
#             },
#             {
#                 "prompt": "Name a famous German composer.",
#                 "lambda2": 0.6277669270833334,
#                 "used_small": true,
#                 "new_tokens": 1
#             },
#             {
#                 "prompt": "What is the main ingredient in bread?",
#                 "lambda2": 0.07438151041666667,
#                 "used_small": false,
#                 "new_tokens": 5
#             },
#             {
#                 "prompt": "What does WWW stand for?",
#                 "lambda2": 0.11897786458333333,
#                 "used_small": false,
#                 "new_tokens": 5
#             },
#             {
#                 "prompt": "Which gas do humans primarily exhale?",
#                 "lambda2": 0.07014973958333333,
#                 "used_small": false,
#                 "new_tokens": 5
#             },
#             {
#                 "prompt": "What is the largest country by land area?",
#                 "lambda2": 0.824462890625,
#                 "used_small": true,
#                 "new_tokens": 1
#             },
#             {
#                 "prompt": "What is the currency of Japan?",
#                 "lambda2": 0.6103515625,
#                 "used_small": true,
#                 "new_tokens": 1
#             },
#             {
#                 "prompt": "Who wrote Romeo and Juliet?",
#                 "lambda2": 0.669921875,
#                 "used_small": true,
#                 "new_tokens": 1
#             },
#             {
#                 "prompt": "What is the unit of electric resistance?",
#                 "lambda2": 0.23583984375,
#                 "used_small": false,
#                 "new_tokens": 5
#             },
#             {
#                 "prompt": "What color is chlorophyll?",
#                 "lambda2": 0.5467122395833334,
#                 "used_small": true,
#                 "new_tokens": 1
#             },
#             {
#                 "prompt": "How many sides does a hexagon have?",
#                 "lambda2": 0.17985026041666666,
#                 "used_small": false,
#                 "new_tokens": 5
#             },
#             {
#                 "prompt": "What is the name of our galaxy?",
#                 "lambda2": 0.26123046875,
#                 "used_small": false,
#                 "new_tokens": 5
#             },
#             {
#                 "prompt": "Name the highest mountain in Africa.",
#                 "lambda2": 0.49658203125,
#                 "used_small": true,
#                 "new_tokens": 1
#             },
#             {
#                 "prompt": "What is the chemical symbol for water?",
#                 "lambda2": 0.82421875,
#                 "used_small": true,
#                 "new_tokens": 1
#             },
#             {
#                 "prompt": "Who was the first U.S. President?",
#                 "lambda2": 0.603515625,
#                 "used_small": true,
#                 "new_tokens": 1
#             },
#             {
#                 "prompt": "What is the square root of 9?",
#                 "lambda2": 0.7224934895833334,
#                 "used_small": true,
#                 "new_tokens": 1
#             },
#             {
#                 "prompt": "What animal is known as the 'King of the Jungle'?",
#                 "lambda2": 0.8533528645833334,
#                 "used_small": true,
#                 "new_tokens": 1
#             },
#             {
#                 "prompt": "What metal is liquid at room temperature?",
#                 "lambda2": 0.28369140625,
#                 "used_small": false,
#                 "new_tokens": 5
#             },
#             {
#                 "prompt": "How many days are in a leap year?",
#                 "lambda2": 0.57763671875,
#                 "used_small": true,
#                 "new_tokens": 1
#             },
#             {
#                 "prompt": "What is the official language of China?",
#                 "lambda2": 0.842529296875,
#                 "used_small": true,
#                 "new_tokens": 1
#             },
#             {
#                 "prompt": "Name a type of pasta.",
#                 "lambda2": 0.9698893229166666,
#                 "used_small": true,
#                 "new_tokens": 1
#             },
#             {
#                 "prompt": "What is the capital of Italy?",
#                 "lambda2": 0.23958333333333334,
#                 "used_small": false,
#                 "new_tokens": 5
#             },
#             {
#                 "prompt": "What is the closest star to Earth (besides the sun)?",
#                 "lambda2": 0.6280924479166666,
#                 "used_small": true,
#                 "new_tokens": 1
#             },
#             {
#                 "prompt": "What is the chemical symbol for oxygen?",
#                 "lambda2": 0.4456380208333333,
#                 "used_small": true,
#                 "new_tokens": 1
#             },
#             {
#                 "prompt": "Who painted the Mona Lisa?",
#                 "lambda2": 0.9373372395833334,
#                 "used_small": true,
#                 "new_tokens": 1
#             },
#             {
#                 "prompt": "What is the boiling point of water in Fahrenheit?",
#                 "lambda2": 0.08675130208333333,
#                 "used_small": false,
#                 "new_tokens": 5
#             },
#             {
#                 "prompt": "What is the main component of Earth's atmosphere?",
#                 "lambda2": 0.86767578125,
#                 "used_small": true,
#                 "new_tokens": 1
#             },
#             {
#                 "prompt": "What is the definition of a desert?",
#                 "lambda2": 0.8873697916666666,
#                 "used_small": true,
#                 "new_tokens": 1
#             },
#             {
#                 "prompt": "How many strings does a standard guitar have?",
#                 "lambda2": 0.22184244791666666,
#                 "used_small": false,
#                 "new_tokens": 5
#             },
#             {
#                 "prompt": "Name a South American country.",
#                 "lambda2": 0.021158854166666668,
#                 "used_small": false,
#                 "new_tokens": 5
#             },
#             {
#                 "prompt": "What is the largest organ in the human body?",
#                 "lambda2": 0.019775390625,
#                 "used_small": false,
#                 "new_tokens": 5
#             },
#             {
#                 "prompt": "What does the acronym 'URL' stand for?",
#                 "lambda2": 0.4754231770833333,
#                 "used_small": true,
#                 "new_tokens": 1
#             },
#             {
#                 "prompt": "Which element has the atomic number 1?",
#                 "lambda2": 0.06315104166666667,
#                 "used_small": false,
#                 "new_tokens": 5
#             },
#             {
#                 "prompt": "What is the currency of the UK?",
#                 "lambda2": 0.9959309895833334,
#                 "used_small": true,
#                 "new_tokens": 1
#             },
#             {
#                 "prompt": "Who directed the film Jaws?",
#                 "lambda2": 0.35400390625,
#                 "used_small": true,
#                 "new_tokens": 1
#             },
#             {
#                 "prompt": "What is the next prime number after 7?",
#                 "lambda2": 0.6490885416666666,
#                 "used_small": true,
#                 "new_tokens": 1
#             }
#         ],
#         "energy_per_token_Wh": 1.464740028014931e-06
#     }
# }
# (base) brendanlynch@Mac zzzzzzzhourglass % 
