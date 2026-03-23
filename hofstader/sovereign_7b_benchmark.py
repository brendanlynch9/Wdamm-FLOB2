import torch
import torch.nn as nn
import math
import json
import lm_eval
from lm_eval.models.huggingface import HFLM
from lm_eval.utils import make_table
from transformers import AutoModelForCausalLM, AutoTokenizer

# Force clear VRAM
torch.cuda.empty_cache()

class SovereignTransformer(nn.Module):
    def __init__(self, model_id="Qwen/Qwen2.5-7B-Instruct"):
        super().__init__()
        print(f"\n--- [UFT-F] Initializing Sovereign Kernel (7B Cloud Scale) ---")
        
        self.base_model = AutoModelForCausalLM.from_pretrained(
            model_id, 
            torch_dtype=torch.bfloat16,
            device_map="auto",
            trust_remote_code=True
        )
        self.config = self.base_model.config
        self.dim = self.config.hidden_size
        self.device = self.base_model.device
        
        # UFT-F Constants
        self.omega_u = 0.0002073 
        self.lambda_0 = 15.04545
        
        # Generate and register PMNS
        pmns_matrix = self._generate_pmns(self.dim)
        self.register_buffer('pmns', pmns_matrix.to(dtype=torch.bfloat16))

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
        angle = self.omega_u * t
        cos_a, sin_a = math.cos(angle), math.sin(angle)
        
        x_rot = x.clone()
        x0 = x[..., 0::2]
        x1 = x[..., 1::2]
        x_rot[..., 0::2] = x0 * cos_a - x1 * sin_a
        x_rot[..., 1::2] = x0 * sin_a + x1 * cos_a
        
        norm = torch.norm(x_rot, p=1, dim=-1, keepdim=True)
        scale = torch.where(norm > self.lambda_0, self.lambda_0 / (norm + 1e-6), torch.ones_like(norm))
        
        # FINAL PROTECTION: Dynamically ensure device match
        pmns_enforced = self.pmns.to(device=x.device, dtype=x.dtype)
        return torch.matmul(x_rot * scale, pmns_enforced)

    def forward(self, input_ids, **kwargs):
        outputs = self.base_model(input_ids, output_hidden_states=True, **kwargs)
        hidden_states = outputs.hidden_states[-1] 
        regulated_hidden = self.sovereign_gate(hidden_states, input_ids.shape[1])
        return self.base_model.lm_head(regulated_hidden)

class SovereignEvalWrapper(HFLM):
    def __init__(self, model_id="Qwen/Qwen2.5-7B-Instruct"):
        self.sovereign_kernel = SovereignTransformer(model_id=model_id)
        self.sovereign_kernel.eval()
        tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True)
        super().__init__(
            pretrained=self.sovereign_kernel.base_model,
            tokenizer=tokenizer,
            batch_size=1, # SAFE BATCH SIZE
            device="cuda"
        )

    def _model_call(self, inps):
        with torch.no_grad():
            return self.sovereign_kernel(inps)

if __name__ == "__main__":
    TARGET_MODEL = "Qwen/Qwen2.5-7B-Instruct"
    tasks = ["mmlu", "gsm8k", "hellaswag", "arc_challenge"]
    model_wrapper = SovereignEvalWrapper(model_id=TARGET_MODEL)

    print(f"\n--- [UFT-F] STARTING BENCHMARK (Batch Size 1) ---")
    results = lm_eval.simple_evaluate(
        model=model_wrapper,
        tasks=tasks,
        num_fewshot=5, 
        batch_size=1 # MATCHED SAFE BATCH SIZE
    )

    print("\n" + "="*60)
    print(make_table(results))
    
    with open("sovereign_7b_results.json", "w") as f:
        json.dump(results["results"], f, indent=4)



