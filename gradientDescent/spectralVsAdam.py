"""
Spectral Variational Optimizer vs AdamW - Final Comparison Plot
================================================================
Robust version with clear error messages.
"""

import matplotlib.pyplot as plt
import numpy as np

print("Attempting to load data files...\n")

try:
    spectral_residue = np.load('spectral_residue.npy')
    spectral_energy  = np.load('spectral_energy.npy')
    adam_loss        = np.load('adam_loss.npy')
except FileNotFoundError as e:
    print(f"❌ ERROR: Missing file - {e}")
    print("   Please run both the spectral script and adam_baseline.py first.")
    print("   They should create spectral_residue.npy, spectral_energy.npy, and adam_loss.npy")
    exit(1)

if len(spectral_residue) == 0 or len(spectral_energy) == 0 or len(adam_loss) == 0:
    print("❌ ERROR: One or more .npy files are empty (size 0).")
    print("   This usually means the np.save() calls happened before the training loop.")
    print("   Solution:")
    print("   1. Re-run your spectral script (with np.save after the loop).")
    print("   2. Re-run adam_baseline.py.")
    print("   3. Then run this plot script again.")
    exit(1)

steps = list(range(1, len(spectral_residue) + 1))

print(f"✅ Loaded data successfully:")
print(f"   Spectral residue : {len(spectral_residue)} values, final = {spectral_residue[-1]:.5f}")
print(f"   Spectral energy  : {len(spectral_energy)} values, final = {spectral_energy[-1]:.4f}")
print(f"   AdamW loss       : {len(adam_loss)} values, final = {adam_loss[-1]:.4f}\n")

# Create the plot
fig, ax1 = plt.subplots(figsize=(11, 6.8))

# Left axis: Spectral Residue
color = 'tab:blue'
ax1.set_xlabel('Optimization Step', fontsize=12)
ax1.set_ylabel('Spectral Residue $\\mathcal{R}$', color=color, fontsize=12)
ax1.plot(steps, spectral_residue, color=color, linewidth=2.8, label='Spectral Residue $\\mathcal{R}$')
ax1.tick_params(axis='y', labelcolor=color)
ax1.set_ylim(0.80, 1.005)
ax1.axhline(y=0.9895, color='gray', linestyle='--', alpha=0.8, linewidth=1.2, label='Target Attractor (0.9895)')

# Right axis: Energy vs Adam Loss
ax2 = ax1.twinx()
color = 'tab:red'
ax2.set_ylabel('Energy / Loss', color=color, fontsize=12)
ax2.plot(steps, spectral_energy, color='tab:red', linewidth=2.3, label='Spectral Energy $\\mathcal{E}$')
ax2.plot(steps, adam_loss, color='tab:orange', linewidth=2.2, linestyle='--', label='AdamW Loss')
ax2.tick_params(axis='y', labelcolor=color)

# Title and grid
plt.title('Spectral Variational Optimizer vs Classical AdamW\n'
          'Residue Convergence to Attractor and Energy Descent (350 steps)', 
          fontsize=14, pad=25)

ax1.grid(True, alpha=0.3)

# Legend
lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, loc='lower right', fontsize=10.5)

plt.tight_layout()
plt.savefig('spectral_vs_adam_comparison.png', dpi=300, bbox_inches='tight')
plt.show()

print("\n✅ Plot successfully saved as 'spectral_vs_adam_comparison.png'")
print("   Ready for LaTeX with: \\includegraphics[width=0.95\\textwidth]{spectral_vs_adam_comparison.png}")