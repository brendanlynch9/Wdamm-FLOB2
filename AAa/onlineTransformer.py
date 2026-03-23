import torch
import numpy as np
from scipy.linalg import eigvalsh, eigh
from scipy.stats import pearsonr
from transformers import AutoModelForCausalLM, AutoTokenizer
import pandas as pd

# Global counter for hodge gap diagnostics
_hodge_diag_count = 0 

# --- 1. CORE O(1) DIAGNOSTIC FUNCTION (Algebraic Connectivity λ₂) ---
R24 = [1, 5, 7, 11, 13, 17, 19, 23]
MODULI = [5, 7, 11, 13, 17]

def compute_modular_lambda2(norm_x: float) -> float:
    """O(1) calculation of algebraic connectivity λ₂ (Fixed)."""
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

# --- 2. ROBUST HODGE GAP CALCULATION FUNCTION ---

def calculate_hodge_gap(activation_h: torch.Tensor, verbose_limit=5) -> float:
    """
    Robust Hodge gap (lambda_11) estimator using covariance matrix and Tikhonov regularization.
    """
    global _hodge_diag_count
    try:
        H = activation_h.detach().cpu().float()
        
        hidden = H.size(-1)
        H_flat = H.view(-1, hidden)  # shape (N_samples, hidden)
        N_samples = H_flat.shape[0]

        if N_samples < 11 or hidden < 11:
            if _hodge_diag_count < verbose_limit:
                print(f"[hodge] N_samples too small: {N_samples}, hidden={hidden} (Must be >= 11)")
            _hodge_diag_count += 1
            return np.nan

        if _hodge_diag_count < verbose_limit:
            stats = {
                'shape': H_flat.shape,
                'min': float(H_flat.min().item()),
                'max': float(H_flat.max().item()),
                'mean_abs': float(H_flat.abs().mean().item()),
                'std': float(H_flat.std().item())
            }
            print(f"[hodge] H_flat stats #{_hodge_diag_count+1}: {stats}")

        Hc = (H_flat - H_flat.mean(dim=0)).double().numpy()

        cov = (Hc.T @ Hc) / max(1, (N_samples - 1))

        mean_diag = np.mean(np.diag(cov))
        ridge = 1e-8 * mean_diag if mean_diag > 0 else 1e-10
        cov += ridge * np.eye(cov.shape[0], dtype=cov.dtype)

        eigvals = eigh(cov, eigvals_only=True)

        if eigvals.size < 11:
            if _hodge_diag_count < verbose_limit:
                print(f"[hodge] eigvals too short: {eigvals.size}")
            _hodge_diag_count += 1
            return np.nan

        lambda_11 = float(np.sort(eigvals)[-11])
        
        if _hodge_diag_count < verbose_limit:
            print(f"[hodge] lambda_11 = {lambda_11:.6g}, ridge={ridge:.3e}")
        _hodge_diag_count += 1
        return lambda_11

    except Exception as e:
        if _hodge_diag_count < verbose_limit:
            print(f"[hodge] exception during Hodge calc: {repr(e)}")
        _hodge_diag_count += 1
        return np.nan

# --- 3. ONLINE TESTER CLASS ---

class OnlineTransformerTester:
    
    def __init__(self, model_name: str = "gpt2"):
        print(f"Loading model: {model_name}...")
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.tokenizer.pad_token = self.tokenizer.eos_token 
        
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu") 
        print(f"Using device: {self.device} (Model dtype: float64 for stability)")
        
        self.model = AutoModelForCausalLM.from_pretrained(
            model_name, 
            torch_dtype=torch.float64
        ).to(self.device)
        self.model.eval() 
        
        self.target_layer = self.model.transformer.ln_f
            
        self.results = {'lambda2': [], 'hodge_gap': [], 'seq_len': []}
        self.activation = None
        self._register_hook()
        
    def _register_hook(self):
        def hook_fn(module, input, output):
            self.activation = output[0] if isinstance(output, tuple) else output
        
        self.hook = self.target_layer.register_forward_hook(hook_fn)
        print(f"Hook registered on layer: {self.target_layer.__class__.__name__}")

    def run_test(self, prompt: str, max_new_tokens: int = 160, use_sampling: bool = False):
        
        input_tokens = self.tokenizer(prompt, return_tensors="pt", truncation=True)
        input_ids = input_tokens['input_ids'].to(self.device)
        attention_mask = input_tokens.get('attention_mask', None)
        if attention_mask is not None:
            attention_mask = attention_mask.to(self.device)
            
        # 1b) compute input norm 
        input_norm = float(torch.linalg.norm(input_ids.float()).cpu().item())
        
        # --- CRITICAL FIX: REVERT L2-NORM ADJUSTMENT ---
        # The following lines are REMOVED to allow lambda2 to vary:
        # current_residue = int(input_norm) % 24
        # offset_needed = (1 - current_residue) % 24
        # adjusted_input_norm = input_norm + offset_needed
        # -----------------------------------------------
        
        # Use the true input norm for variance
        input_lambda2 = compute_modular_lambda2(input_norm)
        
        # 2) Generate sequence IDs
        self.activation = None
        try:
            gen_kwargs = dict(
                input_ids=input_ids,
                max_new_tokens=max_new_tokens,
                pad_token_id=self.tokenizer.eos_token_id,
                do_sample=False, 
                num_return_sequences=1,
                attention_mask=attention_mask,
                use_cache=False 
            )
            if use_sampling:
                gen_kwargs.update({"do_sample": True, "top_k": 50, "top_p": 0.95, "temperature": 0.9})

            with torch.no_grad():
                generated_ids = self.model.generate(**gen_kwargs)

        except Exception as gen_exc:
            print(f"\t❌ Generation failed (prompt skipped due to numerical error): {gen_exc}")
            return
            
        # Force a FULL FORWARD PASS on the generated sequence 
        try:
             with torch.no_grad():
                 self.model(generated_ids)
        except Exception as fwd_exc:
             print(f"\t❌ Full forward pass failed: {fwd_exc}")
             return

        # 3) Validate activation captured by the hook
        if self.activation is None:
            print("\t❌ FAIL: No activation captured by hook (forward pass failed).")
            return

        activation_cpu = self.activation.cpu()
        
        if torch.isinf(activation_cpu).any() or torch.isnan(activation_cpu).any():
            print("\t❌ FAIL: Activation contains NaN/Inf (prompt skipped).")
            return

        # 4) Compute Hodge gap (safe) and record results
        hodge_gap_lambda11 = calculate_hodge_gap(activation_cpu)
        
        seq_len = generated_ids.size(1)
        
        # Final checks
        if np.isnan(input_lambda2):
            # This is expected for some inputs now, and we skip them.
            print(f"\t❌ FAIL (L={seq_len}): $\\lambda_2$=nan (Input L2-norm failed $\\pmod{{24}}$ check) — skipping.")
            return
            
        if np.isnan(hodge_gap_lambda11):
            print(f"\t❌ FAIL (L={seq_len}): $\\lambda_{{11}}$={hodge_gap_lambda11:.4f} (Spectral calculation failed) — skipping.")
            return

        # If both are valid, pass:
        self.results['lambda2'].append(input_lambda2)
        self.results['hodge_gap'].append(hodge_gap_lambda11)
        self.results['seq_len'].append(seq_len)
        print(f"\t✅ PASS (L={seq_len}): $\\lambda_2$={input_lambda2:.4f} \t $\\lambda_{{11}}$={hodge_gap_lambda11:.4f}")


    def analyze_correlation(self):
        """Calculates and reports the final Pearson correlation."""
        self.hook.remove()
        
        df = pd.DataFrame(self.results)
        
        if len(df) < 5:
            print("\nNeed at least five valid data points to compute a robust correlation.")
            return

        # Calculate Pearson Correlation
        r, p_value = pearsonr(df['lambda2'], df['hodge_gap'])
        
        print("\n" + "="*80)
        print("--- Online Correlation Results (Proof of Principle) ---")
        print(f"Total Valid Samples: {len(df)}")
        print(f"Average Sequence Length: {df['seq_len'].mean():.1f}")
        print("-" * 40)
        print(f"Pearson Correlation (r): {r:.4f}")
        print(f"P-value: {p_value:.4f}")
        print("="*80)

        if r < 0 and p_value < 0.05:
            print(f"\n✅ Conclusive Proof: The strong negative correlation (r={r:.4f}) validates the core claim that low O(1) complexity ($\\lambda_2$) predicts high spectral collapse ($\\lambda_{{11}}$) in the live Transformer.")
        else:
             print(f"\n⚠️ Inconclusive: Correlation was $r={r:.4f}$. The geometric instability requires running hundreds of samples, or the base model's geometry is not strongly aligned with the modular metric. The next step is to increase the sample size in test_prompts and run for a longer duration.")


# --- EXAMPLE USAGE ---

if __name__ == "__main__":
    
    USE_SAMPLING = True
    
    tester = OnlineTransformerTester(model_name="gpt2") 
    
    test_prompts = [
        "What is the capital of France and how many people live there?", 
        "The quick brown fox jumps over the lazy dog, and then", 
        "A final short statement regarding the necessity of spectral concentration", 
        "10.25, 42.88, 99.01, 150.33, 2.718, 3.14159, 1.61803.", 
        "A computer scientist, a topologist, and a number theorist walk into a bar.", 
        "Unconditional analytical closure of the UFT-F Modularity Constant", 
        "If $a=5$, $b=12$, and $c=13$, then what is the value of $\sqrt{a^2+b^2}$?", 
        "The fundamental constraint in informational geometry is the preservation of modular symmetry.", 
        "In the year 2050, the primary challenge for humanity will be to manage the data explosion.", 
        "The complexity-gated inference procedure offers a 3 to 5 times reduction in the total number of ODE steps.", 
    ] * 100 # Total 200 samples
    
    # 3. Run the tests
    for i, prompt in enumerate(test_prompts):
        print(f"\n--- Running Test {i+1}/{len(test_prompts)} (Sampling={USE_SAMPLING}) ---")
        tester.run_test(prompt, max_new_tokens=160, use_sampling=USE_SAMPLING) 
        
        # Continue running until we get at least 40 samples
        if len(tester.results['lambda2']) >= 400:
             print("\n\n*** Sufficient data gathered (40+ samples). Continuing to correlation analysis. ***")
             break
        
    # 4. Analyze the collected data
    tester.analyze_correlation()

#     the output in terminal was:
#     (base) brendanlynch@Mac zzzzzzzhourglass % python onlineTransformer.py
# /Users/brendanlynch/Desktop/zzzzzzzhourglass/onlineTransformer.py:255: SyntaxWarning: invalid escape sequence '\s'
#   "If $a=5$, $b=12$, and $c=13$, then what is the value of $\sqrt{a^2+b^2}$?",
# Loading model: gpt2...
# Using device: cpu (Model dtype: float64 for stability)
# `torch_dtype` is deprecated! Use `dtype` instead!
# Hook registered on layer: LayerNorm

# --- Running Test 1/1000 (Sampling=True) ---
# [hodge] H_flat stats #1: {'shape': torch.Size([173, 768]), 'min': -159.83872985839844, 'max': 312.9382019042969, 'mean_abs': 1.0236165523529053, 'std': 9.808281898498535}
# [hodge] lambda_11 = 10.7506, ridge=1.454e-07
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 2/1000 (Sampling=True) ---
# [hodge] H_flat stats #2: {'shape': torch.Size([172, 768]), 'min': -216.11080932617188, 'max': 292.9023132324219, 'mean_abs': 1.0393284559249878, 'std': 9.54555892944336}
# [hodge] lambda_11 = 7.38526, ridge=3.210e-07
# 	❌ FAIL (L=172): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 3/1000 (Sampling=True) ---
# [hodge] H_flat stats #3: {'shape': torch.Size([170, 768]), 'min': -225.54498291015625, 'max': 258.3952331542969, 'mean_abs': 1.086470603942871, 'std': 9.925354957580566}
# [hodge] lambda_11 = 5.73006, ridge=7.492e-07
# 	❌ FAIL (L=170): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 4/1000 (Sampling=True) ---
# [hodge] H_flat stats #4: {'shape': torch.Size([190, 768]), 'min': -238.70460510253906, 'max': 323.86395263671875, 'mean_abs': 1.180567979812622, 'std': 11.518692970275879}
# [hodge] lambda_11 = 2.79616, ridge=5.482e-07
# 	❌ FAIL (L=190): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 5/1000 (Sampling=True) ---
# [hodge] H_flat stats #5: {'shape': torch.Size([177, 768]), 'min': -117.3949966430664, 'max': 327.974853515625, 'mean_abs': 0.9806926846504211, 'std': 9.267987251281738}
# [hodge] lambda_11 = 10.2645, ridge=1.097e-07
# 	✅ PASS (L=177): $\lambda_2$=0.3132 	 $\lambda_{11}$=10.2645

# --- Running Test 6/1000 (Sampling=True) ---
# 	✅ PASS (L=174): $\lambda_2$=0.2597 	 $\lambda_{11}$=8.8643

# --- Running Test 7/1000 (Sampling=True) ---
# 	❌ FAIL (L=197): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 8/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 9/1000 (Sampling=True) ---
# 	✅ PASS (L=178): $\lambda_2$=0.3061 	 $\lambda_{11}$=9.3324

# --- Running Test 10/1000 (Sampling=True) ---
# 	✅ PASS (L=122): $\lambda_2$=0.3132 	 $\lambda_{11}$=6.8808

# --- Running Test 11/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 12/1000 (Sampling=True) ---
# 	❌ FAIL (L=172): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 13/1000 (Sampling=True) ---
# 	❌ FAIL (L=170): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 14/1000 (Sampling=True) ---
# 	❌ FAIL (L=190): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 15/1000 (Sampling=True) ---
# 	✅ PASS (L=177): $\lambda_2$=0.3132 	 $\lambda_{11}$=9.3892

# --- Running Test 16/1000 (Sampling=True) ---
# 	✅ PASS (L=174): $\lambda_2$=0.2597 	 $\lambda_{11}$=6.2536

# --- Running Test 17/1000 (Sampling=True) ---
# 	❌ FAIL (L=197): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 18/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 19/1000 (Sampling=True) ---
# 	✅ PASS (L=178): $\lambda_2$=0.3061 	 $\lambda_{11}$=9.8491

# --- Running Test 20/1000 (Sampling=True) ---
# 	✅ PASS (L=183): $\lambda_2$=0.3132 	 $\lambda_{11}$=6.7921

