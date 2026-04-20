"""
plot_spectral_results.py
========================
Generates publication-ready plots for the Spectral Variational Optimizer paper.
Reads the compiled 'all_results.pt' dictionary.
"""

import torch
import matplotlib.pyplot as plt
import numpy as np
import os

# Set global matplotlib style for academic papers
plt.rcParams.update({
    'font.size': 12,
    'axes.labelsize': 14,
    'axes.titlesize': 14,
    'legend.fontsize': 11,
    'xtick.labelsize': 11,
    'ytick.labelsize': 11,
    'lines.linewidth': 2.5,
    'figure.dpi': 300
})

def generate_plots(results_path="./results/all_results.pt", output_dir="./results"):
    if not os.path.exists(results_path):
        raise FileNotFoundError(f"Could not find {results_path}. Ensure the file exists.")
    
    print(f"Loading data from {results_path}...")
    data = torch.load(results_path, map_location="cpu")
    os.makedirs(output_dir, exist_ok=True)

    epsilons = [0.1, 0.05, 0.01, 0.005, 0.001, 0.0]
    seeds = [42, 43, 44]

    # ---------------------------------------------------------
    # FIGURE 1: Final Accuracy vs Epsilon (Mean + Std Dev)
    # ---------------------------------------------------------
    print("Generating Figure 1: Accuracy vs Epsilon...")
    means = []
    stds = []
    
    for eps in epsilons:
        final_accs = []
        for seed in seeds:
            key = f"cifar_eps_{eps}_seed_{seed}"
            if key in data and len(data[key]['test_acc']) > 0:
                final_accs.append(data[key]['test_acc'][-1])
        
        if final_accs:
            means.append(np.mean(final_accs))
            stds.append(np.std(final_accs))
        else:
            means.append(0)
            stds.append(0)

    fig, ax = plt.subplots(figsize=(8, 5))
    x_pos = np.arange(len(epsilons))
    
    ax.bar(x_pos, means, yerr=stds, capsize=6, color='steelblue', alpha=0.8, edgecolor='black')
    ax.set_xticks(x_pos)
    ax.set_xticklabels([str(e) for e in epsilons])
    ax.set_xlabel(r'Dirichlet Regularization Strength ($\epsilon$)')
    ax.set_ylabel('Final Test Accuracy (%)')
    ax.set_title('CIFAR-10 Final Accuracy and Stability by $\epsilon$')
    ax.set_ylim(60, 90)
    
    # Highlight the classical baseline
    ax.get_xticklabels()[-1].set_fontweight("bold")
    ax.get_xticklabels()[-1].set_color("darkred")
    
    plt.grid(axis='y', linestyle='--', alpha=0.6)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'fig_accuracy_vs_epsilon.png'))
    plt.close()

    # ---------------------------------------------------------
    # FIGURE 2: Catastrophic Collapse Prevention (Seed 43)
    # ---------------------------------------------------------
    print("Generating Figure 2: Catastrophic Collapse Prevention...")
    fig, ax = plt.subplots(figsize=(9, 5))
    
    # Extract specifically seed 43 for 0.001 (Failed) vs 0.01 (Stable) vs 0.0 (Baseline)
    key_stable = "cifar_eps_0.01_seed_43"
    key_collapse = "cifar_eps_0.001_seed_43"
    key_baseline = "cifar_eps_0.0_seed_43"
    
    if key_stable in data and key_collapse in data and key_baseline in data:
        epochs = data[key_stable]['epoch']
        
        ax.plot(epochs, data[key_stable]['test_acc'], label=r'Stable Spectral ($\epsilon=0.01$)', color='green')
        ax.plot(epochs, data[key_baseline]['test_acc'], label=r'Classical Baseline ($\epsilon=0.0$)', color='orange', linestyle='--')
        ax.plot(epochs, data[key_collapse]['test_acc'], label=r'Weak Spectral Collapse ($\epsilon=0.001$)', color='red')
        
        ax.set_xlabel('Epoch')
        ax.set_ylabel('Test Accuracy (%)')
        ax.set_title('Prevention of Late-Stage Degradation (Seed 43)')
        ax.legend(loc='lower right')
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, 'fig_collapse_prevention.png'))
    plt.close()

    # ---------------------------------------------------------
    # FIGURE 3: Energy Descent & Spectral Residue (The Goldilocks Run)
    # ---------------------------------------------------------
    print("Generating Figure 3: Energy Descent and Residue Dynamics...")
    
    # Use the best stable run: eps=0.005, seed=44
    goldilocks_key = "cifar_eps_0.005_seed_44"
    if goldilocks_key in data:
        run_data = data[goldilocks_key]
        epochs = run_data['epoch']
        energy = run_data['train_energy']
        residue = run_data['residue']
        
        fig, ax1 = plt.subplots(figsize=(10, 6))
        
        # Plot Energy on left Y axis
        color1 = 'tab:red'
        ax1.set_xlabel('Epoch')
        ax1.set_ylabel(r'Spectral Energy $\mathcal{E}$', color=color1)
        ax1.plot(epochs, energy, color=color1, label='Energy Descent')
        ax1.tick_params(axis='y', labelcolor=color1)
        
        # Plot Residue on right Y axis
        ax2 = ax1.twinx()
        color2 = 'tab:blue'
        ax2.set_ylabel(r'Spectral Residue $\mathcal{R}$', color=color2)
        ax2.plot(epochs, residue, color=color2, label='Spectral Residue')
        ax2.tick_params(axis='y', labelcolor=color2)
        
        # Add target attractor line
        ax2.axhline(y=0.9995, color='gray', linestyle='--', alpha=0.7, label='Target Attractor')
        
        # Combine legends
        lines1, labels1 = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax1.legend(lines1 + lines2, labels1 + labels2, loc='center right')
        
        plt.title(r'Isospectral Confinement ($\epsilon=0.005$)')
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, 'fig_energy_residue.png'))
    plt.close()

    print(f"All figures generated successfully in '{output_dir}'.")

if __name__ == "__main__":
    generate_plots()