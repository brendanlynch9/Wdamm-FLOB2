import numpy as np
import pandas as pd
from scipy.integrate import solve_ivp
import matplotlib.pyplot as plt
import os
import gzip

# ───────────────────────────────────────────────────────────────
# Build 5x5 Commuting Matrix from LOCAL LODES Files (Metro-Aggregated)
# ───────────────────────────────────────────────────────────────
def build_lodes_mobility_matrix_local(folder_path="."):
    """
    Reads your local 5 LODES files and builds metro-aggregated 5x5 commuting matrix.
    Files must be in folder_path: ny/ca/il/tx/az_od_main_JT00_2020.csv(.gz)
    """
    # Metro county FIPS lists (expanded for realistic flows)
    metro_counties = [
        # 0: NYC metro
        ["36005", "36047", "36061", "36081", "36085", "36059", "36103"],
        # 1: LA metro
        ["06037", "06059", "06065", "06071", "06111"],
        # 2: Chicago metro
        ["17031", "17043", "17097", "17197"],
        # 3: Houston metro
        ["48201", "48157", "48339"],
        # 4: Phoenix metro
        ["04013", "04021"]
    ]

    labels = ["NYC", "LA", "Chicago", "Houston", "Phoenix"]

    matrix = np.zeros((5, 5))
    total_outflow = np.zeros(5)

    for i, (state_prefix, county_list) in enumerate(zip(["ny", "ca", "il", "tx", "az"], metro_counties)):
        file_name = f"{state_prefix}_od_main_JT00_2020.csv"
        file_path = os.path.join(folder_path, file_name)
        gz_path = file_path + ".gz"

        # Load file
        if os.path.exists(gz_path):
            print(f"Reading gzipped LODES for {labels[i]}: {gz_path}")
            with gzip.open(gz_path, 'rt') as f:
                df = pd.read_csv(f, dtype={"h_geocode": str, "w_geocode": str})
        elif os.path.exists(file_path):
            print(f"Reading LODES for {labels[i]}: {file_path}")
            df = pd.read_csv(file_path, dtype={"h_geocode": str, "w_geocode": str})
        else:
            print(f"File missing for {labels[i]}: {file_name} or {file_name}.gz")
            continue

        df['origin_county'] = df['h_geocode'].str[:5]
        df['dest_county'] = df['w_geocode'].str[:5]

        # Flows from any county in this metro
        metro_od = df[df['origin_county'].isin(county_list)].copy()

        if metro_od.empty:
            print(f"No data for metro {labels[i]}")
            continue

        outflow = metro_od.groupby('dest_county')['S000'].sum()

        total_outflow[i] = outflow.sum()

        # Distribute to destination metros
        for j, dest_list in enumerate(metro_counties):
            for prefix in dest_list:
                if prefix in outflow.index:
                    matrix[i, j] += outflow[prefix]

    # Normalize + stay-home + small long-distance for realism
    matrix = matrix / np.maximum(total_outflow[:, None], 1e-6)
    np.fill_diagonal(matrix, 0.8)  # 80% stay home

    # Add small inter-metro connectivity (simulates air/business travel)
    inter_edge = 0.02  # 2% long-distance flow between all pairs
    for i in range(5):
        for j in range(5):
            if i != j:
                matrix[i, j] += inter_edge

    # Re-normalize rows
    matrix = matrix / matrix.sum(axis=1, keepdims=True)

    print("\nReal Metro-Aggregated + Long-Distance Commuting Matrix (row-normalized):")
    print(np.round(matrix, 4))
    print("Rows/Columns:", labels)
    return matrix


# ───────────────────────────────────────────────────────────────
# UFT-F Multi-Node Class
# ───────────────────────────────────────────────────────────────
class UFTFalsifierMultiNode:
    def __init__(self, populations):
        self.populations = np.array(populations, dtype=float)
        self.n_nodes = len(populations)
        self.N_total = np.sum(populations)
        self.THRESHOLD = 10.0

    def coupled_seir_model(self, t, y, beta, sigma, gamma, mobility):
        S = np.maximum(y[0::4], 0.0)
        E = np.maximum(y[1::4], 0.0)
        I = np.maximum(y[2::4], 0.0)
        R = np.maximum(y[3::4], 0.0)

        incoming_I = np.dot(mobility.T, I)
        incoming_density = np.clip(incoming_I / self.populations, 0.0, 0.1)

        local_density = I / self.populations

        dSdt = -beta * S * (local_density + incoming_density)
        dEdt = beta * S * (local_density + incoming_density) - sigma * E
        dIdt = sigma * E - gamma * I
        dRdt = gamma * I

        return np.concatenate([dSdt, dEdt, dIdt, dRdt])

    def get_spectral_norm(self, I_t):
        if I_t.ndim == 1:
            I_t = I_t[:, None]

        density = I_t / self.populations[None, :]
        k = np.arange(1, 101)
        s = np.where(density < 0.001, 2.0, 0.8)
        base = np.sum(1.0 / (k[None, None, :] ** s[:, :, None]), axis=2)
        norm = base * (1 + density * 100)
        return norm

    def run_simulation(self, t_span, beta=0.3, sigma=0.2, gamma=0.1, mobility=None):
        if mobility is None:
            mobility = build_lodes_mobility_matrix_local()  # Local files

        print("Mobility matrix (row-normalized):\n", np.round(mobility, 4))

        y0 = np.zeros(4 * self.n_nodes)
        for i in range(self.n_nodes):
            y0[4*i]     = self.populations[i] - 10.0
            y0[4*i + 1] = 10.0

        t_eval = np.linspace(t_span[0], t_span[1], 600)

        sol = solve_ivp(
            self.coupled_seir_model,
            t_span,
            y0,
            args=(beta, sigma, gamma, mobility),
            method='BDF',
            t_eval=t_eval,
            rtol=1e-6,
            atol=1e-8,
            max_step=1.0
        )

        if not sol.success:
            print("Integration failed:", sol.message)
            return None, None, None, None

        t = sol.t
        y = sol.y.T

        S = y[:, 0::4]
        E = y[:, 1::4]
        I = y[:, 2::4]
        R = y[:, 3::4]

        norms_per_node = self.get_spectral_norm(I)
        global_I = np.sum(I, axis=1)
        global_norms = self.get_spectral_norm(global_I[:, None])[:, 0]

        return t, I, norms_per_node, global_norms


