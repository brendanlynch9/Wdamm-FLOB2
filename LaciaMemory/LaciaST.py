import numpy as np
import itertools

class LaciaSovereignScanner:
    def __init__(self):
        self.C_UFT_F = 0.00311903  
        self.LYNCH_SLOPE = -1.6466 
        self.DELTA = 0.005 
        
        # UNIVERSAL ARCHIVE
        self.ARCHIVE = {
            "Hydrogen (H)": (13.598, 1.008), "Helium (He)": (24.587, 4.002),
            "Carbon (C)": (11.260, 12.011), "Nitrogen (N)": (14.534, 14.007),
            "Oxygen (O)": (13.618, 15.999), "Aluminum (Al)": (5.986, 26.982),
            "Silicon (Si)": (8.152, 28.085), "Iron (Fe)": (7.902, 55.845),
            "Copper (Cu)": (7.726, 63.546), "Silver (Ag)": (7.576, 107.868),
            "Gold (Au)": (9.226, 196.966), "Lead (Pb)": (7.417, 207.2),
            "Uranium (U)": (6.194, 238.028), "Water (H2O)": (12.610, 18.015),
            "Chromium (Cr)": (6.767, 51.996), "Nickel (Ni)": (7.640, 58.693)
        }

    def solve_manifold(self, total_ev):
        items = list(self.ARCHIVE.items())
        
        # 1. Single Element Check
        for name, (res, weight) in items:
            if abs(total_ev - res) < self.DELTA:
                return [(name, weight, res)]
        
        # 2. Doublet Check (Alloys)
        for combo in itertools.combinations(items, 2):
            res_sum = sum(c[1][0] for c in combo)
            if abs(total_ev - res_sum) < self.DELTA:
                return [(c[0], c[1][1], c[1][0]) for c in combo]
                
        # 3. Triplet Check (Super-alloys)
        for combo in itertools.combinations(items, 3):
            res_sum = sum(c[1][0] for c in combo)
            if abs(total_ev - res_sum) < self.DELTA:
                return [(c[0], c[1][1], c[1][0]) for c in combo]
        
        return []

    def scan(self, signal, target_name="Target"):
        v_x = np.abs(signal).flatten()
        k = np.arange(1, len(v_x) + 1)
        slope, _ = np.polyfit(np.log(k), np.log(np.where(v_x > 1e-12, v_x, 1e-12)), 1)
        total_ev = v_x[0] / self.C_UFT_F
        elements = self.solve_manifold(total_ev)
        
        print(f"--- [LACIA SCAN: {target_name}] ---")
        if not elements:
            print(f"!! ALERT: UNIDENTIFIED ISOTOPE DETECTED ({total_ev:.3f} eV) !!")
        else:
            total_mass = sum(e[1] for e in elements)
            for name, weight, ev in sorted(elements, key=lambda x: x[1], reverse=True):
                print(f"[{name:12}] | Residue: {ev:6.3f} eV | Mass: {(weight/total_mass)*100:5.1f}%")
                if "Uranium" in name or "Lead" in name:
                    print(">> WARNING: RADIOACTIVE/TOXIC MATERIAL DETECTED <<")
        
        print(f"Inertial Slope: {slope:.4f} | Status: [{'SOVEREIGN' if abs(slope-self.LYNCH_SLOPE)<0.05 else 'FAKE'}]\n")

if __name__ == "__main__":
    scanner = LaciaSovereignScanner()
    k = np.arange(1, 101)
    # Simulation: 304 Stainless Steel (Iron + Chromium + Nickel)
    stainless = (7.902 + 6.767 + 7.640) * scanner.C_UFT_F * k**scanner.LYNCH_SLOPE
    # Simulation: Alien/Unknown Substance (Random Residue)
    unknown = 31.415 * scanner.C_UFT_F * k**scanner.LYNCH_SLOPE

    scanner.scan(stainless, "304 Stainless Steel")
    scanner.scan(unknown, "Meteorite Sample X-1")