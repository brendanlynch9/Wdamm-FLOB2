import numpy as np
N, sectors, Sgrav = 100000, 24, 0.04344799
n = np.arange(1, N+1)
theta = np.linspace(0, 2*np.pi, 4096, endpoint=False)
a_n = Sgrav * np.cos(2*np.pi*n/24) / np.log(1 + np.abs(np.cos(2*np.pi*n/24)))
coeff = a_n / np.log(n+1)
V = np.zeros_like(theta)
for j, th in enumerate(theta):
    V[j] = np.sum(coeff * np.cos(2*np.pi*n*th/24))
# sector integration follows standard trapezoidal rule