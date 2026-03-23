# Spectral Gate Experiments: The Redundancy Cliff (TinyLlama-1.1B)

This reproducibility package contains code and artifacts used to run the PoC experiments described in the manuscript.

## Contents
- `spectral_gate_FINAL_MLP_V2.py` : Main dynamic gating script (safe guards + CLI).
- `spectral_gate_ABLATON_STUDY.py` : Ablation runner (calls the main script with fixed kappa values).
- `kappa_compute_clean.py` : Spectral gate computation (λ2 table and helper).
- `test_patch_signature.py` : Small unit test that ensures `kappa_x` kwarg is accepted.
- `requirements.txt` : Template of dependencies (fill exact versions from your environment).
- `LICENSE` : MIT license for code.
- `run_smoke.sh` : Quick smoke test script.

## Quick smoke test (recommended)
1. Create a python environment and install required packages (fill versions in requirements.txt).
   ```bash
   conda create -n spectral python=3.10 -y
   conda activate spectral
   pip install -r requirements.txt
   ```
2. Run the smoke test (one chunk only):
   ```bash
   bash run_smoke.sh
   ```
3. Full run (example):
   ```bash
   python spectral_gate_FINAL_MLP_V2.py --eval_limit 15
   ```

## Notes and Caveats
- This repository **does not** include TinyLlama weights. Models are loaded via Hugging Face model references. Do not redistribute model weights.
- Replace the placeholder versions in `requirements.txt` with the exact versions from your environment (e.g., `pip freeze > reqs.txt`).
- For reproducible statistics, run each experiment multiple times (3-5) with different RNG seeds and report mean±std.
- The monkey-patching approach is fragile across `transformers` releases; the unit test helps detect API changes.

