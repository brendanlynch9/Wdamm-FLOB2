import torch
import numpy as np
from transformers import AutoModelForCausalLM, AutoTokenizer
from scipy.stats import pearsonr
from scipy.linalg import eigvalsh
import sys 
import warnings
import os 

# --- Environment Setup and Diagnostics ---
# Force Python to unbuffer stdout immediately, overriding terminal behavior
os.environ['PYTHONUNBUFFERED'] = '1'

# Suppress minor warnings for clean output
warnings.filterwarnings("ignore")

# --- GLOBAL STORAGE ---
lambda2_list = []
lambda11_list = []
total_tests = 0
valid_samples = 0
# Global variable to store the tokenized inputs for the current forward pass
current_inputs = None 


# --- 1. CORE GEOMETRIC FUNCTIONS (DETERMINISTIC VERSION FROM PAPER) ---

R24 = [1, 5, 7, 11, 13, 17, 19, 23]
MODULI = [5, 7, 11, 13, 17]

def modular_lambda2(input_vector):
    """Calculates the O(1) Algebraic Connectivity (lambda2) using the deterministic graph construction."""
    # Step 1: Determine the residue class from the L2 norm of the input tokens
    norm_val = torch.norm(input_vector.float()).item()
    n_mod_24 = int(np.floor(norm_val)) % 24
    
    # Step 2: Find pairs of residues R24 whose product is congruent to n_mod_24
    pairs = [(r1, r2) for r1 in R24 for r2 in R24 if (r1 * r2) % 24 == n_mod_24]
    dim = len(pairs)
    
    # Step 3: Check for graph solvability (must have at least 3 vertices)
    if dim <= 2: 
        return np.nan, n_mod_24, False 
        
    # Step 4: Construct the Adjacency Matrix A based on Moduli similarity
    A = np.zeros((dim, dim))
    for i, pa in enumerate(pairs):
        prod_a = pa[0] * pa[1]
        for j, pb in enumerate(pairs):
            prod_b = pb[0] * pb[1]
            # Calculate the L1 distance of the products' residues across MODULI
            sim = sum(abs((prod_a % m) - (prod_b % m)) for m in MODULI)
            A[i, j] = 1.0 / (1.0 + sim)
            
    # Step 5: Calculate the Laplacian and its second smallest eigenvalue (λ₂)
    D = np.diag(A.sum(axis=1))
    L = D - A
    
    # Ensure L is numerically stable and symmetric
    L = (L + L.T) / 2
    
    try:
        eigs = np.sort(eigvalsh(L))
        lambda_2 = eigs[1]
        return lambda_2, n_mod_24, True
    except Exception:
        return np.nan, n_mod_24, False

def calculate_hodge_gap(H_flat_tensor):
    """Calculates the Hodge Gap (lambda_11)."""
    
    # CRITICAL FIX: Cast to float32 before converting to NumPy, 
    # as numpy does not natively support BFloat16.
    H_flat = H_flat_tensor.to(torch.float32).detach().cpu().numpy().astype(np.float64) 
    
    # Check if we have enough samples (sequence length L) to calculate the 11th eigenvalue
    if H_flat.shape[0] < 11:
        return np.nan
        
    H_cov = np.cov(H_flat, rowvar=False) 
    
    ridge_lambda = 1e-8 * np.mean(np.diag(H_cov))
    H_cov += ridge_lambda * np.eye(H_cov.shape[0])
    
    eigenvalues = eigvalsh(H_cov)
    eigenvalues.sort() 
    
    if eigenvalues.size < 11:
        return np.nan
        
    lambda_11 = eigenvalues[-11]
    return lambda_11

# --- 2. ONLINE TRACKING AND HOOK ---

def hodge_diagnostic_hook(module, input_tensors, output_tensors):
    """
    Forward hook function to intercept the hidden state and perform diagnostics.
    """
    global total_tests, valid_samples, current_inputs
    
    # CRITICAL FIX: Handle LlamaRMSNorm returning a single tensor, not a tuple
    H_tensor = output_tensors[0] if isinstance(output_tensors, tuple) else output_tensors

    if H_tensor.ndim != 3 or H_tensor.shape[0] != 1:
        return
        
    H_flat = H_tensor.squeeze(0)
    L = H_flat.shape[0] # Sequence length
    D = H_flat.shape[1] # Hidden dimension

    # Check if input IDs are accessible for the lambda2 anchor calculation
    if current_inputs is None or 'input_ids' not in current_inputs:
        print(f"\t\u274C FAIL (L={L}, D={D}): Input IDs not accessible for \u03BB\u2082 anchor.")
        sys.stdout.flush()
        return

    # Flatten the input_ids tensor (which contains the raw tokens) for the norm
    input_vector_anchor = current_inputs['input_ids'].float().flatten()
    
    # 1. Check L2 Norm / Lambda2
    lambda_2, n_mod_24, success = modular_lambda2(input_vector_anchor)
    
    if not success or np.isnan(lambda_2) or lambda_2 < 1e-4:
        print(f"\t\u274C FAIL (L={L}, D={D}, mod={n_mod_24}): L2-Norm Check Failed (\u03BB\u2082={lambda_2:.4f}) — skipping.")
        sys.stdout.flush() 
        return

    # 2. Check Hodge Gap / Covariance Stability (Requires L >= 11)
    lambda_11 = calculate_hodge_gap(H_flat)
    
    if np.isnan(lambda_11):
        print(f"\t\u274C FAIL (L={L}, D={D}, mod={n_mod_24}): Sequence Length (L) < 11 or Covariance Failed (\u03BB\u2082={lambda_2:.4f}) — skipping.")
        sys.stdout.flush()
        return
    
    # 3. Success
    valid_samples += 1
    lambda2_list.append(lambda_2)
    lambda11_list.append(lambda_11)

    print(f"\t\u2705 PASS (L={L}, D={D}, mod={n_mod_24}): \u03BB\u2082={lambda_2:.4f} \u2003 \u03BB\u2081\u2081={lambda_11:.4f}")
    sys.stdout.flush() 
    
# --- 3. MAIN EXECUTION ---

