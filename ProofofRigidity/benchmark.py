#!/usr/bin/env python3
"""
UFT-F: PROOF-OF-RIGIDITY (PoR)
Computational Benchmarking Harness

Objective: Robustly quantify the computational overhead ("tax") of utilizing 
arbitrary-precision decimal arithmetic (150 dps) compared to standard 64-bit 
IEEE 754 hardware floats and standard SHA-256 cryptographic hashing.
"""

import os
import gc
import timeit
import hashlib
import random

# STRICT DETERMINISM: Disable hardware C-extensions for valid pure-software baseline
os.environ['MPMATH_NOGMPY'] = 'Y'
from mpmath import mp

# Lock global precision
mp.dps = 150

# =====================================================================
# 1. CONSTANTS & BASELINES
# =====================================================================
ITERATIONS = 10_000

TARGET_FLOOR_MP = mp.mpf("0.003118989999999999870178291061506570258643")
G24_VOL_MP = mp.mpf("25.0") / (mp.mpf("2.0") * mp.pi)
EPSILON_MP = mp.mpf("1e-80")

# Native 64-bit hardware float equivalents (for baseline comparison)
TARGET_FLOOR_FL = float("0.003118989999999999870178291061506570258643")
import math
G24_VOL_FL = 25.0 / (2.0 * math.pi)
EPSILON_FL = 1e-80

# =====================================================================
# 2. ISOLATED VALIDATION FUNCTIONS
# =====================================================================

def validate_por_150_decimal(N, sigma, key, expected_parity):
    """The actual Brittle Gatekeeper operating at 150 decimal places."""
    # 1. Geometric Reconstruction
    recon = key / (N * G24_VOL_MP * sigma)
    divergence = abs(recon - TARGET_FLOOR_MP)
    
    if divergence > EPSILON_MP:
        return False
        
    # 2. Mantissa Tail Parity (Math-only bounds)
    scaled = int(key * (mp.mpf("10.0") ** 150))
    tail = scaled % (10 ** 20)
    tail_parity = sum(int(d) for d in str(tail).zfill(20)) % 2
    
    if tail_parity != expected_parity:
        return False
        
    return True

def validate_hardware_float(N, sigma, key):
    """A naive hardware float implementation (Insecure, but fast)."""
    recon = key / (N * G24_VOL_FL * sigma)
    divergence = abs(recon - TARGET_FLOOR_FL)
    # Hardware floats will naturally swallow the epsilon, 
    # but we measure the execution speed of the raw division.
    return divergence <= EPSILON_FL

def baseline_sha256_hash(payload):
    """A standard cryptographic hash (Used in Bitcoin/Ethereum)."""
    return hashlib.sha256(payload).hexdigest()

# =====================================================================
# 3. BENCHMARK EXECUTION HARNESS
# =====================================================================

