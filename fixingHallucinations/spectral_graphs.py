# spectral_graphs.py
import numpy as np

def build_graph(x, distance_metric="hamming"):
    """
    Builds a weighted graph from token vectors x.

    Args:
        x: np.ndarray of shape (n_nodes, d), input vectors
        distance_metric: str, "hamming" or "l2"

    Returns:
        A: np.ndarray, adjacency matrix of shape (n_nodes, n_nodes)
    """
    n_nodes = x.shape[0]  # use actual number of vectors
    A = np.zeros((n_nodes, n_nodes), dtype=float)

    for i in range(n_nodes):
        for j in range(n_nodes):
            if i == j:
                A[i, j] = 0.0
            else:
                if distance_metric == "hamming":
                    # Count mismatches element-wise
                    mismatch_count = np.sum(x[i] != x[j])
                elif distance_metric == "l2":
                    mismatch_count = np.linalg.norm(x[i] - x[j])
                else:
                    raise ValueError(f"Unknown distance_metric {distance_metric}")
                A[i, j] = 1.0 / (1 + mismatch_count)

    return A

def compute_lambda2(A):
    """
    Computes the algebraic connectivity (second-smallest eigenvalue) of the Laplacian.

    Args:
        A: np.ndarray, adjacency matrix

    Returns:
        lambda2: float, second-smallest eigenvalue
    """
    L = np.diag(np.sum(A, axis=1)) - A  # Laplacian
    eigs = np.linalg.eigvalsh(L)       # use eigvalsh for symmetric
    eigs_sorted = np.sort(eigs)
    if len(eigs_sorted) < 2:
        return eigs_sorted[0]
    return eigs_sorted[1]
