"""
ONE SCRIPT - Spectral vs Adam Comparison Plot
=============================================
Loads your existing .npy files and creates the final figure for the paper.
"""

import matplotlib.pyplot as plt
import numpy as np

print("Loading data files...\n")

# Load the files you already have
try:
    spectral_residue = np.load('spectral_residue.npy')
    spectral_energy  = np.load('spectral_energy.npy')
    adam_loss        = np.load('adam_loss.npy')
except FileNotFoundError as e:
    print(f"ERROR: Could not find {e}")
    print("Make sure spectral_residue.npy, spectral_energy.npy, and adam_loss.npy exist in this folder.")
    exit()

steps = list(range(1, len(spectral_residue) + 1))

print(f"Loaded {len(steps)} steps")
print(f"Final Spectral Residue : {spectral_residue[-1]:.5f}")
print(f"Final Spectral Energy  : {spectral_energy[-1]:.4f}")
print(f"Final AdamW Loss       : {adam_loss[-1]:.4f}\n")

# Create the plot
fig, ax1 = plt.subplots(figsize=(11, 6.8))

# Left: Residue
ax1.set_xlabel('Optimization Step', fontsize=12)
ax1.set_ylabel('Spectral Residue $\\mathcal{R}$', color='tab:blue', fontsize=12)
ax1.plot(steps, spectral_residue, color='tab:blue', linewidth=2.8, label='Spectral Residue $\\mathcal{R}$')
ax1.tick_params(axis='y', labelcolor='tab:blue')
ax1.set_ylim(0.80, 1.005)
ax1.axhline(y=0.9895, color='gray', linestyle='--', alpha=0.8, linewidth=1.2, label='Target Attractor (0.9895)')

# Right: Energy vs Loss
ax2 = ax1.twinx()
ax2.set_ylabel('Energy / Loss', color='tab:red', fontsize=12)
ax2.plot(steps, spectral_energy, color='tab:red', linewidth=2.3, label='Spectral Energy $\\mathcal{E}$')
ax2.plot(steps, adam_loss, color='tab:orange', linewidth=2.2, linestyle='--', label='AdamW Loss')
ax2.tick_params(axis='y', labelcolor='tab:red')

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

print("\n✅ Plot saved successfully as 'spectral_vs_adam_comparison.png'")
print("   You can now insert it into your LaTeX paper.")