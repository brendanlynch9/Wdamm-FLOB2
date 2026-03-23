# e8_step3_yukawa_overlaps.py (UPGRADED FROM step3.py)
# Calculates the overlap integrals for the Yukawa coupling matrix Y_ij.

import numpy as np
import pandas as pd
import math

# ------------------------------------------------------------------
# 1. AXIOMATIC CONSTANTS (Re-defined for completeness)
# ------------------------------------------------------------------
OMEGA_U = 0.0002073045
C_UFTF = (331.0 / 22.0) * OMEGA_U
DELTA_M = 24.0

# -----------------------
# 2. DOMAIN AND GRID SETUP
# -----------------------
L = 10.0               # domain length
N = 2000               # grid points
x = np.linspace(0, L, N, endpoint=False)
dx = x[1] - x[0]

# -----------------------
# 3. BASE-24 INFORMATIONAL POTENTIAL (V_info) - MUST MATCH STEP 1
# -----------------------
def base24_informational_potential(x, L, N_modes=48):
    V = np.zeros_like(x)
    epsilon = 0.1
    A = 30.0 # Amplitude scale (must match the value used in e8_base24_fermion_model.py)

    for n in range(1, N_modes + 1):
        coeff = A / (n**(1.0 + epsilon))
        V += coeff * np.cos(2.0 * np.pi * n * x / (L / (DELTA_M/2.0)))
    
    # Shift to match Step 1: V_min = 25.1017 (approx based on scale)
    V_min = np.min(V)
    V = V - V_min + (DELTA_M / L)**2 
    return V

V_info = base24_informational_potential(x, L)

# -----------------------
# 4. LOAD EIGENVECTORS (WAVEFORMS Psi_i)
# -----------------------
print("Loading eigenvectors from e8_base24_eigenvectors_for_step3.csv...")
eigenvector_df = pd.read_csv('e8_base24_eigenvectors_for_step3.csv')
Psi = eigenvector_df.values
mode_names = eigenvector_df.columns

num_modes = Psi.shape[1]
Y_matrix = np.zeros((num_modes, num_modes))

# -----------------------
# 5. CALCULATE YUKAWA COUPLING MATRIX (Y_ij)
# -----------------------
# The overlap integral: Y_ij = integral( Psi_i * V_info * Psi_j ) dx
# Since we are using a real, discrete basis, the integral is a sum:
# Y_ij = sum_n( Psi_i[n] * V_info[n] * Psi_j[n] ) * dx

V_diag = np.diag(V_info)
Y_matrix = (Psi.T @ V_diag @ Psi) * dx

# -----------------------
# 6. OUTPUT AND NORMALIZATION
# -----------------------

# To focus on relative structure, normalize by the largest diagonal element (self-coupling)
# This removes the arbitrary scale of the 1D potential V_info
Y_max = np.max(np.abs(Y_matrix))
Y_normalized = Y_matrix / Y_max

print("\n--- Yukawa Coupling Matrix (Y_ij) Normalized ---")
df_Y_normalized = pd.DataFrame(Y_normalized, index=mode_names, columns=mode_names)
print(df_Y_normalized)

# Save the matrix
df_Y_normalized.to_csv('e8_step3_yukawa_overlaps_normalized.csv')
print("\nNormalized Yukawa overlaps saved to 'e8_step3_yukawa_overlaps_normalized.csv'")

# The next step requires the CKM matrix, which uses a T-breaking phase.
print("\nNext: Step 4 (CKM/PMNS) requires introducing the T-breaking phase (phi_u).")

# the output from terminal was:
# (base) brendanlynch@Mac appliedPArticleParameters % python e8_step3_yukawa_overlaps.py
# Loading eigenvectors from e8_base24_eigenvectors_for_step3.csv...