#         root@7b997a8a19de:/workspace# pkill -9 python
# root@7b997a8a19de:/workspace# nvidia-smi
# Sat Jan 17 23:07:55 2026       
# +-----------------------------------------------------------------------------------------+
# | NVIDIA-SMI 550.127.05             Driver Version: 550.127.05     CUDA Version: 12.4     |
# |-----------------------------------------+------------------------+----------------------+
# | GPU  Name                 Persistence-M | Bus-Id          Disp.A | Volatile Uncorr. ECC |
# | Fan  Temp   Perf          Pwr:Usage/Cap |           Memory-Usage | GPU-Util  Compute M. |
# |                                         |                        |               MIG M. |
# |=========================================+========================+======================|
# |   0  NVIDIA A100 80GB PCIe          On  |   00000000:C1:00.0 Off |                    0 |
# | N/A   29C    P0             44W /  300W |       1MiB /  81920MiB |      0%      Default |
# |                                         |                        |             Disabled |
# +-----------------------------------------+------------------------+----------------------+
                                                                                         
# +-----------------------------------------------------------------------------------------+
# | Processes:                                                                              |
# |  GPU   GI   CI        PID   Type   Process name                              GPU Memory |
# |        ID   ID                                                               Usage      |
# |=========================================================================================|
# |  No running processes found                                                             |
# +-----------------------------------------------------------------------------------------+
# root@7b997a8a19de:/workspace# python sovereign_7b_benchmark.p
# python: can't open file '/workspace/sovereign_7b_benchmark.p': [Errno 2] No such file or directory
# root@7b997a8a19de:/workspace# python sovereign_7b_benchmark.py

# --- [UFT-F] Initializing Sovereign Kernel (7B Cloud Scale) ---
# `torch_dtype` is deprecated! Use `dtype` instead!
# Loading checkpoint shards: 100%|██████████████████████| 4/4 [00:02<00:00,  1.83it/s]
# `pretrained` model kwarg is not of type `str`. Many other model arguments may be ignored. Please do not launch via accelerate or use `parallelize=True` if passing an existing model this way.
# Passed an already-initialized model through `pretrained`, assuming single-process call to evaluate() or custom distributed integration

