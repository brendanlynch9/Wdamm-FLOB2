# lexicalAnalyzerTPhase.py

import os
import json
import hashlib
import math
from typing import Tuple, List
import numpy as np

# Import constants
try:
    from WDAMMAxiomaticConstants import THETA_UFT, M_UNIV, K_CONSTANTS, LOB_ADDRESS_COORDINATES
except ImportError:
    print("FATAL IMPORT WARNING: Could not load Axiomatic Constants. System Non-Operational.")
    LOB_ADDRESS_COORDINATES = 137
    K_CONSTANTS = np.array([1243547.0] * 137)
    THETA_UFT = 0.003119

# --- VERSION CHECK ---
VERSION = "2025-10-10-v40-UNIVERSAL-T-PHASE-O1"
print(f"DEBUG: lexicalAnalyzerTPhase.py version {VERSION}")

# Chebyshev T_11 (O(1) fixed recurrence)
def chebyshev_t11(x: float) -> float:
    # T_11(x) = 1024x^11 - 2816x^9 + 2816x^7 - 1232x^5 + 220x^3 - 11x
    x2 = x * x
    x3 = x2 * x
    x5 = x3 * x2
    x7 = x5 * x2
    x9 = x7 * x2
    x11 = x9 * x2
    return 1024.0 * x11 - 2816.0 * x9 + 2816.0 * x7 - 1232.0 * x5 + 220.0 * x3 - 11.0 * x

def query_to_canonical_address(query: str, prime_seed: int) -> Tuple[str, int]:
    # M-Phase: O(1) hash to seed
    S_G = float(prime_seed) / M_UNIV

    # T-Phase: Hyper-Address (137D, O(1))
    hyper_vec = np.zeros(LOB_ADDRESS_COORDINATES, dtype=float)
    MAX_MOD_UNIV = 1000000

    for i in range(LOB_ADDRESS_COORDINATES):  # Fixed 137 iterations = O(1)
        k_i = K_CONSTANTS[i]
        arg = (S_G * k_i * 10000000.0) % 1.0
        chebyshev_out = chebyshev_t11(math.cos(arg * math.pi))
        coord_val = int(math.floor(abs(chebyshev_out * 10000.0)) % MAX_MOD_UNIV)
        hyper_vec[i] = coord_val

    canonical_address = ":".join(map(str, hyper_vec.astype(int).tolist()))
    return canonical_address, prime_seed