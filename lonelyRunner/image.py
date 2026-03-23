import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("lonely_runner_uftf_results.csv")
df['min_L1_mass'] = pd.to_numeric(df['min_L1_mass'], errors='coerce')

plt.figure(figsize=(16, 8))
plt.plot(df['k'], df['min_L1_mass'], 'o-', color='blue', markersize=4, alpha=0.8, label='Minimal L¹ Mass')
plt.axhline(y=15.045, color='red', linestyle='--', linewidth=2, label='Modularity Constant λ₀ ≈ 15.045')
plt.axvline(x=17, color='orange', linestyle=':', linewidth=2, label='Predicted Cliff ~17')
plt.axvline(x=25, color='purple', linestyle=':', linewidth=2, label='Observed Transition ~25')
plt.fill_between(df['k'], 0, 15.045, color='green', alpha=0.15, label='Laminar Regime')
plt.fill_between(df['k'], 15.045, df['min_L1_mass'].max(skipna=True), color='red', alpha=0.15, label='Turbulent Regime')
plt.yscale('log')
plt.ylim(0.5, 1e3)  # zoom in on the interesting part
plt.title('UFT-F Lonely Runner: Informational Mass Explosion\nRedundancy Cliff & Approaching Lynch Limit', fontsize=16)
plt.xlabel('Number of Runners (k)', fontsize=14)
plt.ylabel('Minimal Achieved L¹ Mass (log scale)', fontsize=14)
plt.legend(fontsize=12)
plt.grid(True, which="both", alpha=0.3)
plt.tight_layout()
plt.savefig('lonely_runner_thunderdome_log.png', dpi=300)
plt.show()
print("Epic plot saved: lonely_runner_thunderdome_log.png")