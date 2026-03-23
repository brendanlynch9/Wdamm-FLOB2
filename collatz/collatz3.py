import numpy as np

# Collatz step to next odd
def next_odd_mod24(m):
    n = (3 * m + 1) % 24
    while n % 2 == 0:
        n //= 2
        n %= 24  # Keep mod 24
    return n

# Odds mod 24
odds = [1,3,5,7,9,11,13,15,17,19,21,23]

# Transitions
trans = {m: next_odd_mod24(m) for m in odds}
print("Mod 24 odd transitions:")
for m in sorted(trans):
    print(f"{m} -> {trans[m]}")

# Simulate orbits mod 24 until 1 or loop
def orbit_mod24(start, max_steps=50):
    orbit = [start]
    current = start
    seen = set()
    for _ in range(max_steps):
        if current in seen:
            return orbit + ['loop']
        seen.add(current)
        current = trans.get(current, next_odd_mod24(current))
        orbit.append(current)
        if current == 1:
            break
    return orbit

print("\nOrbits from odds:")
for m in odds:
    orb = orbit_mod24(m)
    print(f"{m}: {orb}")

#     (base) brendanlynch@Brendans-Laptop collatz % python collatz3.py
# Mod 24 odd transitions:
# 1 -> 1
# 3 -> 5
# 5 -> 1
# 7 -> 11
# 9 -> 1
# 11 -> 5
# 13 -> 1
# 15 -> 11
# 17 -> 1
# 19 -> 5
# 21 -> 1
# 23 -> 11

# Orbits from odds:
# 1: [1, 1]
# 3: [3, 5, 1]
# 5: [5, 1]
# 7: [7, 11, 5, 1]
# 9: [9, 1]
# 11: [11, 5, 1]
# 13: [13, 1]
# 15: [15, 11, 5, 1]
# 17: [17, 1]
# 19: [19, 5, 1]
# 21: [21, 1]
# 23: [23, 11, 5, 1]
# (base) brendanlynch@Brendans-Laptop collatz % 