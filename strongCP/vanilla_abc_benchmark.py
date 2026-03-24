import numpy as np
from scipy.linalg import eigh
import matplotlib.pyplot as plt
from tqdm import tqdm
import time

# NO UFT-F CONSTANTS HERE — pure vanilla

# Grid: theta proxy for "x" in potential (periodic circle)
N = 2048
theta = np.linspace(-np.pi, np.pi, N, endpoint=False)
dtheta = theta[1] - theta[0]
print(f"Grid: N={N}, dtheta={dtheta:.6f}")

# Periodic Laplacian (-Δ)
diag = np.ones(N) * (-2.0)
off_diag = np.ones(N)
Laplacian = np.diag(diag) + np.diag(off_diag[:-1], 1) + np.diag(off_diag[:-1], -1)
Laplacian /= dtheta**2
Laplacian[0, -1] = Laplacian[-1, 0] = 1.0 / dtheta**2
kinetic = -Laplacian

# Proxy "primes" (your Base-24 residues as frequency modes — standard harmonic analysis)
prime_residues = np.array([1, 5, 7, 11, 13, 17, 19, 23])

def height_potential(theta, q):
    """
    Vanilla proxy for V_abc(x) from your paper:
    sum_p log(p+1) exp(-q |x| / log(p+2))
    Here: use cos(r θ) as periodic "exp(-q |x|)" analog, r = prime residues
    """
    V = np.zeros_like(theta)
    for r in prime_residues:
        # log(p+1) proxy as weight, exp(-q |x|) proxy as cos(r θ) decay envelope
        weight = np.log(r + 1)
        decay = np.exp(-q * np.abs(theta) / np.log(r + 2))  # direct from your eq (2)
        V += weight * decay * np.cos(r * theta)  # harmonic modulation
    V *= np.exp(q - 1.0)  # the key exp(Q-1) amplification from your eq (1)
    V -= 0.5  # small negative offset so low-q can have positive E0 → crossing possible
    return V

def L1_norm(V):
    return np.sum(np.abs(V)) * dtheta

# Sweep q (quality proxy)
q_values = np.linspace(0.0, 3.0, 100)
E0_list = []
L1_list = []

for q in tqdm(q_values, desc="Sweeping q"):
    start = time.time()
    V = height_potential(theta, q)
    H = kinetic + np.diag(V)
    
    try:
        evals = eigh(H, eigvals_only=True, subset_by_index=[0, 0])
        E0 = evals[0]
    except:
        evals = eigh(H, eigvals_only=True)
        E0 = evals[0]
    
    E0_list.append(E0)
    L1_list.append(L1_norm(V))

E0_arr = np.array(E0_list)
L1_arr = np.array(L1_list)

# Detect zero-crossing or sharp drop
sign_changes = np.diff(np.sign(E0_arr))
cross_idx = np.where(sign_changes != 0)[0]

if len(cross_idx) > 0:
    idx = cross_idx[0]
    q1, q2 = q_values[idx], q_values[idx+1]
    e1, e2 = E0_arr[idx], E0_arr[idx+1]
    q_star = q1 - e1 * (q2 - q1) / (e2 - e1)
    print(f"\nZERO-CROSSING / PHASE TRANSITION at q* ≈ {q_star:.4f}")
    print(f"E0 near cross: {e1:.6f} → {e2:.6f}")
else:
    print("\nNo zero-crossing. Checking for sharp negative plunge...")
    min_idx = np.argmin(E0_arr)
    print(f"Minimum E0 = {E0_arr[min_idx]:.6f} at q = {q_values[min_idx]:.4f}")

# Summary
print(f"\nq=0.0: E₀ = {E0_arr[0]:.6f}, L¹ ≈ {L1_arr[0]:.2f}")
print(f"q=max ({q_values[-1]:.2f}): E₀ = {E0_arr[-1]:.6f}, L¹ ≈ {L1_arr[-1]:.2f}")

if E0_arr[-1] < -1.0 and L1_arr[-1] > 100:
    print(" → Collapse signature: high-q states unstable (deep negative E0 + L1 blow-up)")

# Plot
plt.figure(figsize=(12, 5))
plt.subplot(1, 2, 1)
plt.plot(q_values, E0_arr, 'b-', lw=2)
plt.axhline(0, color='k', ls='--')
plt.xlabel('q (quality proxy)')
plt.ylabel('Ground state E₀')
plt.title('Vanilla Benchmark: E₀ vs q')
plt.grid(True)

