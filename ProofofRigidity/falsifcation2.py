#!/usr/bin/env python3
import hashlib
import random
from mpmath import mp
from dataclasses import dataclass

# EXACT CONTEXT LOCK
mp.dps = 150

TARGET_FLOOR = mp.mpf("0.003118989999999999870178291061506570258643")
G24_VOL = mp.mpf("25.0") / (mp.mpf("2.0") * mp.pi)
EPSILON = mp.mpf("1e-80")

@dataclass
class State:
    N: mp.mpf
    sigma: mp.mpf
    miner: str
    key: mp.mpf

def tail_parity(key):
    scaled = int(key * (mp.mpf("10.0") ** 150))
    tail = scaled % (10 ** 20)
    return sum(int(d) for d in str(tail).zfill(20)) % 2

def expected_parity(address):
    h = hashlib.sha256(address.encode()).hexdigest()
    return int(h, 16) % 2

def validate(state):
    recon = state.key / (state.N * G24_VOL * state.sigma)
    divergence = abs(recon - TARGET_FLOOR)
    
    if divergence > EPSILON:
        return False, "SHATTER"
    if tail_parity(state.key) != expected_parity(state.miner):
        return False, "PARITY_MISMATCH"
    return True, "PASS"

def canonical_state():
    """Generates a mathematically perfect, valid block."""
    # Cast to string first to prevent 64-bit Python float coercion
    N = mp.mpf(str(random.uniform(37.0, 100.0)))
    sigma = mp.mpf(str(random.uniform(0.01, 1.0)))
    miner = f"miner_{random.randint(0,1000000)}"
    
    key = TARGET_FLOOR * N * G24_VOL * sigma
    
    target_p = expected_parity(miner)
    for i in range(100):
        if tail_parity(key) == target_p:
            break
        # Force string notation for the imperceptible delta
        key += mp.mpf(str(f'{i+1}e-145'))
        
    return State(N, sigma, miner, key)

# ============================================================
# The Real Attack Suite
# ============================================================

def perturbation_attack(state):
    # Attacker injects a micro-payload (1e-40)
    attack = State(state.N, state.sigma, state.miner, state.key + mp.mpf("1e-40"))
    return validate(attack)[0]

def parity_forgery_attack(state):
    # Attacker steals block and applies their own address
    attacker = f"evil_miner_{random.randint(0,1000000)}"
    forged = State(state.N, state.sigma, attacker, state.key)
    return validate(forged)[0]

def replay_attack(state):
    # Attacker takes Block 1 and tries to replay it at Block 2 (N advances)
    advanced_N = state.N + mp.mpf("0.1") 
    copied = State(advanced_N, state.sigma, state.miner, state.key)
    return validate(copied)[0]

def serialization_attack(state):
    # Attacker truncates to 70 decimals, losing precision
    s = mp.nstr(state.key, 70)
    reconstructed = mp.mpf(s)
    attack = State(state.N, state.sigma, state.miner, reconstructed)
    return validate(attack)[0]

# ============================================================
# Campaign Execution
# ============================================================

def run_campaign(iterations=100000):
    failures = {"perturbation": 0, "parity_collision": 0, "serialization": 0, "replay": 0}

    for _ in range(iterations):
        state = canonical_state()

        if perturbation_attack(state): failures["perturbation"] += 1
        if parity_forgery_attack(state): failures["parity_collision"] += 1
        if serialization_attack(state): failures["serialization"] += 1
        if replay_attack(state): failures["replay"] += 1

    print("\n=== PROOF-OF-RIGIDITY ADVERSARIAL RESULTS ===")
    print(f"Total Iterations           : {iterations}")
    print(f"Topological Shatter Bypassed: {failures['perturbation']}")
    print(f"Replay Attack Bypassed     : {failures['replay']}")
    print(f"Serialization Bypassed     : {failures['serialization']}")
    print(f"MEV Parity Collisions (50%): {failures['parity_collision']}")
    
    print("\nCONCLUSION:")
    if failures['perturbation'] == 0 and failures['replay'] == 0 and failures['serialization'] == 0:
        print("-> PROTOCOL GEOMETRY SECURE. 0% Structural Bypass.")
        print(f"-> MEV Sieve performed at expected statistical rate (~50% mitigation).")
    else:
        print("-> PROTOCOL COMPROMISED.")

if __name__ == "__main__":
    run_campaign(100_000)

#     the terminal output was:
#     (base) brendanlynch@Brendans-Laptop crypto % python falsifcation2.py

# === PROOF-OF-RIGIDITY ADVERSARIAL RESULTS ===
# Total Iterations           : 100000
# Topological Shatter Bypassed: 0
# Replay Attack Bypassed     : 0
# Serialization Bypassed     : 0
# MEV Parity Collisions (50%): 50136

# CONCLUSION:
# -> PROTOCOL GEOMETRY SECURE. 0% Structural Bypass.
# -> MEV Sieve performed at expected statistical rate (~50% mitigation).
# (base) brendanlynch@Brendans-Laptop crypto % 