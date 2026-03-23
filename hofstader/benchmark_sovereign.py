import torch
import torch.nn as nn
import math
import lm_eval
from lm_eval.models.huggingface import HFLM
from lm_eval.utils import make_table
from transformers import AutoModelForCausalLM, AutoTokenizer

# --- Part 1: The Sovereign Kernel (wrapper.py logic) ---
class SovereignTransformer(nn.Module):
    def __init__(self, model_id="Qwen/Qwen2.5-0.5B-Instruct"):
        super().__init__()
        print(f"\n--- [UFT-F] Initializing Sovereign Kernel (Safe Mode) ---")
        
        self.base_model = AutoModelForCausalLM.from_pretrained(
            model_id, 
            output_hidden_states=True,
            trust_remote_code=True
        )
        self.config = self.base_model.config
        self.dim = self.config.hidden_size
        
        # UFT-F Constants
        self.omega_u = 0.0002073 
        self.lambda_0 = 15.04545  # The Lynch Truncation Ceiling
        
        # PMNS Bridge
        self.register_buffer('pmns', self._generate_pmns(self.dim))

    def _generate_pmns(self, dim):
        th12, th23, th13 = map(math.radians, [33.8, 49.0, 8.6])
        s12, c12, s23, c23, s13, c13 = math.sin(th12), math.cos(th12), math.sin(th23), math.cos(th23), math.sin(th13), math.cos(th13)
        U = torch.tensor([
            [c12*c13, s12*c13, s13],
            [-s12*c23 - c12*s23*s13, c12*c23 - s12*s23*s13, s23*c13],
            [s12*s23 - c12*c23*s13, -c12*s23 - s12*c23*s13, c23*c13]
        ], dtype=torch.float32)
        repeats = (dim // 3) + 1
        return torch.block_diag(*([U] * repeats))[:dim, :dim]

    def sovereign_gate(self, x, t):
        # Hopf Torsion
        angle = self.omega_u * t
        cos_a, sin_a = math.cos(angle), math.sin(angle)
        x_rot = x.clone()
        x_rot[..., 0::2] = x[..., 0::2] * cos_a - x[..., 1::2] * sin_a
        x_rot[..., 1::2] = x[..., 0::2] * sin_a + x[..., 1::2] * cos_a
        
        # ACI Spectral Truncation (Prevents the "Strange Loop" crash)
        norm = torch.norm(x_rot, p=1, dim=-1, keepdim=True)
        scale = torch.where(norm > self.lambda_0, self.lambda_0 / (norm + 1e-6), torch.ones_like(norm))
        return torch.matmul(x_rot * scale, self.pmns)

    def forward(self, input_ids, **kwargs):
        outputs = self.base_model(input_ids, output_hidden_states=True, **kwargs)
        hidden_states = outputs.hidden_states[-1] 
        regulated_hidden = self.sovereign_gate(hidden_states, input_ids.shape[1])
        return self.base_model.lm_head(regulated_hidden)

# --- Part 2: The Harness Bridge ---
class SovereignEvalWrapper(HFLM):
    def __init__(self, model_id="Qwen/Qwen2.5-0.5B-Instruct"):
        self.sovereign_kernel = SovereignTransformer(model_id=model_id)
        self.sovereign_kernel.eval()
        tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True)

        super().__init__(
            pretrained=self.sovereign_kernel.base_model,
            tokenizer=tokenizer,
            batch_size=1, # FIXED TO 1 FOR STABILITY
            device="cuda" if torch.cuda.is_available() else "cpu"
        )

    def _model_call(self, inps):
        with torch.no_grad():
            return self.sovereign_kernel(inps)

# --- Part 3: Execution ---
if __name__ == "__main__":
    TARGET_MODEL = "Qwen/Qwen2.5-0.5B-Instruct"
    model_wrapper = SovereignEvalWrapper(model_id=TARGET_MODEL)

    # Core AGI tasks
    tasks = ["mmlu", "gsm8k", "hellaswag"]

    print(f"--- [UFT-F] Starting Safe-Mode Benchmark: {tasks} ---")
    
    results = lm_eval.simple_evaluate(
        model=model_wrapper,
        tasks=tasks,
        num_fewshot=5, 
        batch_size=8 # Hard-coded to prevent laptop memory overflow
    )

    print("\n" + "="*50)
    print("FINAL SOVEREIGN RESULTS (0.5B KERNEL)")
    print("="*50)
    print(make_table(results))