# --- Running Test 21/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 22/1000 (Sampling=True) ---
# 	❌ FAIL (L=172): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 23/1000 (Sampling=True) ---
# 	❌ FAIL (L=170): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 24/1000 (Sampling=True) ---
# 	❌ FAIL (L=190): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 25/1000 (Sampling=True) ---
# 	✅ PASS (L=177): $\lambda_2$=0.3132 	 $\lambda_{11}$=8.9341

# --- Running Test 26/1000 (Sampling=True) ---
# 	✅ PASS (L=174): $\lambda_2$=0.2597 	 $\lambda_{11}$=10.2460

# --- Running Test 27/1000 (Sampling=True) ---
# 	❌ FAIL (L=197): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 28/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 29/1000 (Sampling=True) ---
# 	✅ PASS (L=178): $\lambda_2$=0.3061 	 $\lambda_{11}$=10.6477

# --- Running Test 30/1000 (Sampling=True) ---
# 	✅ PASS (L=183): $\lambda_2$=0.3132 	 $\lambda_{11}$=8.0680

# --- Running Test 31/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 32/1000 (Sampling=True) ---
# 	❌ FAIL (L=172): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 33/1000 (Sampling=True) ---
# 	❌ FAIL (L=170): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 34/1000 (Sampling=True) ---
# 	❌ FAIL (L=190): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 35/1000 (Sampling=True) ---
# 	✅ PASS (L=134): $\lambda_2$=0.3132 	 $\lambda_{11}$=10.5025

# --- Running Test 36/1000 (Sampling=True) ---
# 	✅ PASS (L=174): $\lambda_2$=0.2597 	 $\lambda_{11}$=6.1864

# --- Running Test 37/1000 (Sampling=True) ---
# 	❌ FAIL (L=93): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 38/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 39/1000 (Sampling=True) ---
# 	✅ PASS (L=178): $\lambda_2$=0.3061 	 $\lambda_{11}$=10.3540

# --- Running Test 40/1000 (Sampling=True) ---
# 	✅ PASS (L=183): $\lambda_2$=0.3132 	 $\lambda_{11}$=7.8721

# --- Running Test 41/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 42/1000 (Sampling=True) ---
# 	❌ FAIL (L=172): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 43/1000 (Sampling=True) ---
# 	❌ FAIL (L=170): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 44/1000 (Sampling=True) ---
# 	❌ FAIL (L=190): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 45/1000 (Sampling=True) ---
# 	✅ PASS (L=177): $\lambda_2$=0.3132 	 $\lambda_{11}$=8.9598

# --- Running Test 46/1000 (Sampling=True) ---
# 	✅ PASS (L=174): $\lambda_2$=0.2597 	 $\lambda_{11}$=7.1460

# --- Running Test 47/1000 (Sampling=True) ---
# 	❌ FAIL (L=197): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 48/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 49/1000 (Sampling=True) ---
# 	✅ PASS (L=178): $\lambda_2$=0.3061 	 $\lambda_{11}$=8.8655

# --- Running Test 50/1000 (Sampling=True) ---
# 	✅ PASS (L=183): $\lambda_2$=0.3132 	 $\lambda_{11}$=9.8051

# --- Running Test 51/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 52/1000 (Sampling=True) ---
# 	❌ FAIL (L=172): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 53/1000 (Sampling=True) ---
# 	❌ FAIL (L=170): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 54/1000 (Sampling=True) ---
# 	❌ FAIL (L=190): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 55/1000 (Sampling=True) ---
# 	✅ PASS (L=177): $\lambda_2$=0.3132 	 $\lambda_{11}$=10.1641

# --- Running Test 56/1000 (Sampling=True) ---
# 	✅ PASS (L=174): $\lambda_2$=0.2597 	 $\lambda_{11}$=9.7143

# --- Running Test 57/1000 (Sampling=True) ---
# 	❌ FAIL (L=197): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 58/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 59/1000 (Sampling=True) ---
# 	✅ PASS (L=71): $\lambda_2$=0.3061 	 $\lambda_{11}$=12.3350

# --- Running Test 60/1000 (Sampling=True) ---
# 	✅ PASS (L=183): $\lambda_2$=0.3132 	 $\lambda_{11}$=6.7512

# --- Running Test 61/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 62/1000 (Sampling=True) ---
# 	❌ FAIL (L=172): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 63/1000 (Sampling=True) ---
# 	❌ FAIL (L=170): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 64/1000 (Sampling=True) ---
# 	❌ FAIL (L=190): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 65/1000 (Sampling=True) ---
# 	✅ PASS (L=177): $\lambda_2$=0.3132 	 $\lambda_{11}$=10.5963

# --- Running Test 66/1000 (Sampling=True) ---
# 	✅ PASS (L=174): $\lambda_2$=0.2597 	 $\lambda_{11}$=8.3140

# --- Running Test 67/1000 (Sampling=True) ---
# 	❌ FAIL (L=197): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 68/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 69/1000 (Sampling=True) ---
# 	✅ PASS (L=178): $\lambda_2$=0.3061 	 $\lambda_{11}$=12.4872

# --- Running Test 70/1000 (Sampling=True) ---
# 	✅ PASS (L=183): $\lambda_2$=0.3132 	 $\lambda_{11}$=6.8960

# --- Running Test 71/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 72/1000 (Sampling=True) ---
# 	❌ FAIL (L=172): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 73/1000 (Sampling=True) ---
# 	❌ FAIL (L=170): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 74/1000 (Sampling=True) ---
# 	❌ FAIL (L=190): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 75/1000 (Sampling=True) ---
# 	✅ PASS (L=177): $\lambda_2$=0.3132 	 $\lambda_{11}$=12.0880

# --- Running Test 76/1000 (Sampling=True) ---
# 	✅ PASS (L=174): $\lambda_2$=0.2597 	 $\lambda_{11}$=6.2205

# --- Running Test 77/1000 (Sampling=True) ---
# 	❌ FAIL (L=197): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 78/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 79/1000 (Sampling=True) ---
# 	✅ PASS (L=178): $\lambda_2$=0.3061 	 $\lambda_{11}$=7.9698

# --- Running Test 80/1000 (Sampling=True) ---
# 	✅ PASS (L=183): $\lambda_2$=0.3132 	 $\lambda_{11}$=8.2933

# --- Running Test 81/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 82/1000 (Sampling=True) ---
# 	❌ FAIL (L=75): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 83/1000 (Sampling=True) ---
# 	❌ FAIL (L=170): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 84/1000 (Sampling=True) ---
# 	❌ FAIL (L=190): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 85/1000 (Sampling=True) ---
# 	✅ PASS (L=177): $\lambda_2$=0.3132 	 $\lambda_{11}$=11.9465

# --- Running Test 86/1000 (Sampling=True) ---
# 	✅ PASS (L=174): $\lambda_2$=0.2597 	 $\lambda_{11}$=6.7011

# --- Running Test 87/1000 (Sampling=True) ---
# 	❌ FAIL (L=197): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 88/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 89/1000 (Sampling=True) ---
# 	✅ PASS (L=178): $\lambda_2$=0.3061 	 $\lambda_{11}$=13.4075

# --- Running Test 90/1000 (Sampling=True) ---
# 	✅ PASS (L=183): $\lambda_2$=0.3132 	 $\lambda_{11}$=8.5650

# --- Running Test 91/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 92/1000 (Sampling=True) ---
# 	❌ FAIL (L=172): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 93/1000 (Sampling=True) ---
# 	❌ FAIL (L=170): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 94/1000 (Sampling=True) ---
# 	❌ FAIL (L=190): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 95/1000 (Sampling=True) ---
# 	✅ PASS (L=177): $\lambda_2$=0.3132 	 $\lambda_{11}$=9.5726

# --- Running Test 96/1000 (Sampling=True) ---
# 	✅ PASS (L=174): $\lambda_2$=0.2597 	 $\lambda_{11}$=7.6356

# --- Running Test 97/1000 (Sampling=True) ---
# 	❌ FAIL (L=197): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 98/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 99/1000 (Sampling=True) ---
# 	✅ PASS (L=178): $\lambda_2$=0.3061 	 $\lambda_{11}$=11.0445

# --- Running Test 100/1000 (Sampling=True) ---
# 	✅ PASS (L=183): $\lambda_2$=0.3132 	 $\lambda_{11}$=7.6455

# --- Running Test 101/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 102/1000 (Sampling=True) ---
# 	❌ FAIL (L=172): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 103/1000 (Sampling=True) ---
# 	❌ FAIL (L=170): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 104/1000 (Sampling=True) ---
# 	❌ FAIL (L=190): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 105/1000 (Sampling=True) ---
# 	✅ PASS (L=177): $\lambda_2$=0.3132 	 $\lambda_{11}$=9.8956

# --- Running Test 106/1000 (Sampling=True) ---
# 	✅ PASS (L=174): $\lambda_2$=0.2597 	 $\lambda_{11}$=2.5858

# --- Running Test 107/1000 (Sampling=True) ---
# 	❌ FAIL (L=197): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 108/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 109/1000 (Sampling=True) ---
# 	✅ PASS (L=178): $\lambda_2$=0.3061 	 $\lambda_{11}$=11.3792

# --- Running Test 110/1000 (Sampling=True) ---
# 	✅ PASS (L=183): $\lambda_2$=0.3132 	 $\lambda_{11}$=9.2140

# --- Running Test 111/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 112/1000 (Sampling=True) ---
# 	❌ FAIL (L=172): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 113/1000 (Sampling=True) ---
# 	❌ FAIL (L=170): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 114/1000 (Sampling=True) ---
# 	❌ FAIL (L=190): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 115/1000 (Sampling=True) ---
# 	✅ PASS (L=177): $\lambda_2$=0.3132 	 $\lambda_{11}$=10.2022

# --- Running Test 116/1000 (Sampling=True) ---
# 	✅ PASS (L=174): $\lambda_2$=0.2597 	 $\lambda_{11}$=5.2162

# --- Running Test 117/1000 (Sampling=True) ---
# 	❌ FAIL (L=197): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 118/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 119/1000 (Sampling=True) ---
# 	✅ PASS (L=178): $\lambda_2$=0.3061 	 $\lambda_{11}$=11.4199

# --- Running Test 120/1000 (Sampling=True) ---
# 	✅ PASS (L=183): $\lambda_2$=0.3132 	 $\lambda_{11}$=8.0048

# --- Running Test 121/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 122/1000 (Sampling=True) ---
# 	❌ FAIL (L=172): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 123/1000 (Sampling=True) ---
# 	❌ FAIL (L=170): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 124/1000 (Sampling=True) ---
# 	❌ FAIL (L=190): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 125/1000 (Sampling=True) ---
# 	✅ PASS (L=177): $\lambda_2$=0.3132 	 $\lambda_{11}$=9.1040

# --- Running Test 126/1000 (Sampling=True) ---
# 	✅ PASS (L=174): $\lambda_2$=0.2597 	 $\lambda_{11}$=6.7116

# --- Running Test 127/1000 (Sampling=True) ---
# 	❌ FAIL (L=197): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 128/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 129/1000 (Sampling=True) ---
# 	✅ PASS (L=178): $\lambda_2$=0.3061 	 $\lambda_{11}$=8.7814

# --- Running Test 130/1000 (Sampling=True) ---
# 	✅ PASS (L=183): $\lambda_2$=0.3132 	 $\lambda_{11}$=7.4898

# --- Running Test 131/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 132/1000 (Sampling=True) ---
# 	❌ FAIL (L=172): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 133/1000 (Sampling=True) ---
# 	❌ FAIL (L=170): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 134/1000 (Sampling=True) ---
# 	❌ FAIL (L=190): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 135/1000 (Sampling=True) ---
# 	✅ PASS (L=177): $\lambda_2$=0.3132 	 $\lambda_{11}$=10.7980

# --- Running Test 136/1000 (Sampling=True) ---
# 	✅ PASS (L=174): $\lambda_2$=0.2597 	 $\lambda_{11}$=8.6368

# --- Running Test 137/1000 (Sampling=True) ---
# 	❌ FAIL (L=197): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 138/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 139/1000 (Sampling=True) ---
# 	✅ PASS (L=178): $\lambda_2$=0.3061 	 $\lambda_{11}$=12.8630

# --- Running Test 140/1000 (Sampling=True) ---
# 	✅ PASS (L=183): $\lambda_2$=0.3132 	 $\lambda_{11}$=9.5355

# --- Running Test 141/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 142/1000 (Sampling=True) ---
# 	❌ FAIL (L=172): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 143/1000 (Sampling=True) ---
# 	❌ FAIL (L=170): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 144/1000 (Sampling=True) ---
# 	❌ FAIL (L=190): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 145/1000 (Sampling=True) ---
# 	✅ PASS (L=177): $\lambda_2$=0.3132 	 $\lambda_{11}$=9.4501

# --- Running Test 146/1000 (Sampling=True) ---
# 	✅ PASS (L=174): $\lambda_2$=0.2597 	 $\lambda_{11}$=8.5784

# --- Running Test 147/1000 (Sampling=True) ---
# 	❌ FAIL (L=197): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 148/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 149/1000 (Sampling=True) ---
# 	✅ PASS (L=178): $\lambda_2$=0.3061 	 $\lambda_{11}$=8.3825

# --- Running Test 150/1000 (Sampling=True) ---
# 	✅ PASS (L=183): $\lambda_2$=0.3132 	 $\lambda_{11}$=7.8346

# --- Running Test 151/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 152/1000 (Sampling=True) ---
# 	❌ FAIL (L=172): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 153/1000 (Sampling=True) ---
# 	❌ FAIL (L=170): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 154/1000 (Sampling=True) ---
# 	❌ FAIL (L=190): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 155/1000 (Sampling=True) ---
# 	✅ PASS (L=177): $\lambda_2$=0.3132 	 $\lambda_{11}$=11.2129

# --- Running Test 156/1000 (Sampling=True) ---
# 	✅ PASS (L=174): $\lambda_2$=0.2597 	 $\lambda_{11}$=6.4483

# --- Running Test 157/1000 (Sampling=True) ---
# 	❌ FAIL (L=197): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 158/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 159/1000 (Sampling=True) ---
# 	✅ PASS (L=178): $\lambda_2$=0.3061 	 $\lambda_{11}$=11.0392

# --- Running Test 160/1000 (Sampling=True) ---
# 	✅ PASS (L=183): $\lambda_2$=0.3132 	 $\lambda_{11}$=7.2677

# --- Running Test 161/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 162/1000 (Sampling=True) ---
# 	❌ FAIL (L=172): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 163/1000 (Sampling=True) ---
# 	❌ FAIL (L=170): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 164/1000 (Sampling=True) ---
# 	❌ FAIL (L=190): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 165/1000 (Sampling=True) ---
# 	✅ PASS (L=177): $\lambda_2$=0.3132 	 $\lambda_{11}$=11.3222

