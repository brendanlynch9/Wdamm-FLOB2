import numpy as np

def geometric_median(points, eps=1e-10, max_iter=500):
    y = np.mean(points, axis=0)
    for _ in range(max_iter):
        dists = np.linalg.norm(points - y, axis=1)
        dists = np.maximum(dists, 1e-12)
        weights = 1.0 / dists
        y_new = np.average(points, axis=0, weights=weights)
        if np.linalg.norm(y_new - y) < eps:
            break
        y = y_new
    return y

def star_length(points, pt):
    return np.sum(np.linalg.norm(points - pt, axis=1))

def run_spectral_scan():
    np.random.seed(42)
    configs = {
        "3D Random (n=100)": np.random.uniform(-10, 10, (100, 3)),
        "2D Prime Offset Circle": np.array([
            [np.cos(2*np.pi*k/13) + 0.017, np.sin(2*np.pi*k/13) - 0.013]
            for k in range(13)
        ]),
        "2D Clusters": np.concatenate([
            np.random.normal([-10, -10], 0.5, (20, 2)),
            np.random.normal([10, 10], 0.5, (20, 2)),
            np.random.normal([0, 0], 2.0, (20, 2))
        ]),
        "2D Corridor (n=200)": np.column_stack([
            np.linspace(-50, 50, 200),
            np.sin(np.linspace(0, 10, 200)) * 0.2 + np.random.normal(0, 0.05, 200)
        ])
    }

    grids = [8, 12, 16, 20, 22, 23, 24, 25, 26, 30, 36, 48, 60, 72, 96]
    
    print(f"{'Config':<25} {'Grid':>5} {'Len Err %':>12} {'Dist (L2)':>12} {'Ratio'}")
    print("-" * 75)

    for name, pts in configs.items():
        med = geometric_median(pts)
        l_cont = star_length(pts, med)
        
        for g in grids:
            step = 1.0 / g
            q_med = np.round(med / step) * step
            l_quant = star_length(pts, q_med)
            
            rel_err = 100 * (l_quant - l_cont) / l_cont
            dist_err = np.linalg.norm(q_med - med)
            ratio = rel_err / dist_err if dist_err > 1e-12 else 0
            
            print(f"{name:<25} 1/{g:<3} {rel_err:12.7f}% {dist_err:12.7f} {ratio:10.5f}")
        print("-" * 75)

if __name__ == "__main__":
    run_spectral_scan()