# --- [UFT-F] STARTING BENCHMARK (Batch Size 1) ---
# Overwriting default num_fewshot of arc_challenge from None to 5
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
# 100%|██████████████████████████████████████████| 1172/1172 [00:05<00:00, 204.52it/s]
# 100%|████████████████████████████████████████| 10042/10042 [00:23<00:00, 430.02it/s]
# 100%|██████████████████████████████████████████| 1319/1319 [00:03<00:00, 409.20it/s]
# 100%|████████████████████████████████████████████| 100/100 [00:00<00:00, 219.59it/s]
# 100%|████████████████████████████████████████████| 135/135 [00:00<00:00, 219.14it/s]
# 100%|████████████████████████████████████████████| 152/152 [00:00<00:00, 221.14it/s]
# 100%|████████████████████████████████████████████| 144/144 [00:00<00:00, 220.42it/s]
# 100%|████████████████████████████████████████████| 100/100 [00:00<00:00, 218.97it/s]
# 100%|████████████████████████████████████████████| 100/100 [00:00<00:00, 223.09it/s]
# 100%|████████████████████████████████████████████| 100/100 [00:00<00:00, 223.56it/s]
# 100%|████████████████████████████████████████████| 102/102 [00:00<00:00, 220.87it/s]
# 100%|████████████████████████████████████████████| 100/100 [00:00<00:00, 218.79it/s]
# 100%|████████████████████████████████████████████| 235/235 [00:01<00:00, 222.84it/s]
# 100%|████████████████████████████████████████████| 145/145 [00:00<00:00, 223.15it/s]
# 100%|████████████████████████████████████████████| 378/378 [00:01<00:00, 222.83it/s]
# 100%|████████████████████████████████████████████| 310/310 [00:01<00:00, 222.84it/s]
# 100%|████████████████████████████████████████████| 203/203 [00:00<00:00, 222.79it/s]
# 100%|████████████████████████████████████████████| 100/100 [00:00<00:00, 222.04it/s]
# 100%|████████████████████████████████████████████| 270/270 [00:01<00:00, 222.50it/s]
# 100%|████████████████████████████████████████████| 151/151 [00:00<00:00, 219.33it/s]
# 100%|████████████████████████████████████████████| 216/216 [00:00<00:00, 216.56it/s]
# 100%|████████████████████████████████████████████| 112/112 [00:00<00:00, 219.30it/s]
# 100%|████████████████████████████████████████████| 100/100 [00:00<00:00, 218.46it/s]
# 100%|████████████████████████████████████████████| 265/265 [00:01<00:00, 221.85it/s]
# 100%|████████████████████████████████████████████| 173/173 [00:00<00:00, 222.44it/s]
# 100%|████████████████████████████████████████████| 100/100 [00:00<00:00, 223.22it/s]
# 100%|████████████████████████████████████████████| 223/223 [00:01<00:00, 220.19it/s]
# 100%|████████████████████████████████████████████| 103/103 [00:00<00:00, 223.31it/s]
# 100%|████████████████████████████████████████████| 234/234 [00:01<00:00, 224.11it/s]
# 100%|████████████████████████████████████████████| 100/100 [00:00<00:00, 219.75it/s]
# 100%|████████████████████████████████████████████| 783/783 [00:03<00:00, 201.42it/s]
# 100%|████████████████████████████████████████████| 306/306 [00:01<00:00, 219.79it/s]
# 100%|████████████████████████████████████████████| 282/282 [00:01<00:00, 220.49it/s]
# 100%|████████████████████████████████████████████| 272/272 [00:01<00:00, 221.38it/s]
# 100%|████████████████████████████████████████████| 166/166 [00:00<00:00, 222.42it/s]
# 100%|████████████████████████████████████████████| 114/114 [00:00<00:00, 222.48it/s]
# 100%|████████████████████████████████████████████| 198/198 [00:00<00:00, 222.46it/s]
# 100%|████████████████████████████████████████████| 193/193 [00:00<00:00, 221.61it/s]
# 100%|████████████████████████████████████████████| 390/390 [00:01<00:00, 223.19it/s]
# 100%|████████████████████████████████████████████| 238/238 [00:01<00:00, 222.65it/s]
# 100%|████████████████████████████████████████████| 545/545 [00:02<00:00, 221.40it/s]
# 100%|████████████████████████████████████████████| 131/131 [00:00<00:00, 220.76it/s]
# 100%|████████████████████████████████████████████| 612/612 [00:02<00:00, 218.44it/s]
# 100%|████████████████████████████████████████████| 110/110 [00:00<00:00, 220.34it/s]
# 100%|████████████████████████████████████████████| 245/245 [00:01<00:00, 221.74it/s]
# 100%|████████████████████████████████████████████| 201/201 [00:00<00:00, 221.89it/s]
# 100%|████████████████████████████████████████████| 100/100 [00:00<00:00, 222.96it/s]
# 100%|████████████████████████████████████████████| 126/126 [00:00<00:00, 221.71it/s]
# 100%|████████████████████████████████████████████| 165/165 [00:00<00:00, 218.95it/s]
# 100%|████████████████████████████████████████████| 204/204 [00:00<00:00, 220.72it/s]
# 100%|████████████████████████████████████████████| 237/237 [00:01<00:00, 219.81it/s]
# 100%|████████████████████████████████████████████| 121/121 [00:00<00:00, 220.59it/s]
# 100%|████████████████████████████████████████████| 108/108 [00:00<00:00, 223.08it/s]
# 100%|████████████████████████████████████████████| 163/163 [00:00<00:00, 219.52it/s]
# 100%|████████████████████████████████████████████| 346/346 [00:01<00:00, 221.22it/s]
# 100%|████████████████████████████████████████████| 895/895 [00:04<00:00, 219.29it/s]
# 100%|████████████████████████████████████████████| 311/311 [00:01<00:00, 218.37it/s]
# 100%|████████████████████████████████████████████| 324/324 [00:01<00:00, 217.48it/s]
# 100%|██████████████████████████████████████████| 1534/1534 [00:06<00:00, 220.21it/s]
# 100%|████████████████████████████████████████████| 171/171 [00:00<00:00, 223.37it/s]
# Running loglikelihood requests: 100%|███████| 101023/101023 [56:07<00:00, 30.00it/s]
# Running generate_until requests:   0%|                     | 0/1319 [00:00<?, ?it/s]The following generation flags are not valid and may be ignored: ['temperature', 'top_p', 'top_k']. Set `TRANSFORMERS_VERBOSITY=info` for more details.