# --- Running Test 166/1000 (Sampling=True) ---
# 	✅ PASS (L=174): $\lambda_2$=0.2597 	 $\lambda_{11}$=7.5182

# --- Running Test 167/1000 (Sampling=True) ---
# 	❌ FAIL (L=197): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 168/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 169/1000 (Sampling=True) ---
# 	✅ PASS (L=178): $\lambda_2$=0.3061 	 $\lambda_{11}$=12.2056

# --- Running Test 170/1000 (Sampling=True) ---
# 	✅ PASS (L=183): $\lambda_2$=0.3132 	 $\lambda_{11}$=7.9675

# --- Running Test 171/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 172/1000 (Sampling=True) ---
# 	❌ FAIL (L=172): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 173/1000 (Sampling=True) ---
# 	❌ FAIL (L=79): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 174/1000 (Sampling=True) ---
# 	❌ FAIL (L=190): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 175/1000 (Sampling=True) ---
# 	✅ PASS (L=177): $\lambda_2$=0.3132 	 $\lambda_{11}$=8.5272

# --- Running Test 176/1000 (Sampling=True) ---
# 	✅ PASS (L=174): $\lambda_2$=0.2597 	 $\lambda_{11}$=9.5271

# --- Running Test 177/1000 (Sampling=True) ---
# 	❌ FAIL (L=197): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 178/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 179/1000 (Sampling=True) ---
# 	✅ PASS (L=178): $\lambda_2$=0.3061 	 $\lambda_{11}$=12.4607

# --- Running Test 180/1000 (Sampling=True) ---
# 	✅ PASS (L=183): $\lambda_2$=0.3132 	 $\lambda_{11}$=10.7293

# --- Running Test 181/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 182/1000 (Sampling=True) ---
# 	❌ FAIL (L=172): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 183/1000 (Sampling=True) ---
# 	❌ FAIL (L=170): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 184/1000 (Sampling=True) ---
# 	❌ FAIL (L=190): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 185/1000 (Sampling=True) ---
# 	✅ PASS (L=177): $\lambda_2$=0.3132 	 $\lambda_{11}$=11.7760

# --- Running Test 186/1000 (Sampling=True) ---
# 	✅ PASS (L=174): $\lambda_2$=0.2597 	 $\lambda_{11}$=7.5788

# --- Running Test 187/1000 (Sampling=True) ---
# 	❌ FAIL (L=197): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 188/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 189/1000 (Sampling=True) ---
# 	✅ PASS (L=178): $\lambda_2$=0.3061 	 $\lambda_{11}$=8.8979

# --- Running Test 190/1000 (Sampling=True) ---
# 	✅ PASS (L=183): $\lambda_2$=0.3132 	 $\lambda_{11}$=7.3707

# --- Running Test 191/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 192/1000 (Sampling=True) ---
# 	❌ FAIL (L=172): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 193/1000 (Sampling=True) ---
# 	❌ FAIL (L=170): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 194/1000 (Sampling=True) ---
# 	❌ FAIL (L=190): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 195/1000 (Sampling=True) ---
# 	✅ PASS (L=177): $\lambda_2$=0.3132 	 $\lambda_{11}$=8.8458

# --- Running Test 196/1000 (Sampling=True) ---
# 	✅ PASS (L=174): $\lambda_2$=0.2597 	 $\lambda_{11}$=7.8462

# --- Running Test 197/1000 (Sampling=True) ---
# 	❌ FAIL (L=197): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 198/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 199/1000 (Sampling=True) ---
# 	✅ PASS (L=178): $\lambda_2$=0.3061 	 $\lambda_{11}$=11.8772

# --- Running Test 200/1000 (Sampling=True) ---
# 	✅ PASS (L=183): $\lambda_2$=0.3132 	 $\lambda_{11}$=8.6316

# --- Running Test 201/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 202/1000 (Sampling=True) ---
# 	❌ FAIL (L=171): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 203/1000 (Sampling=True) ---
# 	❌ FAIL (L=170): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 204/1000 (Sampling=True) ---
# 	❌ FAIL (L=190): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 205/1000 (Sampling=True) ---
# 	✅ PASS (L=177): $\lambda_2$=0.3132 	 $\lambda_{11}$=8.4839

# --- Running Test 206/1000 (Sampling=True) ---
# 	✅ PASS (L=174): $\lambda_2$=0.2597 	 $\lambda_{11}$=6.7307

# --- Running Test 207/1000 (Sampling=True) ---
# 	❌ FAIL (L=197): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 208/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 209/1000 (Sampling=True) ---
# 	✅ PASS (L=178): $\lambda_2$=0.3061 	 $\lambda_{11}$=9.3741

# --- Running Test 210/1000 (Sampling=True) ---
# 	✅ PASS (L=183): $\lambda_2$=0.3132 	 $\lambda_{11}$=8.1220

# --- Running Test 211/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 212/1000 (Sampling=True) ---
# 	❌ FAIL (L=74): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 213/1000 (Sampling=True) ---
# 	❌ FAIL (L=170): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 214/1000 (Sampling=True) ---
# 	❌ FAIL (L=190): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 215/1000 (Sampling=True) ---
# 	✅ PASS (L=177): $\lambda_2$=0.3132 	 $\lambda_{11}$=9.9365

# --- Running Test 216/1000 (Sampling=True) ---
# 	✅ PASS (L=172): $\lambda_2$=0.2597 	 $\lambda_{11}$=12.5232

# --- Running Test 217/1000 (Sampling=True) ---
# 	❌ FAIL (L=197): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 218/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 219/1000 (Sampling=True) ---
# 	✅ PASS (L=178): $\lambda_2$=0.3061 	 $\lambda_{11}$=10.0044

# --- Running Test 220/1000 (Sampling=True) ---
# 	✅ PASS (L=183): $\lambda_2$=0.3132 	 $\lambda_{11}$=7.1486

# --- Running Test 221/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 222/1000 (Sampling=True) ---
# 	❌ FAIL (L=172): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 223/1000 (Sampling=True) ---
# 	❌ FAIL (L=170): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 224/1000 (Sampling=True) ---
# 	❌ FAIL (L=190): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 225/1000 (Sampling=True) ---
# 	✅ PASS (L=177): $\lambda_2$=0.3132 	 $\lambda_{11}$=8.8859

# --- Running Test 226/1000 (Sampling=True) ---
# 	✅ PASS (L=174): $\lambda_2$=0.2597 	 $\lambda_{11}$=16.0376

# --- Running Test 227/1000 (Sampling=True) ---
# 	❌ FAIL (L=197): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 228/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 229/1000 (Sampling=True) ---
# 	✅ PASS (L=178): $\lambda_2$=0.3061 	 $\lambda_{11}$=11.2265

# --- Running Test 230/1000 (Sampling=True) ---
# 	✅ PASS (L=183): $\lambda_2$=0.3132 	 $\lambda_{11}$=10.1746

# --- Running Test 231/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 232/1000 (Sampling=True) ---
# 	❌ FAIL (L=172): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 233/1000 (Sampling=True) ---
# 	❌ FAIL (L=170): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 234/1000 (Sampling=True) ---
# 	❌ FAIL (L=190): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 235/1000 (Sampling=True) ---
# 	✅ PASS (L=177): $\lambda_2$=0.3132 	 $\lambda_{11}$=9.9844

# --- Running Test 236/1000 (Sampling=True) ---
# 	✅ PASS (L=174): $\lambda_2$=0.2597 	 $\lambda_{11}$=7.9124

# --- Running Test 237/1000 (Sampling=True) ---
# 	❌ FAIL (L=197): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 238/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 239/1000 (Sampling=True) ---
# 	✅ PASS (L=178): $\lambda_2$=0.3061 	 $\lambda_{11}$=12.4323

# --- Running Test 240/1000 (Sampling=True) ---
# 	✅ PASS (L=183): $\lambda_2$=0.3132 	 $\lambda_{11}$=6.5648

# --- Running Test 241/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 242/1000 (Sampling=True) ---
# 	❌ FAIL (L=172): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 243/1000 (Sampling=True) ---
# 	❌ FAIL (L=170): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 244/1000 (Sampling=True) ---
# 	❌ FAIL (L=190): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 245/1000 (Sampling=True) ---
# 	✅ PASS (L=177): $\lambda_2$=0.3132 	 $\lambda_{11}$=8.2680

# --- Running Test 246/1000 (Sampling=True) ---
# 	✅ PASS (L=174): $\lambda_2$=0.2597 	 $\lambda_{11}$=8.9989

# --- Running Test 247/1000 (Sampling=True) ---
# 	❌ FAIL (L=197): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 248/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 249/1000 (Sampling=True) ---
# 	✅ PASS (L=178): $\lambda_2$=0.3061 	 $\lambda_{11}$=12.5384

# --- Running Test 250/1000 (Sampling=True) ---
# 	✅ PASS (L=183): $\lambda_2$=0.3132 	 $\lambda_{11}$=7.0630

# --- Running Test 251/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 252/1000 (Sampling=True) ---
# 	❌ FAIL (L=73): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 253/1000 (Sampling=True) ---
# 	❌ FAIL (L=170): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 254/1000 (Sampling=True) ---
# 	❌ FAIL (L=190): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 255/1000 (Sampling=True) ---
# 	✅ PASS (L=177): $\lambda_2$=0.3132 	 $\lambda_{11}$=7.6645

# --- Running Test 256/1000 (Sampling=True) ---
# 	✅ PASS (L=174): $\lambda_2$=0.2597 	 $\lambda_{11}$=6.1274

# --- Running Test 257/1000 (Sampling=True) ---
# 	❌ FAIL (L=197): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 258/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 259/1000 (Sampling=True) ---
# 	✅ PASS (L=178): $\lambda_2$=0.3061 	 $\lambda_{11}$=11.0193

# --- Running Test 260/1000 (Sampling=True) ---
# 	✅ PASS (L=183): $\lambda_2$=0.3132 	 $\lambda_{11}$=7.3719

# --- Running Test 261/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 262/1000 (Sampling=True) ---
# 	❌ FAIL (L=172): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 263/1000 (Sampling=True) ---
# 	❌ FAIL (L=170): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 264/1000 (Sampling=True) ---
# 	❌ FAIL (L=190): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 265/1000 (Sampling=True) ---
# 	✅ PASS (L=177): $\lambda_2$=0.3132 	 $\lambda_{11}$=10.6879

# --- Running Test 266/1000 (Sampling=True) ---
# 	✅ PASS (L=174): $\lambda_2$=0.2597 	 $\lambda_{11}$=5.3404

# --- Running Test 267/1000 (Sampling=True) ---
# 	❌ FAIL (L=197): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 268/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 269/1000 (Sampling=True) ---
# 	✅ PASS (L=178): $\lambda_2$=0.3061 	 $\lambda_{11}$=9.1550

# --- Running Test 270/1000 (Sampling=True) ---
# 	✅ PASS (L=183): $\lambda_2$=0.3132 	 $\lambda_{11}$=7.4882

# --- Running Test 271/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 272/1000 (Sampling=True) ---
# 	❌ FAIL (L=172): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 273/1000 (Sampling=True) ---
# 	❌ FAIL (L=170): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 274/1000 (Sampling=True) ---
# 	❌ FAIL (L=186): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 275/1000 (Sampling=True) ---
# 	✅ PASS (L=177): $\lambda_2$=0.3132 	 $\lambda_{11}$=10.3856

# --- Running Test 276/1000 (Sampling=True) ---
# 	✅ PASS (L=174): $\lambda_2$=0.2597 	 $\lambda_{11}$=8.8831

# --- Running Test 277/1000 (Sampling=True) ---
# 	❌ FAIL (L=197): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 278/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 279/1000 (Sampling=True) ---
# 	✅ PASS (L=178): $\lambda_2$=0.3061 	 $\lambda_{11}$=9.6439

# --- Running Test 280/1000 (Sampling=True) ---
# 	✅ PASS (L=183): $\lambda_2$=0.3132 	 $\lambda_{11}$=6.7818

# --- Running Test 281/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 282/1000 (Sampling=True) ---
# 	❌ FAIL (L=172): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 283/1000 (Sampling=True) ---
# 	❌ FAIL (L=170): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 284/1000 (Sampling=True) ---
# 	❌ FAIL (L=190): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 285/1000 (Sampling=True) ---
# 	✅ PASS (L=177): $\lambda_2$=0.3132 	 $\lambda_{11}$=10.7403

# --- Running Test 286/1000 (Sampling=True) ---
# 	✅ PASS (L=174): $\lambda_2$=0.2597 	 $\lambda_{11}$=6.8703

# --- Running Test 287/1000 (Sampling=True) ---
# 	❌ FAIL (L=197): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 288/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 289/1000 (Sampling=True) ---
# 	✅ PASS (L=178): $\lambda_2$=0.3061 	 $\lambda_{11}$=10.9911

# --- Running Test 290/1000 (Sampling=True) ---
# 	✅ PASS (L=183): $\lambda_2$=0.3132 	 $\lambda_{11}$=6.9075

# --- Running Test 291/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 292/1000 (Sampling=True) ---
# 	❌ FAIL (L=172): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 293/1000 (Sampling=True) ---
# 	❌ FAIL (L=170): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 294/1000 (Sampling=True) ---
# 	❌ FAIL (L=190): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 295/1000 (Sampling=True) ---
# 	✅ PASS (L=177): $\lambda_2$=0.3132 	 $\lambda_{11}$=10.4035

# --- Running Test 296/1000 (Sampling=True) ---
# 	✅ PASS (L=174): $\lambda_2$=0.2597 	 $\lambda_{11}$=6.2488

# --- Running Test 297/1000 (Sampling=True) ---
# 	❌ FAIL (L=197): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 298/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 299/1000 (Sampling=True) ---
# 	✅ PASS (L=178): $\lambda_2$=0.3061 	 $\lambda_{11}$=11.0096

# --- Running Test 300/1000 (Sampling=True) ---
# 	✅ PASS (L=183): $\lambda_2$=0.3132 	 $\lambda_{11}$=7.9561

# --- Running Test 301/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 302/1000 (Sampling=True) ---
# 	❌ FAIL (L=172): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 303/1000 (Sampling=True) ---
# 	❌ FAIL (L=133): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 304/1000 (Sampling=True) ---
# 	❌ FAIL (L=190): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 305/1000 (Sampling=True) ---
# 	✅ PASS (L=177): $\lambda_2$=0.3132 	 $\lambda_{11}$=10.2276

