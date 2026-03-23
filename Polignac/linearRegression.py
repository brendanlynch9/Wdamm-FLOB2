import pandas as pd
import numpy as np

df = pd.read_csv("polignac_B_values.csv")
for h in [2,4,6,8,10,12,14,16,18,20,22,24,26,28,30]:
    x_tail = df['x'].values[-10:]
    B_tail = df[f'B_{h}'].values[-10:]
    coeffs = np.polyfit(x_tail, B_tail, 1)  # linear fit
    B_inf_estimate = coeffs[1]
    print(f"h={h}, extrapolated B_inf ≈ {B_inf_estimate:.6f}")

# (base) brendanlynch@Brendans-Laptop Polignac % python linearRegression.py
# h=2, extrapolated B_inf ≈ 2.007373
# h=4, extrapolated B_inf ≈ 2.007502
# h=6, extrapolated B_inf ≈ 1.194715
# h=8, extrapolated B_inf ≈ 2.007366
# h=10, extrapolated B_inf ≈ 1.552020
# h=12, extrapolated B_inf ≈ 1.194789
# h=14, extrapolated B_inf ≈ 1.691888
# h=16, extrapolated B_inf ≈ 2.007535
# h=18, extrapolated B_inf ≈ 1.194779
# h=20, extrapolated B_inf ≈ 1.552054
# h=22, extrapolated B_inf ≈ 1.812058
# h=24, extrapolated B_inf ≈ 1.194901
# h=26, extrapolated B_inf ≈ 1.843253
# h=28, extrapolated B_inf ≈ 1.691772
# h=30, extrapolated B_inf ≈ 0.942624
# (base) brendanlynch@Brendans-Laptop Polignac % 

