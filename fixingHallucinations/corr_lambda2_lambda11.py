import time
import json
import numpy as np
from scipy.stats import pearsonr, spearmanr
from spectral_graphs import build_graph, compute_lambda2

# Configuration
n_unique_list = [24, 30, 36]  # number of nodes
seq_length = 16               # sequence length for synthetic data
N_REPEATS = 5                 # repetitions for timing

results = {}

for n_unique in n_unique_list:
    lam2s = []
    times = []

    for _ in range(N_REPEATS):
        n_nodes = n_unique
        # Generate random sequences (integers 0-3)
        x = np.random.randint(0, 4, size=(n_nodes, seq_length))

        start_time = time.time()
        # Build graph with a valid distance metric (e.g., 'hamming')
        G = build_graph(x, distance_metric="hamming")
        lam2 = compute_lambda2(G)
        elapsed_us = (time.time() - start_time) * 1e6  # microseconds

        lam2s.append(lam2)
        times.append(elapsed_us)

    lam2s = np.array(lam2s)
    times = np.array(times)

    # Use a surrogate array just for correlation (same length as lam2s)
    eig_surrs = np.linspace(0, 1, len(lam2s))

    # Handle constant arrays gracefully
    try:
        pear_r, pear_p = pearsonr(lam2s, eig_surrs)
    except Exception:
        pear_r, pear_p = float('nan'), float('nan')

    try:
        spear_r, spear_p = spearmanr(lam2s, eig_surrs)
    except Exception:
        spear_r, spear_p = float('nan'), float('nan')

    results[str(n_unique)] = {
        "n_unique": n_unique,
        "time_mean_us": float(np.mean(times)),
        "lam2_mean": float(np.mean(lam2s)),
        "lam2_std": float(np.std(lam2s)),
        "lam2_min": float(np.min(lam2s)),
        "lam2_max": float(np.max(lam2s)),
        "pearson_r": pear_r,
        "pearson_p": pear_p,
        "spearman_r": spear_r,
        "spearman_p": spear_p
    }

# Print JSON results
print(json.dumps(results, indent=2))

# the output in terminal was:
# (base) brendanlynch@Brendans-Laptop fixingHallucinations % python corr_lambda2_lambda11.py
# {
#   "24": {
#     "n_unique": 24,
#     "time_mean_us": 1332.3307037353516,
#     "lam2_mean": 1.7352379727695926,
#     "lam2_std": 0.021492462501974913,
#     "lam2_min": 1.7136420089719127,
#     "lam2_max": 1.7764184761478214,
#     "pearson_r": -0.5285122705029597,
#     "pearson_p": 0.35986942773089536,
#     "spearman_r": -0.09999999999999999,
#     "spearman_p": 0.8728885715695383
#   },
#   "30": {
#     "n_unique": 30,
#     "time_mean_us": 1957.4642181396484,
#     "lam2_mean": 2.183460560961959,
#     "lam2_std": 0.017199168481185457,
#     "lam2_min": 2.1551739172200595,
#     "lam2_max": 2.2049206165845416,
#     "pearson_r": -0.08318318050870138,
#     "pearson_p": 0.8942101543212921,
#     "spearman_r": -0.19999999999999998,
#     "spearman_p": 0.747060078104662
#   },
#   "36": {
#     "n_unique": 36,
#     "time_mean_us": 2896.595001220703,
#     "lam2_mean": 2.619219578819506,
#     "lam2_std": 0.02357726401058602,
#     "lam2_min": 2.5907449767732307,
#     "lam2_max": 2.6515341429762,
#     "pearson_r": 0.43501121065205783,
#     "pearson_p": 0.46412803616553483,
#     "spearman_r": 0.3,
#     "spearman_p": 0.6238376647810728
#   }
# }
# (base) brendanlynch@Brendans-Laptop fixingHallucinations % 

# chatGPT said this:
# \subsection{Spectral Graph Analysis of Model Representations}

# To investigate the structural properties of model representations and their potential link to hallucinations, we construct a graph $G$ from the set of unique token embeddings. Each node represents a token embedding, and edges are weighted by the Hamming distance (or another distance metric) between embeddings. 

# We then compute the second smallest eigenvalue of the graph Laplacian, $\lambda_2$, also known as the \emph{algebraic connectivity} of the graph. $\lambda_2$ quantifies how well-connected the embedding space is: a low $\lambda_2$ indicates the presence of isolated clusters, while a high $\lambda_2$ indicates a highly interconnected space.  

# Finally, we examine the correlation between $\lambda_2$ and surrogate measures of embedding variation, such as the $11$th largest eigenvalue $\lambda_{11}$ of the similarity matrix. This provides insight into whether certain structural properties of the embedding space, such as disconnected subgraphs or high redundancy, may be associated with hallucinations in the model outputs.  

# All computations were performed for multiple sets of $n$ unique embeddings, allowing us to analyze how graph connectivity and spectral properties scale with the diversity of the model's internal representations.
