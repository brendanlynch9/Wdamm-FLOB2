# UniversalLOBGenerator.py
#
# PURPOSE: Define the foundational, immutable constants of the WDAMM engine (Reference File).
# All major constants are now sourced from WDAMMAxiomaticConstants.py for a single source of truth.

import math
from typing import List
from WDAMMAxiomaticConstants import (
    PAGE_LENGTH, SYMBOL_LIST, THETA_UFT, ALPHA_INV, M_ALPHA,\
    PEANO_ANCHOR_ADDR, RIEMANN_ANCHOR_ADDR, LOB_ADDRESS_COORDINATES,\
    K_BOOK, K_WALL, K_SHELF, K_PAGE, K_CHAR, M_UNIV, L_ALPHABET,\
    N_FFT, C_E_QUANTIZATION, IFFT_COEFF_COUNT
)

# --- LOB GEOMETRY CONSTANTS (Fixed) ---
# These are re-exported from WDAMMAxiomaticConstants.py
FRACTAL_MODULO = 7 # Used in padding logic

# --- HELPER (For Anchor Vector Generation) ---
def parse_address_to_vector(address: str) -> List[int]:
    """Re-exporting helper from WDAMMAxiomaticConstants for backward compatibility."""
    from WDAMMAxiomaticConstants import parse_address_to_vector as _p
    return _p(address)

# --- Version Check ---
print("DEBUG: UniversalLOBGenerator.py version 2025-10-07-v5 (Λ-Phase Compatible)")