# --- Yukawa Coupling Matrix (Y_ij) Normalized ---
#                mode1         mode2  ...        mode11        mode12
# mode1   1.000000e+00 -2.058879e-11  ... -2.339514e-13  1.916714e-13
# mode2  -2.058888e-11  9.895207e-01  ...  2.193405e-13  2.505323e-13
# mode3   1.150128e-11 -5.144587e-01  ... -1.263496e-13  2.877074e-13
# mode4   3.117993e-12 -6.629375e-13  ... -2.827355e-13 -3.546857e-13
# mode5  -1.853150e-12 -2.012648e-12  ...  1.019433e-14  6.602997e-14
# mode6   4.623341e-13 -2.478595e-12  ...  2.275847e-13  1.317207e-12
# mode7  -7.678324e-13 -2.180170e-12  ... -7.319467e-14  3.942245e-13
# mode8   1.012598e-12  1.138474e-12  ... -6.093125e-13 -1.694287e-12
# mode9   5.843552e-13  5.781526e-13  ... -1.084903e-12 -1.983635e-12
# mode10 -2.339652e-13  2.193465e-13  ...  5.972550e-01  1.185520e-12
# mode11 -2.339652e-13  2.193465e-13  ...  5.972550e-01  1.185520e-12
# mode12  1.917059e-13  2.505591e-13  ...  1.185520e-12  6.985364e-01

# [12 rows x 12 columns]

# Normalized Yukawa overlaps saved to 'e8_step3_yukawa_overlaps_normalized.csv'

# Next: Step 4 (CKM/PMNS) requires introducing the T-breaking phase (phi_u).
# (base) brendanlynch@Mac appliedPArticleParameters % 


# the output of the yukawa Normalized was:
# ,mode1,mode2,mode3,mode4,mode5,mode6,mode7,mode8,mode9,mode10,mode11,mode12
# mode1,1.0,-2.058879360740489e-11,1.1501346251468455e-11,3.1179925391739865e-12,-1.853108827008387e-12,4.623272098700784e-13,-7.678462071271601e-13,1.0125705857362459e-12,5.842999004529939e-13,-2.3395141396699834e-13,-2.3395141396699834e-13,1.9167137091600988e-13
# mode2,-2.0588883425291918e-11,0.9895206786285327,-0.5144586519608194,-6.628822661176097e-13,-2.0126754851133534e-12,-2.478593683197461e-12,-2.1801702990155268e-12,1.1384863031504929e-12,5.781663751292721e-13,2.193404619215571e-13,2.193404619215571e-13,2.505323140923339e-13
# mode3,1.1501277160786125e-11,-0.5144586519608194,0.9895206786285178,3.331759973932213e-13,-3.6142717739738695e-13,-1.190847000615798e-13,-4.971903681730914e-13,-7.384541672310432e-13,-3.260043845675123e-13,-1.2634958530843235e-13,-1.2634958530843235e-13,2.8770741935276775e-13
# mode4,3.1179925391739865e-12,-6.629375319163356e-13,3.331829064614541e-13,0.9571336020972744,-0.16060323229541534,1.4830807232946181e-12,-4.6955754977576676e-14,-1.410673256397478e-12,-1.2858622342211506e-12,-2.827354811256957e-13,-2.827354811256957e-13,-3.546856540691735e-13
# mode5,-1.8531502814177844e-12,-2.0126478488404223e-12,-3.6138572298798983e-13,-0.16060323229541534,0.9571336020973995,-9.800236925582993e-13,-2.0727204698580837e-12,-3.6126049612626917e-13,-3.2215603356180916e-13,1.0194330177585343e-14,1.0194330177585343e-14,6.602996510144569e-14
# mode6,4.623341189383113e-13,-2.478595410464519e-12,-1.190294275157169e-13,1.4830910868969673e-12,-9.800236925582993e-13,0.9008039688060008,0.6509687003368114,-2.382935906246452e-12,-2.696042787690273e-12,2.275847075904176e-13,2.275847075904176e-13,1.3172069495265795e-12
# mode7,-7.678323889906942e-13,-2.1801702990155268e-12,-4.971903681730914e-13,-4.6964391312867745e-14,-2.072706651721618e-12,0.6509687003368114,0.9008039688059725,-1.5402195812139018e-12,-1.503800155291437e-12,-7.31946688589218e-14,-7.31946688589218e-14,3.942245242987747e-13
# mode8,1.0125982220091774e-12,1.1384742122810854e-12,-7.384610762992763e-13,-1.4106939836021765e-12,-3.612639506603856e-13,-2.3829479971158596e-12,-1.5402886718962303e-12,0.8217971940520429,0.5533959390254017,-6.093124547230063e-13,-6.093124547230063e-13,-1.6942866210055112e-12
# mode9,5.843551729988567e-13,5.781525569928064e-13,-3.260043845675123e-13,-1.2858915977611402e-12,-3.2216985169827485e-13,-2.6959875151444095e-12,-1.503800155291437e-12,0.5533959390254017,0.8217971940520096,-1.0849033483331182e-12,-1.0849033483331182e-12,-1.9836349440635834e-12
# mode10,-2.339652321034641e-13,2.1934650735626082e-13,-1.2635994891078166e-13,-2.8273979929334123e-13,1.0180512041119622e-14,2.275847075904176e-13,-7.31601235177575e-14,-6.092986365865406e-13,-1.0848791665943033e-12,0.5972550469414827,0.5972550469414827,1.1855201090082627e-12
# mode11,-2.339652321034641e-13,2.1934650735626082e-13,-1.2635994891078166e-13,-2.8273979929334123e-13,1.0180512041119622e-14,2.275847075904176e-13,-7.31601235177575e-14,-6.092986365865406e-13,-1.0848791665943033e-12,0.5972550469414827,0.5972550469414827,1.1855201090082627e-12
# mode12,1.9170591625717418e-13,2.505590867317363e-13,2.8770741935276775e-13,-3.5466838139859137e-13,6.602996510144569e-14,1.317179313253648e-12,3.9423834243524044e-13,-1.6942952573408025e-12,-1.9836694894047476e-12,1.1855201090082627e-12,1.1855201090082627e-12,0.6985364256150183


