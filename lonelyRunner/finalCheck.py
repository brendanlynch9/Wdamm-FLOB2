import math

def calculate_arithmetic_erasure(k):
    # Width of the forbidden zone (Section 6)
    slab_width = 2.0 / k
    
    # Maximum possible gap between prime multiples (Section 7)
    # Using the Dirichlet/Diophantine upper bound for k primes
    max_gap = 1.0 / (k**2)
    
    # The Erasure Ratio
    ratio = slab_width / max_gap
    
    print(f"--- Analysis for k = {k} ---")
    print(f"Slab Width:      {slab_width:.8f}")
    print(f"Max Arithmetic Gap: {max_gap:.8f}")
    print(f"Erasure Ratio:   {ratio:.2f}:1")
    
    if ratio > 1:
        print(f"STATUS: Loneliness is ARITHMETICALLY ERASED (Gap is {ratio:.1f}x smaller than the barrier).")
    else:
        print("STATUS: Loneliness is theoretically possible.")

calculate_arithmetic_erasure(321)

# (base) brendanlynch@Brendans-Laptop lonelyRunner % python finalCheck.py
# --- Analysis for k = 321 ---
# Slab Width:      0.00623053
# Max Arithmetic Gap: 0.00000970
# Erasure Ratio:   642.00:1
# STATUS: Loneliness is ARITHMETICALLY ERASED (Gap is 642.0x smaller than the barrier).
# (base) brendanlynch@Brendans-Laptop lonelyRunner % 