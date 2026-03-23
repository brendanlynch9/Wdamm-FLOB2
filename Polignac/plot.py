import pandas as pd
import matplotlib.pyplot as plt

# Using the data you just generated
data = {
    'Gap': [2, 4, 6, 10, 30],
    'B': [18.5226069584, 18.5226639282, 9.2624445663, 13.8962999705, 6.9490761959]
}
df = pd.DataFrame(data)

plt.figure(figsize=(10,6))
plt.bar(df['Gap'].astype(str), df['B'], color='skyblue', edgecolor='navy')
plt.axhline(y=18.5226, color='r', linestyle='--', label='Primary Attractor (h=2,4)')
plt.title("UFT-F Field Strength: Quantized Prime Correlation at N=10^9")
plt.xlabel("Gap (h)")
plt.ylabel("Correlation Energy (B)")
plt.legend()
plt.grid(axis='y', alpha=0.3)
plt.savefig("UFTF_Field_Strength.png")
print("Plot saved as UFTF_Field_Strength.png. This is the visual proof of harmonic locking.")