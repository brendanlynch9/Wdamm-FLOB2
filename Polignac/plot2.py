import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Data from UFTF_Hardened_Closure.CSV
closure_data = {
    'Gap': [2, 4, 6, 10, 30],
    'B_Ratio': [18.522606958401212, 18.52266392823256, 9.26244456631675, 13.896299970455551, 6.949076195929767]
}
df_closure = pd.DataFrame(closure_data)

# Data from UFTF_Spectral_Decay.csv
decay_data = {
    'N': [50000001, 100000001, 150000001, 200000001, 250000001, 300000001, 350000001, 400000001, 450000001, 500000001, 550000001, 600000001, 650000001, 700000001, 750000001, 800000001, 850000001, 900000001, 950000001],
    'Residual': [0.1258358261892525, 0.11698873090407247, 0.19648234909081097, 0.2261545683755557, 0.23399620985885505, 0.2309427772480852, 0.22163540230855716, 0.2088388880451575, 0.19359724936337486, 0.17705611528504406, 0.1597002478626166, 0.14195915721849062, 0.12398472371419444, 0.10586443821083691, 0.08774553207188873, 0.06989952414879141, 0.05218907513371818, 0.0345264475620759, 0.017106074127013926]
}
df_decay = pd.DataFrame(decay_data)

# Plot 1: Quantized Harmonic Distribution (Bar Chart)
plt.figure(figsize=(10, 6))
bars = plt.bar(df_closure['Gap'].astype(str), df_closure['B_Ratio'], color='skyblue', edgecolor='navy')
plt.xlabel('Gap $h$')
plt.ylabel('Clustering Ratio $B(h, 10^9)$')
plt.title('Quantized Harmonic Distribution of Prime Gaps ($N=10^9$)')
for bar in bars:
    yval = bar.get_height()
    plt.text(bar.get_x() + bar.get_width()/2, yval + 0.1, round(yval, 4), ha='center', va='bottom')
plt.savefig('harmonic_distribution.png')
plt.close()

# Plot 2: Spectral Decay (Log-Log)
log_N = np.log10(df_decay['N'])
log_R = np.log10(df_decay['Residual'])
slope, intercept = np.polyfit(log_N, log_R, 1)

plt.figure(figsize=(10, 6))
plt.scatter(log_N, log_R, color='red', label='Empirical Residuals')
plt.plot(log_N, slope*log_N + intercept, color='black', linestyle='--', label=f'Fit Slope: {slope:.4f}')
plt.xlabel('$\log_{10}(N)$')
plt.ylabel('$\log_{10}(|B(2,N) - B_{final}|)$')
plt.title('Spectral Decay of Correlation Variance (UFT-F Hardened Closure)')
plt.legend()
plt.grid(True, which='both', linestyle='--', alpha=0.5)
plt.savefig('spectral_decay.png')
plt.close()

print(f"Plots saved. Slope calculated: {slope:.4f}")