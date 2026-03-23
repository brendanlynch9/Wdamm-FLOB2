# tune_alpha_beta.py
import random, json, numpy as np
from spectral_graphs import build_G_angular_corrected, build_G_residue_corrected, algebraic_connectivity
from scipy.stats import spearmanr

random.seed(0)
np.random.seed(0)

NUM_SAMPLES = 2000
TOKEN_LEN = 16

def gen_samples(num):
    samples = []
    for _ in range(num):
        tokens = [random.randint(1,1000) for _ in range(TOKEN_LEN)]
        x = np.array(tokens, dtype=float)
        n = int(np.floor(np.linalg.norm(x)**2)) % 24
        # synthetic internal proxy: use variance or later replace with real lambda11 per input
        proxy = 1.0 / (1.0 + np.var(x))
        samples.append((tokens, n, proxy))
    return samples

samples = gen_samples(NUM_SAMPLES)

betas = [0.5, 1.0, 2.0]
alphas = [0.2, 0.6, 1.0]

results = {"angular": {}, "residue": {}}

for b in betas:
    lam2s = []
    proxies = []
    for tokens, n, proxy in samples:
        G = build_G_angular_corrected(n, beta=b)
        lam2 = algebraic_connectivity(G)
        lam2s.append(lam2); proxies.append(proxy)
    r, p = spearmanr(lam2s, proxies)
    results["angular"][str(b)] = {"spearman_r": float(r), "p": float(p), "lam2_std": float(np.std(lam2s))}

for a in alphas:
    lam2s = []
    proxies = []
    for tokens, n, proxy in samples:
        G = build_G_residue_corrected(n, alpha=a)
        lam2 = algebraic_connectivity(G)
        lam2s.append(lam2); proxies.append(proxy)
    r, p = spearmanr(lam2s, proxies)
    results["residue"][str(a)] = {"spearman_r": float(r), "p": float(p), "lam2_std": float(np.std(lam2s))}

print(json.dumps(results, indent=2))