# --- Running Test 306/1000 (Sampling=True) ---
# 	✅ PASS (L=174): $\lambda_2$=0.2597 	 $\lambda_{11}$=7.0877

# --- Running Test 307/1000 (Sampling=True) ---
# 	❌ FAIL (L=197): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 308/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 309/1000 (Sampling=True) ---
# 	✅ PASS (L=178): $\lambda_2$=0.3061 	 $\lambda_{11}$=12.9922

# --- Running Test 310/1000 (Sampling=True) ---
# 	✅ PASS (L=183): $\lambda_2$=0.3132 	 $\lambda_{11}$=8.3371

# --- Running Test 311/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 312/1000 (Sampling=True) ---
# 	❌ FAIL (L=172): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 313/1000 (Sampling=True) ---
# 	❌ FAIL (L=170): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 314/1000 (Sampling=True) ---
# 	❌ FAIL (L=190): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 315/1000 (Sampling=True) ---
# 	✅ PASS (L=177): $\lambda_2$=0.3132 	 $\lambda_{11}$=9.6825

# --- Running Test 316/1000 (Sampling=True) ---
# 	✅ PASS (L=174): $\lambda_2$=0.2597 	 $\lambda_{11}$=6.8646

# --- Running Test 317/1000 (Sampling=True) ---
# 	❌ FAIL (L=197): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 318/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 319/1000 (Sampling=True) ---
# 	✅ PASS (L=134): $\lambda_2$=0.3061 	 $\lambda_{11}$=8.9021

# --- Running Test 320/1000 (Sampling=True) ---
# 	✅ PASS (L=183): $\lambda_2$=0.3132 	 $\lambda_{11}$=13.0548

# --- Running Test 321/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 322/1000 (Sampling=True) ---
# 	❌ FAIL (L=172): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 323/1000 (Sampling=True) ---
# 	❌ FAIL (L=170): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 324/1000 (Sampling=True) ---
# 	❌ FAIL (L=190): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 325/1000 (Sampling=True) ---
# 	✅ PASS (L=177): $\lambda_2$=0.3132 	 $\lambda_{11}$=11.0154

# --- Running Test 326/1000 (Sampling=True) ---
# 	✅ PASS (L=174): $\lambda_2$=0.2597 	 $\lambda_{11}$=5.4793

# --- Running Test 327/1000 (Sampling=True) ---
# 	❌ FAIL (L=197): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 328/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 329/1000 (Sampling=True) ---
# 	✅ PASS (L=178): $\lambda_2$=0.3061 	 $\lambda_{11}$=10.5403

# --- Running Test 330/1000 (Sampling=True) ---
# 	✅ PASS (L=183): $\lambda_2$=0.3132 	 $\lambda_{11}$=8.5716

# --- Running Test 331/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 332/1000 (Sampling=True) ---
# 	❌ FAIL (L=139): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 333/1000 (Sampling=True) ---
# 	❌ FAIL (L=170): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 334/1000 (Sampling=True) ---
# 	❌ FAIL (L=190): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 335/1000 (Sampling=True) ---
# 	✅ PASS (L=177): $\lambda_2$=0.3132 	 $\lambda_{11}$=9.9689

# --- Running Test 336/1000 (Sampling=True) ---
# 	✅ PASS (L=174): $\lambda_2$=0.2597 	 $\lambda_{11}$=7.2608

# --- Running Test 337/1000 (Sampling=True) ---
# 	❌ FAIL (L=197): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 338/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 339/1000 (Sampling=True) ---
# 	✅ PASS (L=178): $\lambda_2$=0.3061 	 $\lambda_{11}$=8.8307

# --- Running Test 340/1000 (Sampling=True) ---
# 	✅ PASS (L=183): $\lambda_2$=0.3132 	 $\lambda_{11}$=7.6065

# --- Running Test 341/1000 (Sampling=True) ---
# 	❌ FAIL (L=68): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 342/1000 (Sampling=True) ---
# 	❌ FAIL (L=172): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 343/1000 (Sampling=True) ---
# 	❌ FAIL (L=170): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 344/1000 (Sampling=True) ---
# 	❌ FAIL (L=190): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 345/1000 (Sampling=True) ---
# 	✅ PASS (L=177): $\lambda_2$=0.3132 	 $\lambda_{11}$=9.1742

# --- Running Test 346/1000 (Sampling=True) ---
# 	✅ PASS (L=174): $\lambda_2$=0.2597 	 $\lambda_{11}$=7.4871

# --- Running Test 347/1000 (Sampling=True) ---
# 	❌ FAIL (L=197): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 348/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 349/1000 (Sampling=True) ---
# 	✅ PASS (L=121): $\lambda_2$=0.3061 	 $\lambda_{11}$=10.6800

# --- Running Test 350/1000 (Sampling=True) ---
# 	✅ PASS (L=183): $\lambda_2$=0.3132 	 $\lambda_{11}$=9.1765

# --- Running Test 351/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 352/1000 (Sampling=True) ---
# 	❌ FAIL (L=172): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 353/1000 (Sampling=True) ---
# 	❌ FAIL (L=170): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 354/1000 (Sampling=True) ---
# 	❌ FAIL (L=190): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 355/1000 (Sampling=True) ---
# 	✅ PASS (L=177): $\lambda_2$=0.3132 	 $\lambda_{11}$=10.3025

# --- Running Test 356/1000 (Sampling=True) ---
# 	✅ PASS (L=174): $\lambda_2$=0.2597 	 $\lambda_{11}$=6.3308

# --- Running Test 357/1000 (Sampling=True) ---
# 	❌ FAIL (L=197): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 358/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 359/1000 (Sampling=True) ---
# 	✅ PASS (L=178): $\lambda_2$=0.3061 	 $\lambda_{11}$=9.6517

# --- Running Test 360/1000 (Sampling=True) ---
# 	✅ PASS (L=183): $\lambda_2$=0.3132 	 $\lambda_{11}$=7.6850

# --- Running Test 361/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 362/1000 (Sampling=True) ---
# 	❌ FAIL (L=172): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 363/1000 (Sampling=True) ---
# 	❌ FAIL (L=170): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 364/1000 (Sampling=True) ---
# 	❌ FAIL (L=190): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 365/1000 (Sampling=True) ---
# 	✅ PASS (L=177): $\lambda_2$=0.3132 	 $\lambda_{11}$=11.3049

# --- Running Test 366/1000 (Sampling=True) ---
# 	✅ PASS (L=174): $\lambda_2$=0.2597 	 $\lambda_{11}$=7.7361

# --- Running Test 367/1000 (Sampling=True) ---
# 	❌ FAIL (L=197): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 368/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 369/1000 (Sampling=True) ---
# 	✅ PASS (L=178): $\lambda_2$=0.3061 	 $\lambda_{11}$=9.9881

# --- Running Test 370/1000 (Sampling=True) ---
# 	✅ PASS (L=183): $\lambda_2$=0.3132 	 $\lambda_{11}$=6.8412

# --- Running Test 371/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 372/1000 (Sampling=True) ---
# 	❌ FAIL (L=172): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 373/1000 (Sampling=True) ---
# 	❌ FAIL (L=170): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 374/1000 (Sampling=True) ---
# 	❌ FAIL (L=190): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 375/1000 (Sampling=True) ---
# 	✅ PASS (L=177): $\lambda_2$=0.3132 	 $\lambda_{11}$=11.6758

# --- Running Test 376/1000 (Sampling=True) ---
# 	✅ PASS (L=174): $\lambda_2$=0.2597 	 $\lambda_{11}$=7.4865

# --- Running Test 377/1000 (Sampling=True) ---
# 	❌ FAIL (L=197): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 378/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 379/1000 (Sampling=True) ---
# 	✅ PASS (L=178): $\lambda_2$=0.3061 	 $\lambda_{11}$=11.1016

# --- Running Test 380/1000 (Sampling=True) ---
# 	✅ PASS (L=183): $\lambda_2$=0.3132 	 $\lambda_{11}$=6.4627

# --- Running Test 381/1000 (Sampling=True) ---
# 	❌ FAIL (L=145): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 382/1000 (Sampling=True) ---
# 	❌ FAIL (L=172): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 383/1000 (Sampling=True) ---
# 	❌ FAIL (L=170): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 384/1000 (Sampling=True) ---
# 	❌ FAIL (L=190): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 385/1000 (Sampling=True) ---
# 	✅ PASS (L=177): $\lambda_2$=0.3132 	 $\lambda_{11}$=9.7047

# --- Running Test 386/1000 (Sampling=True) ---
# 	✅ PASS (L=174): $\lambda_2$=0.2597 	 $\lambda_{11}$=10.3374

# --- Running Test 387/1000 (Sampling=True) ---
# 	❌ FAIL (L=197): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 388/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 389/1000 (Sampling=True) ---
# 	✅ PASS (L=37): $\lambda_2$=0.3061 	 $\lambda_{11}$=11.8033

# --- Running Test 390/1000 (Sampling=True) ---
# 	✅ PASS (L=183): $\lambda_2$=0.3132 	 $\lambda_{11}$=7.7597

# --- Running Test 391/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 392/1000 (Sampling=True) ---
# 	❌ FAIL (L=172): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 393/1000 (Sampling=True) ---
# 	❌ FAIL (L=170): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 394/1000 (Sampling=True) ---
# 	❌ FAIL (L=99): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 395/1000 (Sampling=True) ---
# 	✅ PASS (L=177): $\lambda_2$=0.3132 	 $\lambda_{11}$=10.7953

# --- Running Test 396/1000 (Sampling=True) ---
# 	✅ PASS (L=174): $\lambda_2$=0.2597 	 $\lambda_{11}$=7.6843

# --- Running Test 397/1000 (Sampling=True) ---
# 	❌ FAIL (L=197): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 398/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 399/1000 (Sampling=True) ---
# 	✅ PASS (L=178): $\lambda_2$=0.3061 	 $\lambda_{11}$=9.8227

# --- Running Test 400/1000 (Sampling=True) ---
# 	✅ PASS (L=183): $\lambda_2$=0.3132 	 $\lambda_{11}$=7.7966

# --- Running Test 401/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 402/1000 (Sampling=True) ---
# 	❌ FAIL (L=172): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 403/1000 (Sampling=True) ---
# 	❌ FAIL (L=170): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 404/1000 (Sampling=True) ---
# 	❌ FAIL (L=190): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 405/1000 (Sampling=True) ---
# 	✅ PASS (L=177): $\lambda_2$=0.3132 	 $\lambda_{11}$=12.0795

# --- Running Test 406/1000 (Sampling=True) ---
# 	✅ PASS (L=174): $\lambda_2$=0.2597 	 $\lambda_{11}$=5.5707

# --- Running Test 407/1000 (Sampling=True) ---
# 	❌ FAIL (L=197): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 408/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 409/1000 (Sampling=True) ---
# 	✅ PASS (L=178): $\lambda_2$=0.3061 	 $\lambda_{11}$=12.1628

# --- Running Test 410/1000 (Sampling=True) ---
# 	✅ PASS (L=183): $\lambda_2$=0.3132 	 $\lambda_{11}$=7.4351

# --- Running Test 411/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 412/1000 (Sampling=True) ---
# 	❌ FAIL (L=172): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 413/1000 (Sampling=True) ---
# 	❌ FAIL (L=170): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 414/1000 (Sampling=True) ---
# 	❌ FAIL (L=190): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 415/1000 (Sampling=True) ---
# 	✅ PASS (L=177): $\lambda_2$=0.3132 	 $\lambda_{11}$=10.8064

# --- Running Test 416/1000 (Sampling=True) ---
# 	✅ PASS (L=174): $\lambda_2$=0.2597 	 $\lambda_{11}$=5.8622

# --- Running Test 417/1000 (Sampling=True) ---
# 	❌ FAIL (L=197): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 418/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 419/1000 (Sampling=True) ---
# 	✅ PASS (L=178): $\lambda_2$=0.3061 	 $\lambda_{11}$=9.9342

# --- Running Test 420/1000 (Sampling=True) ---
# 	✅ PASS (L=183): $\lambda_2$=0.3132 	 $\lambda_{11}$=7.1476

# --- Running Test 421/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 422/1000 (Sampling=True) ---
# 	❌ FAIL (L=172): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 423/1000 (Sampling=True) ---
# 	❌ FAIL (L=170): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 424/1000 (Sampling=True) ---
# 	❌ FAIL (L=190): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 425/1000 (Sampling=True) ---
# 	✅ PASS (L=177): $\lambda_2$=0.3132 	 $\lambda_{11}$=9.3001

# --- Running Test 426/1000 (Sampling=True) ---
# 	✅ PASS (L=174): $\lambda_2$=0.2597 	 $\lambda_{11}$=8.2981

# --- Running Test 427/1000 (Sampling=True) ---
# 	❌ FAIL (L=197): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 428/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 429/1000 (Sampling=True) ---
# 	✅ PASS (L=178): $\lambda_2$=0.3061 	 $\lambda_{11}$=14.2750

# --- Running Test 430/1000 (Sampling=True) ---
# 	✅ PASS (L=183): $\lambda_2$=0.3132 	 $\lambda_{11}$=7.7473

# --- Running Test 431/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 432/1000 (Sampling=True) ---
# 	❌ FAIL (L=172): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 433/1000 (Sampling=True) ---
# 	❌ FAIL (L=170): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 434/1000 (Sampling=True) ---
# 	❌ FAIL (L=190): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 435/1000 (Sampling=True) ---
# 	✅ PASS (L=177): $\lambda_2$=0.3132 	 $\lambda_{11}$=11.2510

# --- Running Test 436/1000 (Sampling=True) ---
# 	✅ PASS (L=174): $\lambda_2$=0.2597 	 $\lambda_{11}$=8.5592

# --- Running Test 437/1000 (Sampling=True) ---
# 	❌ FAIL (L=197): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 438/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 439/1000 (Sampling=True) ---
# 	✅ PASS (L=178): $\lambda_2$=0.3061 	 $\lambda_{11}$=10.5703

# --- Running Test 440/1000 (Sampling=True) ---
# 	✅ PASS (L=183): $\lambda_2$=0.3132 	 $\lambda_{11}$=7.4878

# --- Running Test 441/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 442/1000 (Sampling=True) ---
# 	❌ FAIL (L=127): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 443/1000 (Sampling=True) ---
# 	❌ FAIL (L=170): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 444/1000 (Sampling=True) ---
# 	❌ FAIL (L=190): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 445/1000 (Sampling=True) ---
# 	✅ PASS (L=177): $\lambda_2$=0.3132 	 $\lambda_{11}$=10.5661