#     (base) brendanlynch@Brendans-Laptop SteinerTree % python spectralResolution.py
# Config                     Grid    Len Err %    Dist (L2) Ratio
# ---------------------------------------------------------------------------
# 3D Random (n=100)         1/8      0.0016217%    0.0680266    0.02384
# 3D Random (n=100)         1/12     0.0002781%    0.0275266    0.01010
# 3D Random (n=100)         1/16     0.0003564%    0.0293575    0.01214
# 3D Random (n=100)         1/20     0.0000787%    0.0149112    0.00528
# 3D Random (n=100)         1/22     0.0000658%    0.0130388    0.00505
# 3D Random (n=100)         1/23     0.0001769%    0.0229224    0.00772
# 3D Random (n=100)         1/24     0.0001355%    0.0195194    0.00694
# 3D Random (n=100)         1/25     0.0001228%    0.0176768    0.00695
# 3D Random (n=100)         1/26     0.0001029%    0.0156867    0.00656
# 3D Random (n=100)         1/30     0.0000787%    0.0149112    0.00528
# 3D Random (n=100)         1/36     0.0000490%    0.0109896    0.00446
# 3D Random (n=100)         1/48     0.0000561%    0.0116332    0.00482
# 3D Random (n=100)         1/60     0.0000676%    0.0133630    0.00506
# 3D Random (n=100)         1/72     0.0000361%    0.0093039    0.00389
# 3D Random (n=100)         1/96     0.0000139%    0.0061104    0.00227
# ---------------------------------------------------------------------------
# 2D Prime Offset Circle    1/8      0.0114503%    0.0214009    0.53504
# 2D Prime Offset Circle    1/12     0.0114503%    0.0214009    0.53504
# 2D Prime Offset Circle    1/16     0.0114503%    0.0214009    0.53504
# 2D Prime Offset Circle    1/20     0.0114503%    0.0214009    0.53504
# 2D Prime Offset Circle    1/22     0.0114503%    0.0214009    0.53504
# 2D Prime Offset Circle    1/23     0.0114503%    0.0214009    0.53504
# 2D Prime Offset Circle    1/24     0.0114503%    0.0214009    0.53504
# 2D Prime Offset Circle    1/25     0.0114503%    0.0214009    0.53504
# 2D Prime Offset Circle    1/26     0.0114503%    0.0214009    0.53504
# 2D Prime Offset Circle    1/30     0.0108947%    0.0208753    0.52190
# 2D Prime Offset Circle    1/36     0.0071291%    0.0168867    0.42217
# 2D Prime Offset Circle    1/48     0.0019014%    0.0087210    0.21803
# 2D Prime Offset Circle    1/60     0.0003389%    0.0036818    0.09204
# 2D Prime Offset Circle    1/72     0.0002617%    0.0032356    0.08089
# 2D Prime Offset Circle    1/96     0.0005342%    0.0046226    0.11556
# ---------------------------------------------------------------------------
# 2D Clusters               1/8      0.0022170%    0.0589143    0.03763
# 2D Clusters               1/12     0.0010500%    0.0382379    0.02746
# 2D Clusters               1/16     0.0001465%    0.0146017    0.01003
# 2D Clusters               1/20     0.0001205%    0.0135022    0.00892
# 2D Clusters               1/22     0.0000757%    0.0111079    0.00681
# 2D Clusters               1/23     0.0000559%    0.0087323    0.00640
# 2D Clusters               1/24     0.0003011%    0.0207618    0.01450
# 2D Clusters               1/25     0.0003361%    0.0225560    0.01490
# 2D Clusters               1/26     0.0001685%    0.0152021    0.01109
# 2D Clusters               1/30     0.0000564%    0.0090395    0.00623
# 2D Clusters               1/36     0.0000019%    0.0017723    0.00109
# 2D Clusters               1/48     0.0000569%    0.0088622    0.00642
# 2D Clusters               1/60     0.0000564%    0.0090395    0.00623
# 2D Clusters               1/72     0.0000019%    0.0017723    0.00109
# 2D Clusters               1/96     0.0000231%    0.0061128    0.00379
# ---------------------------------------------------------------------------
# 2D Corridor (n=200)       1/8      0.0000077%    0.0394800    0.00020
# 2D Corridor (n=200)       1/12     0.0004913%    0.0394395    0.01246
# 2D Corridor (n=200)       1/16     0.0000091%    0.0232001    0.00039
# 2D Corridor (n=200)       1/20     0.0001669%    0.0268964    0.00621
# 2D Corridor (n=200)       1/22     0.0000222%    0.0196273    0.00113
# 2D Corridor (n=200)       1/23     0.0000025%    0.0100062    0.00025
# 2D Corridor (n=200)       1/24     0.0000019%    0.0032138    0.00059
# 2D Corridor (n=200)       1/25     0.0000151%    0.0085232    0.00178
# 2D Corridor (n=200)       1/26     0.0000387%    0.0159199    0.00243
# 2D Corridor (n=200)       1/30     0.0000110%    0.0064483    0.00170
# 2D Corridor (n=200)       1/36     0.0000415%    0.0118142    0.00352
# 2D Corridor (n=200)       1/48     0.0000019%    0.0032138    0.00059
# 2D Corridor (n=200)       1/60     0.0000110%    0.0064483    0.00170
# 2D Corridor (n=200)       1/72     0.0000019%    0.0032138    0.00059
# 2D Corridor (n=200)       1/96     0.0000019%    0.0032138    0.00059
# ---------------------------------------------------------------------------
# (base) brendanlynch@Brendans-Laptop SteinerTree % 

