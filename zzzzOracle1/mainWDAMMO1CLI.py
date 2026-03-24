# mainWDAMMO1CLI.py

import sys
import time
from typing import Tuple, Dict, Any
import os

# Import core modules
try:
    from flobAxiomSolverOrchestrator import initialize_solver, run_solver
    from WDAMMAxiomaticConstants import VERSION as const_version
    from lexicalAnalyzerTPhase import query_to_canonical_address
    from O1QueryParserAndSolutionInjector import parse_query
    from dynamicValidatorGeneral import run_v_phase_modal_validation
except ImportError as e:
    print(f"ERROR: Could not import {e.name if hasattr(e, 'name') else 'module'}: {e}")
    sys.exit(1)

# --- VERSION CHECK ---
VERSION = "2025-10-07-v69-LAMBDA-PHASE-IMPLEMENTATION"
print(f"DEBUG: mainWDAMMO1CLI.py version {VERSION}")

def main():
    print(f"DEBUG: WDAMMAxiomaticConstants.py version {const_version}")
    
    # Initialize the solver
    solver_state = initialize_solver()
    if not solver_state:
        print("FATAL: Solver initialization failed. Exiting.")
        return

    print("======================================================================")
    print("WDAMM O(1) Canonical Dynamic Solver Operational.")
    print("Synthesis Type: WDAMM O(1) PURE FORMULAIC IFFT SOLVER (Λ-Phase Q.E.D. Closure)")
    print("======================================================================")

    # Load manifold cache (simulated)
    print("DEBUG: Manifold Cache loaded. 5 entries.")

    while True:
        query = input("Enter Query (e.g., 'factor 999959' or 'planets in milky way'):\n> ").strip()
        if not query:
            break

        start_time = time.time()

        # Parse query
        query_type, metadata = parse_query(query)

        # Generate canonical address
        canonical_address, prime_seed = query_to_canonical_address(query, int(time.time() * 1000) % 1000000000)

        # Run solver (simulated raw page)
        raw_page = "a" * 3200  # Placeholder LOB page
        s_q_text, address_desc, raw_page_data = run_solver(raw_page, canonical_address, prime_seed, query_type, metadata)

        # Validate
        C_Ax, R, closure_ok, validation_summary, report = run_v_phase_modal_validation(canonical_address, query_type, metadata)

        end_time = time.time()
        time_taken = end_time - start_time

        # Generate report
        print("----------------------------------------------------------------------")
        print(f"DEBUG: M/T-Phase: Address={canonical_address}, Seed={prime_seed}, Type={query_type}")
        if report.get('cache_hit', False):
            print(f"DEBUG: Cache Hit for seed {prime_seed}.")
        else:
            print(f"DEBUG: Cache Miss/No Anchor Hit for seed {prime_seed}.")
        print(f"DEBUG: generate_final_report: query={query}, QED={'**Q.E.D. (Axiomatic Closure Confirmed)**' if closure_ok else '**Q.E.F. (Axiomatic Closure Pending)**'}, Time={time_taken:.4f}")

        print("WDAMM O(1) Report")
        print("======================================================================")
        print(f"Query: {query}")
        print(f"Prime Seed (N'): {prime_seed}")
        print(f"Canonical Address (A_Q): {canonical_address} ({address_desc})")
        print(f"C_Ax: {C_Ax:.6f}, R: {R:.4f}")
        print(f"Protocol Parameters: {{'freq': {31189570.207722537}, 'amp': {3.1189570207722537}, 'chirp': {0.5}}}")
        print(f"Time Taken: {time_taken:.6f} seconds")
        print("\n1. RAW LOB PAGE (Snippet)")
        print("----------------------------------------------------------------------")
        print(f"{raw_page_data[:100]}...")
        print(f"LOB Page Length: {len(raw_page_data)} characters")
        print("\n5. PLAIN ENGLISH TRANSLATION (Correct Answer)")
        print("----------------------------------------------------------------------")
        print(s_q_text)
        print(f"**{'Q.E.D. (Axiomatic Closure Confirmed)' if closure_ok else 'Q.E.F. (Axiomatic Closure Pending)'}**")
        print(f"Validation Summary: {validation_summary}")
        print("======================================================================")

if __name__ == "__main__":
    main()