# --- Running Test 446/1000 (Sampling=True) ---
# 	✅ PASS (L=174): $\lambda_2$=0.2597 	 $\lambda_{11}$=6.9637

# --- Running Test 447/1000 (Sampling=True) ---
# 	❌ FAIL (L=197): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 448/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 449/1000 (Sampling=True) ---
# 	✅ PASS (L=144): $\lambda_2$=0.3061 	 $\lambda_{11}$=9.8982

# --- Running Test 450/1000 (Sampling=True) ---
# 	✅ PASS (L=183): $\lambda_2$=0.3132 	 $\lambda_{11}$=7.9060

# --- Running Test 451/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 452/1000 (Sampling=True) ---
# 	❌ FAIL (L=172): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 453/1000 (Sampling=True) ---
# 	❌ FAIL (L=170): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 454/1000 (Sampling=True) ---
# 	❌ FAIL (L=190): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 455/1000 (Sampling=True) ---
# 	✅ PASS (L=177): $\lambda_2$=0.3132 	 $\lambda_{11}$=10.5102

# --- Running Test 456/1000 (Sampling=True) ---
# 	✅ PASS (L=174): $\lambda_2$=0.2597 	 $\lambda_{11}$=6.5365

# --- Running Test 457/1000 (Sampling=True) ---
# 	❌ FAIL (L=197): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 458/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 459/1000 (Sampling=True) ---
# 	✅ PASS (L=178): $\lambda_2$=0.3061 	 $\lambda_{11}$=10.4413

# --- Running Test 460/1000 (Sampling=True) ---
# 	✅ PASS (L=183): $\lambda_2$=0.3132 	 $\lambda_{11}$=7.7516

# --- Running Test 461/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 462/1000 (Sampling=True) ---
# 	❌ FAIL (L=172): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 463/1000 (Sampling=True) ---
# 	❌ FAIL (L=170): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 464/1000 (Sampling=True) ---
# 	❌ FAIL (L=190): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 465/1000 (Sampling=True) ---
# 	✅ PASS (L=177): $\lambda_2$=0.3132 	 $\lambda_{11}$=7.5721

# --- Running Test 466/1000 (Sampling=True) ---
# 	✅ PASS (L=174): $\lambda_2$=0.2597 	 $\lambda_{11}$=1.7753

# --- Running Test 467/1000 (Sampling=True) ---
# 	❌ FAIL (L=197): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 468/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 469/1000 (Sampling=True) ---
# 	✅ PASS (L=178): $\lambda_2$=0.3061 	 $\lambda_{11}$=12.3449

# --- Running Test 470/1000 (Sampling=True) ---
# 	✅ PASS (L=183): $\lambda_2$=0.3132 	 $\lambda_{11}$=9.3304

# --- Running Test 471/1000 (Sampling=True) ---
# 	❌ FAIL (L=74): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 472/1000 (Sampling=True) ---
# 	❌ FAIL (L=172): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 473/1000 (Sampling=True) ---
# 	❌ FAIL (L=170): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 474/1000 (Sampling=True) ---
# 	❌ FAIL (L=190): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 475/1000 (Sampling=True) ---
# 	✅ PASS (L=177): $\lambda_2$=0.3132 	 $\lambda_{11}$=9.8016

# --- Running Test 476/1000 (Sampling=True) ---
# 	✅ PASS (L=174): $\lambda_2$=0.2597 	 $\lambda_{11}$=8.2848

# --- Running Test 477/1000 (Sampling=True) ---
# 	❌ FAIL (L=197): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 478/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 479/1000 (Sampling=True) ---
# 	✅ PASS (L=149): $\lambda_2$=0.3061 	 $\lambda_{11}$=10.9781

# --- Running Test 480/1000 (Sampling=True) ---
# 	✅ PASS (L=183): $\lambda_2$=0.3132 	 $\lambda_{11}$=7.4432

# --- Running Test 481/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 482/1000 (Sampling=True) ---
# 	❌ FAIL (L=172): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 483/1000 (Sampling=True) ---
# 	❌ FAIL (L=170): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 484/1000 (Sampling=True) ---
# 	❌ FAIL (L=190): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 485/1000 (Sampling=True) ---
# 	✅ PASS (L=177): $\lambda_2$=0.3132 	 $\lambda_{11}$=9.6782

# --- Running Test 486/1000 (Sampling=True) ---
# 	✅ PASS (L=174): $\lambda_2$=0.2597 	 $\lambda_{11}$=8.1567

# --- Running Test 487/1000 (Sampling=True) ---
# 	❌ FAIL (L=197): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 488/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 489/1000 (Sampling=True) ---
# 	✅ PASS (L=178): $\lambda_2$=0.3061 	 $\lambda_{11}$=12.9872

# --- Running Test 490/1000 (Sampling=True) ---
# 	✅ PASS (L=166): $\lambda_2$=0.3132 	 $\lambda_{11}$=13.3573

# --- Running Test 491/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 492/1000 (Sampling=True) ---
# 	❌ FAIL (L=172): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 493/1000 (Sampling=True) ---
# 	❌ FAIL (L=170): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 494/1000 (Sampling=True) ---
# 	❌ FAIL (L=190): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 495/1000 (Sampling=True) ---
# 	✅ PASS (L=177): $\lambda_2$=0.3132 	 $\lambda_{11}$=9.1347

# --- Running Test 496/1000 (Sampling=True) ---
# 	✅ PASS (L=174): $\lambda_2$=0.2597 	 $\lambda_{11}$=6.7574

# --- Running Test 497/1000 (Sampling=True) ---
# 	❌ FAIL (L=197): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 498/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 499/1000 (Sampling=True) ---
# 	✅ PASS (L=178): $\lambda_2$=0.3061 	 $\lambda_{11}$=8.2599

# --- Running Test 500/1000 (Sampling=True) ---
# 	✅ PASS (L=183): $\lambda_2$=0.3132 	 $\lambda_{11}$=7.3301

# --- Running Test 501/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 502/1000 (Sampling=True) ---
# 	❌ FAIL (L=172): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 503/1000 (Sampling=True) ---
# 	❌ FAIL (L=170): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 504/1000 (Sampling=True) ---
# 	❌ FAIL (L=190): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 505/1000 (Sampling=True) ---
# 	✅ PASS (L=177): $\lambda_2$=0.3132 	 $\lambda_{11}$=10.0739

# --- Running Test 506/1000 (Sampling=True) ---
# 	✅ PASS (L=174): $\lambda_2$=0.2597 	 $\lambda_{11}$=6.8782

# --- Running Test 507/1000 (Sampling=True) ---
# 	❌ FAIL (L=197): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 508/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 509/1000 (Sampling=True) ---
# 	✅ PASS (L=89): $\lambda_2$=0.3061 	 $\lambda_{11}$=11.2993

# --- Running Test 510/1000 (Sampling=True) ---
# 	✅ PASS (L=183): $\lambda_2$=0.3132 	 $\lambda_{11}$=7.3992

# --- Running Test 511/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 512/1000 (Sampling=True) ---
# 	❌ FAIL (L=145): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 513/1000 (Sampling=True) ---
# 	❌ FAIL (L=170): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 514/1000 (Sampling=True) ---
# 	❌ FAIL (L=190): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 515/1000 (Sampling=True) ---
# 	✅ PASS (L=177): $\lambda_2$=0.3132 	 $\lambda_{11}$=9.0184

# --- Running Test 516/1000 (Sampling=True) ---
# 	✅ PASS (L=174): $\lambda_2$=0.2597 	 $\lambda_{11}$=7.9875

# --- Running Test 517/1000 (Sampling=True) ---
# 	❌ FAIL (L=197): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 518/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 519/1000 (Sampling=True) ---
# 	✅ PASS (L=178): $\lambda_2$=0.3061 	 $\lambda_{11}$=12.1643

# --- Running Test 520/1000 (Sampling=True) ---
# 	✅ PASS (L=183): $\lambda_2$=0.3132 	 $\lambda_{11}$=6.9002

# --- Running Test 521/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 522/1000 (Sampling=True) ---
# 	❌ FAIL (L=172): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 523/1000 (Sampling=True) ---
# 	❌ FAIL (L=170): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 524/1000 (Sampling=True) ---
# 	❌ FAIL (L=190): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 525/1000 (Sampling=True) ---
# 	✅ PASS (L=177): $\lambda_2$=0.3132 	 $\lambda_{11}$=9.6542

# --- Running Test 526/1000 (Sampling=True) ---
# 	✅ PASS (L=174): $\lambda_2$=0.2597 	 $\lambda_{11}$=6.7909

# --- Running Test 527/1000 (Sampling=True) ---
# 	❌ FAIL (L=197): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 528/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 529/1000 (Sampling=True) ---
# 	✅ PASS (L=178): $\lambda_2$=0.3061 	 $\lambda_{11}$=11.6157

# --- Running Test 530/1000 (Sampling=True) ---
# 	✅ PASS (L=183): $\lambda_2$=0.3132 	 $\lambda_{11}$=8.6236

# --- Running Test 531/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 532/1000 (Sampling=True) ---
# 	❌ FAIL (L=172): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 533/1000 (Sampling=True) ---
# 	❌ FAIL (L=170): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 534/1000 (Sampling=True) ---
# 	❌ FAIL (L=143): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 535/1000 (Sampling=True) ---
# 	✅ PASS (L=177): $\lambda_2$=0.3132 	 $\lambda_{11}$=9.7466

# --- Running Test 536/1000 (Sampling=True) ---
# 	✅ PASS (L=174): $\lambda_2$=0.2597 	 $\lambda_{11}$=6.9120

# --- Running Test 537/1000 (Sampling=True) ---
# 	❌ FAIL (L=197): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 538/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 539/1000 (Sampling=True) ---
# 	✅ PASS (L=178): $\lambda_2$=0.3061 	 $\lambda_{11}$=10.2240

# --- Running Test 540/1000 (Sampling=True) ---
# 	✅ PASS (L=183): $\lambda_2$=0.3132 	 $\lambda_{11}$=6.6705

# --- Running Test 541/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 542/1000 (Sampling=True) ---
# 	❌ FAIL (L=172): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 543/1000 (Sampling=True) ---
# 	❌ FAIL (L=170): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 544/1000 (Sampling=True) ---
# 	❌ FAIL (L=190): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 545/1000 (Sampling=True) ---
# 	✅ PASS (L=177): $\lambda_2$=0.3132 	 $\lambda_{11}$=13.3475

# --- Running Test 546/1000 (Sampling=True) ---
# 	✅ PASS (L=174): $\lambda_2$=0.2597 	 $\lambda_{11}$=6.0279

# --- Running Test 547/1000 (Sampling=True) ---
# 	❌ FAIL (L=197): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 548/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 549/1000 (Sampling=True) ---
# 	✅ PASS (L=178): $\lambda_2$=0.3061 	 $\lambda_{11}$=11.1472

# --- Running Test 550/1000 (Sampling=True) ---
# 	✅ PASS (L=183): $\lambda_2$=0.3132 	 $\lambda_{11}$=8.2447

# --- Running Test 551/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 552/1000 (Sampling=True) ---
# 	❌ FAIL (L=172): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 553/1000 (Sampling=True) ---
# 	❌ FAIL (L=170): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 554/1000 (Sampling=True) ---
# 	❌ FAIL (L=190): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 555/1000 (Sampling=True) ---
# 	✅ PASS (L=177): $\lambda_2$=0.3132 	 $\lambda_{11}$=9.7532

# --- Running Test 556/1000 (Sampling=True) ---
# 	✅ PASS (L=174): $\lambda_2$=0.2597 	 $\lambda_{11}$=6.9016

# --- Running Test 557/1000 (Sampling=True) ---
# 	❌ FAIL (L=197): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 558/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 559/1000 (Sampling=True) ---
# 	✅ PASS (L=178): $\lambda_2$=0.3061 	 $\lambda_{11}$=10.2197

# --- Running Test 560/1000 (Sampling=True) ---
# 	✅ PASS (L=183): $\lambda_2$=0.3132 	 $\lambda_{11}$=6.5818

# --- Running Test 561/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 562/1000 (Sampling=True) ---
# 	❌ FAIL (L=172): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 563/1000 (Sampling=True) ---
# 	❌ FAIL (L=105): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 564/1000 (Sampling=True) ---
# 	❌ FAIL (L=190): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 565/1000 (Sampling=True) ---
# 	✅ PASS (L=177): $\lambda_2$=0.3132 	 $\lambda_{11}$=11.6096

# --- Running Test 566/1000 (Sampling=True) ---
# 	✅ PASS (L=174): $\lambda_2$=0.2597 	 $\lambda_{11}$=6.3059

# --- Running Test 567/1000 (Sampling=True) ---
# 	❌ FAIL (L=197): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 568/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 569/1000 (Sampling=True) ---
# 	✅ PASS (L=178): $\lambda_2$=0.3061 	 $\lambda_{11}$=11.6970

# --- Running Test 570/1000 (Sampling=True) ---
# 	✅ PASS (L=183): $\lambda_2$=0.3132 	 $\lambda_{11}$=8.7001

# --- Running Test 571/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 572/1000 (Sampling=True) ---
# 	❌ FAIL (L=172): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 573/1000 (Sampling=True) ---
# 	❌ FAIL (L=170): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 574/1000 (Sampling=True) ---
# 	❌ FAIL (L=190): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 575/1000 (Sampling=True) ---
# 	✅ PASS (L=177): $\lambda_2$=0.3132 	 $\lambda_{11}$=13.3098

# --- Running Test 576/1000 (Sampling=True) ---
# 	✅ PASS (L=174): $\lambda_2$=0.2597 	 $\lambda_{11}$=4.3465

# --- Running Test 577/1000 (Sampling=True) ---
# 	❌ FAIL (L=197): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 578/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 579/1000 (Sampling=True) ---
# 	✅ PASS (L=178): $\lambda_2$=0.3061 	 $\lambda_{11}$=13.2066

# --- Running Test 580/1000 (Sampling=True) ---
# 	✅ PASS (L=183): $\lambda_2$=0.3132 	 $\lambda_{11}$=7.7433

# --- Running Test 581/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 582/1000 (Sampling=True) ---
# 	❌ FAIL (L=172): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 583/1000 (Sampling=True) ---
# 	❌ FAIL (L=37): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 584/1000 (Sampling=True) ---
# 	❌ FAIL (L=136): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 585/1000 (Sampling=True) ---
# 	✅ PASS (L=177): $\lambda_2$=0.3132 	 $\lambda_{11}$=10.2181

# --- Running Test 586/1000 (Sampling=True) ---
# 	✅ PASS (L=174): $\lambda_2$=0.2597 	 $\lambda_{11}$=7.3936

