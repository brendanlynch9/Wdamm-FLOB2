import qutip as qt
import numpy as np

# Prototype a Base-24 qudit quantum code
# Using a qudit with dimension 24 (Base-24 states)
# Simple phase-error correcting code using Quantum Fourier Transform mod 24
# Inspired by UFT-F Base-24 harmonics for noise filtering

d = 24  # Dimension

# Define Fourier transform operator for mod 24
omega = np.exp(2j * np.pi / d)
F = np.zeros((d, d), dtype=complex)
for k in range(d):
    for l in range(d):
        F[k, l] = omega**(k * l) / np.sqrt(d)
F_op = qt.Qobj(F)  # Fourier operator

# Define logical state: Example superposition in computational basis, using UFT-F inspired residues (e.g., 1 and 13 from quadratic residues)
psi_logical = (qt.basis(d, 1) + qt.basis(d, 13)) / np.sqrt(2)

# Apply QFT to go to momentum basis (where phases become shifts)
psi_mom = F_op * psi_logical

# Apply a phase error on one basis state (simulating decoherence phase noise)
error_phase = np.exp(2j * np.pi * 0.1)  # Phase error on state |1>
error_op = qt.Qobj(np.diag([1 if i != 1 else error_phase for i in range(d)]))
psi_err = error_op * psi_logical
rho_err = psi_err * psi_err.dag()

# Transform to Fourier (momentum) basis to detect the error as a shift
rho_mom = rho_err.transform(F_op)

# Probabilities in momentum basis
probs = rho_mom.diag().real

# Detected syndrome: The shift is the position of the peak
detected_shift = np.argmax(probs)

# Correction: Apply inverse shift operator (phase gradient)
# Shift operator X^k |j> = |j + k mod d>, but for phase correction, it's Z^{-detected_shift} or similar
# Since phase error in comp basis is shift in Fourier, to correct, apply inverse phase gradient
corr_phases = [omega ** (-detected_shift * i) for i in range(d)]
corr_op = qt.Qobj(np.diag(corr_phases))

# Apply correction
psi_corrected = corr_op * psi_err

# Compute fidelity with original state
fidelity = qt.fidelity(psi_corrected, psi_logical)

# Output results
print(f"Dimension (Base): {d}")
print(f"Logical state: {psi_logical.full().flatten()}")
print(f"State after error: {psi_err.full().flatten()}")
print(f"Probabilities in Fourier basis: {probs}")
print(f"Detected shift: {detected_shift}")
print(f"Corrected state: {psi_corrected.full().flatten()}")
print(f"Fidelity after correction: {fidelity:.4f}")

# the output in terminal was:
# (base) brendanlynch@Mac QUANTUM % python test1.py
# Dimension (Base): 24
# Logical state: [0.        +0.j 0.70710678+0.j 0.        +0.j 0.        +0.j
#  0.        +0.j 0.        +0.j 0.        +0.j 0.        +0.j
#  0.        +0.j 0.        +0.j 0.        +0.j 0.        +0.j
#  0.        +0.j 0.70710678+0.j 0.        +0.j 0.        +0.j
#  0.        +0.j 0.        +0.j 0.        +0.j 0.        +0.j
#  0.        +0.j 0.        +0.j 0.        +0.j 0.        +0.j]
# State after error: [0.        +0.j         0.5720614 +0.41562694j 0.        +0.j
#  0.        +0.j         0.        +0.j         0.        +0.j
#  0.        +0.j         0.        +0.j         0.        +0.j
#  0.        +0.j         0.        +0.j         0.        +0.j
#  0.        +0.j         0.70710678+0.j         0.        +0.j
#  0.        +0.j         0.        +0.j         0.        +0.j
#  0.        +0.j         0.        +0.j         0.        +0.j
#  0.        +0.j         0.        +0.j         0.        +0.j        ]
# Probabilities in Fourier basis: [0.07537571 0.00795763 0.07537571 0.00795763 0.07537571 0.00795763
#  0.07537571 0.00795763 0.07537571 0.00795763 0.07537571 0.00795763
#  0.07537571 0.00795763 0.07537571 0.00795763 0.07537571 0.00795763
#  0.07537571 0.00795763 0.07537571 0.00795763 0.07537571 0.00795763]
# Detected shift: 20
# Corrected state: [ 0.        +0.j         -0.07391279+0.70323318j  0.        +0.j
#   0.        +0.j          0.        +0.j          0.        +0.j
#   0.        +0.j          0.        +0.j          0.        +0.j
#   0.        +0.j          0.        +0.j          0.        +0.j
#   0.        +0.j          0.35355339+0.61237244j  0.        +0.j
#   0.        +0.j          0.        +0.j          0.        +0.j
#   0.        +0.j          0.        +0.j          0.        +0.j
#   0.        +0.j          0.        +0.j          0.        +0.j        ]
# Fidelity after correction: 0.9511
# (base) brendanlynch@Mac QUANTUM % 