# ───────────────────────────────────────────────────────────────
# Run
# ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    pops = [8400000, 10000000, 2700000, 2300000, 1600000]  # NYC, LA, Chicago, Houston, Phoenix

    model = UFTFalsifierMultiNode(pops)

    t, I, norms_per_node, global_norms = model.run_simulation(
        t_span=(0, 180), beta=0.3
    )

    if t is not None:
        # Global norm
        plt.figure(figsize=(10, 6))
        plt.plot(t, global_norms, 'b-', linewidth=2, label="Global Spectral Norm")
        plt.axhline(y=10, color='r', linestyle='--', label="Threshold")
        plt.title("Global Spectral Norm – Real Metro Commuting")
        plt.xlabel("Days")
        plt.ylabel(r"$||V||_{L^1}$")
        plt.legend()
        plt.grid(alpha=0.3)
        plt.savefig("global_multi_node_real.png", dpi=300)
        plt.show()

        # Per-node norms
        plt.figure(figsize=(12, 7))
        labels = ["NYC", "LA", "Chicago", "Houston", "Phoenix"]
        for i in range(len(pops)):
            plt.plot(t, norms_per_node[:, i], label=labels[i])
        plt.axhline(y=10, color='r', linestyle='--')
        plt.title("Per-Node Spectral Norms – Real Metro Spread")
        plt.xlabel("Days")
        plt.ylabel(r"$||V||_{L^1}$ per Node")
        plt.legend()
        plt.grid(alpha=0.3)
        plt.savefig("per_node_multi_real.png", dpi=300)
        plt.show()

        # Alerts
        print("\nFold Alert Days (norm > 10):")
        for i, label in enumerate(labels):
            alert_idx = np.argmax(norms_per_node[:, i] > 10)
            if norms_per_node[:, i].max() > 10:
                print(f"{label}: alert at day {t[alert_idx]:.1f}, max {norms_per_node[:, i].max():.2f}")
            else:
                print(f"{label}: no alert (max {norms_per_node[:, i].max():.2f})")

        gidx = np.argmax(global_norms > 10)
        if global_norms.max() > 10:
            print(f"\nGlobal alert at day {t[gidx]:.1f}, max {global_norms.max():.2f}")
        else:
            print(f"\nNo global alert (max {global_norms.max():.2f})")

#             (base) brendanlynch@Brendans-Laptop pandemics % python multiNode_real_commuting.py
# Reading gzipped LODES for NYC: ./ny_od_main_JT00_2020.csv.gz
# Reading gzipped LODES for LA: ./ca_od_main_JT00_2020.csv.gz
# Reading gzipped LODES for Chicago: ./il_od_main_JT00_2020.csv.gz
# Reading gzipped LODES for Houston: ./tx_od_main_JT00_2020.csv.gz
# Reading gzipped LODES for Phoenix: ./az_od_main_JT00_2020.csv.gz

# Real Metro-Aggregated + Long-Distance Commuting Matrix (row-normalized):
# [[0.9091 0.0227 0.0227 0.0227 0.0227]
#  [0.0227 0.9091 0.0227 0.0227 0.0227]
#  [0.0227 0.0227 0.9091 0.0227 0.0227]
#  [0.0227 0.0227 0.0227 0.9091 0.0227]
#  [0.0227 0.0227 0.0227 0.0227 0.9091]]
# Rows/Columns: ['NYC', 'LA', 'Chicago', 'Houston', 'Phoenix']
# Mobility matrix (row-normalized):
#  [[0.9091 0.0227 0.0227 0.0227 0.0227]
#  [0.0227 0.9091 0.0227 0.0227 0.0227]
#  [0.0227 0.0227 0.9091 0.0227 0.0227]
#  [0.0227 0.0227 0.0227 0.9091 0.0227]
#  [0.0227 0.0227 0.0227 0.0227 0.9091]]

# Fold Alert Days (norm > 10):
# NYC: no alert (max 1.63)
# LA: alert at day 33.7, max 9952.39
# Chicago: no alert (max 1.64)
# Houston: no alert (max 1.64)
# Phoenix: no alert (max 1.74)

# Global alert at day 33.4, max 11715.72
# (base) brendanlynch@Brendans-Laptop pandemics % 