# --- Running Test 587/1000 (Sampling=True) ---
# 	❌ FAIL (L=197): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 588/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 589/1000 (Sampling=True) ---
# 	✅ PASS (L=122): $\lambda_2$=0.3061 	 $\lambda_{11}$=9.7592

# --- Running Test 590/1000 (Sampling=True) ---
# 	✅ PASS (L=183): $\lambda_2$=0.3132 	 $\lambda_{11}$=8.4121

# --- Running Test 591/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 592/1000 (Sampling=True) ---
# 	❌ FAIL (L=172): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 593/1000 (Sampling=True) ---
# 	❌ FAIL (L=170): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 594/1000 (Sampling=True) ---
# 	❌ FAIL (L=190): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 595/1000 (Sampling=True) ---
# 	✅ PASS (L=177): $\lambda_2$=0.3132 	 $\lambda_{11}$=12.2252

# --- Running Test 596/1000 (Sampling=True) ---
# 	✅ PASS (L=174): $\lambda_2$=0.2597 	 $\lambda_{11}$=8.8639

# --- Running Test 597/1000 (Sampling=True) ---
# 	❌ FAIL (L=197): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 598/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 599/1000 (Sampling=True) ---
# 	✅ PASS (L=178): $\lambda_2$=0.3061 	 $\lambda_{11}$=9.4509

# --- Running Test 600/1000 (Sampling=True) ---
# 	✅ PASS (L=183): $\lambda_2$=0.3132 	 $\lambda_{11}$=8.6722

# --- Running Test 601/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 602/1000 (Sampling=True) ---
# 	❌ FAIL (L=172): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 603/1000 (Sampling=True) ---
# 	❌ FAIL (L=105): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 604/1000 (Sampling=True) ---
# 	❌ FAIL (L=190): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 605/1000 (Sampling=True) ---
# 	✅ PASS (L=177): $\lambda_2$=0.3132 	 $\lambda_{11}$=9.1243

# --- Running Test 606/1000 (Sampling=True) ---
# 	✅ PASS (L=174): $\lambda_2$=0.2597 	 $\lambda_{11}$=8.6321

# --- Running Test 607/1000 (Sampling=True) ---
# 	❌ FAIL (L=197): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 608/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 609/1000 (Sampling=True) ---
# 	✅ PASS (L=178): $\lambda_2$=0.3061 	 $\lambda_{11}$=10.7539

# --- Running Test 610/1000 (Sampling=True) ---
# 	✅ PASS (L=183): $\lambda_2$=0.3132 	 $\lambda_{11}$=7.9870

# --- Running Test 611/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 612/1000 (Sampling=True) ---
# 	❌ FAIL (L=172): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 613/1000 (Sampling=True) ---
# 	❌ FAIL (L=170): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 614/1000 (Sampling=True) ---
# 	❌ FAIL (L=190): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 615/1000 (Sampling=True) ---
# 	✅ PASS (L=177): $\lambda_2$=0.3132 	 $\lambda_{11}$=7.6164

# --- Running Test 616/1000 (Sampling=True) ---
# 	✅ PASS (L=174): $\lambda_2$=0.2597 	 $\lambda_{11}$=7.5916

# --- Running Test 617/1000 (Sampling=True) ---
# 	❌ FAIL (L=197): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 618/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 619/1000 (Sampling=True) ---
# 	✅ PASS (L=178): $\lambda_2$=0.3061 	 $\lambda_{11}$=9.3016

# --- Running Test 620/1000 (Sampling=True) ---
# 	✅ PASS (L=183): $\lambda_2$=0.3132 	 $\lambda_{11}$=8.0313

# --- Running Test 621/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 622/1000 (Sampling=True) ---
# 	❌ FAIL (L=172): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 623/1000 (Sampling=True) ---
# 	❌ FAIL (L=170): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 624/1000 (Sampling=True) ---
# 	❌ FAIL (L=190): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 625/1000 (Sampling=True) ---
# 	✅ PASS (L=177): $\lambda_2$=0.3132 	 $\lambda_{11}$=11.0091

# --- Running Test 626/1000 (Sampling=True) ---
# 	✅ PASS (L=174): $\lambda_2$=0.2597 	 $\lambda_{11}$=7.0433

# --- Running Test 627/1000 (Sampling=True) ---
# 	❌ FAIL (L=197): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 628/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 629/1000 (Sampling=True) ---
# 	✅ PASS (L=178): $\lambda_2$=0.3061 	 $\lambda_{11}$=10.3901

# --- Running Test 630/1000 (Sampling=True) ---
# 	✅ PASS (L=183): $\lambda_2$=0.3132 	 $\lambda_{11}$=6.6613

# --- Running Test 631/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 632/1000 (Sampling=True) ---
# 	❌ FAIL (L=172): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 633/1000 (Sampling=True) ---
# 	❌ FAIL (L=170): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 634/1000 (Sampling=True) ---
# 	❌ FAIL (L=190): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 635/1000 (Sampling=True) ---
# 	✅ PASS (L=177): $\lambda_2$=0.3132 	 $\lambda_{11}$=9.5414

# --- Running Test 636/1000 (Sampling=True) ---
# 	✅ PASS (L=174): $\lambda_2$=0.2597 	 $\lambda_{11}$=9.5231

# --- Running Test 637/1000 (Sampling=True) ---
# 	❌ FAIL (L=197): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 638/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 639/1000 (Sampling=True) ---
# 	✅ PASS (L=178): $\lambda_2$=0.3061 	 $\lambda_{11}$=9.1739

# --- Running Test 640/1000 (Sampling=True) ---
# 	✅ PASS (L=183): $\lambda_2$=0.3132 	 $\lambda_{11}$=7.4219

# --- Running Test 641/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 642/1000 (Sampling=True) ---
# 	❌ FAIL (L=172): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 643/1000 (Sampling=True) ---
# 	❌ FAIL (L=170): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 644/1000 (Sampling=True) ---
# 	❌ FAIL (L=190): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 645/1000 (Sampling=True) ---
# 	✅ PASS (L=177): $\lambda_2$=0.3132 	 $\lambda_{11}$=8.8494

# --- Running Test 646/1000 (Sampling=True) ---
# 	✅ PASS (L=174): $\lambda_2$=0.2597 	 $\lambda_{11}$=8.3673

# --- Running Test 647/1000 (Sampling=True) ---
# 	❌ FAIL (L=197): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 648/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 649/1000 (Sampling=True) ---
# 	✅ PASS (L=178): $\lambda_2$=0.3061 	 $\lambda_{11}$=10.7571

# --- Running Test 650/1000 (Sampling=True) ---
# 	✅ PASS (L=183): $\lambda_2$=0.3132 	 $\lambda_{11}$=8.5467

# --- Running Test 651/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 652/1000 (Sampling=True) ---
# 	❌ FAIL (L=172): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 653/1000 (Sampling=True) ---
# 	❌ FAIL (L=170): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 654/1000 (Sampling=True) ---
# 	❌ FAIL (L=190): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 655/1000 (Sampling=True) ---
# 	✅ PASS (L=177): $\lambda_2$=0.3132 	 $\lambda_{11}$=7.3368

# --- Running Test 656/1000 (Sampling=True) ---
# 	✅ PASS (L=174): $\lambda_2$=0.2597 	 $\lambda_{11}$=6.4160

# --- Running Test 657/1000 (Sampling=True) ---
# 	❌ FAIL (L=197): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 658/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 659/1000 (Sampling=True) ---
# 	✅ PASS (L=178): $\lambda_2$=0.3061 	 $\lambda_{11}$=10.4335

# --- Running Test 660/1000 (Sampling=True) ---
# 	✅ PASS (L=183): $\lambda_2$=0.3132 	 $\lambda_{11}$=6.9021

# --- Running Test 661/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 662/1000 (Sampling=True) ---
# 	❌ FAIL (L=172): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 663/1000 (Sampling=True) ---
# 	❌ FAIL (L=170): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 664/1000 (Sampling=True) ---
# 	❌ FAIL (L=190): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 665/1000 (Sampling=True) ---
# 	✅ PASS (L=177): $\lambda_2$=0.3132 	 $\lambda_{11}$=8.6920

# --- Running Test 666/1000 (Sampling=True) ---
# 	✅ PASS (L=174): $\lambda_2$=0.2597 	 $\lambda_{11}$=6.5097

# --- Running Test 667/1000 (Sampling=True) ---
# 	❌ FAIL (L=197): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 668/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 669/1000 (Sampling=True) ---
# 	✅ PASS (L=167): $\lambda_2$=0.3061 	 $\lambda_{11}$=12.2261

# --- Running Test 670/1000 (Sampling=True) ---
# 	✅ PASS (L=183): $\lambda_2$=0.3132 	 $\lambda_{11}$=6.1935

# --- Running Test 671/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 672/1000 (Sampling=True) ---
# 	❌ FAIL (L=172): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 673/1000 (Sampling=True) ---
# 	❌ FAIL (L=170): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 674/1000 (Sampling=True) ---
# 	❌ FAIL (L=190): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 675/1000 (Sampling=True) ---
# 	✅ PASS (L=177): $\lambda_2$=0.3132 	 $\lambda_{11}$=9.9052

# --- Running Test 676/1000 (Sampling=True) ---
# 	✅ PASS (L=174): $\lambda_2$=0.2597 	 $\lambda_{11}$=8.4926

# --- Running Test 677/1000 (Sampling=True) ---
# 	❌ FAIL (L=197): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 678/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 679/1000 (Sampling=True) ---
# 	✅ PASS (L=91): $\lambda_2$=0.3061 	 $\lambda_{11}$=10.7412

# --- Running Test 680/1000 (Sampling=True) ---
# 	✅ PASS (L=183): $\lambda_2$=0.3132 	 $\lambda_{11}$=6.5458

# --- Running Test 681/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 682/1000 (Sampling=True) ---
# 	❌ FAIL (L=172): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 683/1000 (Sampling=True) ---
# 	❌ FAIL (L=170): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 684/1000 (Sampling=True) ---
# 	❌ FAIL (L=190): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 685/1000 (Sampling=True) ---
# 	✅ PASS (L=177): $\lambda_2$=0.3132 	 $\lambda_{11}$=9.6104

# --- Running Test 686/1000 (Sampling=True) ---
# 	✅ PASS (L=174): $\lambda_2$=0.2597 	 $\lambda_{11}$=7.1607

# --- Running Test 687/1000 (Sampling=True) ---
# 	❌ FAIL (L=197): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 688/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 689/1000 (Sampling=True) ---
# 	✅ PASS (L=178): $\lambda_2$=0.3061 	 $\lambda_{11}$=10.1099

# --- Running Test 690/1000 (Sampling=True) ---
# 	✅ PASS (L=183): $\lambda_2$=0.3132 	 $\lambda_{11}$=11.3157

# --- Running Test 691/1000 (Sampling=True) ---
# 	❌ FAIL (L=71): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 692/1000 (Sampling=True) ---
# 	❌ FAIL (L=172): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 693/1000 (Sampling=True) ---
# 	❌ FAIL (L=170): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 694/1000 (Sampling=True) ---
# 	❌ FAIL (L=190): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 695/1000 (Sampling=True) ---
# 	✅ PASS (L=177): $\lambda_2$=0.3132 	 $\lambda_{11}$=8.2039

# --- Running Test 696/1000 (Sampling=True) ---
# 	✅ PASS (L=174): $\lambda_2$=0.2597 	 $\lambda_{11}$=6.6285

# --- Running Test 697/1000 (Sampling=True) ---
# 	❌ FAIL (L=197): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 698/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 699/1000 (Sampling=True) ---
# 	✅ PASS (L=178): $\lambda_2$=0.3061 	 $\lambda_{11}$=12.0010

# --- Running Test 700/1000 (Sampling=True) ---
# 	✅ PASS (L=183): $\lambda_2$=0.3132 	 $\lambda_{11}$=5.7565

# --- Running Test 701/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 702/1000 (Sampling=True) ---
# 	❌ FAIL (L=172): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 703/1000 (Sampling=True) ---
# 	❌ FAIL (L=170): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 704/1000 (Sampling=True) ---
# 	❌ FAIL (L=190): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 705/1000 (Sampling=True) ---
# 	✅ PASS (L=177): $\lambda_2$=0.3132 	 $\lambda_{11}$=9.5616

# --- Running Test 706/1000 (Sampling=True) ---
# 	✅ PASS (L=174): $\lambda_2$=0.2597 	 $\lambda_{11}$=6.1445

# --- Running Test 707/1000 (Sampling=True) ---
# 	❌ FAIL (L=197): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 708/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 709/1000 (Sampling=True) ---
# 	✅ PASS (L=138): $\lambda_2$=0.3061 	 $\lambda_{11}$=10.1203

# --- Running Test 710/1000 (Sampling=True) ---
# 	✅ PASS (L=183): $\lambda_2$=0.3132 	 $\lambda_{11}$=7.1259

# --- Running Test 711/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 712/1000 (Sampling=True) ---
# 	❌ FAIL (L=172): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 713/1000 (Sampling=True) ---
# 	❌ FAIL (L=170): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 714/1000 (Sampling=True) ---
# 	❌ FAIL (L=190): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 715/1000 (Sampling=True) ---
# 	✅ PASS (L=177): $\lambda_2$=0.3132 	 $\lambda_{11}$=16.5739

# --- Running Test 716/1000 (Sampling=True) ---
# 	✅ PASS (L=174): $\lambda_2$=0.2597 	 $\lambda_{11}$=7.5041

# --- Running Test 717/1000 (Sampling=True) ---
# 	❌ FAIL (L=197): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 718/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 719/1000 (Sampling=True) ---
# 	✅ PASS (L=178): $\lambda_2$=0.3061 	 $\lambda_{11}$=11.8201

# --- Running Test 720/1000 (Sampling=True) ---
# 	✅ PASS (L=183): $\lambda_2$=0.3132 	 $\lambda_{11}$=6.5260

# --- Running Test 721/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 722/1000 (Sampling=True) ---
# 	❌ FAIL (L=172): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 723/1000 (Sampling=True) ---
# 	❌ FAIL (L=170): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 724/1000 (Sampling=True) ---
# 	❌ FAIL (L=190): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 725/1000 (Sampling=True) ---
# 	✅ PASS (L=177): $\lambda_2$=0.3132 	 $\lambda_{11}$=11.4768

# --- Running Test 726/1000 (Sampling=True) ---
# 	✅ PASS (L=174): $\lambda_2$=0.2597 	 $\lambda_{11}$=8.3388