plt.subplot(1, 2, 2)
plt.plot(q_values, L1_arr, 'r-', lw=2)
plt.xlabel('q')
plt.ylabel('L¹ norm')
plt.title('L¹ Blow-up')
plt.grid(True)

plt.tight_layout()
plt.savefig('vanilla_abc_benchmark.png', dpi=150)
plt.close()
print("Plot saved: vanilla_abc_benchmark.png")


#  ______                 ______            _
# (_____ \               (_____ \          | |
#  _____) ) _   _  ____   _____) )___    __| |
# |  __  / | | | ||  _ \ |  ____// _ \  / _  |
# | |  \ \ | |_| || | | || |    | |_| |( (_| |
# |_|   |_||____/ |_| |_||_|     \___/  \____|

# For detailed documentation and guides, please visit:
# https://docs.runpod.io/ and https://blog.runpod.io/


# root@bd38678d4ced:/workspace# python vanilla_abc_benchmark.py
# Traceback (most recent call last):
#   File "/workspace/vanilla_abc_benchmark.py", line 2, in <module>
#     from scipy.linalg import eigh
# ModuleNotFoundError: No module named 'scipy'
# root@bd38678d4ced:/workspace# pip install scipy
# Collecting scipy
#   Downloading scipy-1.17.0-cp311-cp311-manylinux_2_27_x86_64.manylinux_2_28_x86_64.whl.metadata (62 kB)
# Collecting numpy<2.7,>=1.26.4 (from scipy)
#   Downloading numpy-2.4.1-cp311-cp311-manylinux_2_27_x86_64.manylinux_2_28_x86_64.whl.metadata (6.6 kB)
# Downloading scipy-1.17.0-cp311-cp311-manylinux_2_27_x86_64.manylinux_2_28_x86_64.whl (35.1 MB)
#    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 35.1/35.1 MB 15.6 MB/s eta 0:00:00
# Downloading numpy-2.4.1-cp311-cp311-manylinux_2_27_x86_64.manylinux_2_28_x86_64.whl (16.7 MB)
#    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 16.7/16.7 MB 5.3 MB/s eta 0:00:00
# Installing collected packages: numpy, scipy
#   Attempting uninstall: numpy
#     Found existing installation: numpy 1.26.3
#     Uninstalling numpy-1.26.3:
#       Successfully uninstalled numpy-1.26.3
# Successfully installed numpy-2.4.1 scipy-1.17.0
# WARNING: Running pip as the 'root' user can result in broken permissions and conflicting behaviour with the system package manager, possibly rendering your system unusable.It is recommended to use a virtual environment instead: https://pip.pypa.io/warnings/venv. Use the --root-user-action option if you know what you are doing and want to suppress this warning.