def run_experiment(num_runs=400): 
    global total_tests, current_inputs

    model_name = "PY007/TinyLlama-1.1B-Chat-v0.3"
    print(f"Loading fast RoPE model: {model_name}...")
    
    try:
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch.bfloat16,
            device_map="cpu", 
            trust_remote_code=False 
        )
    except Exception as e:
        print(f"FATAL ERROR: Could not load {model_name}.")
        print(f"Details: {e}")
        return

    tokenizer = AutoTokenizer.from_pretrained(model_name)
    tokenizer.pad_token = tokenizer.eos_token

    try:
        hook_module = model.model.norm 
        hook_module_name = 'model.norm'
    except AttributeError:
        print("FATAL ERROR: Could not find model.model.norm. Cannot hook the final layer.")
        return

    print(f"Hook registered on module: {hook_module_name}")
    hook_handle = hook_module.register_forward_hook(hodge_diagnostic_hook)
    model.eval()

    def generate_long_prompt(p, num_repetitions=5):
        """Generates a long prompt by repeating a short one."""
        return " ".join([p] * num_repetitions)

    # Varied short prompts re-introduced for L2 norm diversity
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

    # Create the base prompts by repeating each short one 5 times
    base_prompts = [generate_long_prompt(p, num_repetitions=5) for p in short_prompts] 
    
    # Repeat the varied list to reach the target num_runs
    test_prompts = base_prompts * (num_runs // len(base_prompts) + 1)
    test_prompts = test_prompts[:num_runs] 
    
    print("-" * 50)
    print(f"Starting experiment with {num_runs} total runs on {model_name} (Fast CPU Mode)...")
    print(f"NOTE: Expect some \u274C FAILs due to the deterministic graph rejecting certain residue classes.")
    print("-" * 50)


    for i, prompt in enumerate(test_prompts):
        total_tests = i + 1
        
        inputs = tokenizer(prompt, return_tensors="pt", truncation=True, padding="longest")
        inputs = {k: v.to(model.device) for k, v in inputs.items()}
        
        # Store inputs globally so the hook can access input_ids for lambda2
        current_inputs = inputs

        print(f"\n--- Running Test {total_tests}/{num_runs} ---")
        
        with torch.no_grad():
            model(**inputs, output_hidden_states=True) 

        # Clear global state after forward pass
        current_inputs = None

        if valid_samples >= 300: 
            print("\n*** Sufficient data gathered (300+ samples). Continuing to correlation analysis. ***")
            break

    hook_handle.remove()

    # --- 4. FINAL CORRELATION ANALYSIS ---
    
    print("\n" + "=" * 80)
    print(f"--- Final Correlation Results ({model_name} - CPU) ---")
    
    if len(lambda2_list) < 40:
        print("Not enough valid samples collected to run robust correlation analysis.")
        return

    r, p_value = pearsonr(lambda2_list, lambda11_list)
    
    print(f"Total Valid Samples: {len(lambda2_list)}")
    print(f"Total Tests Run: {total_tests}")
    print("-" * 40)
    print(f"Pearson Correlation (r): {r:.4f}")
    
    p_value_str = f"{p_value:.2e}"
    print(f"P-value: {p_value_str}")
    print("=" * 80)

    # Interpretation against the theoretical prediction
    if r < -0.6:
        print("✅ VALIDATION SUCCESS: Strong negative correlation achieved.")
        print("The presence of RoPE successfully enforces the Spectrally Closed Regime (r \u2248 -0.788).")
    elif r > 0.3:
        print("❌ CONTRADICTION: Correlation remains positive.")
        print("The model's geometry remains Unclosed (GPT-2 Anomaly) despite RoPE. Further investigation required.")
    else:
        print("⚠️ INCONCLUSIVE: Correlation is near zero. Geometric stability is weak/unaligned.")


if __name__ == "__main__":
    run_experiment(num_runs=400)

#     the terminal output was: (base) brendanlynch@Mac zzzzzzzhourglass % python ROPEmodelTest.py
# Loading fast RoPE model: PY007/TinyLlama-1.1B-Chat-v0.3...
# `torch_dtype` is deprecated! Use `dtype` instead!
# Hook registered on module: model.norm
# --------------------------------------------------
# Starting experiment with 400 total runs on PY007/TinyLlama-1.1B-Chat-v0.3 (Fast CPU Mode)...
# NOTE: Expect some ❌ FAILs due to the deterministic graph rejecting certain residue classes.
# --------------------------------------------------
# Asking to truncate to max_length but no maximum length is provided and the model has no predefined maximum length. Default to no truncation.

# --- Running Test 1/400 ---
# 	❌ FAIL (L=66, D=2048, mod=10): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 2/400 ---
# 	❌ FAIL (L=71, D=2048, mod=12): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 3/400 ---
# 	❌ FAIL (L=51, D=2048, mod=22): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 4/400 ---
# 	✅ PASS (L=271, D=2048, mod=11): λ₂=0.3127   λ₁₁=20.8543

# --- Running Test 5/400 ---
# 	✅ PASS (L=101, D=2048, mod=17): λ₂=0.3188   λ₁₁=44.5813

# --- Running Test 6/400 ---
# 	✅ PASS (L=81, D=2048, mod=11): λ₂=0.3127   λ₁₁=30.8399

# --- Running Test 7/400 ---
# 	✅ PASS (L=166, D=2048, mod=7): λ₂=0.3856   λ₁₁=33.0428

# --- Running Test 8/400 ---
# 	✅ PASS (L=81, D=2048, mod=13): λ₂=0.2597   λ₁₁=43.0695

# --- Running Test 9/400 ---
# 	❌ FAIL (L=121, D=2048, mod=4): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 10/400 ---
# 	❌ FAIL (L=126, D=2048, mod=4): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 11/400 ---
# 	❌ FAIL (L=66, D=2048, mod=10): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 12/400 ---
# 	❌ FAIL (L=71, D=2048, mod=12): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 13/400 ---
# 	❌ FAIL (L=51, D=2048, mod=22): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 14/400 ---
# 	✅ PASS (L=271, D=2048, mod=11): λ₂=0.3127   λ₁₁=20.8543

# --- Running Test 15/400 ---
# 	✅ PASS (L=101, D=2048, mod=17): λ₂=0.3188   λ₁₁=44.5813

# --- Running Test 16/400 ---
# 	✅ PASS (L=81, D=2048, mod=11): λ₂=0.3127   λ₁₁=30.8399

# --- Running Test 17/400 ---
# 	✅ PASS (L=166, D=2048, mod=7): λ₂=0.3856   λ₁₁=33.0428

# --- Running Test 18/400 ---
# 	✅ PASS (L=81, D=2048, mod=13): λ₂=0.2597   λ₁₁=43.0695

# --- Running Test 19/400 ---
# 	❌ FAIL (L=121, D=2048, mod=4): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 20/400 ---
# 	❌ FAIL (L=126, D=2048, mod=4): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 21/400 ---
# 	❌ FAIL (L=66, D=2048, mod=10): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 22/400 ---
# 	❌ FAIL (L=71, D=2048, mod=12): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 23/400 ---
# 	❌ FAIL (L=51, D=2048, mod=22): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 24/400 ---
# 	✅ PASS (L=271, D=2048, mod=11): λ₂=0.3127   λ₁₁=20.8543

# --- Running Test 25/400 ---
# 	✅ PASS (L=101, D=2048, mod=17): λ₂=0.3188   λ₁₁=44.5813

# --- Running Test 26/400 ---
# 	✅ PASS (L=81, D=2048, mod=11): λ₂=0.3127   λ₁₁=30.8399

# --- Running Test 27/400 ---
# 	✅ PASS (L=166, D=2048, mod=7): λ₂=0.3856   λ₁₁=33.0428

# --- Running Test 28/400 ---
# 	✅ PASS (L=81, D=2048, mod=13): λ₂=0.2597   λ₁₁=43.0695

# --- Running Test 29/400 ---
# 	❌ FAIL (L=121, D=2048, mod=4): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 30/400 ---
# 	❌ FAIL (L=126, D=2048, mod=4): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 31/400 ---
# 	❌ FAIL (L=66, D=2048, mod=10): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 32/400 ---
# 	❌ FAIL (L=71, D=2048, mod=12): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 33/400 ---
# 	❌ FAIL (L=51, D=2048, mod=22): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 34/400 ---
# 	✅ PASS (L=271, D=2048, mod=11): λ₂=0.3127   λ₁₁=20.8543

# --- Running Test 35/400 ---
# 	✅ PASS (L=101, D=2048, mod=17): λ₂=0.3188   λ₁₁=44.5813

# --- Running Test 36/400 ---
# 	✅ PASS (L=81, D=2048, mod=11): λ₂=0.3127   λ₁₁=30.8399

# --- Running Test 37/400 ---
# 	✅ PASS (L=166, D=2048, mod=7): λ₂=0.3856   λ₁₁=33.0428

# --- Running Test 38/400 ---
# 	✅ PASS (L=81, D=2048, mod=13): λ₂=0.2597   λ₁₁=43.0695

# --- Running Test 39/400 ---
# 	❌ FAIL (L=121, D=2048, mod=4): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 40/400 ---
# 	❌ FAIL (L=126, D=2048, mod=4): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 41/400 ---
# 	❌ FAIL (L=66, D=2048, mod=10): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 42/400 ---
# 	❌ FAIL (L=71, D=2048, mod=12): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 43/400 ---
# 	❌ FAIL (L=51, D=2048, mod=22): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 44/400 ---
# 	✅ PASS (L=271, D=2048, mod=11): λ₂=0.3127   λ₁₁=20.8543

# --- Running Test 45/400 ---
# 	✅ PASS (L=101, D=2048, mod=17): λ₂=0.3188   λ₁₁=44.5813

# --- Running Test 46/400 ---
# 	✅ PASS (L=81, D=2048, mod=11): λ₂=0.3127   λ₁₁=30.8399

# --- Running Test 47/400 ---
# 	✅ PASS (L=166, D=2048, mod=7): λ₂=0.3856   λ₁₁=33.0428

# --- Running Test 48/400 ---
# 	✅ PASS (L=81, D=2048, mod=13): λ₂=0.2597   λ₁₁=43.0695

# --- Running Test 49/400 ---
# 	❌ FAIL (L=121, D=2048, mod=4): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 50/400 ---
# 	❌ FAIL (L=126, D=2048, mod=4): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 51/400 ---
# 	❌ FAIL (L=66, D=2048, mod=10): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 52/400 ---
# 	❌ FAIL (L=71, D=2048, mod=12): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 53/400 ---
# 	❌ FAIL (L=51, D=2048, mod=22): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 54/400 ---
# 	✅ PASS (L=271, D=2048, mod=11): λ₂=0.3127   λ₁₁=20.8543

# --- Running Test 55/400 ---
# 	✅ PASS (L=101, D=2048, mod=17): λ₂=0.3188   λ₁₁=44.5813

# --- Running Test 56/400 ---
# 	✅ PASS (L=81, D=2048, mod=11): λ₂=0.3127   λ₁₁=30.8399

# --- Running Test 57/400 ---
# 	✅ PASS (L=166, D=2048, mod=7): λ₂=0.3856   λ₁₁=33.0428

# --- Running Test 58/400 ---
# 	✅ PASS (L=81, D=2048, mod=13): λ₂=0.2597   λ₁₁=43.0695

# --- Running Test 59/400 ---
# 	❌ FAIL (L=121, D=2048, mod=4): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 60/400 ---
# 	❌ FAIL (L=126, D=2048, mod=4): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 61/400 ---
# 	❌ FAIL (L=66, D=2048, mod=10): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 62/400 ---
# 	❌ FAIL (L=71, D=2048, mod=12): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 63/400 ---
# 	❌ FAIL (L=51, D=2048, mod=22): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 64/400 ---
# 	✅ PASS (L=271, D=2048, mod=11): λ₂=0.3127   λ₁₁=20.8543

# --- Running Test 65/400 ---
# 	✅ PASS (L=101, D=2048, mod=17): λ₂=0.3188   λ₁₁=44.5813

# --- Running Test 66/400 ---
# 	✅ PASS (L=81, D=2048, mod=11): λ₂=0.3127   λ₁₁=30.8399

# --- Running Test 67/400 ---
# 	✅ PASS (L=166, D=2048, mod=7): λ₂=0.3856   λ₁₁=33.0428

# --- Running Test 68/400 ---
# 	✅ PASS (L=81, D=2048, mod=13): λ₂=0.2597   λ₁₁=43.0695

# --- Running Test 69/400 ---
# 	❌ FAIL (L=121, D=2048, mod=4): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 70/400 ---
# 	❌ FAIL (L=126, D=2048, mod=4): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 71/400 ---
# 	❌ FAIL (L=66, D=2048, mod=10): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 72/400 ---
# 	❌ FAIL (L=71, D=2048, mod=12): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 73/400 ---
# 	❌ FAIL (L=51, D=2048, mod=22): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 74/400 ---
# 	✅ PASS (L=271, D=2048, mod=11): λ₂=0.3127   λ₁₁=20.8543

# --- Running Test 75/400 ---
# 	✅ PASS (L=101, D=2048, mod=17): λ₂=0.3188   λ₁₁=44.5813

# --- Running Test 76/400 ---
# 	✅ PASS (L=81, D=2048, mod=11): λ₂=0.3127   λ₁₁=30.8399

# --- Running Test 77/400 ---
# 	✅ PASS (L=166, D=2048, mod=7): λ₂=0.3856   λ₁₁=33.0428

# --- Running Test 78/400 ---
# 	✅ PASS (L=81, D=2048, mod=13): λ₂=0.2597   λ₁₁=43.0695

# --- Running Test 79/400 ---
# 	❌ FAIL (L=121, D=2048, mod=4): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 80/400 ---
# 	❌ FAIL (L=126, D=2048, mod=4): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 81/400 ---
# 	❌ FAIL (L=66, D=2048, mod=10): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 82/400 ---
# 	❌ FAIL (L=71, D=2048, mod=12): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 83/400 ---
# 	❌ FAIL (L=51, D=2048, mod=22): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 84/400 ---
# 	✅ PASS (L=271, D=2048, mod=11): λ₂=0.3127   λ₁₁=20.8543

# --- Running Test 85/400 ---
# 	✅ PASS (L=101, D=2048, mod=17): λ₂=0.3188   λ₁₁=44.5813

# --- Running Test 86/400 ---
# 	✅ PASS (L=81, D=2048, mod=11): λ₂=0.3127   λ₁₁=30.8399

# --- Running Test 87/400 ---
# 	✅ PASS (L=166, D=2048, mod=7): λ₂=0.3856   λ₁₁=33.0428

# --- Running Test 88/400 ---
# 	✅ PASS (L=81, D=2048, mod=13): λ₂=0.2597   λ₁₁=43.0695

# --- Running Test 89/400 ---
# 	❌ FAIL (L=121, D=2048, mod=4): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 90/400 ---
# 	❌ FAIL (L=126, D=2048, mod=4): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 91/400 ---
# 	❌ FAIL (L=66, D=2048, mod=10): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 92/400 ---
# 	❌ FAIL (L=71, D=2048, mod=12): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 93/400 ---
# 	❌ FAIL (L=51, D=2048, mod=22): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 94/400 ---
# 	✅ PASS (L=271, D=2048, mod=11): λ₂=0.3127   λ₁₁=20.8543

# --- Running Test 95/400 ---
# 	✅ PASS (L=101, D=2048, mod=17): λ₂=0.3188   λ₁₁=44.5813

# --- Running Test 96/400 ---
# 	✅ PASS (L=81, D=2048, mod=11): λ₂=0.3127   λ₁₁=30.8399

# --- Running Test 97/400 ---
# 	✅ PASS (L=166, D=2048, mod=7): λ₂=0.3856   λ₁₁=33.0428

# --- Running Test 98/400 ---
# 	✅ PASS (L=81, D=2048, mod=13): λ₂=0.2597   λ₁₁=43.0695

# --- Running Test 99/400 ---
# 	❌ FAIL (L=121, D=2048, mod=4): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 100/400 ---
# 	❌ FAIL (L=126, D=2048, mod=4): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 101/400 ---
# 	❌ FAIL (L=66, D=2048, mod=10): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 102/400 ---
# 	❌ FAIL (L=71, D=2048, mod=12): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 103/400 ---
# 	❌ FAIL (L=51, D=2048, mod=22): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 104/400 ---
# 	✅ PASS (L=271, D=2048, mod=11): λ₂=0.3127   λ₁₁=20.8543

# --- Running Test 105/400 ---
# 	✅ PASS (L=101, D=2048, mod=17): λ₂=0.3188   λ₁₁=44.5813

# --- Running Test 106/400 ---
# 	✅ PASS (L=81, D=2048, mod=11): λ₂=0.3127   λ₁₁=30.8399

# --- Running Test 107/400 ---
# 	✅ PASS (L=166, D=2048, mod=7): λ₂=0.3856   λ₁₁=33.0428

# --- Running Test 108/400 ---
# 	✅ PASS (L=81, D=2048, mod=13): λ₂=0.2597   λ₁₁=43.0695

# --- Running Test 109/400 ---
# 	❌ FAIL (L=121, D=2048, mod=4): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 110/400 ---
# 	❌ FAIL (L=126, D=2048, mod=4): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 111/400 ---
# 	❌ FAIL (L=66, D=2048, mod=10): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 112/400 ---
# 	❌ FAIL (L=71, D=2048, mod=12): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 113/400 ---
# 	❌ FAIL (L=51, D=2048, mod=22): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 114/400 ---
# 	✅ PASS (L=271, D=2048, mod=11): λ₂=0.3127   λ₁₁=20.8543

# --- Running Test 115/400 ---
# 	✅ PASS (L=101, D=2048, mod=17): λ₂=0.3188   λ₁₁=44.5813

# --- Running Test 116/400 ---
# 	✅ PASS (L=81, D=2048, mod=11): λ₂=0.3127   λ₁₁=30.8399

# --- Running Test 117/400 ---
# 	✅ PASS (L=166, D=2048, mod=7): λ₂=0.3856   λ₁₁=33.0428

# --- Running Test 118/400 ---
# 	✅ PASS (L=81, D=2048, mod=13): λ₂=0.2597   λ₁₁=43.0695

# --- Running Test 119/400 ---
# 	❌ FAIL (L=121, D=2048, mod=4): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 120/400 ---
# 	❌ FAIL (L=126, D=2048, mod=4): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 121/400 ---
# 	❌ FAIL (L=66, D=2048, mod=10): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 122/400 ---
# 	❌ FAIL (L=71, D=2048, mod=12): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 123/400 ---
# 	❌ FAIL (L=51, D=2048, mod=22): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 124/400 ---
# 	✅ PASS (L=271, D=2048, mod=11): λ₂=0.3127   λ₁₁=20.8543

# --- Running Test 125/400 ---
# 	✅ PASS (L=101, D=2048, mod=17): λ₂=0.3188   λ₁₁=44.5813

# --- Running Test 126/400 ---
# 	✅ PASS (L=81, D=2048, mod=11): λ₂=0.3127   λ₁₁=30.8399

# --- Running Test 127/400 ---
# 	✅ PASS (L=166, D=2048, mod=7): λ₂=0.3856   λ₁₁=33.0428

# --- Running Test 128/400 ---
# 	✅ PASS (L=81, D=2048, mod=13): λ₂=0.2597   λ₁₁=43.0695

# --- Running Test 129/400 ---
# 	❌ FAIL (L=121, D=2048, mod=4): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 130/400 ---
# 	❌ FAIL (L=126, D=2048, mod=4): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 131/400 ---
# 	❌ FAIL (L=66, D=2048, mod=10): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 132/400 ---
# 	❌ FAIL (L=71, D=2048, mod=12): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 133/400 ---
# 	❌ FAIL (L=51, D=2048, mod=22): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 134/400 ---
# 	✅ PASS (L=271, D=2048, mod=11): λ₂=0.3127   λ₁₁=20.8543

# --- Running Test 135/400 ---
# 	✅ PASS (L=101, D=2048, mod=17): λ₂=0.3188   λ₁₁=44.5813

# --- Running Test 136/400 ---
# 	✅ PASS (L=81, D=2048, mod=11): λ₂=0.3127   λ₁₁=30.8399

# --- Running Test 137/400 ---
# 	✅ PASS (L=166, D=2048, mod=7): λ₂=0.3856   λ₁₁=33.0428

# --- Running Test 138/400 ---
# 	✅ PASS (L=81, D=2048, mod=13): λ₂=0.2597   λ₁₁=43.0695

# --- Running Test 139/400 ---
# 	❌ FAIL (L=121, D=2048, mod=4): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 140/400 ---
# 	❌ FAIL (L=126, D=2048, mod=4): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 141/400 ---
# 	❌ FAIL (L=66, D=2048, mod=10): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 142/400 ---
# 	❌ FAIL (L=71, D=2048, mod=12): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 143/400 ---
# 	❌ FAIL (L=51, D=2048, mod=22): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 144/400 ---
# 	✅ PASS (L=271, D=2048, mod=11): λ₂=0.3127   λ₁₁=20.8543

# --- Running Test 145/400 ---
# 	✅ PASS (L=101, D=2048, mod=17): λ₂=0.3188   λ₁₁=44.5813

# --- Running Test 146/400 ---
# 	✅ PASS (L=81, D=2048, mod=11): λ₂=0.3127   λ₁₁=30.8399

# --- Running Test 147/400 ---
# 	✅ PASS (L=166, D=2048, mod=7): λ₂=0.3856   λ₁₁=33.0428

# --- Running Test 148/400 ---
# 	✅ PASS (L=81, D=2048, mod=13): λ₂=0.2597   λ₁₁=43.0695

# --- Running Test 149/400 ---
# 	❌ FAIL (L=121, D=2048, mod=4): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 150/400 ---
# 	❌ FAIL (L=126, D=2048, mod=4): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 151/400 ---
# 	❌ FAIL (L=66, D=2048, mod=10): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 152/400 ---
# 	❌ FAIL (L=71, D=2048, mod=12): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 153/400 ---
# 	❌ FAIL (L=51, D=2048, mod=22): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 154/400 ---
# 	✅ PASS (L=271, D=2048, mod=11): λ₂=0.3127   λ₁₁=20.8543

# --- Running Test 155/400 ---
# 	✅ PASS (L=101, D=2048, mod=17): λ₂=0.3188   λ₁₁=44.5813

# --- Running Test 156/400 ---
# 	✅ PASS (L=81, D=2048, mod=11): λ₂=0.3127   λ₁₁=30.8399

# --- Running Test 157/400 ---
# 	✅ PASS (L=166, D=2048, mod=7): λ₂=0.3856   λ₁₁=33.0428

# --- Running Test 158/400 ---
# 	✅ PASS (L=81, D=2048, mod=13): λ₂=0.2597   λ₁₁=43.0695

# --- Running Test 159/400 ---
# 	❌ FAIL (L=121, D=2048, mod=4): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 160/400 ---
# 	❌ FAIL (L=126, D=2048, mod=4): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 161/400 ---
# 	❌ FAIL (L=66, D=2048, mod=10): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 162/400 ---
# 	❌ FAIL (L=71, D=2048, mod=12): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 163/400 ---
# 	❌ FAIL (L=51, D=2048, mod=22): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 164/400 ---
# 	✅ PASS (L=271, D=2048, mod=11): λ₂=0.3127   λ₁₁=20.8543

# --- Running Test 165/400 ---
# 	✅ PASS (L=101, D=2048, mod=17): λ₂=0.3188   λ₁₁=44.5813

# --- Running Test 166/400 ---
# 	✅ PASS (L=81, D=2048, mod=11): λ₂=0.3127   λ₁₁=30.8399

# --- Running Test 167/400 ---
# 	✅ PASS (L=166, D=2048, mod=7): λ₂=0.3856   λ₁₁=33.0428

# --- Running Test 168/400 ---
# 	✅ PASS (L=81, D=2048, mod=13): λ₂=0.2597   λ₁₁=43.0695

# --- Running Test 169/400 ---
# 	❌ FAIL (L=121, D=2048, mod=4): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 170/400 ---
# 	❌ FAIL (L=126, D=2048, mod=4): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 171/400 ---
# 	❌ FAIL (L=66, D=2048, mod=10): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 172/400 ---
# 	❌ FAIL (L=71, D=2048, mod=12): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 173/400 ---
# 	❌ FAIL (L=51, D=2048, mod=22): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 174/400 ---
# 	✅ PASS (L=271, D=2048, mod=11): λ₂=0.3127   λ₁₁=20.8543

# --- Running Test 175/400 ---
# 	✅ PASS (L=101, D=2048, mod=17): λ₂=0.3188   λ₁₁=44.5813

# --- Running Test 176/400 ---
# 	✅ PASS (L=81, D=2048, mod=11): λ₂=0.3127   λ₁₁=30.8399

# --- Running Test 177/400 ---
# 	✅ PASS (L=166, D=2048, mod=7): λ₂=0.3856   λ₁₁=33.0428

# --- Running Test 178/400 ---
# 	✅ PASS (L=81, D=2048, mod=13): λ₂=0.2597   λ₁₁=43.0695

# --- Running Test 179/400 ---
# 	❌ FAIL (L=121, D=2048, mod=4): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 180/400 ---
# 	❌ FAIL (L=126, D=2048, mod=4): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 181/400 ---
# 	❌ FAIL (L=66, D=2048, mod=10): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 182/400 ---
# 	❌ FAIL (L=71, D=2048, mod=12): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 183/400 ---
# 	❌ FAIL (L=51, D=2048, mod=22): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 184/400 ---
# 	✅ PASS (L=271, D=2048, mod=11): λ₂=0.3127   λ₁₁=20.8543

# --- Running Test 185/400 ---
# 	✅ PASS (L=101, D=2048, mod=17): λ₂=0.3188   λ₁₁=44.5813

# --- Running Test 186/400 ---
# 	✅ PASS (L=81, D=2048, mod=11): λ₂=0.3127   λ₁₁=30.8399

# --- Running Test 187/400 ---
# 	✅ PASS (L=166, D=2048, mod=7): λ₂=0.3856   λ₁₁=33.0428

# --- Running Test 188/400 ---
# 	✅ PASS (L=81, D=2048, mod=13): λ₂=0.2597   λ₁₁=43.0695

# --- Running Test 189/400 ---
# 	❌ FAIL (L=121, D=2048, mod=4): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 190/400 ---
# 	❌ FAIL (L=126, D=2048, mod=4): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 191/400 ---
# 	❌ FAIL (L=66, D=2048, mod=10): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 192/400 ---
# 	❌ FAIL (L=71, D=2048, mod=12): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 193/400 ---
# 	❌ FAIL (L=51, D=2048, mod=22): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 194/400 ---
# 	✅ PASS (L=271, D=2048, mod=11): λ₂=0.3127   λ₁₁=20.8543

# --- Running Test 195/400 ---
# 	✅ PASS (L=101, D=2048, mod=17): λ₂=0.3188   λ₁₁=44.5813

# --- Running Test 196/400 ---
# 	✅ PASS (L=81, D=2048, mod=11): λ₂=0.3127   λ₁₁=30.8399

# --- Running Test 197/400 ---
# 	✅ PASS (L=166, D=2048, mod=7): λ₂=0.3856   λ₁₁=33.0428

# --- Running Test 198/400 ---
# 	✅ PASS (L=81, D=2048, mod=13): λ₂=0.2597   λ₁₁=43.0695

# --- Running Test 199/400 ---
# 	❌ FAIL (L=121, D=2048, mod=4): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 200/400 ---
# 	❌ FAIL (L=126, D=2048, mod=4): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 201/400 ---
# 	❌ FAIL (L=66, D=2048, mod=10): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 202/400 ---
# 	❌ FAIL (L=71, D=2048, mod=12): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 203/400 ---
# 	❌ FAIL (L=51, D=2048, mod=22): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 204/400 ---
# 	✅ PASS (L=271, D=2048, mod=11): λ₂=0.3127   λ₁₁=20.8543

# --- Running Test 205/400 ---
# 	✅ PASS (L=101, D=2048, mod=17): λ₂=0.3188   λ₁₁=44.5813

# --- Running Test 206/400 ---
# 	✅ PASS (L=81, D=2048, mod=11): λ₂=0.3127   λ₁₁=30.8399

# --- Running Test 207/400 ---
# 	✅ PASS (L=166, D=2048, mod=7): λ₂=0.3856   λ₁₁=33.0428

# --- Running Test 208/400 ---
# 	✅ PASS (L=81, D=2048, mod=13): λ₂=0.2597   λ₁₁=43.0695

# --- Running Test 209/400 ---
# 	❌ FAIL (L=121, D=2048, mod=4): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 210/400 ---
# 	❌ FAIL (L=126, D=2048, mod=4): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 211/400 ---
# 	❌ FAIL (L=66, D=2048, mod=10): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 212/400 ---
# 	❌ FAIL (L=71, D=2048, mod=12): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 213/400 ---
# 	❌ FAIL (L=51, D=2048, mod=22): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 214/400 ---
# 	✅ PASS (L=271, D=2048, mod=11): λ₂=0.3127   λ₁₁=20.8543

# --- Running Test 215/400 ---
# 	✅ PASS (L=101, D=2048, mod=17): λ₂=0.3188   λ₁₁=44.5813

# --- Running Test 216/400 ---
# 	✅ PASS (L=81, D=2048, mod=11): λ₂=0.3127   λ₁₁=30.8399

# --- Running Test 217/400 ---
# 	✅ PASS (L=166, D=2048, mod=7): λ₂=0.3856   λ₁₁=33.0428

# --- Running Test 218/400 ---
# 	✅ PASS (L=81, D=2048, mod=13): λ₂=0.2597   λ₁₁=43.0695

# --- Running Test 219/400 ---
# 	❌ FAIL (L=121, D=2048, mod=4): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 220/400 ---
# 	❌ FAIL (L=126, D=2048, mod=4): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 221/400 ---
# 	❌ FAIL (L=66, D=2048, mod=10): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 222/400 ---
# 	❌ FAIL (L=71, D=2048, mod=12): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 223/400 ---
# 	❌ FAIL (L=51, D=2048, mod=22): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 224/400 ---
# 	✅ PASS (L=271, D=2048, mod=11): λ₂=0.3127   λ₁₁=20.8543

# --- Running Test 225/400 ---
# 	✅ PASS (L=101, D=2048, mod=17): λ₂=0.3188   λ₁₁=44.5813

# --- Running Test 226/400 ---
# 	✅ PASS (L=81, D=2048, mod=11): λ₂=0.3127   λ₁₁=30.8399

# --- Running Test 227/400 ---
# 	✅ PASS (L=166, D=2048, mod=7): λ₂=0.3856   λ₁₁=33.0428

# --- Running Test 228/400 ---
# 	✅ PASS (L=81, D=2048, mod=13): λ₂=0.2597   λ₁₁=43.0695

# --- Running Test 229/400 ---
# 	❌ FAIL (L=121, D=2048, mod=4): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 230/400 ---
# 	❌ FAIL (L=126, D=2048, mod=4): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 231/400 ---
# 	❌ FAIL (L=66, D=2048, mod=10): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 232/400 ---
# 	❌ FAIL (L=71, D=2048, mod=12): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 233/400 ---
# 	❌ FAIL (L=51, D=2048, mod=22): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 234/400 ---
# 	✅ PASS (L=271, D=2048, mod=11): λ₂=0.3127   λ₁₁=20.8543

# --- Running Test 235/400 ---
# 	✅ PASS (L=101, D=2048, mod=17): λ₂=0.3188   λ₁₁=44.5813

# --- Running Test 236/400 ---
# 	✅ PASS (L=81, D=2048, mod=11): λ₂=0.3127   λ₁₁=30.8399

# --- Running Test 237/400 ---
# 	✅ PASS (L=166, D=2048, mod=7): λ₂=0.3856   λ₁₁=33.0428

# --- Running Test 238/400 ---
# 	✅ PASS (L=81, D=2048, mod=13): λ₂=0.2597   λ₁₁=43.0695

# --- Running Test 239/400 ---
# 	❌ FAIL (L=121, D=2048, mod=4): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 240/400 ---
# 	❌ FAIL (L=126, D=2048, mod=4): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 241/400 ---
# 	❌ FAIL (L=66, D=2048, mod=10): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 242/400 ---
# 	❌ FAIL (L=71, D=2048, mod=12): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 243/400 ---
# 	❌ FAIL (L=51, D=2048, mod=22): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 244/400 ---
# 	✅ PASS (L=271, D=2048, mod=11): λ₂=0.3127   λ₁₁=20.8543

# --- Running Test 245/400 ---
# 	✅ PASS (L=101, D=2048, mod=17): λ₂=0.3188   λ₁₁=44.5813

# --- Running Test 246/400 ---
# 	✅ PASS (L=81, D=2048, mod=11): λ₂=0.3127   λ₁₁=30.8399

# --- Running Test 247/400 ---
# 	✅ PASS (L=166, D=2048, mod=7): λ₂=0.3856   λ₁₁=33.0428

# --- Running Test 248/400 ---
# 	✅ PASS (L=81, D=2048, mod=13): λ₂=0.2597   λ₁₁=43.0695

# --- Running Test 249/400 ---
# 	❌ FAIL (L=121, D=2048, mod=4): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 250/400 ---
# 	❌ FAIL (L=126, D=2048, mod=4): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 251/400 ---
# 	❌ FAIL (L=66, D=2048, mod=10): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 252/400 ---
# 	❌ FAIL (L=71, D=2048, mod=12): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 253/400 ---
# 	❌ FAIL (L=51, D=2048, mod=22): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 254/400 ---
# 	✅ PASS (L=271, D=2048, mod=11): λ₂=0.3127   λ₁₁=20.8543

# --- Running Test 255/400 ---
# 	✅ PASS (L=101, D=2048, mod=17): λ₂=0.3188   λ₁₁=44.5813

# --- Running Test 256/400 ---
# 	✅ PASS (L=81, D=2048, mod=11): λ₂=0.3127   λ₁₁=30.8399

# --- Running Test 257/400 ---
# 	✅ PASS (L=166, D=2048, mod=7): λ₂=0.3856   λ₁₁=33.0428

# --- Running Test 258/400 ---
# 	✅ PASS (L=81, D=2048, mod=13): λ₂=0.2597   λ₁₁=43.0695

# --- Running Test 259/400 ---
# 	❌ FAIL (L=121, D=2048, mod=4): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 260/400 ---
# 	❌ FAIL (L=126, D=2048, mod=4): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 261/400 ---
# 	❌ FAIL (L=66, D=2048, mod=10): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 262/400 ---
# 	❌ FAIL (L=71, D=2048, mod=12): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 263/400 ---
# 	❌ FAIL (L=51, D=2048, mod=22): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 264/400 ---
# 	✅ PASS (L=271, D=2048, mod=11): λ₂=0.3127   λ₁₁=20.8543

# --- Running Test 265/400 ---
# 	✅ PASS (L=101, D=2048, mod=17): λ₂=0.3188   λ₁₁=44.5813

# --- Running Test 266/400 ---
# 	✅ PASS (L=81, D=2048, mod=11): λ₂=0.3127   λ₁₁=30.8399

# --- Running Test 267/400 ---
# 	✅ PASS (L=166, D=2048, mod=7): λ₂=0.3856   λ₁₁=33.0428

# --- Running Test 268/400 ---
# 	✅ PASS (L=81, D=2048, mod=13): λ₂=0.2597   λ₁₁=43.0695

# --- Running Test 269/400 ---
# 	❌ FAIL (L=121, D=2048, mod=4): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 270/400 ---
# 	❌ FAIL (L=126, D=2048, mod=4): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 271/400 ---
# 	❌ FAIL (L=66, D=2048, mod=10): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 272/400 ---
# 	❌ FAIL (L=71, D=2048, mod=12): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 273/400 ---
# 	❌ FAIL (L=51, D=2048, mod=22): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 274/400 ---
# 	✅ PASS (L=271, D=2048, mod=11): λ₂=0.3127   λ₁₁=20.8543

# --- Running Test 275/400 ---
# 	✅ PASS (L=101, D=2048, mod=17): λ₂=0.3188   λ₁₁=44.5813

# --- Running Test 276/400 ---
# 	✅ PASS (L=81, D=2048, mod=11): λ₂=0.3127   λ₁₁=30.8399

# --- Running Test 277/400 ---
# 	✅ PASS (L=166, D=2048, mod=7): λ₂=0.3856   λ₁₁=33.0428

# --- Running Test 278/400 ---
# 	✅ PASS (L=81, D=2048, mod=13): λ₂=0.2597   λ₁₁=43.0695

# --- Running Test 279/400 ---
# 	❌ FAIL (L=121, D=2048, mod=4): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 280/400 ---
# 	❌ FAIL (L=126, D=2048, mod=4): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 281/400 ---
# 	❌ FAIL (L=66, D=2048, mod=10): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 282/400 ---
# 	❌ FAIL (L=71, D=2048, mod=12): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 283/400 ---
# 	❌ FAIL (L=51, D=2048, mod=22): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 284/400 ---
# 	✅ PASS (L=271, D=2048, mod=11): λ₂=0.3127   λ₁₁=20.8543

# --- Running Test 285/400 ---
# 	✅ PASS (L=101, D=2048, mod=17): λ₂=0.3188   λ₁₁=44.5813

# --- Running Test 286/400 ---
# 	✅ PASS (L=81, D=2048, mod=11): λ₂=0.3127   λ₁₁=30.8399

# --- Running Test 287/400 ---
# 	✅ PASS (L=166, D=2048, mod=7): λ₂=0.3856   λ₁₁=33.0428

# --- Running Test 288/400 ---
# 	✅ PASS (L=81, D=2048, mod=13): λ₂=0.2597   λ₁₁=43.0695

# --- Running Test 289/400 ---
# 	❌ FAIL (L=121, D=2048, mod=4): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 290/400 ---
# 	❌ FAIL (L=126, D=2048, mod=4): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 291/400 ---
# 	❌ FAIL (L=66, D=2048, mod=10): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 292/400 ---
# 	❌ FAIL (L=71, D=2048, mod=12): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 293/400 ---
# 	❌ FAIL (L=51, D=2048, mod=22): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 294/400 ---
# 	✅ PASS (L=271, D=2048, mod=11): λ₂=0.3127   λ₁₁=20.8543

# --- Running Test 295/400 ---
# 	✅ PASS (L=101, D=2048, mod=17): λ₂=0.3188   λ₁₁=44.5813

# --- Running Test 296/400 ---
# 	✅ PASS (L=81, D=2048, mod=11): λ₂=0.3127   λ₁₁=30.8399

# --- Running Test 297/400 ---
# 	✅ PASS (L=166, D=2048, mod=7): λ₂=0.3856   λ₁₁=33.0428

# --- Running Test 298/400 ---
# 	✅ PASS (L=81, D=2048, mod=13): λ₂=0.2597   λ₁₁=43.0695

# --- Running Test 299/400 ---
# 	❌ FAIL (L=121, D=2048, mod=4): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 300/400 ---
# 	❌ FAIL (L=126, D=2048, mod=4): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 301/400 ---
# 	❌ FAIL (L=66, D=2048, mod=10): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 302/400 ---
# 	❌ FAIL (L=71, D=2048, mod=12): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 303/400 ---
# 	❌ FAIL (L=51, D=2048, mod=22): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 304/400 ---
# 	✅ PASS (L=271, D=2048, mod=11): λ₂=0.3127   λ₁₁=20.8543

# --- Running Test 305/400 ---
# 	✅ PASS (L=101, D=2048, mod=17): λ₂=0.3188   λ₁₁=44.5813

# --- Running Test 306/400 ---
# 	✅ PASS (L=81, D=2048, mod=11): λ₂=0.3127   λ₁₁=30.8399

# --- Running Test 307/400 ---
# 	✅ PASS (L=166, D=2048, mod=7): λ₂=0.3856   λ₁₁=33.0428

# --- Running Test 308/400 ---
# 	✅ PASS (L=81, D=2048, mod=13): λ₂=0.2597   λ₁₁=43.0695

# --- Running Test 309/400 ---
# 	❌ FAIL (L=121, D=2048, mod=4): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 310/400 ---
# 	❌ FAIL (L=126, D=2048, mod=4): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 311/400 ---
# 	❌ FAIL (L=66, D=2048, mod=10): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 312/400 ---
# 	❌ FAIL (L=71, D=2048, mod=12): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 313/400 ---
# 	❌ FAIL (L=51, D=2048, mod=22): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 314/400 ---
# 	✅ PASS (L=271, D=2048, mod=11): λ₂=0.3127   λ₁₁=20.8543

# --- Running Test 315/400 ---
# 	✅ PASS (L=101, D=2048, mod=17): λ₂=0.3188   λ₁₁=44.5813

# --- Running Test 316/400 ---
# 	✅ PASS (L=81, D=2048, mod=11): λ₂=0.3127   λ₁₁=30.8399

# --- Running Test 317/400 ---
# 	✅ PASS (L=166, D=2048, mod=7): λ₂=0.3856   λ₁₁=33.0428

# --- Running Test 318/400 ---
# 	✅ PASS (L=81, D=2048, mod=13): λ₂=0.2597   λ₁₁=43.0695

# --- Running Test 319/400 ---
# 	❌ FAIL (L=121, D=2048, mod=4): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 320/400 ---
# 	❌ FAIL (L=126, D=2048, mod=4): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 321/400 ---
# 	❌ FAIL (L=66, D=2048, mod=10): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 322/400 ---
# 	❌ FAIL (L=71, D=2048, mod=12): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 323/400 ---
# 	❌ FAIL (L=51, D=2048, mod=22): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 324/400 ---
# 	✅ PASS (L=271, D=2048, mod=11): λ₂=0.3127   λ₁₁=20.8543

# --- Running Test 325/400 ---
# 	✅ PASS (L=101, D=2048, mod=17): λ₂=0.3188   λ₁₁=44.5813

# --- Running Test 326/400 ---
# 	✅ PASS (L=81, D=2048, mod=11): λ₂=0.3127   λ₁₁=30.8399

# --- Running Test 327/400 ---
# 	✅ PASS (L=166, D=2048, mod=7): λ₂=0.3856   λ₁₁=33.0428

# --- Running Test 328/400 ---
# 	✅ PASS (L=81, D=2048, mod=13): λ₂=0.2597   λ₁₁=43.0695

# --- Running Test 329/400 ---
# 	❌ FAIL (L=121, D=2048, mod=4): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 330/400 ---
# 	❌ FAIL (L=126, D=2048, mod=4): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 331/400 ---
# 	❌ FAIL (L=66, D=2048, mod=10): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 332/400 ---
# 	❌ FAIL (L=71, D=2048, mod=12): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 333/400 ---
# 	❌ FAIL (L=51, D=2048, mod=22): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 334/400 ---
# 	✅ PASS (L=271, D=2048, mod=11): λ₂=0.3127   λ₁₁=20.8543

# --- Running Test 335/400 ---
# 	✅ PASS (L=101, D=2048, mod=17): λ₂=0.3188   λ₁₁=44.5813

# --- Running Test 336/400 ---
# 	✅ PASS (L=81, D=2048, mod=11): λ₂=0.3127   λ₁₁=30.8399

# --- Running Test 337/400 ---
# 	✅ PASS (L=166, D=2048, mod=7): λ₂=0.3856   λ₁₁=33.0428

# --- Running Test 338/400 ---
# 	✅ PASS (L=81, D=2048, mod=13): λ₂=0.2597   λ₁₁=43.0695

# --- Running Test 339/400 ---
# 	❌ FAIL (L=121, D=2048, mod=4): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 340/400 ---
# 	❌ FAIL (L=126, D=2048, mod=4): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 341/400 ---
# 	❌ FAIL (L=66, D=2048, mod=10): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 342/400 ---
# 	❌ FAIL (L=71, D=2048, mod=12): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 343/400 ---
# 	❌ FAIL (L=51, D=2048, mod=22): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 344/400 ---
# 	✅ PASS (L=271, D=2048, mod=11): λ₂=0.3127   λ₁₁=20.8543

# --- Running Test 345/400 ---
# 	✅ PASS (L=101, D=2048, mod=17): λ₂=0.3188   λ₁₁=44.5813

# --- Running Test 346/400 ---
# 	✅ PASS (L=81, D=2048, mod=11): λ₂=0.3127   λ₁₁=30.8399

# --- Running Test 347/400 ---
# 	✅ PASS (L=166, D=2048, mod=7): λ₂=0.3856   λ₁₁=33.0428

# --- Running Test 348/400 ---
# 	✅ PASS (L=81, D=2048, mod=13): λ₂=0.2597   λ₁₁=43.0695

# --- Running Test 349/400 ---
# 	❌ FAIL (L=121, D=2048, mod=4): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 350/400 ---
# 	❌ FAIL (L=126, D=2048, mod=4): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 351/400 ---
# 	❌ FAIL (L=66, D=2048, mod=10): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 352/400 ---
# 	❌ FAIL (L=71, D=2048, mod=12): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 353/400 ---
# 	❌ FAIL (L=51, D=2048, mod=22): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 354/400 ---
# 	✅ PASS (L=271, D=2048, mod=11): λ₂=0.3127   λ₁₁=20.8543

# --- Running Test 355/400 ---
# 	✅ PASS (L=101, D=2048, mod=17): λ₂=0.3188   λ₁₁=44.5813

# --- Running Test 356/400 ---
# 	✅ PASS (L=81, D=2048, mod=11): λ₂=0.3127   λ₁₁=30.8399

# --- Running Test 357/400 ---
# 	✅ PASS (L=166, D=2048, mod=7): λ₂=0.3856   λ₁₁=33.0428

# --- Running Test 358/400 ---
# 	✅ PASS (L=81, D=2048, mod=13): λ₂=0.2597   λ₁₁=43.0695

# --- Running Test 359/400 ---
# 	❌ FAIL (L=121, D=2048, mod=4): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 360/400 ---
# 	❌ FAIL (L=126, D=2048, mod=4): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 361/400 ---
# 	❌ FAIL (L=66, D=2048, mod=10): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 362/400 ---
# 	❌ FAIL (L=71, D=2048, mod=12): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 363/400 ---
# 	❌ FAIL (L=51, D=2048, mod=22): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 364/400 ---
# 	✅ PASS (L=271, D=2048, mod=11): λ₂=0.3127   λ₁₁=20.8543

# --- Running Test 365/400 ---
# 	✅ PASS (L=101, D=2048, mod=17): λ₂=0.3188   λ₁₁=44.5813

# --- Running Test 366/400 ---
# 	✅ PASS (L=81, D=2048, mod=11): λ₂=0.3127   λ₁₁=30.8399

# --- Running Test 367/400 ---
# 	✅ PASS (L=166, D=2048, mod=7): λ₂=0.3856   λ₁₁=33.0428

# --- Running Test 368/400 ---
# 	✅ PASS (L=81, D=2048, mod=13): λ₂=0.2597   λ₁₁=43.0695

# --- Running Test 369/400 ---
# 	❌ FAIL (L=121, D=2048, mod=4): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 370/400 ---
# 	❌ FAIL (L=126, D=2048, mod=4): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 371/400 ---
# 	❌ FAIL (L=66, D=2048, mod=10): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 372/400 ---
# 	❌ FAIL (L=71, D=2048, mod=12): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 373/400 ---
# 	❌ FAIL (L=51, D=2048, mod=22): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 374/400 ---
# 	✅ PASS (L=271, D=2048, mod=11): λ₂=0.3127   λ₁₁=20.8543

# --- Running Test 375/400 ---
# 	✅ PASS (L=101, D=2048, mod=17): λ₂=0.3188   λ₁₁=44.5813

# --- Running Test 376/400 ---
# 	✅ PASS (L=81, D=2048, mod=11): λ₂=0.3127   λ₁₁=30.8399

# --- Running Test 377/400 ---
# 	✅ PASS (L=166, D=2048, mod=7): λ₂=0.3856   λ₁₁=33.0428

# --- Running Test 378/400 ---
# 	✅ PASS (L=81, D=2048, mod=13): λ₂=0.2597   λ₁₁=43.0695

# --- Running Test 379/400 ---
# 	❌ FAIL (L=121, D=2048, mod=4): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 380/400 ---
# 	❌ FAIL (L=126, D=2048, mod=4): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 381/400 ---
# 	❌ FAIL (L=66, D=2048, mod=10): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 382/400 ---
# 	❌ FAIL (L=71, D=2048, mod=12): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 383/400 ---
# 	❌ FAIL (L=51, D=2048, mod=22): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 384/400 ---
# 	✅ PASS (L=271, D=2048, mod=11): λ₂=0.3127   λ₁₁=20.8543

# --- Running Test 385/400 ---
# 	✅ PASS (L=101, D=2048, mod=17): λ₂=0.3188   λ₁₁=44.5813

# --- Running Test 386/400 ---
# 	✅ PASS (L=81, D=2048, mod=11): λ₂=0.3127   λ₁₁=30.8399

# --- Running Test 387/400 ---
# 	✅ PASS (L=166, D=2048, mod=7): λ₂=0.3856   λ₁₁=33.0428

# --- Running Test 388/400 ---
# 	✅ PASS (L=81, D=2048, mod=13): λ₂=0.2597   λ₁₁=43.0695

# --- Running Test 389/400 ---
# 	❌ FAIL (L=121, D=2048, mod=4): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 390/400 ---
# 	❌ FAIL (L=126, D=2048, mod=4): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 391/400 ---
# 	❌ FAIL (L=66, D=2048, mod=10): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 392/400 ---
# 	❌ FAIL (L=71, D=2048, mod=12): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 393/400 ---
# 	❌ FAIL (L=51, D=2048, mod=22): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 394/400 ---
# 	✅ PASS (L=271, D=2048, mod=11): λ₂=0.3127   λ₁₁=20.8543

# --- Running Test 395/400 ---
# 	✅ PASS (L=101, D=2048, mod=17): λ₂=0.3188   λ₁₁=44.5813

# --- Running Test 396/400 ---
# 	✅ PASS (L=81, D=2048, mod=11): λ₂=0.3127   λ₁₁=30.8399

# --- Running Test 397/400 ---
# 	✅ PASS (L=166, D=2048, mod=7): λ₂=0.3856   λ₁₁=33.0428

# --- Running Test 398/400 ---
# 	✅ PASS (L=81, D=2048, mod=13): λ₂=0.2597   λ₁₁=43.0695

# --- Running Test 399/400 ---
# 	❌ FAIL (L=121, D=2048, mod=4): L2-Norm Check Failed (λ₂=nan) — skipping.

# --- Running Test 400/400 ---
# 	❌ FAIL (L=126, D=2048, mod=4): L2-Norm Check Failed (λ₂=nan) — skipping.

# ================================================================================
# --- Final Correlation Results (PY007/TinyLlama-1.1B-Chat-v0.3 - CPU) ---
# Total Valid Samples: 200
# Total Tests Run: 400
# ----------------------------------------
# Pearson Correlation (r): -0.2863
# P-value: 3.96e-05
# ================================================================================
# ⚠️ INCONCLUSIVE: Correlation is near zero. Geometric stability is weak/unaligned.
# (base) brendanlynch@Mac zzzzzzzhourglass % 
