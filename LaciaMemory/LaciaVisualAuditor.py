import cv2
import numpy as np
import itertools

class LaciaSovereignScanner:
    def __init__(self):
        self.C_UFT_F = 0.00311903  
        self.LYNCH_SLOPE = -1.6466 
        self.DELTA = 0.15 # Widened slightly for complex image gradients
        self.ARCHIVE = {
            "Hydrogen (H)": (13.598, 1.008), "Helium (He)": (24.587, 4.002),
            "Carbon (C)": (11.260, 12.011), "Nitrogen (N)": (14.534, 14.007),
            "Oxygen (O)": (13.618, 15.999), "Aluminum (Al)": (5.986, 26.982),
            "Silicon (Si)": (8.152, 28.085), "Iron (Fe)": (7.902, 55.845),
            "Copper (Cu)": (7.726, 63.546), "Silver (Ag)": (7.576, 107.868),
            "Gold (Au)": (9.226, 196.966), "Water (H2O)": (12.610, 18.015),
            "Chromium (Cr)": (6.767, 51.996), "Uranium (U)": (6.194, 238.028)
        }

    def deconvolve(self, total_ev):
        items = list(self.ARCHIVE.items())
        for n in range(1, 4):
            for combo in itertools.combinations(items, n):
                if abs(total_ev - sum(c[1][0] for c in combo)) < self.DELTA:
                    return [(c[0], c[1][1], c[1][0]) for c in combo]
        return []

    def process_click(self, event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            pixel_val = int(param['gray'][y, x]) # Ensure standard Python int
            # Increased multiplier to better map the bright lines in the png
            sim_ev = (pixel_val / 255) * 35.0 
            
            elements = self.deconvolve(sim_ev)
            display_img = param['original'].copy()

            if elements and sim_ev > 0.5: # Ignore noise/black space
                names = [e[0] for e in elements]
                print(f"\n[SCAN SUCCESS] Location: {x},{y} | Identity: {' + '.join(names)} ({sim_ev:.2f} eV)")
                
                # FIX: Explicitly cast bounds to float/int for OpenCV
                lower = float(max(0, pixel_val - 10))
                upper = float(min(255, pixel_val + 10))
                
                mask = cv2.inRange(param['gray'], lower, upper)
                
                overlay = display_img.copy()
                # If radioactive, use RED. Otherwise, use CYAN.
                color = [0, 0, 255] if any("Uranium" in n for n in names) else [255, 165, 0]
                overlay[mask > 0] = color 
                cv2.addWeighted(overlay, 0.6, display_img, 0.4, 0, display_img)
                
                cv2.putText(display_img, f"MATCH: {'+'.join(names)}", (10, 30), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
            else:
                print(f"[SCAN] Location: {x},{y} | UNKNOWN MANIFOLD ({sim_ev:.2f} eV)")
                cv2.putText(display_img, f"UNKNOWN ({sim_ev:.1f} eV)", (10, 30), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

            cv2.imshow("Lacia Visual Auditor", display_img)

if __name__ == "__main__":
    img_path = "spectroscopy.png" 
    img = cv2.imread(img_path)
    
    if img is None:
        print(f"Error: Could not find '{img_path}'.")
    else:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        scanner = LaciaSovereignScanner()
        cv2.namedWindow("Lacia Visual Auditor")
        cv2.setMouseCallback("Lacia Visual Auditor", scanner.process_click, 
                             {'gray': gray, 'original': img})
        
        print(f"--- LACIA SCANNER ACTIVE ON {img_path} ---")
        print("Click on the bright emission lines. Press ESC to quit.")
        cv2.imshow("Lacia Visual Auditor", img)
        cv2.waitKey(0)
        cv2.destroyAllWindows()