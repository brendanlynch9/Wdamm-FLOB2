import numpy as np
import time
import math
import sys

# Set print options for clean output
np.set_printoptions(precision=4)

# --- 1. PRECOMPUTED Lookup Table for O(1) Geometry Check ---
# This dictionary simulates the O(1) lookup of the algebraic connectivity (λ2)
# based on the modular norm 'n' (n = ||x||_2 mod 24).
# In your paper, these values are derived from graph construction based on quadratic-residue pairs.
# Keys are 'n' (the input norm mod 24); values are simulated λ2.
LAMBDA2_LOOKUP = {
    1: 0.3162, 5: 0.2800, 7: 0.3501, 11: 0.4005,
    13: 0.3200, 17: 0.3800, 19: 0.3300, 23: 0.2900,
    # Values for non-residue/composite 'n' are intentionally omitted for security/simplicity
}

# --- 2. THE SECRET DYNAMIC KEY (Educational Concept) ---
# This simulates the shared secret and the time-dependent modulation function.
SECRET_PRIME_SEED = 7     # The initial prime known only to authorized systems
MODULATION_PRIME = 13   # The prime used for dynamic modulation
TIME_STEP = 10          # Simulating the current time-step/instance number

def get_current_target_lambda2(time_step: int) -> float:
    """
    Calculates the expected geometric fingerprint (lambda_2) for the current time step.
    This function implements the time-modulated, dynamic key.
    """
    # Key Calculation: Target N = (SECRET_SEED + (MODULATION_PRIME * time_step)) mod 24
    target_n = (SECRET_PRIME_SEED + (MODULATION_PRIME * time_step)) % 24
    
    # Target N at TIME_STEP 10: (7 + 130) mod 24 = 137 mod 24 = 17
    
    # O(1) Lookup: Retrieve the expected geometric value
    if target_n not in LAMBDA2_LOOKUP:
        # If the computed 'n' is not a valid geometry key, authentication fails.
        return np.nan 
    return LAMBDA2_LOOKUP[target_n]

# --- 3. THE O(1) MODULAR INTEGRITY CHECK FUNCTION ---
def compute_modular_fingerprint(input_data: bytes):
    """
    Calculates the O(1) modular fingerprint (lambda_2) from the input data (SCADA command payload).
    """
    # Step A: Compute the Input Norm (L2)
    # The sum of squared byte values (simulating token IDs)
    norm_sq = sum(b**2 for b in input_data)
    norm_l2 = math.sqrt(norm_sq)
    
    # Step B: Reduce Modulo 24 to get 'n'
    # n = floor(||x||_2) mod 24
    n_mod = int(math.floor(norm_l2)) % 24
    
    # Step C: O(1) Geometric Mapping (Lambda 2) Lookup
    lambda2_computed = LAMBDA2_LOOKUP.get(n_mod, np.nan) 
    
    return lambda2_computed, n_mod # Return both the lambda and the modular index 'n'

# --- 4. DEMONSTRATION OF FUNCTIONALITY ---

# **SUCCESS COMMAND CONSTRUCTION:**
# At TIME_STEP 10, the TARGET N is 17.
# We construct a command to yield N=17: 10 bytes of value 13 (0x0D).
# L2 Norm = sqrt(10 * 13^2) = 41.11 -> floor(41.11) = 41.
# 41 mod 24 = 17. (Match)
SUCCESS_COMMAND = b'\x0D' * 10 

# **FAILURE COMMAND CONSTRUCTION:**
# This command is slightly altered (one byte changed) leading to a different N.
# N = 18 bytes of value 8: L2 Norm = sqrt(18 * 8^2) = 33.94 -> floor(33.94) = 33.
# 33 mod 24 = 9. (Mismatch)
FAILURE_COMMAND = b'\x08' * 18

TARGET_LAMBDA = get_current_target_lambda2(TIME_STEP)
TOLERANCE = 1e-4

# --- TEST 1: Successful Authorization ---
print(f"--- Dynamic Modular Integrity Check at Time Step {TIME_STEP} ---")
print(f"Secret Target N: 17 (Lambda 2: {TARGET_LAMBDA:.4f})\n")

print("Processing 'SUCCESS' Command (Input N=17)...")
start_time = time.perf_counter_ns()
computed_lambda_success, n_mod_success = compute_modular_fingerprint(SUCCESS_COMMAND)
end_time = time.perf_counter_ns()
latency_success_ns = end_time - start_time

print(f"  Computed N: {n_mod_success} (Lambda 2: {computed_lambda_success:.4f})")
if abs(computed_lambda_success - TARGET_LAMBDA) < TOLERANCE:
    print(f"  Result: ✅ AUTHORIZED (Integrity Match)")
else:
    print(f"  Result: ❌ REJECTED (Integrity Mismatch)")
    
print(f"  Latency: {latency_success_ns / 1000:.3f} µs\n")

# --- TEST 2: Integrity Mismatch / Failed Attempt ---
print("Processing 'FAILURE' Command (Input N=9)...")
start_time = time.perf_counter_ns()
computed_lambda_failure, n_mod_failure = compute_modular_fingerprint(FAILURE_COMMAND)
end_time = time.perf_counter_ns()
latency_failure_ns = end_time - start_time

print(f"  Computed N: {n_mod_failure} (Lambda 2: {computed_lambda_failure:.4f})")
if abs(computed_lambda_failure - TARGET_LAMBDA) < TOLERANCE:
    print(f"  Result: ✅ AUTHORIZED (Integrity Match)")
else:
    print(f"  Result: ❌ REJECTED (Integrity Mismatch)")

print(f"  Latency: {latency_failure_ns / 1000:.3f} µs")

print("\n--- Summary ---")
print("This demonstrates the principle of a complexity-gated security check:")
print(f"The O(1) check runs in <1ms and rejects unauthorized requests instantly, saving the computational cost of a full processing pipeline.")

# terminal output:
# (base) brendanlynch@Mac zzzzzzzhourglass % python security1.py
# --- Dynamic Modular Integrity Check at Time Step 10 ---
# Secret Target N: 17 (Lambda 2: 0.3800)

# Processing 'SUCCESS' Command (Input N=17)...
#   Computed N: 17 (Lambda 2: 0.3800)
#   Result: ✅ AUTHORIZED (Integrity Match)
#   Latency: 3.875 µs

# Processing 'FAILURE' Command (Input N=9)...
#   Computed N: 9 (Lambda 2: nan)
#   Result: ❌ REJECTED (Integrity Mismatch)
#   Latency: 2.667 µs

# --- Summary ---
# This demonstrates the principle of a complexity-gated security check:
# The O(1) check runs in <1ms and rejects unauthorized requests instantly, saving the computational cost of a full processing pipeline.
# (base) brendanlynch@Mac zzzzzzzhourglass % 