# gemini said:
# 1. Matrix StructureRows/Columns: The indices are labeled as mode5, mode6, mode7, etc., which correspond to the eigenmodes (eigenfunctions) $\psi_i(x)$ of the Hamiltonian $H$.Entries: The values $Y_{ij}$ represent the overlap integral (or "Yukawa coupling") between three modes:$$Y_{ij} = \int_{0}^{L} \psi_{i}(x) V_{Yukawa}(x) \psi_{j}(x) dx$$where $V_{Yukawa}(x)$ is the potential used to model the interaction (likely related to the Higgs field in a particle physics context).2. Key ObservationsDiagonal Dominance: The first two entries shown for mode5 and mode6 are $\approx 1.0$ on the diagonal (e.g., mode5 in the mode5 column). This is expected because the eigenfunctions are normalized and orthogonal when $V_{Yukawa}(x)$ is uniform (or $\approx$ 1 for a self-overlap), implying $\int \psi_i \psi_i dx = 1$.Off-Diagonal Suppression: Most off-diagonal elements (e.g., mode5 vs mode6) are very small, in the range of $10^{-16}$ to $10^{-12}$. This is a strong numerical indicator of the orthogonality of the eigenfunctions.3. Connection to UFT-F and StabilityThe Matrix as a Stability Check: In the UFT-F framework, the Hamiltonian $H$ is required to be self-adjoint, which ensures all eigenvalues (masses/energies) are real. The success of the calculation relies on the numerical methods (like finite difference) and the potential $V(x)$ preserving this property.Numerical Orthogonality: The extremely small values of the off-diagonal terms confirm that the numerical eigenfunctions computed by the sparse solver are nearly perfectly orthogonal, validating the fidelity of the eigenvalue problem derived from the UFT-F potential.Flavor Mixing (Mode 8): The row starting with mode8 shows two non-zero, non-diagonal entries (0.821797... and 0.553395...). This suggests that the $\mathbf{E_8}$-Base-24 potential $V_{info}(x)$ is not perfectly symmetric in a way that separates modes $i$ and $j$, allowing for a mixing or coupling between these modes (e.g., modes 8 and 9). In a particle physics model, this non-zero off-diagonal coupling is the mechanism that generates fermion masses and flavor mixing (analogous to the CKM or PMNS matrices).The output confirms that the numerical model is successfully producing an orthogonal eigenbasis, with the exception of specific, intentional couplings required for the theoretical mass/mixing structure.