#    (base) brendanlynch@Brendans-Laptop lm-evaluation-harness % python ../benchmark_sovereign.py

# --- [UFT-F] Initializing Sovereign Kernel (Safe Mode) ---
# /Users/brendanlynch/miniconda3/lib/python3.12/site-packages/huggingface_hub/file_download.py:942: FutureWarning: `resume_download` is deprecated and will be removed in version 1.0.0. Downloads always resume when possible. If you want to force a new download, use `force_download=True`.
#   warnings.warn(
# Special tokens have been added in the vocabulary, make sure the associated word embeddings are fine-tuned or trained.
# `pretrained` model kwarg is not of type `str`. Many other model arguments may be ignored. Please do not launch via accelerate or use `parallelize=True` if passing an existing model this way.
# Passed an already-initialized model through `pretrained`, assuming single-process call to evaluate() or custom distributed integration
# --- [UFT-F] Starting Safe-Mode Benchmark: ['mmlu', 'gsm8k', 'hellaswag'] ---
# Overwriting default num_fewshot of hellaswag from None to 5
# Overwriting default num_fewshot of gsm8k from 5 to 5
# Overwriting default num_fewshot of mmlu_abstract_algebra from None to 5
# Overwriting default num_fewshot of mmlu_anatomy from None to 5
# Overwriting default num_fewshot of mmlu_astronomy from None to 5
# Overwriting default num_fewshot of mmlu_college_biology from None to 5
# Overwriting default num_fewshot of mmlu_college_chemistry from None to 5
# Overwriting default num_fewshot of mmlu_college_computer_science from None to 5
# Overwriting default num_fewshot of mmlu_college_mathematics from None to 5
# Overwriting default num_fewshot of mmlu_college_physics from None to 5
# Overwriting default num_fewshot of mmlu_computer_security from None to 5
# Overwriting default num_fewshot of mmlu_conceptual_physics from None to 5
# Overwriting default num_fewshot of mmlu_electrical_engineering from None to 5
# Overwriting default num_fewshot of mmlu_elementary_mathematics from None to 5
# Overwriting default num_fewshot of mmlu_high_school_biology from None to 5
# Overwriting default num_fewshot of mmlu_high_school_chemistry from None to 5
# Overwriting default num_fewshot of mmlu_high_school_computer_science from None to 5
# Overwriting default num_fewshot of mmlu_high_school_mathematics from None to 5
# Overwriting default num_fewshot of mmlu_high_school_physics from None to 5
# Overwriting default num_fewshot of mmlu_high_school_statistics from None to 5
# Overwriting default num_fewshot of mmlu_machine_learning from None to 5
# Overwriting default num_fewshot of mmlu_business_ethics from None to 5
# Overwriting default num_fewshot of mmlu_clinical_knowledge from None to 5
# Overwriting default num_fewshot of mmlu_college_medicine from None to 5
# Overwriting default num_fewshot of mmlu_global_facts from None to 5
# Overwriting default num_fewshot of mmlu_human_aging from None to 5
# Overwriting default num_fewshot of mmlu_management from None to 5
# Overwriting default num_fewshot of mmlu_marketing from None to 5
# Overwriting default num_fewshot of mmlu_medical_genetics from None to 5
# Overwriting default num_fewshot of mmlu_miscellaneous from None to 5
# Overwriting default num_fewshot of mmlu_nutrition from None to 5
# Overwriting default num_fewshot of mmlu_professional_accounting from None to 5
# Overwriting default num_fewshot of mmlu_professional_medicine from None to 5
# Overwriting default num_fewshot of mmlu_virology from None to 5
# Overwriting default num_fewshot of mmlu_econometrics from None to 5
# Overwriting default num_fewshot of mmlu_high_school_geography from None to 5
# Overwriting default num_fewshot of mmlu_high_school_government_and_politics from None to 5
# Overwriting default num_fewshot of mmlu_high_school_macroeconomics from None to 5
# Overwriting default num_fewshot of mmlu_high_school_microeconomics from None to 5
# Overwriting default num_fewshot of mmlu_high_school_psychology from None to 5
# Overwriting default num_fewshot of mmlu_human_sexuality from None to 5
# Overwriting default num_fewshot of mmlu_professional_psychology from None to 5
# Overwriting default num_fewshot of mmlu_public_relations from None to 5
# Overwriting default num_fewshot of mmlu_security_studies from None to 5
# Overwriting default num_fewshot of mmlu_sociology from None to 5
# Overwriting default num_fewshot of mmlu_us_foreign_policy from None to 5
# Overwriting default num_fewshot of mmlu_formal_logic from None to 5
# Overwriting default num_fewshot of mmlu_high_school_european_history from None to 5
# Overwriting default num_fewshot of mmlu_high_school_us_history from None to 5
# Overwriting default num_fewshot of mmlu_high_school_world_history from None to 5
# Overwriting default num_fewshot of mmlu_international_law from None to 5
# Overwriting default num_fewshot of mmlu_jurisprudence from None to 5
# Overwriting default num_fewshot of mmlu_logical_fallacies from None to 5
# Overwriting default num_fewshot of mmlu_moral_disputes from None to 5
# Overwriting default num_fewshot of mmlu_moral_scenarios from None to 5
# Overwriting default num_fewshot of mmlu_philosophy from None to 5
# Overwriting default num_fewshot of mmlu_prehistory from None to 5
# Overwriting default num_fewshot of mmlu_professional_law from None to 5
# Overwriting default num_fewshot of mmlu_world_religions from None to 5
# 100%|████████████████████████████████████| 10042/10042 [00:14<00:00, 710.05it/s]
# 100%|██████████████████████████████████████| 1319/1319 [00:01<00:00, 672.50it/s]
# 100%|████████████████████████████████████████| 100/100 [00:00<00:00, 362.95it/s]
# 100%|████████████████████████████████████████| 135/135 [00:00<00:00, 373.11it/s]
# 100%|████████████████████████████████████████| 152/152 [00:00<00:00, 369.99it/s]
# 100%|████████████████████████████████████████| 144/144 [00:00<00:00, 371.87it/s]
# 100%|████████████████████████████████████████| 100/100 [00:00<00:00, 371.98it/s]
# 100%|████████████████████████████████████████| 100/100 [00:00<00:00, 369.72it/s]
# 100%|████████████████████████████████████████| 100/100 [00:00<00:00, 371.40it/s]
# 100%|████████████████████████████████████████| 102/102 [00:00<00:00, 373.42it/s]
# 100%|████████████████████████████████████████| 100/100 [00:00<00:00, 372.89it/s]
# 100%|████████████████████████████████████████| 235/235 [00:00<00:00, 379.59it/s]
# 100%|████████████████████████████████████████| 145/145 [00:00<00:00, 258.94it/s]
# 100%|████████████████████████████████████████| 378/378 [00:01<00:00, 373.09it/s]
# 100%|████████████████████████████████████████| 310/310 [00:00<00:00, 368.33it/s]
# 100%|████████████████████████████████████████| 203/203 [00:00<00:00, 372.60it/s]
# 100%|████████████████████████████████████████| 100/100 [00:00<00:00, 367.84it/s]
# 100%|████████████████████████████████████████| 270/270 [00:00<00:00, 368.46it/s]
# 100%|████████████████████████████████████████| 151/151 [00:00<00:00, 373.00it/s]
# 100%|████████████████████████████████████████| 216/216 [00:00<00:00, 372.40it/s]
# 100%|████████████████████████████████████████| 112/112 [00:00<00:00, 370.29it/s]
# 100%|████████████████████████████████████████| 100/100 [00:00<00:00, 370.71it/s]
# 100%|████████████████████████████████████████| 265/265 [00:00<00:00, 370.94it/s]
# 100%|████████████████████████████████████████| 173/173 [00:00<00:00, 370.20it/s]
# 100%|████████████████████████████████████████| 100/100 [00:00<00:00, 359.83it/s]
# 100%|████████████████████████████████████████| 223/223 [00:00<00:00, 368.54it/s]
# 100%|████████████████████████████████████████| 103/103 [00:00<00:00, 366.62it/s]
# 100%|████████████████████████████████████████| 234/234 [00:00<00:00, 373.88it/s]
# 100%|████████████████████████████████████████| 100/100 [00:00<00:00, 373.24it/s]
# 100%|████████████████████████████████████████| 783/783 [00:02<00:00, 369.19it/s]
# 100%|████████████████████████████████████████| 306/306 [00:00<00:00, 369.46it/s]
# 100%|████████████████████████████████████████| 282/282 [00:00<00:00, 366.27it/s]
# 100%|████████████████████████████████████████| 272/272 [00:00<00:00, 369.87it/s]
# 100%|████████████████████████████████████████| 166/166 [00:00<00:00, 370.28it/s]
# 100%|████████████████████████████████████████| 114/114 [00:00<00:00, 365.53it/s]
# 100%|████████████████████████████████████████| 198/198 [00:00<00:00, 371.22it/s]
# 100%|████████████████████████████████████████| 193/193 [00:00<00:00, 370.59it/s]
# 100%|████████████████████████████████████████| 390/390 [00:01<00:00, 369.97it/s]
# 100%|████████████████████████████████████████| 238/238 [00:00<00:00, 375.96it/s]
# 100%|████████████████████████████████████████| 545/545 [00:01<00:00, 368.61it/s]
# 100%|████████████████████████████████████████| 131/131 [00:00<00:00, 372.09it/s]
# 100%|████████████████████████████████████████| 612/612 [00:01<00:00, 372.11it/s]
# 100%|████████████████████████████████████████| 110/110 [00:00<00:00, 376.76it/s]
# 100%|████████████████████████████████████████| 245/245 [00:00<00:00, 378.66it/s]
# 100%|████████████████████████████████████████| 201/201 [00:00<00:00, 374.78it/s]
# 100%|████████████████████████████████████████| 100/100 [00:00<00:00, 373.92it/s]
# 100%|████████████████████████████████████████| 126/126 [00:00<00:00, 374.42it/s]
# 100%|████████████████████████████████████████| 165/165 [00:00<00:00, 377.74it/s]
# 100%|████████████████████████████████████████| 204/204 [00:00<00:00, 373.53it/s]
# 100%|████████████████████████████████████████| 237/237 [00:00<00:00, 373.95it/s]
# 100%|████████████████████████████████████████| 121/121 [00:00<00:00, 372.16it/s]
# 100%|████████████████████████████████████████| 108/108 [00:00<00:00, 376.87it/s]
# 100%|████████████████████████████████████████| 163/163 [00:00<00:00, 338.49it/s]
# 100%|████████████████████████████████████████| 346/346 [00:00<00:00, 372.46it/s]
# 100%|████████████████████████████████████████| 895/895 [00:02<00:00, 373.76it/s]
# 100%|████████████████████████████████████████| 311/311 [00:00<00:00, 375.45it/s]
# 100%|████████████████████████████████████████| 324/324 [00:00<00:00, 374.80it/s]
# 100%|██████████████████████████████████████| 1534/1534 [00:04<00:00, 355.97it/s]
# 100%|████████████████████████████████████████| 171/171 [00:00<00:00, 375.19it/s]
# Running loglikelihood requests:  32%|▎| 30562/96336 [4:47:55<3:39:53,  4.99it/s]Running loglikelihood requests: 100%|██| 96336/96336 [14:45:12<00:00,  1.81it/s]Running generate_until requests:   0%|                 | 0/1319 [00:00<?, ?it/s]/Users/brendanlynch/miniconda3/lib/python3.12/site-packages/transformers/generation/configuration_utils.py:492: UserWarning: `do_sample` is set to `False`. However, `temperature` is set to `0.7` -- this flag is only used in sample-based generation modes. You should set `do_sample=True` or unset `temperature`.
#   warnings.warn(
# /Users/brendanlynch/miniconda3/lib/python3.12/site-packages/transformers/generation/configuration_utils.py:497: UserWarning: `do_sample` is set to `False`. However, `top_p` is set to `0.8` -- this flag is only used in sample-based generation modes. You should set `do_sample=True` or unset `top_p`.
#   warnings.warn(
# /Users/brendanlynch/miniconda3/lib/python3.12/site-packages/transformers/generation/configuration_utils.py:509: UserWarning: `do_sample` is set to `False`. However, `top_k` is set to `20` -- this flag is only used in sample-based generation modes. You should set `do_sample=True` or unset `top_k`.
#   warnings.warn(
# Running generate_until requests: 100%|████| 1319/1319 [2:34:33<00:00,  7.03s/it]
# python(16144) MallocStackLogging: can't turn off malloc stack logging because it was not enabled.
# huggingface/tokenizers: The current process just got forked, after parallelism has already been used. Disabling parallelism to avoid deadlocks...
# To disable this warning, you can either:
# 	- Avoid using `tokenizers` before the fork if possible
# 	- Explicitly set the environment variable TOKENIZERS_PARALLELISM=(true | false)
# python(16146) MallocStackLogging: can't turn off malloc stack logging because it was not enabled.
# huggingface/tokenizers: The current process just got forked, after parallelism has already been used. Disabling parallelism to avoid deadlocks...
# To disable this warning, you can either:
# 	- Avoid using `tokenizers` before the fork if possible
# 	- Explicitly set the environment variable TOKENIZERS_PARALLELISM=(true | false)
# python(16147) MallocStackLogging: can't turn off malloc stack logging because it was not enabled.
# huggingface/tokenizers: The current process just got forked, after parallelism has already been used. Disabling parallelism to avoid deadlocks...
# To disable this warning, you can either:
# 	- Avoid using `tokenizers` before the fork if possible
# 	- Explicitly set the environment variable TOKENIZERS_PARALLELISM=(true | false)
# python(16148) MallocStackLogging: can't turn off malloc stack logging because it was not enabled.
# huggingface/tokenizers: The current process just got forked, after parallelism has already been used. Disabling parallelism to avoid deadlocks...
# To disable this warning, you can either:
# 	- Avoid using `tokenizers` before the fork if possible
# 	- Explicitly set the environment variable TOKENIZERS_PARALLELISM=(true | false)
# python(16149) MallocStackLogging: can't turn off malloc stack logging because it was not enabled.
# huggingface/tokenizers: The current process just got forked, after parallelism has already been used. Disabling parallelism to avoid deadlocks...
# To disable this warning, you can either:
# 	- Avoid using `tokenizers` before the fork if possible
# 	- Explicitly set the environment variable TOKENIZERS_PARALLELISM=(true | false)
# python(16150) MallocStackLogging: can't turn off malloc stack logging because it was not enabled.
# huggingface/tokenizers: The current process just got forked, after parallelism has already been used. Disabling parallelism to avoid deadlocks...
# To disable this warning, you can either:
# 	- Avoid using `tokenizers` before the fork if possible
# 	- Explicitly set the environment variable TOKENIZERS_PARALLELISM=(true | false)
# python(16155) MallocStackLogging: can't turn off malloc stack logging because it was not enabled.
# huggingface/tokenizers: The current process just got forked, after parallelism has already been used. Disabling parallelism to avoid deadlocks...
# To disable this warning, you can either:
# 	- Avoid using `tokenizers` before the fork if possible
# 	- Explicitly set the environment variable TOKENIZERS_PARALLELISM=(true | false)
# python(16156) MallocStackLogging: can't turn off malloc stack logging because it was not enabled.
# huggingface/tokenizers: The current process just got forked, after parallelism has already been used. Disabling parallelism to avoid deadlocks...
# To disable this warning, you can either:
# 	- Avoid using `tokenizers` before the fork if possible
# 	- Explicitly set the environment variable TOKENIZERS_PARALLELISM=(true | false)
# python(16157) MallocStackLogging: can't turn off malloc stack logging because it was not enabled.
# huggingface/tokenizers: The current process just got forked, after parallelism has already been used. Disabling parallelism to avoid deadlocks...
# To disable this warning, you can either:
# 	- Avoid using `tokenizers` before the fork if possible
# 	- Explicitly set the environment variable TOKENIZERS_PARALLELISM=(true | false)
# python(16158) MallocStackLogging: can't turn off malloc stack logging because it was not enabled.
# huggingface/tokenizers: The current process just got forked, after parallelism has already been used. Disabling parallelism to avoid deadlocks...
# To disable this warning, you can either:
# 	- Avoid using `tokenizers` before the fork if possible
# 	- Explicitly set the environment variable TOKENIZERS_PARALLELISM=(true | false)
# python(16159) MallocStackLogging: can't turn off malloc stack logging because it was not enabled.
# huggingface/tokenizers: The current process just got forked, after parallelism has already been used. Disabling parallelism to avoid deadlocks...
# To disable this warning, you can either:
# 	- Avoid using `tokenizers` before the fork if possible
# 	- Explicitly set the environment variable TOKENIZERS_PARALLELISM=(true | false)
# python(16160) MallocStackLogging: can't turn off malloc stack logging because it was not enabled.
# huggingface/tokenizers: The current process just got forked, after parallelism has already been used. Disabling parallelism to avoid deadlocks...
# To disable this warning, you can either:
# 	- Avoid using `tokenizers` before the fork if possible
# 	- Explicitly set the environment variable TOKENIZERS_PARALLELISM=(true | false)

