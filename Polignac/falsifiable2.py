import numpy as np
from scipy.fft import fft, ifft
import matplotlib.pyplot as plt
from math import log, sqrt

def get_hl_constant(h):
    """
    Generalized Hardy-Littlewood constant 2 * C_h for even gap h.
    C_2 ≈ 0.660161815846869 (twin prime constant)
    For even h > 2: multiply by product over odd primes p|h of (p-1)/(p-2)
    This is the standard, undisputed formula from 1923.
    """
    if h % 2 != 0 or h <= 0:
        return 0.0
    if h == 2:
        return 2 * 0.660161815846869
    C2 = 0.660161815846869
    factors = set()
    n = h
    i = 3  # start from odd primes
    while i * i <= n:
        if n % i == 0:
            factors.add(i)
            while n % i == 0:
                n //= i
        i += 2
    if n > 2:
        factors.add(n)
    if not factors:
        return 2 * C2
    prod = np.prod([(p - 1) / (p - 2) for p in factors])
    return 2 * C2 * prod

def sieve_primes_up_to(limit):
    """Fast Eratosthenes sieve to get primes up to limit."""
    if limit < 2:
        return []
    is_prime = np.ones(limit + 1, dtype=bool)
    is_prime[0:2] = False
    for i in range(2, int(sqrt(limit)) + 1):
        if is_prime[i]:
            is_prime[i*i : limit+1 : i] = False
    return np.nonzero(is_prime)[0]

def von_mangoldt_up_to(N, primes):
    """Compute von Mangoldt function Λ(n) for n=1 to N."""
    Lambda = np.zeros(N + 1, dtype=float)
    for p in primes:
        if p > N:
            break
        pk = p
        while pk <= N:
            Lambda[pk] = log(p)
            pk *= p
    return Lambda[1:]  # index 1 to N

def compute_spectral_density(N=10**7, max_h=200, plot=True):
    """
    Main function: Compute empirical spectral density via Wiener-Khinchine
    for even gaps h=2,4,...,max_h.
    
    Returns table of results + plots observed vs theoretical.
    """
    print(f"Running spectral diagnostic for Polignac heuristic at N = {N:,}")
    print("This uses only standard number theory + FFT (no axioms).")
    
    # 1. Get primes and Λ(n)
    primes = sieve_primes_up_to(N + 100)  # slight buffer
    Lambda = von_mangoldt_up_to(N, primes)
    
    # 2. Pad to next power of 2 for clean FFT
    M = 1 << (N * 2 - 1).bit_length()  # safe padding
    padded = np.zeros(M, dtype=complex)
    padded[:N] = Lambda
    
    # 3. Power spectrum |FFT|^2 / N
    fft_vals = fft(padded)
    power = np.abs(fft_vals)**2 / N
    
    # 4. Autocorrelation = real part of IFFT(power)
    autocorr = ifft(power).real
    
    # 5. Collect data for even h
    results = []
    max_dev = 0
    for h in range(2, max_h + 2, 2):
        theo = get_hl_constant(h)
        obs = autocorr[h] if h < len(autocorr) else np.nan
        if not np.isnan(obs):
            rel_err = abs(obs - theo) / theo * 100 if theo > 0 else np.inf
            dev = abs(obs - theo)
            max_dev = max(max_dev, dev)
            results.append((h, theo, obs, dev, rel_err))
    
    # 6. Print table
    print("\n{:<6} {:<15} {:<15} {:<12} {:<10}".format(
        "Gap h", "Theoretical 2Ch", "Observed P(h)", "Abs Diff", "Rel Err %"))
    print("-" * 60)
    for h, theo, obs, dev, rel in results:
        print(f"{h:<6} {theo:<15.8f} {obs:<15.8f} {dev:<12.6f} {rel:>8.3f}%")
    
    print(f"\nMax absolute deviation: {max_dev:.6f}")
    if max_dev > 0.1:
        print("WARNING: Large deviation detected — check larger N or code.")
    else:
        print("Convergence appears strong (typical for N=10^7).")
    
    # 7. Optional plot
    if plot:
        hs = [r[0] for r in results]
        theos = [r[1] for r in results]
        obss = [r[2] for r in results]
        
        plt.figure(figsize=(12, 6))
        plt.plot(hs, theos, 'o-', label='Theoretical 2C_h', linewidth=1.5)
        plt.plot(hs, obss, 'x--', label='Observed at N=10^7', linewidth=1.5)
        plt.xlabel("Even gap h")
        plt.ylabel("Spectral density / pair correlation")
        plt.title("Empirical vs Theoretical Prime-Pair Densities\n(Hardy–Littlewood heuristic check)")
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.show()
    
    return results

