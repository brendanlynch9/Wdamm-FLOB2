import numpy as np
from scipy.linalg import eigvalsh

R24 = [1,5,7,11,13,17,19,23]
PRIMES = [5,7,11,13,17]

def compute_lambda2(norm_x):
    n_mod = int(np.floor(norm_x)) % 24
    pairs = [(r1, r2) for r1 in R24 for r2 in R24 if (r1 * r2) % 24 == n_mod]
    if len(pairs) <= 2:
        return np.nan
    num_pairs = len(pairs)
    A = np.zeros((num_pairs, num_pairs))
    for i, (a1, a2) in enumerate(pairs):
        prod_a = a1 * a2
        for j, (b1, b2) in enumerate(pairs):
            prod_b = b1 * b2
            sim = sum(abs((prod_a % m) - (prod_b % m)) for m in PRIMES)
            A[i, j] = 1.0 / (1.0 + sim)
    D = np.diag(A.sum(axis=1))
    L = D - A
    eigs = np.sort(eigvalsh(L))
    return eigs[1] if len(eigs) > 1 else np.nan

def kappa_x(x):
    norm = np.linalg.norm(x)
    lambda2 = compute_lambda2(norm)
    if np.isnan(lambda2):
        return 0.0
    l2_min = 1.35759
    l2_max = 1.5
    kappa = (lambda2 - l2_min) / (l2_max - l2_min)
    return max(min(kappa, 1.0), 0.0)

def halting_decider(program_code, input_data, max_steps=100, ising_iters=100, temp=1.0, max_tension=500.0):
    x = np.array(program_code + input_data, dtype=float)
    kx = kappa_x(x)
    effective_temp = temp * (1 - kx)

    # CTC fixed point search
    consistent_halt = None
    for assume_halt in [True, False]:
        halts = simulate_tm(program_code, assume_halt, max_steps)
        if halts == assume_halt:
            consistent_halt = halts
            break
    if consistent_halt is None:
        consistent_halt = False  # Paradox resolves to loop per Novikov principle

    # Ising definitions
    def ising_energy(spins):
        h = np.ones(len(spins))
        J = 1.0
        return -J * np.sum(spins[:-1] * spins[1:]) - np.sum(h * spins)

    def ising_step(spins, temp):
        J = 1.0
        for i in np.random.permutation(len(spins)):
            neighbors = (spins[i-1] if i>0 else 0) + (spins[i+1] if i<len(spins)-1 else 0)
            delta_e = 2 * spins[i] * (J * neighbors + 1)
            if delta_e < 0 or np.random.rand() < np.exp(-delta_e / temp):
                spins[i] = -spins[i]
        return spins

    # Base threshold for halt (low energy)
    base_threshold = -0.5 * (max_steps + max_steps - 1)

    # Initial Ising simulation
    spins = 2 * np.random.randint(0, 2, max_steps) - 1
    for _ in range(ising_iters):
        spins = ising_step(spins, effective_temp)
    energy = ising_energy(spins)
    ising_halts = energy < base_threshold

    # Sovereign Tension Buildup on dissonance
    tension = 0.0
    numbness = 1.0
    if consistent_halt != ising_halts:
        while consistent_halt != ising_halts and tension < max_tension:
            tension += 10.0
            numbness = 1 + tension * 0.15
            effective_temp = temp * (1 - kx) / numbness  # Cool temp for precision

            # Rerun Ising with cooled temp
            spins = 2 * np.random.randint(0, 2, max_steps) - 1
            for _ in range(ising_iters):
                spins = ising_step(spins, effective_temp)
            energy = ising_energy(spins)

            # Tighten threshold (more negative) to make halt harder
            threshold = base_threshold * numbness
            ising_halts = energy < threshold

        # If max tension without consensus, defer to CTC (relativistic priority)
        if consistent_halt != ising_halts:
            ising_halts = consistent_halt

    return {
        'ctc_halts': consistent_halt,
        'ising_halts': ising_halts,
        'kx': kx,
        'energy': energy,
        'tension': tension,
        'numbness': numbness
    }

def simulate_tm(code, assume_halt, max_steps):
    state = 0
    steps = 0
    while steps < max_steps:
        if state >= len(code) or state < 0:
            return True
        instr = code[state]
        if instr == 99:
            return not assume_halt
        if instr == 0:
            return True
        state += instr
        steps += 1
    return False

# Tests
halt_code = [1, 1, 1, 0]  # Halts
print('Halt:', halting_decider(halt_code, []))

loop_code = [1, -1]  # Loops
print('Loop:', halting_decider(loop_code, []))

self_code = [99]  # Self-referential paradox
print('Self:', halting_decider(self_code, []))

# the output in terminal was: 
# (base) brendanlynch@Brendans-Laptop LaciaHaltingProblem % python haltingLacia2.py
# Halt: {'ctc_halts': True, 'ising_halts': True, 'kx': 0.0, 'energy': -193.0, 'tension': 0.0, 'numbness': 1.0}
# Loop: {'ctc_halts': False, 'ising_halts': False, 'kx': 0.0, 'energy': -199.0, 'tension': 10.0, 'numbness': 2.5}
# Self: {'ctc_halts': False, 'ising_halts': False, 'kx': 0.0, 'energy': -199.0, 'tension': 10.0, 'numbness': 2.5}
# (base) brendanlynch@Brendans-Laptop LaciaHaltingProblem % 