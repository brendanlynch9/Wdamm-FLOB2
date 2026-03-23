#!/usr/bin/env python3
import subprocess, sys, json, os
FIXED_KAPPAS = [1.0, 0.9, 0.8, 0.7, 0.6, 0.5]
results = []
for k in FIXED_KAPPAS:
    print('Running fixed kappa=', k)
    cmd = [sys.executable, 'spectral_gate_FINAL_MLP_V2.py', '--eval_limit', '5', '--seed', '42']
    # We pass an env var to tell the script to use fixed kappa via simple monkey patch
    env = os.environ.copy()
    env['FIXED_KAPPA'] = str(k)
    p = subprocess.run(cmd, env=env, capture_output=True, text=True)
    print(p.stdout)
    results.append({'kappa': k, 'stdout': p.stdout})
# Save JSON
with open('ablation_results.json', 'w') as f:
    json.dump(results, f, indent=2)
print('Ablation run complete, results saved to ablation_results.json')