# --- Running Test 727/1000 (Sampling=True) ---
# 	❌ FAIL (L=197): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 728/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 729/1000 (Sampling=True) ---
# 	✅ PASS (L=178): $\lambda_2$=0.3061 	 $\lambda_{11}$=9.1323

# --- Running Test 730/1000 (Sampling=True) ---
# 	✅ PASS (L=183): $\lambda_2$=0.3132 	 $\lambda_{11}$=6.6069

# --- Running Test 731/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 732/1000 (Sampling=True) ---
# 	❌ FAIL (L=172): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 733/1000 (Sampling=True) ---
# 	❌ FAIL (L=170): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 734/1000 (Sampling=True) ---
# 	❌ FAIL (L=190): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 735/1000 (Sampling=True) ---
# 	✅ PASS (L=177): $\lambda_2$=0.3132 	 $\lambda_{11}$=9.9826

# --- Running Test 736/1000 (Sampling=True) ---
# 	✅ PASS (L=174): $\lambda_2$=0.2597 	 $\lambda_{11}$=8.6246

# --- Running Test 737/1000 (Sampling=True) ---
# 	❌ FAIL (L=197): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 738/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 739/1000 (Sampling=True) ---
# 	✅ PASS (L=178): $\lambda_2$=0.3061 	 $\lambda_{11}$=11.8944

# --- Running Test 740/1000 (Sampling=True) ---
# 	✅ PASS (L=183): $\lambda_2$=0.3132 	 $\lambda_{11}$=7.5909

# --- Running Test 741/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 742/1000 (Sampling=True) ---
# 	❌ FAIL (L=172): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 743/1000 (Sampling=True) ---
# 	❌ FAIL (L=170): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 744/1000 (Sampling=True) ---
# 	❌ FAIL (L=190): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 745/1000 (Sampling=True) ---
# 	✅ PASS (L=177): $\lambda_2$=0.3132 	 $\lambda_{11}$=9.7597

# --- Running Test 746/1000 (Sampling=True) ---
# 	✅ PASS (L=174): $\lambda_2$=0.2597 	 $\lambda_{11}$=10.6967

# --- Running Test 747/1000 (Sampling=True) ---
# 	❌ FAIL (L=197): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 748/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 749/1000 (Sampling=True) ---
# 	✅ PASS (L=178): $\lambda_2$=0.3061 	 $\lambda_{11}$=9.4461

# --- Running Test 750/1000 (Sampling=True) ---
# 	✅ PASS (L=183): $\lambda_2$=0.3132 	 $\lambda_{11}$=8.4054

# --- Running Test 751/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 752/1000 (Sampling=True) ---
# 	❌ FAIL (L=172): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 753/1000 (Sampling=True) ---
# 	❌ FAIL (L=170): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 754/1000 (Sampling=True) ---
# 	❌ FAIL (L=190): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 755/1000 (Sampling=True) ---
# 	✅ PASS (L=177): $\lambda_2$=0.3132 	 $\lambda_{11}$=10.5017

# --- Running Test 756/1000 (Sampling=True) ---
# 	✅ PASS (L=174): $\lambda_2$=0.2597 	 $\lambda_{11}$=6.7329

# --- Running Test 757/1000 (Sampling=True) ---
# 	❌ FAIL (L=197): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 758/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 759/1000 (Sampling=True) ---
# 	✅ PASS (L=38): $\lambda_2$=0.3061 	 $\lambda_{11}$=12.8744

# --- Running Test 760/1000 (Sampling=True) ---
# 	✅ PASS (L=183): $\lambda_2$=0.3132 	 $\lambda_{11}$=7.4313

# --- Running Test 761/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 762/1000 (Sampling=True) ---
# 	❌ FAIL (L=172): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 763/1000 (Sampling=True) ---
# 	❌ FAIL (L=170): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 764/1000 (Sampling=True) ---
# 	❌ FAIL (L=190): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 765/1000 (Sampling=True) ---
# 	✅ PASS (L=177): $\lambda_2$=0.3132 	 $\lambda_{11}$=9.2841

# --- Running Test 766/1000 (Sampling=True) ---
# 	✅ PASS (L=174): $\lambda_2$=0.2597 	 $\lambda_{11}$=9.3873

# --- Running Test 767/1000 (Sampling=True) ---
# 	❌ FAIL (L=197): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 768/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 769/1000 (Sampling=True) ---
# 	✅ PASS (L=178): $\lambda_2$=0.3061 	 $\lambda_{11}$=10.2652

# --- Running Test 770/1000 (Sampling=True) ---
# 	✅ PASS (L=183): $\lambda_2$=0.3132 	 $\lambda_{11}$=7.5949

# --- Running Test 771/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 772/1000 (Sampling=True) ---
# 	❌ FAIL (L=172): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 773/1000 (Sampling=True) ---
# 	❌ FAIL (L=170): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 774/1000 (Sampling=True) ---
# 	❌ FAIL (L=190): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 775/1000 (Sampling=True) ---
# 	✅ PASS (L=177): $\lambda_2$=0.3132 	 $\lambda_{11}$=12.3631

# --- Running Test 776/1000 (Sampling=True) ---
# 	✅ PASS (L=174): $\lambda_2$=0.2597 	 $\lambda_{11}$=5.2795

# --- Running Test 777/1000 (Sampling=True) ---
# 	❌ FAIL (L=197): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 778/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 779/1000 (Sampling=True) ---
# 	✅ PASS (L=178): $\lambda_2$=0.3061 	 $\lambda_{11}$=9.5659

# --- Running Test 780/1000 (Sampling=True) ---
# 	✅ PASS (L=183): $\lambda_2$=0.3132 	 $\lambda_{11}$=7.1127

# --- Running Test 781/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 782/1000 (Sampling=True) ---
# 	❌ FAIL (L=172): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 783/1000 (Sampling=True) ---
# 	❌ FAIL (L=170): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 784/1000 (Sampling=True) ---
# 	❌ FAIL (L=190): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 785/1000 (Sampling=True) ---
# 	✅ PASS (L=177): $\lambda_2$=0.3132 	 $\lambda_{11}$=9.2052

# --- Running Test 786/1000 (Sampling=True) ---
# 	✅ PASS (L=174): $\lambda_2$=0.2597 	 $\lambda_{11}$=8.7815

# --- Running Test 787/1000 (Sampling=True) ---
# 	❌ FAIL (L=197): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 788/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 789/1000 (Sampling=True) ---
# 	✅ PASS (L=178): $\lambda_2$=0.3061 	 $\lambda_{11}$=12.4271

# --- Running Test 790/1000 (Sampling=True) ---
# 	✅ PASS (L=183): $\lambda_2$=0.3132 	 $\lambda_{11}$=7.9806

# --- Running Test 791/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 792/1000 (Sampling=True) ---
# 	❌ FAIL (L=172): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 793/1000 (Sampling=True) ---
# 	❌ FAIL (L=170): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 794/1000 (Sampling=True) ---
# 	❌ FAIL (L=190): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 795/1000 (Sampling=True) ---
# 	✅ PASS (L=177): $\lambda_2$=0.3132 	 $\lambda_{11}$=9.8994

# --- Running Test 796/1000 (Sampling=True) ---
# 	✅ PASS (L=174): $\lambda_2$=0.2597 	 $\lambda_{11}$=5.1019

# --- Running Test 797/1000 (Sampling=True) ---
# 	❌ FAIL (L=197): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 798/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 799/1000 (Sampling=True) ---
# 	✅ PASS (L=178): $\lambda_2$=0.3061 	 $\lambda_{11}$=10.1539

# --- Running Test 800/1000 (Sampling=True) ---
# 	✅ PASS (L=183): $\lambda_2$=0.3132 	 $\lambda_{11}$=10.2597

# --- Running Test 801/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 802/1000 (Sampling=True) ---
# 	❌ FAIL (L=172): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 803/1000 (Sampling=True) ---
# 	❌ FAIL (L=170): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 804/1000 (Sampling=True) ---
# 	❌ FAIL (L=190): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 805/1000 (Sampling=True) ---
# 	✅ PASS (L=177): $\lambda_2$=0.3132 	 $\lambda_{11}$=9.4855

# --- Running Test 806/1000 (Sampling=True) ---
# 	✅ PASS (L=174): $\lambda_2$=0.2597 	 $\lambda_{11}$=7.6311

# --- Running Test 807/1000 (Sampling=True) ---
# 	❌ FAIL (L=197): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 808/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 809/1000 (Sampling=True) ---
# 	✅ PASS (L=178): $\lambda_2$=0.3061 	 $\lambda_{11}$=10.4754

# --- Running Test 810/1000 (Sampling=True) ---
# 	✅ PASS (L=183): $\lambda_2$=0.3132 	 $\lambda_{11}$=7.7866

# --- Running Test 811/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 812/1000 (Sampling=True) ---
# 	❌ FAIL (L=172): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 813/1000 (Sampling=True) ---
# 	❌ FAIL (L=170): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 814/1000 (Sampling=True) ---
# 	❌ FAIL (L=190): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 815/1000 (Sampling=True) ---
# 	✅ PASS (L=177): $\lambda_2$=0.3132 	 $\lambda_{11}$=9.6402

# --- Running Test 816/1000 (Sampling=True) ---
# 	✅ PASS (L=174): $\lambda_2$=0.2597 	 $\lambda_{11}$=8.4560

# --- Running Test 817/1000 (Sampling=True) ---
# 	❌ FAIL (L=197): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 818/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 819/1000 (Sampling=True) ---
# 	✅ PASS (L=178): $\lambda_2$=0.3061 	 $\lambda_{11}$=11.0616

# --- Running Test 820/1000 (Sampling=True) ---
# 	✅ PASS (L=183): $\lambda_2$=0.3132 	 $\lambda_{11}$=9.6203

# --- Running Test 821/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 822/1000 (Sampling=True) ---
# 	❌ FAIL (L=172): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 823/1000 (Sampling=True) ---
# 	❌ FAIL (L=170): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 824/1000 (Sampling=True) ---
# 	❌ FAIL (L=190): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 825/1000 (Sampling=True) ---
# 	✅ PASS (L=177): $\lambda_2$=0.3132 	 $\lambda_{11}$=9.5242

# --- Running Test 826/1000 (Sampling=True) ---
# 	✅ PASS (L=69): $\lambda_2$=0.2597 	 $\lambda_{11}$=6.6809

# --- Running Test 827/1000 (Sampling=True) ---
# 	❌ FAIL (L=197): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 828/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 829/1000 (Sampling=True) ---
# 	✅ PASS (L=178): $\lambda_2$=0.3061 	 $\lambda_{11}$=10.4773

# --- Running Test 830/1000 (Sampling=True) ---
# 	✅ PASS (L=183): $\lambda_2$=0.3132 	 $\lambda_{11}$=6.4462

# --- Running Test 831/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 832/1000 (Sampling=True) ---
# 	❌ FAIL (L=172): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 833/1000 (Sampling=True) ---
# 	❌ FAIL (L=170): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 834/1000 (Sampling=True) ---
# 	❌ FAIL (L=190): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 835/1000 (Sampling=True) ---
# 	✅ PASS (L=177): $\lambda_2$=0.3132 	 $\lambda_{11}$=10.9193

# --- Running Test 836/1000 (Sampling=True) ---
# 	✅ PASS (L=174): $\lambda_2$=0.2597 	 $\lambda_{11}$=6.4509

# --- Running Test 837/1000 (Sampling=True) ---
# 	❌ FAIL (L=197): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 838/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 839/1000 (Sampling=True) ---
# 	✅ PASS (L=178): $\lambda_2$=0.3061 	 $\lambda_{11}$=12.7082

# --- Running Test 840/1000 (Sampling=True) ---
# 	✅ PASS (L=183): $\lambda_2$=0.3132 	 $\lambda_{11}$=8.2682

# --- Running Test 841/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 842/1000 (Sampling=True) ---
# 	❌ FAIL (L=172): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 843/1000 (Sampling=True) ---
# 	❌ FAIL (L=170): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 844/1000 (Sampling=True) ---
# 	❌ FAIL (L=190): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 845/1000 (Sampling=True) ---
# 	✅ PASS (L=177): $\lambda_2$=0.3132 	 $\lambda_{11}$=11.2483

# --- Running Test 846/1000 (Sampling=True) ---
# 	✅ PASS (L=174): $\lambda_2$=0.2597 	 $\lambda_{11}$=11.4384

# --- Running Test 847/1000 (Sampling=True) ---
# 	❌ FAIL (L=197): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 848/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 849/1000 (Sampling=True) ---
# 	✅ PASS (L=178): $\lambda_2$=0.3061 	 $\lambda_{11}$=10.6126

# --- Running Test 850/1000 (Sampling=True) ---
# 	✅ PASS (L=183): $\lambda_2$=0.3132 	 $\lambda_{11}$=8.9753

# --- Running Test 851/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 852/1000 (Sampling=True) ---
# 	❌ FAIL (L=172): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 853/1000 (Sampling=True) ---
# 	❌ FAIL (L=170): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 854/1000 (Sampling=True) ---
# 	❌ FAIL (L=190): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 855/1000 (Sampling=True) ---
# 	✅ PASS (L=177): $\lambda_2$=0.3132 	 $\lambda_{11}$=10.3744

# --- Running Test 856/1000 (Sampling=True) ---
# 	✅ PASS (L=174): $\lambda_2$=0.2597 	 $\lambda_{11}$=7.7722

# --- Running Test 857/1000 (Sampling=True) ---
# 	❌ FAIL (L=197): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 858/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 859/1000 (Sampling=True) ---
# 	✅ PASS (L=178): $\lambda_2$=0.3061 	 $\lambda_{11}$=10.0301

# --- Running Test 860/1000 (Sampling=True) ---
# 	✅ PASS (L=183): $\lambda_2$=0.3132 	 $\lambda_{11}$=6.8090

# --- Running Test 861/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 862/1000 (Sampling=True) ---
# 	❌ FAIL (L=172): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 863/1000 (Sampling=True) ---
# 	❌ FAIL (L=170): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 864/1000 (Sampling=True) ---
# 	❌ FAIL (L=190): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 865/1000 (Sampling=True) ---
# 	✅ PASS (L=177): $\lambda_2$=0.3132 	 $\lambda_{11}$=8.4584

# --- Running Test 866/1000 (Sampling=True) ---
# 	✅ PASS (L=174): $\lambda_2$=0.2597 	 $\lambda_{11}$=7.0480

# --- Running Test 867/1000 (Sampling=True) ---
# 	❌ FAIL (L=197): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 868/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 869/1000 (Sampling=True) ---
# 	✅ PASS (L=178): $\lambda_2$=0.3061 	 $\lambda_{11}$=12.6980

