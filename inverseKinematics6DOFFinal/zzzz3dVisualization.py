import torch
import numpy as np

# =============================================================================
# UFT-GENERATOR: THE OPTIMIZED CHIMERA
# =============================================================================
# - Purpose: Generate final 3D coordinates for the Rank 1 sequence.
# - Format: Standard XYZ for visualization.
# =============================================================================

class UFT_Generator:
    def __init__(self, model_path="uft_global_brain_v2.pth"):
        self.device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
        from theGauntlet import UFT_Transformer
        self.model = UFT_Transformer().to(self.device)
        self.model.load_state_dict(torch.load(model_path, map_location=self.device))
        self.model.eval()
        self.aa_map = {a: i+1 for i, a in enumerate("ACDEFGHIKLMNPQRSTVWY")}

    def generate_pdb_coords(self, sequence, filename="optimized_chimera.txt"):
        tokens = torch.tensor([[self.aa_map.get(a, 21) for a in sequence]]).to(self.device)
        
        with torch.no_grad():
            base_rot, motives = self.model(tokens)
        
        coords = [torch.zeros(3)]
        pos = torch.zeros(3)
        direction = base_rot[0].cpu()
        
        # We'll use the standard Alpha-Carbon distance of 3.8 Angstroms
        for i in range(len(sequence) - 1):
            m = motives[0, i].cpu()
            # Apply the 6DoF rotation to the current direction vector
            direction = (direction + m[0:3]) / torch.norm(direction + m[0:3])
            pos = pos + (direction * 3.8)
            coords.append(pos.clone())
            
        coords = torch.stack(coords).numpy()
        np.savetxt(filename, coords, fmt='%f')
        print(f"--- GENERATION COMPLETE ---")
        print(f"Sequence: {sequence}")
        print(f"Coordinates saved to {filename}")
        return coords

if __name__ == "__main__":
    gen = UFT_Generator()
    best_seq = "TTCCPSIVARNGINGGPQYWMLSDEDFK"
    gen.generate_pdb_coords(best_seq)

#     (base) brendanlynch@Brendans-Laptop AI % python 3dVisualization.py
# --- GENERATION COMPLETE ---
# Sequence: TTCCPSIVARNGINGGPQYWMLSDEDFK
# Coordinates saved to optimized_chimera.txt
# (base) brendanlynch@Brendans-Laptop AI % 

# optimizedChmiera txt: 
# 0.000000 0.000000 0.000000
# 0.890187 -3.645787 -0.596494
# 4.179240 -5.485909 -0.110610
# 6.645654 -8.373940 -0.237391
# 8.072025 -10.461074 2.599745
# 7.417918 -8.324492 5.673368
# 5.752795 -6.689616 8.672459
# 4.598960 -4.611780 11.637465
# 3.016424 -1.723826 13.533593
# 1.711663 0.731264 16.123985
# 1.291289 0.929056 19.895479
# 2.108381 -2.763642 19.526230
# 4.247156 -5.823336 18.816359
# 7.087818 -7.852312 20.317654
# 10.472270 -7.112682 21.879204
# 12.433935 -6.659224 25.101974
# 12.735209 -5.539907 28.720865
# 13.363391 -5.877344 32.453362
# 14.972342 -6.558368 35.827896
# 16.763359 -8.616457 38.472992
# 19.321894 -11.214454 39.542717
# 21.651470 -13.589020 41.379700
# 24.634216 -14.950957 43.300209
# 26.976814 -16.819477 45.637058
# 28.448950 -17.512632 49.071060
# 31.240585 -20.040176 49.579281
# 32.900387 -22.659897 47.383347
# 33.108585 -21.966074 43.653030