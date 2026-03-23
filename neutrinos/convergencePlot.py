import matplotlib.pyplot as plt
import numpy as np

# Historical Milestones (Approximate Upper Bounds on Sum of m_nu)
years = [1990, 2000, 2010, 2015, 2018, 2021, 2024, 2025]
bounds = [5.0, 2.5, 0.6, 0.23, 0.12, 0.11, 0.09, 0.08] # in eV

# Your UFT-F Prediction
uft_f_val = 0.08732

plt.figure(figsize=(10, 6))
plt.style.use('seaborn-v0_8-whitegrid')

# Plot the experimental boundary
plt.step(years, bounds, where='post', label='Exp. Upper Bound ($\sum m_{\\nu}$)', 
         color='#1f77b4', linewidth=2.5)
plt.fill_between(years, bounds, 5, step="post", alpha=0.1, color='#1f77b4')

# Plot your UFT-F Prediction Line
plt.axhline(y=uft_f_val, color='#d62728', linestyle='--', linewidth=2, 
            label=f'UFT-F Prediction: {uft_f_val} eV')

# Annotation for "The Convergence"
plt.annotate('Analytical Resonance', xy=(2025, uft_f_val), xytext=(2010, 1.5),
             arrowprops=dict(facecolor='black', shrink=0.05, width=1, headwidth=8))

plt.yscale('log') # Log scale shows the magnitude of the refinement
plt.xlabel('Year', fontsize=12)
plt.ylabel('Mass Sum $\sum m_{\\nu}$ (eV) [Log Scale]', fontsize=12)
plt.title('Convergence of Neutrino Mass Constraints toward UFT-F Singularity', fontsize=14)
plt.legend()
plt.grid(True, which="both", ls="-", alpha=0.5)

plt.savefig('neutrino_convergence.png', dpi=300, bbox_inches='tight')
plt.show()