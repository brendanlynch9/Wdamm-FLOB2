import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

def generate_uftf_data():
    # Define primes for analysis
    primes = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29]
    e8_constant = 120 # Derived from 240 roots / 2
    alpha_inf = 1/120

    data = []
    for p in primes:
        # Calculate Inflation Factor I(p)
        inflation_factor = e8_constant / p
        
        # Calculate Distance to the alpha_infinity floor
        dist = abs((1/inflation_factor) - alpha_inf)
        
        data.append({
            'Prime': p,
            'Symmetry': 2 * p,
            'I(p)': round(inflation_factor, 4),
            'Alpha_Dist': round(dist, 6)
        })

    df = pd.DataFrame(data)
    
    # Save results for UFT-F records
    df.to_csv('inflation_factors.csv', index=False)
    
    # Visualization of the Shape Layer Decay
    plt.figure(figsize=(10, 6))
    plt.plot(df['Prime'], df['I(p)'], 'bo-', linewidth=2, markersize=8, label='Inflation Pressure')
    plt.axhline(y=1, color='red', linestyle='--', label='Continuum Baseline')
    plt.fill_between(df['Prime'], df['I(p)'], 1, color='blue', alpha=0.1, label='Shape Layer Volume')
    
    plt.title('UFT-F: Figurate Inflation Factor toward E8 Attractor', fontsize=14)
    plt.xlabel('Prime Basis (p)', fontsize=12)
    plt.ylabel('Inflation Factor I(p)', fontsize=12)
    plt.grid(True, which='both', linestyle='--', alpha=0.5)
    plt.legend()
    plt.savefig('inflation_plot.png')
    
    print("UFT-F Analysis Complete. Data saved to inflation_factors.csv")
    return df

if __name__ == "__main__":
    generate_uftf_data()