# Run it (adjust N as your machine allows; 10^7 is ~1-2 min on typical laptop)
if __name__ == "__main__":
    compute_spectral_density(N=10000000, max_h=200, plot=True)

#     (base) brendanlynch@Brendans-Laptop Polignac % python falsifiable2.py
# Running spectral diagnostic for Polignac heuristic at N = 10,000,000
# This uses only standard number theory + FFT (no axioms).

# Gap h  Theoretical 2Ch Observed P(h)   Abs Diff     Rel Err % 
# ------------------------------------------------------------
# 2      1.32032363      1.32716725      0.006844        0.518%
# 4      1.98048545      1.31859278      0.661893       33.421%
# 6      1.65040454      2.63619798      0.985793       59.730%
# 8      1.54037757      1.31729997      0.223078       14.482%
# 10     1.48536409      1.75925901      0.273895       18.440%
# 12     3.96097090      2.64379865      1.317172       33.254%
# 14     1.43035060      1.58462375      0.154273       10.786%
# 16     1.41463246      1.31786259      0.096770        6.841%
# 18     2.64064726      2.64252623      0.001879        0.071%
# 20     1.39367494      1.75909141      0.365416       26.220%
# 22     1.38633981      1.47009167      0.083752        6.041%
# 24     3.08075514      2.63882878      0.441926       14.345%
# 26     1.37533712      1.44358936      0.068252        4.963%
# 28     1.37110531      1.58540392      0.214299       15.630%
# 30     2.97072817      3.51939936      0.548671       18.469%
# 32     1.36433442      1.31766367      0.046671        3.421%
# 34     1.36158375      1.40886213      0.047278        3.472%
# 36     3.96097090      2.65602322      1.304948       32.945%
# 38     1.35699929      1.39780741      0.040808        3.007%
# 40     2.05383676      1.75967256      0.294164       14.323%
# 42     2.86070120      3.16760572      0.306905       10.728%
# 44     1.35175991      1.46621532      0.114455        8.467%
# 46     1.35033099      1.37923913      0.028908        2.141%
# 48     2.82926493      2.63850431      0.190761        6.742%
# 50     1.76043151      1.76039447      0.000037        0.002%
# 52     1.34673010      1.44243756      0.095707        7.107%
# 54     2.64064726      2.64059831      0.000049        0.002%
# 56     1.84845308      1.57802643      0.270427       14.630%
# 58     1.34390084      1.36486627      0.020965        1.560%
# 60     2.78734989      3.51385828      0.726508       26.064%
# 62     1.34232903      1.36348704      0.021158        1.576%
# 64     1.34161917      1.31895683      0.022662        1.689%
# 66     2.77267963      2.93226256      0.159583        5.756%
# 68     1.34032854      1.40524542      0.064917        4.843%
# 70     1.90713413      2.10823853      0.201104       10.545%
# 72     3.08075514      2.63727634      0.443479       14.395%
# 74     1.33866146      1.35556504      0.016904        1.263%
# 76     1.33816584      1.39856457      0.060399        4.514%
# 78     2.75067423      2.88169155      0.131017        4.763%
# 80     1.88617662      1.76613079      0.120046        6.365%
# 82     1.33682768      1.35143881      0.014611        1.093%
# 84     2.74221062      3.16633741      0.424127       15.467%
# 86     1.33604177      1.35129881      0.015257        1.142%
# 88     1.33567623      1.46748469      0.131808        9.868%
# 90     2.97072817      3.52565192      0.554924       18.680%
# 92     1.33499389      1.38498909      0.049995        3.745%
# 94     1.33467498      1.35155462      0.016880        1.265%
# 96     2.72866884      2.63655418      0.092115        3.376%
# 98     1.58438836      1.57837873      0.006010        0.379%
# 100    2.64064726      1.76090198      0.879745       33.316%
# 102    2.72316749      2.81869505      0.095528        3.508%
# 104    1.33326798      1.44241158      0.109144        8.186%
# 106    1.33301905      1.34667977      0.013661        1.025%
# 108    3.96097090      2.63368880      1.327282       33.509%
# 110    1.84845308      1.95016019      0.101707        5.502%
# 112    1.69755896      1.58187544      0.115684        6.815%
# 114    2.71399858      2.79391575      0.079917        2.945%
# 116    1.33190542      1.36566120      0.033756        2.534%
# 118    1.33170573      1.34085796      0.009152        0.687%
# 120    4.10767352      3.52208517      0.585588       14.256%
# 122    1.33132633      1.34137921      0.010053        0.755%
# 124    1.33114596      1.36428877      0.033143        2.490%
# 126    2.86070120      3.17269003      0.311989       10.906%
# 128    1.33080239      1.32025251      0.010550        0.793%
# 130    1.83378282      1.91799629      0.084213        4.592%
# 132    2.70351982      2.93287885      0.229359        8.484%
# 134    1.33032608      1.33877038      0.008444        0.635%
# 136    1.33017679      1.40069088      0.070514        5.301%
# 138    2.70066197      2.76120554      0.060544        2.242%
# 140    1.82814041      2.10705605      0.278916       15.257%
# 142    1.32975451      1.34052663      0.010772        0.810%
# 144    2.82926493      2.63580918      0.193456        6.838%
# 146    1.32949255      1.34254854      0.013056        0.982%
# 148    1.32936694      1.35665740      0.027290        2.053%
# 150    3.52086302      3.52691193      0.006049        0.172%
# 152    1.32912579      1.39237116      0.063245        4.758%
# 154    1.66360778      1.76261662      0.099009        5.951%
# 156    2.69346021      2.87854004      0.185080        6.871%
# 158    1.32878724      1.33856359      0.009776        0.736%
# 160    1.81911256      1.75794448      0.061168        3.363%
# 162    2.64064726      2.64142310      0.000776        0.029%
# 164    1.32847378      1.35169038      0.023217        1.748%
# 166    1.32837439      1.33824931      0.009875        0.743%
# 168    3.69690617      3.16907926      0.527827       14.278%
# 170    1.81544499      1.88027743      0.064832        3.571%
# 172    1.32809024      1.35770063      0.029610        2.230%
# 174    2.68780168      2.74004240      0.052241        1.944%
# 176    1.57181385      1.46733014      0.104484        6.647%
# 178    1.32782547      1.33400131      0.006176        0.465%
# 180    2.78734989      3.52062377      0.733274       26.307%
# 182    1.65040454      1.72253507      0.072131        4.370%
# 184    1.32757816      1.38596240      0.058384        4.398%
# 186    2.68465805      2.73284061      0.048183        1.795%
# 188    1.32742215      1.34822853      0.020806        1.567%
# 190    1.80933238      1.86363193      0.054300        3.001%
# 192    2.68323835      2.64115894      0.042079        1.568%
# 194    1.32720032      1.32998372      0.002783        0.210%
# 196    2.37658254      1.58612507      0.790457       33.260%
# 198    2.77267963      2.93662884      0.163949        5.913%
# 200    2.05383676      1.76193347      0.291903       14.213%

# Max absolute deviation: 1.327282
# WARNING: Large deviation detected — check larger N or code.
# 2026-01-25 06:14:19.231 python[29569:31679551] The class 'NSSavePanel' overrides the method identifier.  This method is implemented by class 'NSWindow'
# (base) brendanlynch@Brendans-Laptop Polignac % 