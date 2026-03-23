import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Read the CSV
df = pd.read_csv('lonely_runner_uftf_results.csv')

# Convert min_L1_mass to float, handling potential errors
df['min_L1_mass'] = pd.to_numeric(df['min_L1_mass'], errors='coerce')

# Plot 1: Full Log Scale
plt.figure(figsize=(14, 7))
plt.semilogy(df['k'], df['min_L1_mass'], 'o-', color='black', markersize=3, alpha=0.7)

# NOTE: Raw strings r'' are used here to handle LaTeX backslashes correctly
plt.axhline(y=15.045, color='red', linestyle='--', label=r'Modularity Constant $\lambda_0 \approx 15.045$')
plt.axvline(x=321, color='blue', linestyle='--', label=r'Lynch Limit $k=321$')

# Color coding regions
plt.fill_between(df['k'], 0.1, 15.045, where=(df['k'] <= 25), color='green', alpha=0.2, label='Laminar Stability')
plt.fill_between(df['k'], 15.045, df['min_L1_mass'].max(), where=(df['k'] > 25), color='red', alpha=0.1, label='Turbulent Regime')

plt.title(r'UFT-F Lonely Runner Stress Test: Spectral Mass vs. k (Log Scale)')
plt.xlabel('Number of Runners (k)')
plt.ylabel(r'Minimal $L^1$ Informational Mass (Log Scale)')
plt.grid(True, which="both", ls="-", alpha=0.2)
plt.legend()
plt.savefig('lonely_runner_thunderdome_log.png', dpi=300)

# Plot 2: Zoomed Early Phase (The Cliff)
plt.figure(figsize=(12, 6))
plt.plot(df['k'], df['min_L1_mass'], 'o-', color='blue', markersize=5)
plt.axhline(y=15.045, color='red', linestyle='--', label=r'$\lambda_0 \approx 15.045$')
plt.axvline(x=17, color='orange', linestyle=':', label='Theoretical Cliff ~17')
plt.axvline(x=25, color='purple', linestyle=':', label='Observed Transition ~25')
plt.fill_between(df['k'], 0, 15.045, color='green', alpha=0.1)
plt.fill_between(df['k'], 15.045, 100, color='red', alpha=0.1)

plt.xlim(0, 60)
plt.ylim(0, 60)
plt.title('Zoom: Laminar to Turbulent Transition (The Stability Cliff)')
plt.xlabel('k')
plt.ylabel(r'Minimal $L^1$ Mass')
plt.legend()
plt.grid(True)
plt.savefig('cliff_zoom.png', dpi=300)