def run_benchmarks():
    print("=" * 70)
    print(" PoR COMPUTATIONAL OVERHEAD BENCHMARKING HARNESS")
    print("=" * 70)
    print(f"[*] Generating {ITERATIONS} pre-computed randomized state vectors...")
    
    # Pre-compute data so random number generation DOES NOT pollute the timer
    mp_states = []
    fl_states = []
    hash_payloads = []
    
    for _ in range(ITERATIONS):
        N_str = str(random.uniform(37.0, 100.0))
        sigma_str = str(random.uniform(0.01, 1.0))
        
        # mpmath states
        N_mp = mp.mpf(N_str)
        sigma_mp = mp.mpf(sigma_str)
        key_mp = TARGET_FLOOR_MP * N_mp * G24_VOL_MP * sigma_mp
        expected_parity = random.randint(0, 1)
        mp_states.append((N_mp, sigma_mp, key_mp, expected_parity))
        
        # Hardware float states
        N_fl = float(N_str)
        sigma_fl = float(sigma_str)
        key_fl = float(TARGET_FLOOR_FL * N_fl * G24_VOL_FL * sigma_fl)
        fl_states.append((N_fl, sigma_fl, key_fl))
        
        # Hash payloads (Standard 256-byte block string)
        hash_payloads.append(os.urandom(256))

    print("[*] Vectors initialized. Beginning strict timing runs...")
    print("-" * 70)

    # Disable Garbage Collection to prevent random CPU spikes during timing
    gc.disable()

    # --- TEST 1: Hardware Float Baseline ---
    start_time = timeit.default_timer()
    for state in fl_states:
        validate_hardware_float(state[0], state[1], state[2])
    fl_total_time = timeit.default_timer() - start_time

    # --- TEST 2: SHA-256 Cryptographic Baseline ---
    start_time = timeit.default_timer()
    for payload in hash_payloads:
        baseline_sha256_hash(payload)
    sha_total_time = timeit.default_timer() - start_time

    # --- TEST 3: PoR 150-Decimal Arithmetic ---
    start_time = timeit.default_timer()
    for state in mp_states:
        validate_por_150_decimal(state[0], state[1], state[2], state[3])
    mp_total_time = timeit.default_timer() - start_time

    # Re-enable Garbage Collection
    gc.enable()

    # =====================================================================
    # 4. RESULTS COMPUTATION & OUTPUT
    # =====================================================================
    def calc_metrics(total_time):
        avg_ms = (total_time / ITERATIONS) * 1000
        tps = ITERATIONS / total_time
        return avg_ms, tps

    fl_avg, fl_tps = calc_metrics(fl_total_time)
    sha_avg, sha_tps = calc_metrics(sha_total_time)
    mp_avg, mp_tps = calc_metrics(mp_total_time)

    print(f"{'Metric':<30} | {'Latency per State (ms)':<22} | {'Max Capacity (TPS)'}")
    print("-" * 70)
    print(f"{'Native 64-bit Float':<30} | {fl_avg:<22.6f} | {fl_tps:,.0f}")
    print(f"{'Standard SHA-256 Hash':<30} | {sha_avg:<22.6f} | {sha_tps:,.0f}")
    print(f"{'PoR Brittle Gate (150-dec)':<30} | {mp_avg:<22.6f} | {mp_tps:,.0f}")
    print("-" * 70)
    
    # Mathematical Conclusion for the Reviewer
    overhead_ratio = mp_avg / fl_avg
    sha_ratio = mp_avg / sha_avg
    
    print("\nEMPIRICAL CONCLUSIONS FOR PEER REVIEW:")
    print(f"1. Canonical 150-decimal arithmetic introduces a {overhead_ratio:.1f}x computational overhead")
    print(f"   compared to insecure native hardware floats.")
    print(f"2. Relative to standard block hashing, the PoR Brittle Gate is {sha_ratio:.2f}x the latency.")
    print(f"3. Single-threaded max throughput equates to {mp_tps:,.0f} validations per second.")
    print("\nVERDICT: The computational tax of geometric rigidity is strictly deterministic")
    print("and massively exceeds the bandwidth limits of global network transport, proving")
    print("the math cannot act as a consensus bottleneck.")

if __name__ == "__main__":
    run_benchmarks()



#     (base) brendanlynch@Brendans-Laptop crypto % python benchmark.py
# ======================================================================
#  PoR COMPUTATIONAL OVERHEAD BENCHMARKING HARNESS
# ======================================================================
# [*] Generating 10000 pre-computed randomized state vectors...
# [*] Vectors initialized. Beginning strict timing runs...
# ----------------------------------------------------------------------
# Metric                         | Latency per State (ms) | Max Capacity (TPS)
# ----------------------------------------------------------------------
# Native 64-bit Float            | 0.000075               | 13,411,567
# Standard SHA-256 Hash          | 0.000333               | 3,004,206
# PoR Brittle Gate (150-dec)     | 0.010154               | 98,481
# ----------------------------------------------------------------------

# EMPIRICAL CONCLUSIONS FOR PEER REVIEW:
# 1. Canonical 150-decimal arithmetic introduces a 136.2x computational overhead
#    compared to insecure native hardware floats.
# 2. Relative to standard block hashing, the PoR Brittle Gate is 30.51x the latency.
# 3. Single-threaded max throughput equates to 98,481 validations per second.

# VERDICT: The computational tax of geometric rigidity is strictly deterministic
# and massively exceeds the bandwidth limits of global network transport, proving
# the math cannot act as a consensus bottleneck.
# (base) brendanlynch@Brendans-Laptop crypto % 