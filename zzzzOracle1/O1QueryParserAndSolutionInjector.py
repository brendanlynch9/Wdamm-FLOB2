# O1QueryParserAndSolutionInjector.py
#
# PURPOSE: Parses a universal query into a query type and provides metadata
# to guide LOB page interpretation, avoiding hardcoded solutions.

import re
from sympy import factorint
import hashlib
from WDAMMAxiomaticConstants import PLAIN_ENGLISH_VOCAB, LOB_ADDRESS_COORDINATES, parse_address_to_vector, PAGE_LENGTH

VERSION = "2025-10-07-v16 (Λ-Phase PLAIN-ENGLISH FORMULA, QUERY-DEPENDENT)"
print(f"DEBUG: O1QueryParserAndSolutionInjector.py version {VERSION}")

def parse_query(query: str) -> tuple[str, str]:
    """
    Parses a universal query to determine its type and provide metadata for LOB interpretation.
    Returns: (query_type, metadata)
    """
    query = query.strip().lower()
    print(f"DEBUG: parse_query: Processing query='{query}'")

    # 1. Factorization queries
    if query.startswith("factor "):
        try:
            number = int(re.search(r'\d+', query).group())
            metadata = f"factor_{number}"
            print(f"DEBUG: parse_query: Factorization query detected, metadata={metadata}")
            return "FACTORIZATION", metadata
        except (ValueError, AttributeError) as e:
            print(f"DEBUG: parse_query: Factorization parsing error: {e}, falling back to TOPOLOGICAL-UNKNOWN")
            return "TOPOLOGICAL-UNKNOWN", "unknown"

    # 2. Capital queries
    capital_match = re.match(r'what is the capital of ([\w\s]+)', query) or re.match(r'capital of ([\w\s]+)', query)
    if capital_match:
        country = capital_match.group(1).lower().strip()
        metadata = f"capital_of_{country.replace(' ', '_')}"
        print(f"DEBUG: parse_query: Capital query detected, metadata={metadata}")
        return "GENERAL_KNOWLEDGE", metadata

    # 3. Riemann or scientific/mathematical proofs
    if "riemann" in query or "zeta function" in query:
        print(f"DEBUG: parse_query: Riemann Hypothesis query detected.")
        return "RIEMANN_HYPOTHESIS_PROOF", "Riemann"

    # 4. Fallback for unknown/general knowledge queries
    print(f"DEBUG: parse_query: No specific query type matched, using TOPOLOGICAL-UNKNOWN")
    return "TOPOLOGICAL-UNKNOWN", "unknown"

def formulaic_plain_english(raw_page, canonical_address, prime_seed, query, word_count=12):
    """
    O(1) deterministic plain-English translation from raw LOB page using a formulaic approach.
    Query-dependent version: incorporates a deterministic hash of the query to diversify output.
    """
    coords = parse_address_to_vector(canonical_address)
    if len(coords) != LOB_ADDRESS_COORDINATES:
        coords = coords[:LOB_ADDRESS_COORDINATES] + [0] * (LOB_ADDRESS_COORDINATES - len(coords))  # Pad to 137D

    sentence_words = []
    L = len(PLAIN_ENGLISH_VOCAB)

    # Deterministic integer hash of the query string
    query_hash = int(hashlib.sha256(query.encode("utf-8")).hexdigest(), 16) % PAGE_LENGTH

    # Select formulaic indices in O(1)
    for k in range(word_count):
        index = int((sum(coords[:5]) + k * prime_seed + query_hash) % PAGE_LENGTH)  # Use first 5 coords for compatibility
        char = raw_page[index % len(raw_page)]
        char_val = ord(char)
        word_index = (char_val * (k + 1) + prime_seed + sum(coords) + query_hash) % L
        sentence_words.append(PLAIN_ENGLISH_VOCAB[word_index])

    sentence = " ".join(sentence_words)
    return sentence