# Running generate_until requests: 100%|████████| 1319/1319 [1:26:46<00:00,  3.95s/it]
# fatal: not a git repository (or any parent up to mount point /)
# Stopping at filesystem boundary (GIT_DISCOVERY_ACROSS_FILESYSTEM not set).

# ============================================================
# |                 Tasks                 |Version|     Filter     |n-shot|  Metric   |   |Value |   |Stderr|
# |---------------------------------------|------:|----------------|-----:|-----------|---|-----:|---|-----:|
# |arc_challenge                          |      1|none            |     5|acc        |↑  |0.2415|±  |0.0125|
# |                                       |       |none            |     5|acc_norm   |↑  |0.2722|±  |0.0130|
# |gsm8k                                  |      3|flexible-extract|     5|exact_match|↑  |0.8241|±  |0.0105|
# |                                       |       |strict-match    |     5|exact_match|↑  |0.7635|±  |0.0117|
# |hellaswag                              |      1|none            |     5|acc        |↑  |0.2546|±  |0.0043|
# |                                       |       |none            |     5|acc_norm   |↑  |0.2642|±  |0.0044|
# |mmlu                                   |      2|none            |      |acc        |↑  |0.5749|±  |0.0040|
# | - humanities                          |      2|none            |      |acc        |↑  |0.4837|±  |0.0071|
# |  - formal_logic                       |      1|none            |     5|acc        |↑  |0.4365|±  |0.0444|
# |  - high_school_european_history       |      1|none            |     5|acc        |↑  |0.2182|±  |0.0323|
# |  - high_school_us_history             |      1|none            |     5|acc        |↑  |0.4608|±  |0.0350|
# |  - high_school_world_history          |      1|none            |     5|acc        |↑  |0.6414|±  |0.0312|
# |  - international_law                  |      1|none            |     5|acc        |↑  |0.7438|±  |0.0398|
# |  - jurisprudence                      |      1|none            |     5|acc        |↑  |0.6667|±  |0.0456|
# |  - logical_fallacies                  |      1|none            |     5|acc        |↑  |0.6380|±  |0.0378|
# |  - moral_disputes                     |      1|none            |     5|acc        |↑  |0.5636|±  |0.0267|
# |  - moral_scenarios                    |      1|none            |     5|acc        |↑  |0.3743|±  |0.0162|
# |  - philosophy                         |      1|none            |     5|acc        |↑  |0.4952|±  |0.0284|
# |  - prehistory                         |      1|none            |     5|acc        |↑  |0.6975|±  |0.0256|
# |  - professional_law                   |      1|none            |     5|acc        |↑  |0.4224|±  |0.0126|
# |  - world_religions                    |      1|none            |     5|acc        |↑  |0.6725|±  |0.0360|
# | - other                               |      2|none            |      |acc        |↑  |0.6257|±  |0.0084|
# |  - business_ethics                    |      1|none            |     5|acc        |↑  |0.6000|±  |0.0492|
# |  - clinical_knowledge                 |      1|none            |     5|acc        |↑  |0.6642|±  |0.0291|
# |  - college_medicine                   |      1|none            |     5|acc        |↑  |0.5954|±  |0.0374|
# |  - global_facts                       |      1|none            |     5|acc        |↑  |0.2600|±  |0.0441|
# |  - human_aging                        |      1|none            |     5|acc        |↑  |0.5964|±  |0.0329|
# |  - management                         |      1|none            |     5|acc        |↑  |0.5049|±  |0.0495|
# |  - marketing                          |      1|none            |     5|acc        |↑  |0.7393|±  |0.0288|
# |  - medical_genetics                   |      1|none            |     5|acc        |↑  |0.7700|±  |0.0423|
# |  - miscellaneous                      |      1|none            |     5|acc        |↑  |0.7318|±  |0.0158|
# |  - nutrition                          |      1|none            |     5|acc        |↑  |0.6797|±  |0.0267|
# |  - professional_accounting            |      1|none            |     5|acc        |↑  |0.4255|±  |0.0295|
# |  - professional_medicine              |      1|none            |     5|acc        |↑  |0.6360|±  |0.0292|
# |  - virology                           |      1|none            |     5|acc        |↑  |0.4217|±  |0.0384|
# | - social sciences                     |      2|none            |      |acc        |↑  |0.6753|±  |0.0083|
# |  - econometrics                       |      1|none            |     5|acc        |↑  |0.5877|±  |0.0463|
# |  - high_school_geography              |      1|none            |     5|acc        |↑  |0.7222|±  |0.0319|
# |  - high_school_government_and_politics|      1|none            |     5|acc        |↑  |0.6891|±  |0.0334|
# |  - high_school_macroeconomics         |      1|none            |     5|acc        |↑  |0.5538|±  |0.0252|
# |  - high_school_microeconomics         |      1|none            |     5|acc        |↑  |0.7731|±  |0.0272|
# |  - high_school_psychology             |      1|none            |     5|acc        |↑  |0.7688|±  |0.0181|
# |  - human_sexuality                    |      1|none            |     5|acc        |↑  |0.7023|±  |0.0401|
# |  - professional_psychology            |      1|none            |     5|acc        |↑  |0.6503|±  |0.0193|
# |  - public_relations                   |      1|none            |     5|acc        |↑  |0.5364|±  |0.0478|
# |  - security_studies                   |      1|none            |     5|acc        |↑  |0.6816|±  |0.0298|
# |  - sociology                          |      1|none            |     5|acc        |↑  |0.6269|±  |0.0342|
# |  - us_foreign_policy                  |      1|none            |     5|acc        |↑  |0.7400|±  |0.0441|
# | - stem                                |      2|none            |      |acc        |↑  |0.5630|±  |0.0086|
# |  - abstract_algebra                   |      1|none            |     5|acc        |↑  |0.3200|±  |0.0469|
# |  - anatomy                            |      1|none            |     5|acc        |↑  |0.5704|±  |0.0428|
# |  - astronomy                          |      1|none            |     5|acc        |↑  |0.7368|±  |0.0358|
# |  - college_biology                    |      1|none            |     5|acc        |↑  |0.6944|±  |0.0385|
# |  - college_chemistry                  |      1|none            |     5|acc        |↑  |0.4100|±  |0.0494|
# |  - college_computer_science           |      1|none            |     5|acc        |↑  |0.6200|±  |0.0488|
# |  - college_mathematics                |      1|none            |     5|acc        |↑  |0.4200|±  |0.0496|
# |  - college_physics                    |      1|none            |     5|acc        |↑  |0.4314|±  |0.0493|
# |  - computer_security                  |      1|none            |     5|acc        |↑  |0.7500|±  |0.0435|
# |  - conceptual_physics                 |      1|none            |     5|acc        |↑  |0.5830|±  |0.0322|
# |  - electrical_engineering             |      1|none            |     5|acc        |↑  |0.5448|±  |0.0415|
# |  - elementary_mathematics             |      1|none            |     5|acc        |↑  |0.5608|±  |0.0256|
# |  - high_school_biology                |      1|none            |     5|acc        |↑  |0.7000|±  |0.0261|
# |  - high_school_chemistry              |      1|none            |     5|acc        |↑  |0.5369|±  |0.0351|
# |  - high_school_computer_science       |      1|none            |     5|acc        |↑  |0.7200|±  |0.0451|
# |  - high_school_mathematics            |      1|none            |     5|acc        |↑  |0.3407|±  |0.0289|
# |  - high_school_physics                |      1|none            |     5|acc        |↑  |0.5430|±  |0.0407|
# |  - high_school_statistics             |      1|none            |     5|acc        |↑  |0.6343|±  |0.0328|
# |  - machine_learning                   |      1|none            |     5|acc        |↑  |0.4732|±  |0.0474|

# root@7b997a8a19de:/workspace# 