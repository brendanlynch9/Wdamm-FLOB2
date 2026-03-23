import numpy as np
import networkx as nx
import warnings

# Note: This code implements the mathematical concepts from the provided papers.
# For the CGA protocol, since no cryptography library is available, we use a mock decryption function.
# In a real implementation, use a library like 'cryptography' for AES-GCM.

class SpectralGate:
    """
    Implements the Spectral Gate from "The Redundancy Cliff" paper.
    Computes κ_x and provides pruning logic.
    """
    def __init__(self):
        # Precompute λ2 min and max over n=0 to 23
        self.lambda_values = [self._compute_lambda2(i) for i in range(24)]
        self.lambda_min = min(self.lambda_values)
        self.lambda_max = max(self.lambda_values)

    def _compute_lambda2(self, n):
        V = [1, 5, 7, 11, 13, 17, 19, 23]
        P = [5, 7, 11, 13, 17]
        G = nx.Graph()
        G.add_nodes_from(V)
        for i in range(len(V)):
            ri = V[i]
            for j in range(len(V)):
                if i == j:
                    continue
                rj = V[j]
                sum_ind = sum(1 for p in P if (ri * rj % p) != (n % p))
                Aij = 1 / (1 + sum_ind)
                G.add_edge(ri, rj, weight=Aij)
        L = nx.laplacian_matrix(G).todense()
        eigenvalues = np.linalg.eigvalsh(L)
        return eigenvalues[1]  # algebraic connectivity

    def compute_kappa_x(self, x):
        """
        Compute κ_x for input tokens x (list or array of integers).
        """
        x = np.array(x)
        norm = np.linalg.norm(x)
        n = int(np.floor(norm ** 2) % 24)
        lambda2 = self._compute_lambda2(n)
        kappa_x = (lambda2 - self.lambda_min) / (self.lambda_max - self.lambda_min)
        return kappa_x

    def prune_dimension(self, kappa_x, total_dim):
        """
        Pruning logic: retained fraction ≈ kappa_x * total_dim
        """
        keep_dim = max(1, int(kappa_x * total_dim))
        return keep_dim

# Example usage:
# gate = SpectralGate()
# kappa = gate.compute_kappa_x([1, 2, 3])
# print(kappa)
# keep_len = gate.prune_dimension(kappa, 1024)
# print(keep_len)


class ModularFingerprint:
    """
    Implements the O(1) Modular Fingerprint from the second paper.
    Computes λ2 for semantic correlation prediction.
    """
    def compute_lambda2(self, x):
        """
        Compute λ2 for input tokens x (list or array of integers).
        Returns None if discarded.
        """
        x = np.array(x)
        norm = np.linalg.norm(x)
        n = int(np.floor(norm ** 2) % 24)
        R24 = [1, 5, 7, 11, 13, 17, 19, 23]
        P = [5, 7, 11, 13, 17]
        Vn = [(r1, r2) for r1 in R24 for r2 in R24 if (r1 * r2 % 24) == (n % 24)]
        if len(Vn) <= 2:
            return None
        G = nx.Graph()
        G.add_nodes_from(range(len(Vn)))  # Use indices for nodes
        for i in range(len(Vn)):
            r1, r2 = Vn[i]
            prod_i = r1 * r2
            for j in range(len(Vn)):
                if i == j:
                    continue
                r1p, r2p = Vn[j]
                prod_j = r1p * r2p
                sum_diff = sum(abs((prod_i % p) - (prod_j % p)) for p in P)
                Aij = 1 / (1 + sum_diff)
                G.add_edge(i, j, weight=Aij)
        L = nx.laplacian_matrix(G).todense()
        eigenvalues = np.linalg.eigvalsh(L)
        return eigenvalues[1]

# Example usage:
# fp = ModularFingerprint()
# lambda2 = fp.compute_lambda2([1, 2, 3])
# print(lambda2)


class ComplexGatedAuthentication:
    """
    Implements the CGA Protocol from the third paper.
    Uses a simplified λ2 lookup (mocked here as normalized from spectral gate).
    Crypto part is mocked due to lack of library.
    """
    def __init__(self):
        warnings.warn("Crypto is mocked; use a real library like 'cryptography' for production.")
        self.T = [0.3, 0.4, 0.5, 0.6, 0.3, 0.4]  # Mock lookup table based on examples
        self.lambda_min, self.lambda_max = 0.3, 0.6  # From paper
        self.secured_state = {"last_counter": 0}  # Mock secured state

    def compute_lambda2(self, x):
        """
        Compute λ2 for byte payload x (list or array of bytes/integers 0-255).
        Uses lookup as per paper.
        """
        x = np.array(x)
        norm = np.linalg.norm(x)
        idx = int(np.floor(norm ** 2) % 24) % 6
        return self.T[idx]

    def verify_cga(self, token, expected_payload, key):
        """
        Mock verification. In real, use AES-GCM decrypt.
        Assume token is dict with 'ciphertext', 'aad', etc.
        Returns 'ACCEPT' or 'FAIL: reason'
        """
        # Mock decrypt
        decryption_success = True  # Assume success for demo
        if not decryption_success:
            return 'FAIL, Cryptographic Forgery'

        # Mock extracted P_CGA
        counter = 2  # From example log
        lambda2 = 0.591  # From example
        hash_x = hash(str(expected_payload))  # Mock hash

        # Mock extracted hash
        extracted_hash = hash(str(expected_payload))  # Assume match for demo

        c_last = self.secured_state['last_counter']

        if counter <= c_last:
            return 'FAIL, Replay/Non-Monotonic'

        if extracted_hash != hash_x:
            return 'FAIL, Payload Tampering'

        # Update state
        self.secured_state['last_counter'] = counter
        return 'ACCEPT'

# Example usage:
# cga = ComplexGatedAuthentication()
# lambda2 = cga.compute_lambda2([ord(c) for c in "hello world"])
# print(lambda2)
# result = cga.verify_cga({'ciphertext': 'mock'}, "hello world", 'mock_key')
# print(result)


# To tie it all together: A simple demo function
def demo_all(x_tokens, x_bytes, total_dim=1024):
    gate = SpectralGate()
    kappa_x = gate.compute_kappa_x(x_tokens)
    keep_dim = gate.prune_dimension(kappa_x, total_dim)
    print(f"Spectral Gate κ_x: {kappa_x}, Pruned dim: {keep_dim}")

    fp = ModularFingerprint()
    lambda2_fp = fp.compute_lambda2(x_tokens)
    print(f"Modular Fingerprint λ2: {lambda2_fp}")

    cga = ComplexGatedAuthentication()
    lambda2_cga = cga.compute_lambda2(x_bytes)
    print(f"CGA λ2: {lambda2_cga}")

# Run demo
if __name__ == "__main__":
    x_tokens = [1, 2, 3, 4]  # Example token IDs
    x_bytes = [ord(c) for c in "hello world"]  # Example bytes
    demo_all(x_tokens, x_bytes)

#     the code output in terminal was:
#     (base) brendanlynch@Brendans-Laptop fixingHallucinations % python test1.py
# Spectral Gate κ_x: 0.0782414741474476, Pruned dim: 80
# Modular Fingerprint λ2: None
# /Users/brendanlynch/Desktop/zzzzzzzhourglass/fixingHallucinations/test1.py:112: UserWarning: Crypto is mocked; use a real library like 'cryptography' for production.
#   warnings.warn("Crypto is mocked; use a real library like 'cryptography' for production.")
# CGA λ2: 0.5
# (base) brendanlynch@Brendans-Laptop fixingHallucinations % 
