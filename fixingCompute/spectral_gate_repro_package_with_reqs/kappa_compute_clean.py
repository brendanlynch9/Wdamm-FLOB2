import numpy as np
import torch

PRIMES = np.array([5, 7, 11, 13, 17], dtype=int)
UNITS = np.array([1, 5, 7, 11, 13, 17, 19, 23], dtype=int)
MOD = 24

def build_weighted_A_for_n(n):
    m = len(UNITS)
    A = np.zeros((m, m), dtype=float)
    for i in range(m):
        for j in range(m):
            if i == j:
                continue
            r1, r2 = int(UNITS[i]), int(UNITS[j])
            dist = sum(1 for p in PRIMES if (r1 * r2) % p != (n % p))
            A[i, j] = 1.0 / (1.0 + dist)
    A = (A + A.T) / 2.0
    np.fill_diagonal(A, 0.0)
    return A

def precompute_lambda2_table(mod=24):
    lambda2s = []
    laplacians = []
    for n in range(mod):
        A = build_weighted_A_for_n(n)
        D = np.diag(A.sum(axis=1))
        L = D - A
        vals = np.linalg.eigvalsh(L)
        lambda2 = float(vals[1]) if vals.shape[0] > 1 else 0.0
        lambda2s.append(lambda2)
        laplacians.append(L)
    lambda2s = np.array(lambda2s, dtype=float)
    return lambda2s, laplacians

LAMBDA2_TABLE, LAPLACIANS = precompute_lambda2_table(MOD)
L2_MIN = float(LAMBDA2_TABLE.min())
L2_MAX = float(LAMBDA2_TABLE.max())
if np.isclose(L2_MAX, L2_MIN):
    L2_MAX = L2_MIN + 1e-12

def kappa_x_from_token_ids(token_ids):
    # token_ids: list or numpy array or torch Tensor of token ids
    if isinstance(token_ids, torch.Tensor):
        token_ids = token_ids.cpu().numpy()
    x = np.asarray(token_ids, dtype=float)
    norm_floor = int(np.floor(np.linalg.norm(x)))
    n = norm_floor % MOD
    lam = float(LAMBDA2_TABLE[n])
    kappa = (lam - L2_MIN) / (L2_MAX - L2_MIN)
    kappa = float(min(max(kappa, 0.0), 1.0))
    return kappa, n, lam

if __name__ == '__main__':
    import numpy as _np
    rng = _np.random.default_rng(42)
    print('demo random:', kappa_x_from_token_ids(rng.integers(0,32000,size=512)))
    print('demo zeros :', kappa_x_from_token_ids([0]*512))
    print('demo arange:', kappa_x_from_token_ids(list(range(512))))