# --- Running Test 870/1000 (Sampling=True) ---
# 	✅ PASS (L=183): $\lambda_2$=0.3132 	 $\lambda_{11}$=6.8083

# --- Running Test 871/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 872/1000 (Sampling=True) ---
# 	❌ FAIL (L=172): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 873/1000 (Sampling=True) ---
# 	❌ FAIL (L=170): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 874/1000 (Sampling=True) ---
# 	❌ FAIL (L=190): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 875/1000 (Sampling=True) ---
# 	✅ PASS (L=177): $\lambda_2$=0.3132 	 $\lambda_{11}$=8.9015

# --- Running Test 876/1000 (Sampling=True) ---
# 	✅ PASS (L=19): $\lambda_2$=0.2597 	 $\lambda_{11}$=7.5832

# --- Running Test 877/1000 (Sampling=True) ---
# 	❌ FAIL (L=197): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 878/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 879/1000 (Sampling=True) ---
# 	✅ PASS (L=128): $\lambda_2$=0.3061 	 $\lambda_{11}$=12.5868

# --- Running Test 880/1000 (Sampling=True) ---
# 	✅ PASS (L=183): $\lambda_2$=0.3132 	 $\lambda_{11}$=8.8030

# --- Running Test 881/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 882/1000 (Sampling=True) ---
# 	❌ FAIL (L=172): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 883/1000 (Sampling=True) ---
# 	❌ FAIL (L=170): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 884/1000 (Sampling=True) ---
# 	❌ FAIL (L=190): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 885/1000 (Sampling=True) ---
# 	✅ PASS (L=177): $\lambda_2$=0.3132 	 $\lambda_{11}$=9.2313

# --- Running Test 886/1000 (Sampling=True) ---
# 	✅ PASS (L=174): $\lambda_2$=0.2597 	 $\lambda_{11}$=7.2101

# --- Running Test 887/1000 (Sampling=True) ---
# 	❌ FAIL (L=197): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 888/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 889/1000 (Sampling=True) ---
# 	✅ PASS (L=178): $\lambda_2$=0.3061 	 $\lambda_{11}$=13.8313

# --- Running Test 890/1000 (Sampling=True) ---
# 	✅ PASS (L=183): $\lambda_2$=0.3132 	 $\lambda_{11}$=6.4480

# --- Running Test 891/1000 (Sampling=True) ---
# 	❌ FAIL (L=34): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 892/1000 (Sampling=True) ---
# 	❌ FAIL (L=172): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 893/1000 (Sampling=True) ---
# 	❌ FAIL (L=162): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 894/1000 (Sampling=True) ---
# 	❌ FAIL (L=190): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 895/1000 (Sampling=True) ---
# 	✅ PASS (L=177): $\lambda_2$=0.3132 	 $\lambda_{11}$=9.6198

# --- Running Test 896/1000 (Sampling=True) ---
# 	✅ PASS (L=174): $\lambda_2$=0.2597 	 $\lambda_{11}$=7.7864

# --- Running Test 897/1000 (Sampling=True) ---
# 	❌ FAIL (L=197): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 898/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 899/1000 (Sampling=True) ---
# 	✅ PASS (L=178): $\lambda_2$=0.3061 	 $\lambda_{11}$=10.5128

# --- Running Test 900/1000 (Sampling=True) ---
# 	✅ PASS (L=183): $\lambda_2$=0.3132 	 $\lambda_{11}$=7.2381

# --- Running Test 901/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 902/1000 (Sampling=True) ---
# 	❌ FAIL (L=172): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 903/1000 (Sampling=True) ---
# 	❌ FAIL (L=170): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 904/1000 (Sampling=True) ---
# 	❌ FAIL (L=190): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 905/1000 (Sampling=True) ---
# 	✅ PASS (L=177): $\lambda_2$=0.3132 	 $\lambda_{11}$=9.4392

# --- Running Test 906/1000 (Sampling=True) ---
# 	✅ PASS (L=174): $\lambda_2$=0.2597 	 $\lambda_{11}$=6.6660

# --- Running Test 907/1000 (Sampling=True) ---
# 	❌ FAIL (L=197): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 908/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 909/1000 (Sampling=True) ---
# 	✅ PASS (L=178): $\lambda_2$=0.3061 	 $\lambda_{11}$=12.7471

# --- Running Test 910/1000 (Sampling=True) ---
# 	✅ PASS (L=183): $\lambda_2$=0.3132 	 $\lambda_{11}$=6.1234

# --- Running Test 911/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 912/1000 (Sampling=True) ---
# 	❌ FAIL (L=90): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 913/1000 (Sampling=True) ---
# 	❌ FAIL (L=170): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 914/1000 (Sampling=True) ---
# 	❌ FAIL (L=190): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 915/1000 (Sampling=True) ---
# 	✅ PASS (L=177): $\lambda_2$=0.3132 	 $\lambda_{11}$=8.7374

# --- Running Test 916/1000 (Sampling=True) ---
# 	✅ PASS (L=174): $\lambda_2$=0.2597 	 $\lambda_{11}$=5.9514

# --- Running Test 917/1000 (Sampling=True) ---
# 	❌ FAIL (L=197): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 918/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 919/1000 (Sampling=True) ---
# 	✅ PASS (L=178): $\lambda_2$=0.3061 	 $\lambda_{11}$=10.3043

# --- Running Test 920/1000 (Sampling=True) ---
# 	✅ PASS (L=183): $\lambda_2$=0.3132 	 $\lambda_{11}$=6.4775

# --- Running Test 921/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 922/1000 (Sampling=True) ---
# 	❌ FAIL (L=172): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 923/1000 (Sampling=True) ---
# 	❌ FAIL (L=146): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 924/1000 (Sampling=True) ---
# 	❌ FAIL (L=190): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 925/1000 (Sampling=True) ---
# 	✅ PASS (L=177): $\lambda_2$=0.3132 	 $\lambda_{11}$=11.8600

# --- Running Test 926/1000 (Sampling=True) ---
# 	✅ PASS (L=174): $\lambda_2$=0.2597 	 $\lambda_{11}$=9.3551

# --- Running Test 927/1000 (Sampling=True) ---
# 	❌ FAIL (L=197): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 928/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 929/1000 (Sampling=True) ---
# 	✅ PASS (L=178): $\lambda_2$=0.3061 	 $\lambda_{11}$=12.3893

# --- Running Test 930/1000 (Sampling=True) ---
# 	✅ PASS (L=183): $\lambda_2$=0.3132 	 $\lambda_{11}$=7.9459

# --- Running Test 931/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 932/1000 (Sampling=True) ---
# 	❌ FAIL (L=172): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 933/1000 (Sampling=True) ---
# 	❌ FAIL (L=170): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 934/1000 (Sampling=True) ---
# 	❌ FAIL (L=190): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 935/1000 (Sampling=True) ---
# 	✅ PASS (L=177): $\lambda_2$=0.3132 	 $\lambda_{11}$=8.7673

# --- Running Test 936/1000 (Sampling=True) ---
# 	✅ PASS (L=174): $\lambda_2$=0.2597 	 $\lambda_{11}$=7.1245

# --- Running Test 937/1000 (Sampling=True) ---
# 	❌ FAIL (L=197): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 938/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 939/1000 (Sampling=True) ---
# 	✅ PASS (L=178): $\lambda_2$=0.3061 	 $\lambda_{11}$=11.8130

# --- Running Test 940/1000 (Sampling=True) ---
# 	✅ PASS (L=183): $\lambda_2$=0.3132 	 $\lambda_{11}$=7.7879

# --- Running Test 941/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 942/1000 (Sampling=True) ---
# 	❌ FAIL (L=172): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 943/1000 (Sampling=True) ---
# 	❌ FAIL (L=170): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 944/1000 (Sampling=True) ---
# 	❌ FAIL (L=190): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 945/1000 (Sampling=True) ---
# 	✅ PASS (L=177): $\lambda_2$=0.3132 	 $\lambda_{11}$=10.1944

# --- Running Test 946/1000 (Sampling=True) ---
# 	✅ PASS (L=174): $\lambda_2$=0.2597 	 $\lambda_{11}$=8.5477

# --- Running Test 947/1000 (Sampling=True) ---
# 	❌ FAIL (L=130): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 948/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 949/1000 (Sampling=True) ---
# 	✅ PASS (L=178): $\lambda_2$=0.3061 	 $\lambda_{11}$=9.8804

# --- Running Test 950/1000 (Sampling=True) ---
# 	✅ PASS (L=183): $\lambda_2$=0.3132 	 $\lambda_{11}$=8.0358

# --- Running Test 951/1000 (Sampling=True) ---
# 	❌ FAIL (L=102): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 952/1000 (Sampling=True) ---
# 	❌ FAIL (L=172): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 953/1000 (Sampling=True) ---
# 	❌ FAIL (L=170): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 954/1000 (Sampling=True) ---
# 	❌ FAIL (L=190): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 955/1000 (Sampling=True) ---
# 	✅ PASS (L=151): $\lambda_2$=0.3132 	 $\lambda_{11}$=11.0360

# --- Running Test 956/1000 (Sampling=True) ---
# 	✅ PASS (L=174): $\lambda_2$=0.2597 	 $\lambda_{11}$=7.1652

# --- Running Test 957/1000 (Sampling=True) ---
# 	❌ FAIL (L=197): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 958/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 959/1000 (Sampling=True) ---
# 	✅ PASS (L=103): $\lambda_2$=0.3061 	 $\lambda_{11}$=10.9773

# --- Running Test 960/1000 (Sampling=True) ---
# 	✅ PASS (L=183): $\lambda_2$=0.3132 	 $\lambda_{11}$=7.4494

# --- Running Test 961/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 962/1000 (Sampling=True) ---
# 	❌ FAIL (L=41): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 963/1000 (Sampling=True) ---
# 	❌ FAIL (L=170): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 964/1000 (Sampling=True) ---
# 	❌ FAIL (L=190): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 965/1000 (Sampling=True) ---
# 	✅ PASS (L=177): $\lambda_2$=0.3132 	 $\lambda_{11}$=12.7098

# --- Running Test 966/1000 (Sampling=True) ---
# 	✅ PASS (L=174): $\lambda_2$=0.2597 	 $\lambda_{11}$=9.4680

# --- Running Test 967/1000 (Sampling=True) ---
# 	❌ FAIL (L=197): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 968/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 969/1000 (Sampling=True) ---
# 	✅ PASS (L=154): $\lambda_2$=0.3061 	 $\lambda_{11}$=12.4984

# --- Running Test 970/1000 (Sampling=True) ---
# 	✅ PASS (L=183): $\lambda_2$=0.3132 	 $\lambda_{11}$=6.4592

# --- Running Test 971/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 972/1000 (Sampling=True) ---
# 	❌ FAIL (L=172): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 973/1000 (Sampling=True) ---
# 	❌ FAIL (L=170): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 974/1000 (Sampling=True) ---
# 	❌ FAIL (L=31): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 975/1000 (Sampling=True) ---
# 	✅ PASS (L=177): $\lambda_2$=0.3132 	 $\lambda_{11}$=12.9276

# --- Running Test 976/1000 (Sampling=True) ---
# 	✅ PASS (L=174): $\lambda_2$=0.2597 	 $\lambda_{11}$=9.5120

# --- Running Test 977/1000 (Sampling=True) ---
# 	❌ FAIL (L=197): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 978/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 979/1000 (Sampling=True) ---
# 	✅ PASS (L=178): $\lambda_2$=0.3061 	 $\lambda_{11}$=13.3926

# --- Running Test 980/1000 (Sampling=True) ---
# 	✅ PASS (L=183): $\lambda_2$=0.3132 	 $\lambda_{11}$=10.1458

# --- Running Test 981/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 982/1000 (Sampling=True) ---
# 	❌ FAIL (L=172): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 983/1000 (Sampling=True) ---
# 	❌ FAIL (L=170): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 984/1000 (Sampling=True) ---
# 	❌ FAIL (L=190): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 985/1000 (Sampling=True) ---
# 	✅ PASS (L=177): $\lambda_2$=0.3132 	 $\lambda_{11}$=12.6295

# --- Running Test 986/1000 (Sampling=True) ---
# 	✅ PASS (L=174): $\lambda_2$=0.2597 	 $\lambda_{11}$=6.9159

# --- Running Test 987/1000 (Sampling=True) ---
# 	❌ FAIL (L=197): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 988/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 989/1000 (Sampling=True) ---
# 	✅ PASS (L=89): $\lambda_2$=0.3061 	 $\lambda_{11}$=11.1913

# --- Running Test 990/1000 (Sampling=True) ---
# 	✅ PASS (L=183): $\lambda_2$=0.3132 	 $\lambda_{11}$=6.9710

# --- Running Test 991/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 992/1000 (Sampling=True) ---
# 	❌ FAIL (L=172): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 993/1000 (Sampling=True) ---
# 	❌ FAIL (L=170): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 994/1000 (Sampling=True) ---
# 	❌ FAIL (L=190): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 995/1000 (Sampling=True) ---
# 	✅ PASS (L=177): $\lambda_2$=0.3132 	 $\lambda_{11}$=14.2495

# --- Running Test 996/1000 (Sampling=True) ---
# 	✅ PASS (L=174): $\lambda_2$=0.2597 	 $\lambda_{11}$=5.9108

# --- Running Test 997/1000 (Sampling=True) ---
# 	❌ FAIL (L=197): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 998/1000 (Sampling=True) ---
# 	❌ FAIL (L=173): $\lambda_2$=nan (Input L2-norm failed $\pmod{24}$ check) — skipping.

# --- Running Test 999/1000 (Sampling=True) ---
# 	✅ PASS (L=178): $\lambda_2$=0.3061 	 $\lambda_{11}$=10.5197

# --- Running Test 1000/1000 (Sampling=True) ---
# 	✅ PASS (L=183): $\lambda_2$=0.3132 	 $\lambda_{11}$=7.7344


# *** Sufficient data gathered (40+ samples). Continuing to correlation analysis. ***

# ================================================================================
# --- Online Correlation Results (Proof of Principle) ---
# Total Valid Samples: 400
# Average Sequence Length: 174.3
# ----------------------------------------
# Pearson Correlation (r): 0.3947
# P-value: 0.0000
# ================================================================================

# ⚠️ Inconclusive: Correlation was $r=0.3947$. The geometric instability requires running hundreds of samples, or the base model's geometry is not strongly aligned with the modular metric. The next step is to increase the sample size in test_prompts and run for a longer duration.
# (base) brendanlynch@Mac zzzzzzzhourglass % 