# [notice] A new release of pip is available: 24.2 -> 25.3
# [notice] To update, run: python -m pip install --upgrade pip
# root@bd38678d4ced:/workspace# python vanilla_abc_benchmark.py
# Traceback (most recent call last):
#   File "/workspace/vanilla_abc_benchmark.py", line 3, in <module>
#     import matplotlib.pyplot as plt
# ModuleNotFoundError: No module named 'matplotlib'
# root@bd38678d4ced:/workspace# pip install matplotlib
# Collecting matplotlib
#   Downloading matplotlib-3.10.8-cp311-cp311-manylinux2014_x86_64.manylinux_2_17_x86_64.whl.metadata (52 kB)
# Collecting contourpy>=1.0.1 (from matplotlib)
#   Downloading contourpy-1.3.3-cp311-cp311-manylinux_2_27_x86_64.manylinux_2_28_x86_64.whl.metadata (5.5 kB)
# Collecting cycler>=0.10 (from matplotlib)
#   Downloading cycler-0.12.1-py3-none-any.whl.metadata (3.8 kB)
# Collecting fonttools>=4.22.0 (from matplotlib)
#   Downloading fonttools-4.61.1-cp311-cp311-manylinux2014_x86_64.manylinux_2_17_x86_64.whl.metadata (114 kB)
# Collecting kiwisolver>=1.3.1 (from matplotlib)
#   Downloading kiwisolver-1.4.9-cp311-cp311-manylinux2014_x86_64.manylinux_2_17_x86_64.whl.metadata (6.3 kB)
# Requirement already satisfied: numpy>=1.23 in /usr/local/lib/python3.11/dist-packages (from matplotlib) (2.4.1)
# Requirement already satisfied: packaging>=20.0 in /usr/local/lib/python3.11/dist-packages (from matplotlib) (24.1)
# Requirement already satisfied: pillow>=8 in /usr/local/lib/python3.11/dist-packages (from matplotlib) (10.2.0)
# Collecting pyparsing>=3 (from matplotlib)
#   Downloading pyparsing-3.3.1-py3-none-any.whl.metadata (5.6 kB)
# Requirement already satisfied: python-dateutil>=2.7 in /usr/local/lib/python3.11/dist-packages (from matplotlib) (2.9.0.post0)
# Requirement already satisfied: six>=1.5 in /usr/lib/python3/dist-packages (from python-dateutil>=2.7->matplotlib) (1.16.0)
# Downloading matplotlib-3.10.8-cp311-cp311-manylinux2014_x86_64.manylinux_2_17_x86_64.whl (8.7 MB)
#    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 8.7/8.7 MB 1.1 MB/s eta 0:00:00
# Downloading contourpy-1.3.3-cp311-cp311-manylinux_2_27_x86_64.manylinux_2_28_x86_64.whl (355 kB)
# Downloading cycler-0.12.1-py3-none-any.whl (8.3 kB)
# Downloading fonttools-4.61.1-cp311-cp311-manylinux2014_x86_64.manylinux_2_17_x86_64.whl (5.0 MB)
#    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 5.0/5.0 MB 78.5 MB/s eta 0:00:00
# Downloading kiwisolver-1.4.9-cp311-cp311-manylinux2014_x86_64.manylinux_2_17_x86_64.whl (1.4 MB)
#    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 1.4/1.4 MB 87.1 MB/s eta 0:00:00
# Downloading pyparsing-3.3.1-py3-none-any.whl (121 kB)
# Installing collected packages: pyparsing, kiwisolver, fonttools, cycler, contourpy, matplotlib
#   Attempting uninstall: pyparsing
#     Found existing installation: pyparsing 2.4.7
#     Uninstalling pyparsing-2.4.7:
#       Successfully uninstalled pyparsing-2.4.7
# Successfully installed contourpy-1.3.3 cycler-0.12.1 fonttools-4.61.1 kiwisolver-1.4.9 matplotlib-3.10.8 pyparsing-3.3.1
# WARNING: Running pip as the 'root' user can result in broken permissions and conflicting behaviour with the system package manager, possibly rendering your system unusable.It is recommended to use a virtual environment instead: https://pip.pypa.io/warnings/venv. Use the --root-user-action option if you know what you are doing and want to suppress this warning.

# [notice] A new release of pip is available: 24.2 -> 25.3
# [notice] To update, run: python -m pip install --upgrade pip
# root@bd38678d4ced:/workspace# python vanilla_abc_benchmark.py
# Traceback (most recent call last):
#   File "/workspace/vanilla_abc_benchmark.py", line 4, in <module>
#     from tqdm import tqdm
# ModuleNotFoundError: No module named 'tqdm'
# root@bd38678d4ced:/workspace# pip install tqdm
# Collecting tqdm
#   Downloading tqdm-4.67.1-py3-none-any.whl.metadata (57 kB)
# Downloading tqdm-4.67.1-py3-none-any.whl (78 kB)
# Installing collected packages: tqdm
# Successfully installed tqdm-4.67.1
# WARNING: Running pip as the 'root' user can result in broken permissions and conflicting behaviour with the system package manager, possibly rendering your system unusable.It is recommended to use a virtual environment instead: https://pip.pypa.io/warnings/venv. Use the --root-user-action option if you know what you are doing and want to suppress this warning.

# [notice] A new release of pip is available: 24.2 -> 25.3
# [notice] To update, run: python -m pip install --upgrade pip
# root@bd38678d4ced:/workspace# python vanilla_abc_benchmark.py
# Grid: N=2048, dtheta=0.003068
# Sweeping q: 100%|████████████████████████████████████████████████████████████████| 100/100 [01:09<00:00,  1.45it/s]

# No zero-crossing. Checking for sharp negative plunge...
# Minimum E0 = -1.520712 at q = 3.0000

# q=0.0: E₀ = -0.558734, L¹ ≈ 8.28
# q=max (3.00): E₀ = -1.520712, L¹ ≈ 53.36
# Plot saved: vanilla_abc_benchmark.png
# root@bd38678d4ced:/workspace# 