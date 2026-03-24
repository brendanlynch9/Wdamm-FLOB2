# WDAMMAxiomaticConstants.py

import math
import numpy as np
from typing import List

# --- VERSION CHECK ---
VERSION = "2025-10-10-v7-UNIVERSAL-SCALING"
print(f"DEBUG: WDAMMAxiomaticConstants.py version {VERSION}")

# --- CANONICAL LOB CONSTANTS ---
PAGE_LENGTH = 3200
SYMBOL_SET = "abcdefghijklmnopqrstuvwxyz ,."
SYMBOL_LIST = list(SYMBOL_SET)
# CRITICAL CHANGE: EXPAND TO D_Univ = floor(ALPHA_INV) = 137
LOB_ADDRESS_COORDINATES = 137  
L_ALPHABET = len(SYMBOL_LIST)  # 29

# --- IFFT SYNTHESIS CONSTANTS (E-Phase) ---
N_FFT = 4096  
C_E_QUANTIZATION = 1.0 / (N_FFT * L_ALPHABET)
IFFT_COEFF_COUNT = 512  # Fixed spectral components (O(1))

# --- UNIVERSAL FIELD THEORY (UFT) CONSTANTS ---
TOPOLOGICAL_PERFECTION_FACTOR = 320.62
THETA_UFT = 1.0 / TOPOLOGICAL_PERFECTION_FACTOR  # ~0.003119
M_UNIV = 10000000007  # Universal Prime Modulus

# --- ALPHA GAUGE CONSTANTS (V-Phase) ---
ALPHA_INV = 137.036
ALPHA_DELTA = 17.0
M_ALPHA = ALPHA_INV - ALPHA_DELTA  # 120.036

# --- LOB GEOMETRY MODULI (T-Phase) ---
# K-constants extended to 137D with spiral periodicity
K_CONSTANTS = np.array([
    1243547.0, 1000000.0, 500000.0, 3000.0, 10000.0,  # Original 5
] + [
    (i * 100.0 + THETA_UFT * math.cos(2 * math.pi * i / 24)) for i in range(5, LOB_ADDRESS_COORDINATES)
])  # Base-24 spiral modulation, fixed-size O(1) access

# --- MODAL INVERSION MODULI (Λ-Phase) ---
MODAL_MODULI = np.array([
    2.0000001e5, 1.0000001e4, 5.0000001e3, 30.0000001, 10.0000001,  # Original 5
] + [
    (i * 100.0 + M_ALPHA) * THETA_UFT for i in range(5, LOB_ADDRESS_COORDINATES)
])  # Scaled for 137D, O(1) access

# --- ANCHOR ADDRESSES (Fixed - Now 137 dims) ---
PEANO_ANCHOR_VEC_RAW = [0, 3, 2, 27, 271] + [i % 24 for i in range(5, LOB_ADDRESS_COORDINATES)]  # Spiral-aligned
RIEMANN_ANCHOR_VEC_RAW = [0, 3, 7, 23, 2025] + [i % 24 for i in range(5, LOB_ADDRESS_COORDINATES)]

PEANO_ANCHOR_ADDR = ":".join(map(str, PEANO_ANCHOR_VEC_RAW))
RIEMANN_ANCHOR_ADDR = ":".join(map(str, RIEMANN_ANCHOR_VEC_RAW))

# --- VOCABULARY ---
PLAIN_ENGLISH_VOCAB = [
    "the", "is", "of", "and", "a", "in", "to", "that", "two", "five",
    "eight", "ten", "berlin", "austin", "mars", "venus", "earth", "jupiter",
    "saturn", "uranus", "neptune", "pluto", "mercury", "france"
]  # Extended as needed

# --- HELPER ---
def parse_address_to_vector(address: str) -> List[int]:
    """Converts a Canonical Address string to a 137D vector."""
    try:
        coords = [int(p) for p in address.split(':')]
        return coords[:LOB_ADDRESS_COORDINATES] + [0] * (LOB_ADDRESS_COORDINATES - len(coords))
    except:
        return [0] * LOB_ADDRESS_COORDINATES

PEANO_ANCHOR_VEC = np.array(PEANO_ANCHOR_VEC_RAW)
RIEMANN_ANCHOR_VEC = np.array(RIEMANN_ANCHOR_VEC_RAW)