# ==================================================
# FINAL SOVEREIGN RESULTS (0.5B KERNEL)
# ==================================================
# |                 Tasks                 |Version|     Filter     |n-shot|  Metric   |   |Value |   |Stderr|
# |---------------------------------------|------:|----------------|-----:|-----------|---|-----:|---|-----:|
# |gsm8k                                  |      3|flexible-extract|     5|exact_match|↑  |0.3252|±  |0.0129|
# |                                       |       |strict-match    |     5|exact_match|↑  |0.2070|±  |0.0112|
# |hellaswag                              |      1|none            |     5|acc        |↑  |0.2631|±  |0.0044|
# |                                       |       |none            |     5|acc_norm   |↑  |0.2643|±  |0.0044|
# |mmlu                                   |      2|none            |      |acc        |↑  |0.3578|±  |0.0040|
# | - humanities                          |      2|none            |      |acc        |↑  |0.3199|±  |0.0067|
# |  - formal_logic                       |      1|none            |     5|acc        |↑  |0.3413|±  |0.0424|
# |  - high_school_european_history       |      1|none            |     5|acc        |↑  |0.3879|±  |0.0380|
# |  - high_school_us_history             |      1|none            |     5|acc        |↑  |0.3284|±  |0.0330|
# |  - high_school_world_history          |      1|none            |     5|acc        |↑  |0.4810|±  |0.0325|
# |  - international_law                  |      1|none            |     5|acc        |↑  |0.3719|±  |0.0441|
# |  - jurisprudence                      |      1|none            |     5|acc        |↑  |0.4074|±  |0.0475|
# |  - logical_fallacies                  |      1|none            |     5|acc        |↑  |0.3497|±  |0.0375|
# |  - moral_disputes                     |      1|none            |     5|acc        |↑  |0.3728|±  |0.0260|
# |  - moral_scenarios                    |      1|none            |     5|acc        |↑  |0.2380|±  |0.0142|
# |  - philosophy                         |      1|none            |     5|acc        |↑  |0.3215|±  |0.0265|
# |  - prehistory                         |      1|none            |     5|acc        |↑  |0.3673|±  |0.0268|
# |  - professional_law                   |      1|none            |     5|acc        |↑  |0.2784|±  |0.0114|
# |  - world_religions                    |      1|none            |     5|acc        |↑  |0.4854|±  |0.0383|
# | - other                               |      2|none            |      |acc        |↑  |0.3869|±  |0.0086|
# |  - business_ethics                    |      1|none            |     5|acc        |↑  |0.4800|±  |0.0502|
# |  - clinical_knowledge                 |      1|none            |     5|acc        |↑  |0.4113|±  |0.0303|
# |  - college_medicine                   |      1|none            |     5|acc        |↑  |0.4046|±  |0.0374|
# |  - global_facts                       |      1|none            |     5|acc        |↑  |0.2200|±  |0.0416|
# |  - human_aging                        |      1|none            |     5|acc        |↑  |0.4081|±  |0.0330|
# |  - management                         |      1|none            |     5|acc        |↑  |0.4563|±  |0.0493|
# |  - marketing                          |      1|none            |     5|acc        |↑  |0.5427|±  |0.0326|
# |  - medical_genetics                   |      1|none            |     5|acc        |↑  |0.3800|±  |0.0488|
# |  - miscellaneous                      |      1|none            |     5|acc        |↑  |0.4125|±  |0.0176|
# |  - nutrition                          |      1|none            |     5|acc        |↑  |0.4150|±  |0.0282|
# |  - professional_accounting            |      1|none            |     5|acc        |↑  |0.2837|±  |0.0269|
# |  - professional_medicine              |      1|none            |     5|acc        |↑  |0.2279|±  |0.0255|
# |  - virology                           |      1|none            |     5|acc        |↑  |0.3494|±  |0.0371|
# | - social sciences                     |      2|none            |      |acc        |↑  |0.4153|±  |0.0088|
# |  - econometrics                       |      1|none            |     5|acc        |↑  |0.2456|±  |0.0405|
# |  - high_school_geography              |      1|none            |     5|acc        |↑  |0.4596|±  |0.0355|
# |  - high_school_government_and_politics|      1|none            |     5|acc        |↑  |0.4404|±  |0.0358|
# |  - high_school_macroeconomics         |      1|none            |     5|acc        |↑  |0.3718|±  |0.0245|
# |  - high_school_microeconomics         |      1|none            |     5|acc        |↑  |0.3782|±  |0.0315|
# |  - high_school_psychology             |      1|none            |     5|acc        |↑  |0.5046|±  |0.0214|
# |  - human_sexuality                    |      1|none            |     5|acc        |↑  |0.4962|±  |0.0439|
# |  - professional_psychology            |      1|none            |     5|acc        |↑  |0.3529|±  |0.0193|
# |  - public_relations                   |      1|none            |     5|acc        |↑  |0.3727|±  |0.0463|
# |  - security_studies                   |      1|none            |     5|acc        |↑  |0.3510|±  |0.0306|
# |  - sociology                          |      1|none            |     5|acc        |↑  |0.4925|±  |0.0354|
# |  - us_foreign_policy                  |      1|none            |     5|acc        |↑  |0.5700|±  |0.0498|
# | - stem                                |      2|none            |      |acc        |↑  |0.3295|±  |0.0084|
# |  - abstract_algebra                   |      1|none            |     5|acc        |↑  |0.2800|±  |0.0451|
# |  - anatomy                            |      1|none            |     5|acc        |↑  |0.3111|±  |0.0400|
# |  - astronomy                          |      1|none            |     5|acc        |↑  |0.3684|±  |0.0393|
# |  - college_biology                    |      1|none            |     5|acc        |↑  |0.3958|±  |0.0409|
# |  - college_chemistry                  |      1|none            |     5|acc        |↑  |0.3100|±  |0.0465|
# |  - college_computer_science           |      1|none            |     5|acc        |↑  |0.2600|±  |0.0441|
# |  - college_mathematics                |      1|none            |     5|acc        |↑  |0.3700|±  |0.0485|
# |  - college_physics                    |      1|none            |     5|acc        |↑  |0.2843|±  |0.0449|
# |  - computer_security                  |      1|none            |     5|acc        |↑  |0.4200|±  |0.0496|
# |  - conceptual_physics                 |      1|none            |     5|acc        |↑  |0.3617|±  |0.0314|
# |  - electrical_engineering             |      1|none            |     5|acc        |↑  |0.3379|±  |0.0394|
# |  - elementary_mathematics             |      1|none            |     5|acc        |↑  |0.3228|±  |0.0241|
# |  - high_school_biology                |      1|none            |     5|acc        |↑  |0.4000|±  |0.0279|
# |  - high_school_chemistry              |      1|none            |     5|acc        |↑  |0.2562|±  |0.0307|
# |  - high_school_computer_science       |      1|none            |     5|acc        |↑  |0.3200|±  |0.0469|
# |  - high_school_mathematics            |      1|none            |     5|acc        |↑  |0.3148|±  |0.0283|
# |  - high_school_physics                |      1|none            |     5|acc        |↑  |0.2583|±  |0.0357|
# |  - high_school_statistics             |      1|none            |     5|acc        |↑  |0.2824|±  |0.0307|
# |  - machine_learning                   |      1|none            |     5|acc        |↑  |0.3750|±  |0.0460|

# (base) brendanlynch@Brendans-Laptop lm-evaluation-harness % 
 