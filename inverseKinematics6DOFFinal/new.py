import torch
import torch.nn as nn
import numpy as np
import requests
import os

# =============================================================================
# UFT-GEN V9.2: OPTIMIZED FOR CONVERGENCE SPEED
# =============================================================================
# - Rule 1: Discards any mapping with RMSD > 1.0A (Successes only).
# - Rule 2: SKIPS proteins > 80 residues to prevent "Long-Chain Hang".
# - Rule 3: Sequential Step Reporting for terminal monitoring.
# =============================================================================

def get_rodrigues_matrix(axis_vec):
    theta = torch.norm(axis_vec)
    if theta < 1e-9: return torch.eye(3)
    k = axis_vec / theta
    K = torch.zeros((3, 3))
    K[0, 1], K[0, 2], K[1, 0], K[1, 2], K[2, 0], K[2, 1] = -k[2], k[1], k[2], -k[0], -k[1], k[0]
    return torch.eye(3) + torch.sin(theta) * K + (1 - torch.cos(theta)) * torch.mm(K, K)

def download_pdb_data(pdb_id, max_residues=80):
    url = f"https://files.rcsb.org/download/{pdb_id}.pdb"
    try:
        r = requests.get(url, timeout=5)
        if r.status_code != 200: return None, None
        lines = r.text.splitlines()
        ca_lines = [l for l in lines if l.startswith("ATOM") and l[12:16].strip() == "CA"]
        
        # LENGTH FILTER: Remove long ones that cause the hang
        if len(ca_lines) > max_residues:
            return "TOO_LONG", len(ca_lines)

        three_to_one = {'ALA':'A','CYS':'C','ASP':'D','GLU':'E','PHE':'F','GLY':'G','HIS':'H','ILE':'I','LYS':'K','LEU':'L','MET':'M','ASN':'N','PRO':'P','GLN':'Q','ARG':'R','SER':'S','THR':'T','VAL':'V','TRP':'W','TYR':'Y'}
        coords, seq, last_resid = [], "", -999
        for l in ca_lines:
            resid = int(l[22:26])
            if l[21] not in ['A', ' '] or resid == last_resid: continue 
            coords.append([float(l[30:38]), float(l[38:46]), float(l[46:54])])
            seq += three_to_one.get(l[17:20].strip(), 'X')
            last_resid = resid
        coords = torch.tensor(coords, dtype=torch.float32)
        return coords - coords[0], seq 
    except: return None, None

def solve_geometry(pdb_id, max_steps=2501):
    target_coords, sequence = download_pdb_data(pdb_id)
    
    if target_coords == "TOO_LONG":
        print(f"   [!] Skipping {pdb_id} (Length {sequence} > 80).")
        return "SKIP", 0.0
    
    if target_coords is None or len(target_coords) < 5: 
        return None, 99.0
    
    target_len = len(target_coords)
    
    for attempt in range(2):
        if attempt > 0: print(f"   --- RETRYING {pdb_id} WITH FRESH NOISE ---")
        
        base_motive = torch.zeros(3, requires_grad=True)
        motives = (torch.randn((target_len - 1, 5)) * 0.1).requires_grad_(True)

        with torch.no_grad():
            v_t = target_coords[1] / torch.norm(target_coords[1])
            axis = torch.linalg.cross(torch.tensor([1.0, 0, 0]), v_t)
            angle = torch.acos(torch.clamp(torch.dot(torch.tensor([1.0, 0, 0]), v_t), -1.0, 1.0))
            if torch.norm(axis) > 1e-6:
                base_motive.copy_(axis / torch.norm(axis) * angle)

        optimizer = torch.optim.Adam([base_motive, motives], lr=0.03)
        
        best_rmsd = 999.0
        best_state = None

        for step in range(max_steps):
            optimizer.zero_grad()
            coords_list = [torch.zeros(3)]
            current_pos = torch.zeros(3)
            current_frame = get_rodrigues_matrix(base_motive)
            
            for i in range(target_len - 1):
                current_frame = torch.mm(current_frame, get_rodrigues_matrix(motives[i, :3]))
                R_tilt = get_rodrigues_matrix(current_frame[:, 1] * (motives[i, 4] * 0.1))
                length = 3.8 * torch.exp(motives[i, 3] * 0.01) 
                forward_vec = torch.matmul(R_tilt, current_frame[:, 0]) * length
                current_pos = current_pos + forward_vec
                coords_list.append(current_pos)
                
            coords = torch.stack(coords_list)
            rmsd = torch.sqrt(torch.mean(torch.sum((coords - target_coords)**2, dim=1)))
            
            # Loss emphasizes geometric fit + small length deviation
            loss = rmsd + torch.norm(motives[:, 3]) * 0.3
            loss.backward()
            optimizer.step()

            if step % 500 == 0:
                avg_l = torch.mean(3.8 * torch.exp(motives[:, 3] * 0.01)).item()
                print(f"   Step {step:4d} | RMSD: {rmsd.item():.4f} | Avg L: {avg_l:.2f}")

            if rmsd.item() < best_rmsd:
                best_rmsd = rmsd.item()
                best_state = {'base': base_motive.detach().clone(), 'motives': motives.detach().clone(), 'seq': sequence}
            
            if best_rmsd < 0.05: break 
        
        if best_rmsd < 1.0:
            return best_state, best_rmsd
            
    return None, best_rmsd

PDB_TARGETS = [
    "1CRN", "1UBQ", "1VII", "1L2Y", "2K0E", "1F4I", "1A1X", "1R69", "1UTG", "256B",
    "1E0L", "1YRF", "2L63", "2M7D", "1WLA", "2MR9", "1Q2K", "2L4Z", "1K43", "1ROP",
    "2K9J", "1BBL", "1PRB", "2HBA", "1D5Q", "1FSD", "1PSV", "1TIT", "2IGD", "1O1Z",
    "1MJC", "2K2P", "1V54", "2L8I", "2LHC", "2M30", "2M8F", "2L3W", "2L6Q", "2K3F",
    "2L2Y", "2L9R", "2M2K", "2L7U", "2L9V", "2LA6", "2LBJ", "2LCL", "2LDL", "2LEL",
    "1ACW", "1DFN", "1KHI", "1MBH", "1PLC", "1SRX", "1TN3", "1WHZ", "1YCC", "2ACT",
    "2CRO", "2FOX", "2LZM", "2MHR", "3CHY", "3ICB", "451C", "4CPV", "5CYT", "6PTI",
    "1A4V", "1A59", "1A62", "1A6M", "1A7V", "1AAJ", "1ABV", "1ACF", "1AD2", "1ADR",
    "1AEP", "1AF7", "1AHO", "1AIE", "1AIL", "1AJ3", "1AJO", "1AL1", "1AMB", "1AOA",
    "1APS", "1AQ0", "1ARU", "1ASZ", "1AU7", "1AY7", "1AZP", "1B0N", "1B2P", "1B4V",
    "1B9O", "1BA2", "1BCF", "1BDD", "1BE9", "1BEO", "1BGK", "1BH0", "1BIA", "1BIG",
    "1BK2", "1BM8", "1BNZ", "1BPI", "1BRF", "1BT6", "1BTA", "1BUJ", "1BV1", "1BW6",
    "1BX7", "1BYI", "1C5A", "1C8C", "1C9O", "1CAG", "1CC5", "1CC7", "1CC8", "1CCZ",
    "1CEI", "1CFH", "1CGI", "1CHK", "1CHL", "1CJP", "1CKA", "1CLB", "1CLM", "1CMB",
    "1COA", "1CSP", "1CTF", "1CUK", "1CVZ", "1CYO", "1D2Z", "1D3Z", "1D4T", "1D5T",
    "1DAB", "1DBW", "1DCJ", "1DD9", "1DF4", "1DGL", "1DHN", "1DIV", "1DKT", "1DLW",
    "1DM9", "1DMB", "1DOL", "1DSX", "1DTP", "1DUN", "1DXJ", "1E0M", "1E2A", "1E4F",
    "1E5K", "1E6I", "1E7L", "1E9H", "1EA7", "1EB6", "1EDG", "1EDM", "1EES", "1EF1",
    "1EG3", "1EGN", "1EHE", "1EIG", "1EJ0", "1EJG", "1EKI", "1ELU", "1ELW", "1EM7",
    "1ENH", "1EO0", "1EP0", "1EQ6", "1ERZ", "1ES5", "1ES9", "1ET1", "1EUW", "1EVT"
]

def main():
    print("--- UFT GEOMETRIC MAPPING (FAST-CONVERGE V9.2) ---")
    training_data = {}
    
    for i, pid in enumerate(PDB_TARGETS):
        print(f"Mapping {pid}...")
        state, rmsd = solve_geometry(pid)
        
        if state == "SKIP":
            continue # Just move to next
        elif state:
            training_data[pid] = state
            print(f"RESULT {pid} | RMSD: {rmsd:.4f}Å (SAVED)")
            if len(training_data) % 5 == 0:
                torch.save(training_data, "geometric_truth_pure.pth")
        else:
            print(f"RESULT {pid} | RMSD: {rmsd:.4f}Å (DISCARDED)")
        print("-" * 40)

    torch.save(training_data, "geometric_truth_pure.pth")
    print(f"\nFINISH: {len(training_data)} samples saved.")

if __name__ == "__main__":
    main()

#     (base) brendanlynch@Brendans-Laptop AI % python new.py
# --- UFT GEOMETRIC MAPPING (FAST-CONVERGE V9.2) ---
# Mapping 1CRN...
#    Step    0 | RMSD: 91.5930 | Avg L: 3.80
#    Step  500 | RMSD: 2.2603 | Avg L: 3.80
#    Step 1000 | RMSD: 1.0886 | Avg L: 3.80
#    Step 1500 | RMSD: 0.7198 | Avg L: 3.80
#    Step 2000 | RMSD: 0.5365 | Avg L: 3.80
#    Step 2500 | RMSD: 0.4538 | Avg L: 3.80
# RESULT 1CRN | RMSD: 0.4483Å (SAVED)
# ----------------------------------------
# Mapping 1UBQ...
#    Step    0 | RMSD: 153.5026 | Avg L: 3.80
#    Step  500 | RMSD: 2.4054 | Avg L: 3.80
#    Step 1000 | RMSD: 1.7179 | Avg L: 3.80
#    Step 1500 | RMSD: 1.3223 | Avg L: 3.80
#    Step 2000 | RMSD: 1.1518 | Avg L: 3.80
#    Step 2500 | RMSD: 1.0484 | Avg L: 3.80
#    --- RETRYING 1UBQ WITH FRESH NOISE ---
#    Step    0 | RMSD: 124.9596 | Avg L: 3.80
#    Step  500 | RMSD: 2.4650 | Avg L: 3.80
#    Step 1000 | RMSD: 1.8202 | Avg L: 3.80
#    Step 1500 | RMSD: 1.3824 | Avg L: 3.80
#    Step 2000 | RMSD: 1.1715 | Avg L: 3.80
#    Step 2500 | RMSD: 1.0318 | Avg L: 3.80
# RESULT 1UBQ | RMSD: 1.0318Å (DISCARDED)
# ----------------------------------------
# Mapping 1VII...
#    Step    0 | RMSD: 70.6530 | Avg L: 3.80
#    Step  500 | RMSD: 1.0237 | Avg L: 3.80
#    Step 1000 | RMSD: 0.4459 | Avg L: 3.80
#    Step 1500 | RMSD: 0.3865 | Avg L: 3.80
#    Step 2000 | RMSD: 1.2178 | Avg L: 3.80
#    Step 2500 | RMSD: 0.7351 | Avg L: 3.80
# RESULT 1VII | RMSD: 0.1126Å (SAVED)
# ----------------------------------------
# Mapping 1L2Y...
#    [!] Skipping 1L2Y (Length 760 > 80).
# Mapping 2K0E...
#    [!] Skipping 2K0E (Length 23680 > 80).
# Mapping 1F4I...
#    [!] Skipping 1F4I (Length 945 > 80).
# Mapping 1A1X...
#    [!] Skipping 1A1X (Length 106 > 80).
# Mapping 1R69...
#    Step    0 | RMSD: 119.6104 | Avg L: 3.80
#    Step  500 | RMSD: 3.1422 | Avg L: 3.80
#    Step 1000 | RMSD: 1.9194 | Avg L: 3.80
#    Step 1500 | RMSD: 1.2663 | Avg L: 3.80
#    Step 2000 | RMSD: 1.0221 | Avg L: 3.80
#    Step 2500 | RMSD: 0.8574 | Avg L: 3.80
# RESULT 1R69 | RMSD: 0.8544Å (SAVED)
# ----------------------------------------
# Mapping 1UTG...
#    Step    0 | RMSD: 131.7166 | Avg L: 3.80
#    Step  500 | RMSD: 4.0791 | Avg L: 3.80
#    Step 1000 | RMSD: 2.8074 | Avg L: 3.80
#    Step 1500 | RMSD: 2.0048 | Avg L: 3.80
#    Step 2000 | RMSD: 1.5564 | Avg L: 3.80
#    Step 2500 | RMSD: 1.2998 | Avg L: 3.80
#    --- RETRYING 1UTG WITH FRESH NOISE ---
#    Step    0 | RMSD: 136.1726 | Avg L: 3.80
#    Step  500 | RMSD: 4.0380 | Avg L: 3.80
#    Step 1000 | RMSD: 2.8741 | Avg L: 3.80
#    Step 1500 | RMSD: 2.2335 | Avg L: 3.80
#    Step 2000 | RMSD: 1.8077 | Avg L: 3.80
#    Step 2500 | RMSD: 1.4581 | Avg L: 3.80
# RESULT 1UTG | RMSD: 1.4403Å (DISCARDED)
# ----------------------------------------
# Mapping 256B...
#    [!] Skipping 256B (Length 212 > 80).
# Mapping 1E0L...
#    [!] Skipping 1E0L (Length 370 > 80).
# Mapping 1YRF...
#    Step    0 | RMSD: 79.3233 | Avg L: 3.80
#    Step  500 | RMSD: 1.5074 | Avg L: 3.80
#    Step 1000 | RMSD: 0.6169 | Avg L: 3.80
#    Step 1500 | RMSD: 0.4356 | Avg L: 3.80
#    Step 2000 | RMSD: 0.3703 | Avg L: 3.80
#    Step 2500 | RMSD: 0.2668 | Avg L: 3.80
# RESULT 1YRF | RMSD: 0.2249Å (SAVED)
# ----------------------------------------
# Mapping 2L63...
#    [!] Skipping 2L63 (Length 330 > 80).
# Mapping 2M7D...
#    [!] Skipping 2M7D (Length 540 > 80).
# Mapping 1WLA...
#    [!] Skipping 1WLA (Length 153 > 80).
# Mapping 2MR9...
#    [!] Skipping 2MR9 (Length 440 > 80).
# Mapping 1Q2K...
#    [!] Skipping 1Q2K (Length 651 > 80).
# Mapping 2L4Z...
#    [!] Skipping 2L4Z (Length 2420 > 80).
# Mapping 1K43...
#    [!] Skipping 1K43 (Length 140 > 80).
# Mapping 1ROP...
#    Step    0 | RMSD: 125.9311 | Avg L: 3.80
#    Step  500 | RMSD: 4.1405 | Avg L: 3.80
#    Step 1000 | RMSD: 2.3495 | Avg L: 3.80
#    Step 1500 | RMSD: 1.3918 | Avg L: 3.80
#    Step 2000 | RMSD: 1.0350 | Avg L: 3.80
#    Step 2500 | RMSD: 0.9122 | Avg L: 3.80
# RESULT 1ROP | RMSD: 0.8756Å (SAVED)
# ----------------------------------------
# Mapping 2K9J...
#    [!] Skipping 2K9J (Length 1785 > 80).
# Mapping 1BBL...
#    Step    0 | RMSD: 74.2689 | Avg L: 3.80
#    Step  500 | RMSD: 1.3332 | Avg L: 3.80
#    Step 1000 | RMSD: 0.6856 | Avg L: 3.80
#    Step 1500 | RMSD: 0.4608 | Avg L: 3.80
#    Step 2000 | RMSD: 0.3637 | Avg L: 3.80
#    Step 2500 | RMSD: 0.3253 | Avg L: 3.80
# RESULT 1BBL | RMSD: 0.2569Å (SAVED)
# ----------------------------------------
# Mapping 1PRB...
#    Step    0 | RMSD: 95.8478 | Avg L: 3.80
#    Step  500 | RMSD: 2.6409 | Avg L: 3.80
#    Step 1000 | RMSD: 1.5496 | Avg L: 3.80
#    Step 1500 | RMSD: 1.0902 | Avg L: 3.80
#    Step 2000 | RMSD: 0.8576 | Avg L: 3.80
#    Step 2500 | RMSD: 0.7187 | Avg L: 3.80
# RESULT 1PRB | RMSD: 0.7187Å (SAVED)
# ----------------------------------------
# Mapping 2HBA...
#    [!] Skipping 2HBA (Length 104 > 80).
# Mapping 1D5Q...
#    Step    0 | RMSD: 58.7552 | Avg L: 3.80
#    Step  500 | RMSD: 0.9353 | Avg L: 3.80
#    Step 1000 | RMSD: 0.2983 | Avg L: 3.80
#    Step 1500 | RMSD: 0.2492 | Avg L: 3.80
#    Step 2000 | RMSD: 0.2082 | Avg L: 3.80
#    Step 2500 | RMSD: 0.1899 | Avg L: 3.80
# RESULT 1D5Q | RMSD: 0.1439Å (SAVED)
# ----------------------------------------
# Mapping 1FSD...
#    [!] Skipping 1FSD (Length 1148 > 80).
# Mapping 1PSV...
#    [!] Skipping 1PSV (Length 896 > 80).
# Mapping 1TIT...
#    [!] Skipping 1TIT (Length 89 > 80).
# Mapping 2IGD...
#    Step    0 | RMSD: 99.7871 | Avg L: 3.80
#    Step  500 | RMSD: 2.1352 | Avg L: 3.80
#    Step 1000 | RMSD: 1.4830 | Avg L: 3.80
#    Step 1500 | RMSD: 1.1441 | Avg L: 3.80
#    Step 2000 | RMSD: 0.9217 | Avg L: 3.80
#    Step 2500 | RMSD: 0.7922 | Avg L: 3.80
# RESULT 2IGD | RMSD: 0.7828Å (SAVED)
# ----------------------------------------
# Mapping 1O1Z...
#    [!] Skipping 1O1Z (Length 226 > 80).
# Mapping 1MJC...
#    Step    0 | RMSD: 128.8754 | Avg L: 3.80
#    Step  500 | RMSD: 1.6696 | Avg L: 3.80
#    Step 1000 | RMSD: 1.1600 | Avg L: 3.80
#    Step 1500 | RMSD: 0.9126 | Avg L: 3.80
#    Step 2000 | RMSD: 0.7766 | Avg L: 3.80
#    Step 2500 | RMSD: 0.6607 | Avg L: 3.80
# RESULT 1MJC | RMSD: 0.6603Å (SAVED)
# ----------------------------------------
# Mapping 2K2P...
#    [!] Skipping 2K2P (Length 1280 > 80).
# Mapping 1V54...
#    [!] Skipping 1V54 (Length 3550 > 80).
# Mapping 2L8I...
# RESULT 2L8I | RMSD: 99.0000Å (DISCARDED)
# ----------------------------------------
# Mapping 2LHC...
#    [!] Skipping 2LHC (Length 1120 > 80).
# Mapping 2M30...
#    [!] Skipping 2M30 (Length 1900 > 80).
# Mapping 2M8F...
#    [!] Skipping 2M8F (Length 480 > 80).
# Mapping 2L3W...
#    [!] Skipping 2L3W (Length 2860 > 80).
# Mapping 2L6Q...
#    [!] Skipping 2L6Q (Length 1240 > 80).
# Mapping 2K3F...
#    [!] Skipping 2K3F (Length 2820 > 80).
# Mapping 2L2Y...
#    [!] Skipping 2L2Y (Length 140 > 80).
# Mapping 2L9R...
#    [!] Skipping 2L9R (Length 1380 > 80).
# Mapping 2M2K...
#    [!] Skipping 2M2K (Length 2620 > 80).
# Mapping 2L7U...
#    [!] Skipping 2L7U (Length 2775 > 80).
# Mapping 2L9V...
#    [!] Skipping 2L9V (Length 441 > 80).
# Mapping 2LA6...
#    [!] Skipping 2LA6 (Length 1980 > 80).
# Mapping 2LBJ...
# RESULT 2LBJ | RMSD: 99.0000Å (DISCARDED)
# ----------------------------------------
# Mapping 2LCL...
#    [!] Skipping 2LCL (Length 1320 > 80).
# Mapping 2LDL...
# RESULT 2LDL | RMSD: 99.0000Å (DISCARDED)
# ----------------------------------------
# Mapping 2LEL...
#    [!] Skipping 2LEL (Length 1480 > 80).
# Mapping 1ACW...
#    [!] Skipping 1ACW (Length 725 > 80).
# Mapping 1DFN...
#    Step    0 | RMSD: 51.6158 | Avg L: 3.80
#    Step  500 | RMSD: 0.4533 | Avg L: 3.80
#    Step 1000 | RMSD: 0.3012 | Avg L: 3.80
#    Step 1500 | RMSD: 0.2628 | Avg L: 3.80
#    Step 2000 | RMSD: 0.2579 | Avg L: 3.80
#    Step 2500 | RMSD: 0.2498 | Avg L: 3.80
# RESULT 1DFN | RMSD: 0.2495Å (SAVED)
# ----------------------------------------
# Mapping 1KHI...
#    [!] Skipping 1KHI (Length 147 > 80).
# Mapping 1MBH...
#    [!] Skipping 1MBH (Length 2600 > 80).
# Mapping 1PLC...
#    [!] Skipping 1PLC (Length 102 > 80).
# Mapping 1SRX...
#    [!] Skipping 1SRX (Length 108 > 80).
# Mapping 1TN3...
#    [!] Skipping 1TN3 (Length 137 > 80).
# Mapping 1WHZ...
#    Step    0 | RMSD: 141.0954 | Avg L: 3.80
#    Step  500 | RMSD: 2.1472 | Avg L: 3.80
#    Step 1000 | RMSD: 1.3943 | Avg L: 3.80
#    Step 1500 | RMSD: 1.1027 | Avg L: 3.80
#    Step 2000 | RMSD: 1.0030 | Avg L: 3.80
#    Step 2500 | RMSD: 0.9346 | Avg L: 3.80
# RESULT 1WHZ | RMSD: 0.9340Å (SAVED)
# ----------------------------------------
# Mapping 1YCC...
#    [!] Skipping 1YCC (Length 107 > 80).
# Mapping 2ACT...
#    [!] Skipping 2ACT (Length 217 > 80).
# Mapping 2CRO...
#    Step    0 | RMSD: 132.5567 | Avg L: 3.80
#    Step  500 | RMSD: 2.9532 | Avg L: 3.80
#    Step 1000 | RMSD: 1.6381 | Avg L: 3.80
#    Step 1500 | RMSD: 1.0649 | Avg L: 3.80
#    Step 2000 | RMSD: 0.8413 | Avg L: 3.80
#    Step 2500 | RMSD: 0.7563 | Avg L: 3.80
# RESULT 2CRO | RMSD: 0.7163Å (SAVED)
# ----------------------------------------
# Mapping 2FOX...
#    [!] Skipping 2FOX (Length 138 > 80).
# Mapping 2LZM...
#    [!] Skipping 2LZM (Length 164 > 80).
# Mapping 2MHR...
#    [!] Skipping 2MHR (Length 118 > 80).
# Mapping 3CHY...
#    [!] Skipping 3CHY (Length 128 > 80).
# Mapping 3ICB...
#    Step    0 | RMSD: 149.8742 | Avg L: 3.80
#    Step  500 | RMSD: 3.3704 | Avg L: 3.80
#    Step 1000 | RMSD: 1.9594 | Avg L: 3.80
#    Step 1500 | RMSD: 1.3707 | Avg L: 3.80
#    Step 2000 | RMSD: 1.1687 | Avg L: 3.80
#    Step 2500 | RMSD: 1.0195 | Avg L: 3.80
#    --- RETRYING 3ICB WITH FRESH NOISE ---
#    Step    0 | RMSD: 163.3101 | Avg L: 3.80
#    Step  500 | RMSD: 3.2879 | Avg L: 3.80
#    Step 1000 | RMSD: 2.0357 | Avg L: 3.80
#    Step 1500 | RMSD: 1.4369 | Avg L: 3.80
#    Step 2000 | RMSD: 1.1717 | Avg L: 3.80
#    Step 2500 | RMSD: 1.0201 | Avg L: 3.80
# RESULT 3ICB | RMSD: 1.0182Å (DISCARDED)
# ----------------------------------------
# Mapping 451C...
#    [!] Skipping 451C (Length 82 > 80).
# Mapping 4CPV...
#    [!] Skipping 4CPV (Length 108 > 80).
# Mapping 5CYT...
#    [!] Skipping 5CYT (Length 103 > 80).
# Mapping 6PTI...
#    Step    0 | RMSD: 92.2066 | Avg L: 3.80
#    Step  500 | RMSD: 1.4845 | Avg L: 3.80
#    Step 1000 | RMSD: 0.9839 | Avg L: 3.80
#    Step 1500 | RMSD: 0.7527 | Avg L: 3.80
#    Step 2000 | RMSD: 0.6240 | Avg L: 3.80
#    Step 2500 | RMSD: 0.5539 | Avg L: 3.80
# RESULT 6PTI | RMSD: 0.5480Å (SAVED)
# ----------------------------------------
# Mapping 1A4V...
#    [!] Skipping 1A4V (Length 123 > 80).
# Mapping 1A59...
#    [!] Skipping 1A59 (Length 377 > 80).
# Mapping 1A62...
#    [!] Skipping 1A62 (Length 122 > 80).
# Mapping 1A6M...
#    [!] Skipping 1A6M (Length 151 > 80).
# Mapping 1A7V...
#    [!] Skipping 1A7V (Length 250 > 80).
# Mapping 1AAJ...
#    [!] Skipping 1AAJ (Length 105 > 80).
# Mapping 1ABV...
#    [!] Skipping 1ABV (Length 105 > 80).
# Mapping 1ACF...
#    [!] Skipping 1ACF (Length 125 > 80).
# Mapping 1AD2...
#    [!] Skipping 1AD2 (Length 224 > 80).
# Mapping 1ADR...
#    [!] Skipping 1ADR (Length 1520 > 80).
# Mapping 1AEP...
#    [!] Skipping 1AEP (Length 153 > 80).
# Mapping 1AF7...
#    [!] Skipping 1AF7 (Length 274 > 80).
# Mapping 1AHO...
#    Step    0 | RMSD: 122.5846 | Avg L: 3.80
#    Step  500 | RMSD: 2.0084 | Avg L: 3.80
#    Step 1000 | RMSD: 1.2686 | Avg L: 3.80
#    Step 1500 | RMSD: 0.9693 | Avg L: 3.80
#    Step 2000 | RMSD: 0.8249 | Avg L: 3.80
#    Step 2500 | RMSD: 0.7309 | Avg L: 3.80
# RESULT 1AHO | RMSD: 0.7236Å (SAVED)
# ----------------------------------------
# Mapping 1AIE...
#    Step    0 | RMSD: 61.1186 | Avg L: 3.80
#    Step  500 | RMSD: 1.7347 | Avg L: 3.80
#    Step 1000 | RMSD: 0.5908 | Avg L: 3.80
#    Step 1500 | RMSD: 0.4446 | Avg L: 3.80
#    Step 2000 | RMSD: 0.3981 | Avg L: 3.80
#    Step 2500 | RMSD: 0.3346 | Avg L: 3.80
# RESULT 1AIE | RMSD: 0.3032Å (SAVED)
# ----------------------------------------
# Mapping 1AIL...
#    Step    0 | RMSD: 123.2401 | Avg L: 3.80
#    Step  500 | RMSD: 3.5409 | Avg L: 3.80
#    Step 1000 | RMSD: 2.3520 | Avg L: 3.80
#    Step 1500 | RMSD: 1.8668 | Avg L: 3.80
#    Step 2000 | RMSD: 1.5570 | Avg L: 3.80
#    Step 2500 | RMSD: 1.3259 | Avg L: 3.80
#    --- RETRYING 1AIL WITH FRESH NOISE ---
#    Step    0 | RMSD: 142.5904 | Avg L: 3.80
#    Step  500 | RMSD: 3.4299 | Avg L: 3.80
#    Step 1000 | RMSD: 2.6602 | Avg L: 3.80
#    Step 1500 | RMSD: 1.9846 | Avg L: 3.80
#    Step 2000 | RMSD: 1.4250 | Avg L: 3.80
#    Step 2500 | RMSD: 1.1788 | Avg L: 3.80
# RESULT 1AIL | RMSD: 1.1659Å (DISCARDED)
# ----------------------------------------
# Mapping 1AJ3...
#    [!] Skipping 1AJ3 (Length 1960 > 80).
# Mapping 1AJO...
#    [!] Skipping 1AJO (Length 425 > 80).
# Mapping 1AL1...
#    Step    0 | RMSD: 22.0659 | Avg L: 3.80
#    Step  500 | RMSD: 0.2047 | Avg L: 3.80
# RESULT 1AL1 | RMSD: 0.0374Å (SAVED)
# ----------------------------------------
# Mapping 1AMB...
#    Step    0 | RMSD: 50.8159 | Avg L: 3.80
#    Step  500 | RMSD: 2.1453 | Avg L: 3.80
#    Step 1000 | RMSD: 0.8266 | Avg L: 3.80
#    Step 1500 | RMSD: 0.5778 | Avg L: 3.80
#    Step 2000 | RMSD: 0.4643 | Avg L: 3.80
#    Step 2500 | RMSD: 0.4102 | Avg L: 3.80
# RESULT 1AMB | RMSD: 0.4037Å (SAVED)
# ----------------------------------------
# Mapping 1AOA...
#    [!] Skipping 1AOA (Length 247 > 80).
# Mapping 1APS...
#    [!] Skipping 1APS (Length 490 > 80).
# Mapping 1AQ0...
#    [!] Skipping 1AQ0 (Length 612 > 80).
# Mapping 1ARU...
#    [!] Skipping 1ARU (Length 336 > 80).
# Mapping 1ASZ...
#    [!] Skipping 1ASZ (Length 980 > 80).
# Mapping 1AU7...
#    [!] Skipping 1AU7 (Length 258 > 80).
# Mapping 1AY7...
#    [!] Skipping 1AY7 (Length 186 > 80).
# Mapping 1AZP...
#    Step    0 | RMSD: 120.7065 | Avg L: 3.80
#    Step  500 | RMSD: 1.7553 | Avg L: 3.80
#    Step 1000 | RMSD: 1.3321 | Avg L: 3.80
#    Step 1500 | RMSD: 1.1555 | Avg L: 3.80
#    Step 2000 | RMSD: 1.0295 | Avg L: 3.80
#    Step 2500 | RMSD: 0.9344 | Avg L: 3.80
# RESULT 1AZP | RMSD: 0.9221Å (SAVED)
# ----------------------------------------
# Mapping 1B0N...
#    [!] Skipping 1B0N (Length 134 > 80).
# Mapping 1B2P...
#    [!] Skipping 1B2P (Length 238 > 80).
# Mapping 1B4V...
#    [!] Skipping 1B4V (Length 498 > 80).
# Mapping 1B9O...
#    [!] Skipping 1B9O (Length 123 > 80).
# Mapping 1BA2...
#    [!] Skipping 1BA2 (Length 542 > 80).
# Mapping 1BCF...
#    [!] Skipping 1BCF (Length 1896 > 80).
# Mapping 1BDD...
#    Step    0 | RMSD: 107.3704 | Avg L: 3.80
#    Step  500 | RMSD: 3.3515 | Avg L: 3.80
#    Step 1000 | RMSD: 2.0341 | Avg L: 3.80
#    Step 1500 | RMSD: 1.4917 | Avg L: 3.80
#    Step 2000 | RMSD: 1.2135 | Avg L: 3.80
#    Step 2500 | RMSD: 1.0260 | Avg L: 3.80
#    --- RETRYING 1BDD WITH FRESH NOISE ---
#    Step    0 | RMSD: 104.9272 | Avg L: 3.80
#    Step  500 | RMSD: 3.2597 | Avg L: 3.80
#    Step 1000 | RMSD: 2.1622 | Avg L: 3.80
#    Step 1500 | RMSD: 1.4501 | Avg L: 3.80
#    Step 2000 | RMSD: 1.0365 | Avg L: 3.80
#    Step 2500 | RMSD: 0.8849 | Avg L: 3.80
# RESULT 1BDD | RMSD: 0.8824Å (SAVED)
# ----------------------------------------
# Mapping 1BE9...
#    [!] Skipping 1BE9 (Length 120 > 80).
# Mapping 1BEO...
#    [!] Skipping 1BEO (Length 98 > 80).
# Mapping 1BGK...
#    [!] Skipping 1BGK (Length 555 > 80).
# Mapping 1BH0...
#    Step    0 | RMSD: 66.9004 | Avg L: 3.80
#    Step  500 | RMSD: 1.7378 | Avg L: 3.80
#    Step 1000 | RMSD: 0.6901 | Avg L: 3.80
#    Step 1500 | RMSD: 0.5549 | Avg L: 3.80
#    Step 2000 | RMSD: 0.4938 | Avg L: 3.80
#    Step 2500 | RMSD: 0.4617 | Avg L: 3.80
# RESULT 1BH0 | RMSD: 0.4571Å (SAVED)
# ----------------------------------------
# Mapping 1BIA...
#    [!] Skipping 1BIA (Length 292 > 80).
# Mapping 1BIG...
#    [!] Skipping 1BIG (Length 900 > 80).
# Mapping 1BK2...
#    Step    0 | RMSD: 112.5062 | Avg L: 3.80
#    Step  500 | RMSD: 1.2106 | Avg L: 3.80
#    Step 1000 | RMSD: 0.7721 | Avg L: 3.80
#    Step 1500 | RMSD: 0.6169 | Avg L: 3.80
#    Step 2000 | RMSD: 0.5104 | Avg L: 3.80
#    Step 2500 | RMSD: 0.4788 | Avg L: 3.80
# RESULT 1BK2 | RMSD: 0.4480Å (SAVED)
# ----------------------------------------
# Mapping 1BM8...
#    [!] Skipping 1BM8 (Length 99 > 80).
# Mapping 1BNZ...
#    Step    0 | RMSD: 98.6337 | Avg L: 3.80
#    Step  500 | RMSD: 1.4960 | Avg L: 3.80
#    Step 1000 | RMSD: 1.1033 | Avg L: 3.80
#    Step 1500 | RMSD: 0.9039 | Avg L: 3.80
#    Step 2000 | RMSD: 0.7836 | Avg L: 3.80
#    Step 2500 | RMSD: 0.7115 | Avg L: 3.80
# RESULT 1BNZ | RMSD: 0.7104Å (SAVED)
# ----------------------------------------
# Mapping 1BPI...
#    Step    0 | RMSD: 116.0110 | Avg L: 3.80
#    Step  500 | RMSD: 1.8090 | Avg L: 3.80
#    Step 1000 | RMSD: 1.1039 | Avg L: 3.80
#    Step 1500 | RMSD: 0.8578 | Avg L: 3.80
#    Step 2000 | RMSD: 0.6956 | Avg L: 3.80
#    Step 2500 | RMSD: 0.6358 | Avg L: 3.80
# RESULT 1BPI | RMSD: 0.5964Å (SAVED)
# ----------------------------------------
# Mapping 1BRF...
#    Step    0 | RMSD: 102.5994 | Avg L: 3.80
#    Step  500 | RMSD: 1.6622 | Avg L: 3.80
#    Step 1000 | RMSD: 0.9159 | Avg L: 3.80
#    Step 1500 | RMSD: 0.6662 | Avg L: 3.80
#    Step 2000 | RMSD: 0.5497 | Avg L: 3.80
#    Step 2500 | RMSD: 0.4772 | Avg L: 3.80
# RESULT 1BRF | RMSD: 0.4606Å (SAVED)
# ----------------------------------------
# Mapping 1BT6...
#    [!] Skipping 1BT6 (Length 204 > 80).
# Mapping 1BTA...
#    [!] Skipping 1BTA (Length 89 > 80).
# Mapping 1BUJ...
#    [!] Skipping 1BUJ (Length 2180 > 80).
# Mapping 1BV1...
#    [!] Skipping 1BV1 (Length 165 > 80).
# Mapping 1BW6...
#    Step    0 | RMSD: 101.3968 | Avg L: 3.80
#    Step  500 | RMSD: 2.6842 | Avg L: 3.80
#    Step 1000 | RMSD: 1.2444 | Avg L: 3.80
#    Step 1500 | RMSD: 0.8389 | Avg L: 3.80
#    Step 2000 | RMSD: 0.7193 | Avg L: 3.80
#    Step 2500 | RMSD: 0.6165 | Avg L: 3.80
# RESULT 1BW6 | RMSD: 0.6127Å (SAVED)
# ----------------------------------------
# Mapping 1BX7...
#    Step    0 | RMSD: 93.3863 | Avg L: 3.80
#    Step  500 | RMSD: 1.5391 | Avg L: 3.80
#    Step 1000 | RMSD: 1.1214 | Avg L: 3.80
#    Step 1500 | RMSD: 0.9303 | Avg L: 3.80
#    Step 2000 | RMSD: 0.8480 | Avg L: 3.80
#    Step 2500 | RMSD: 0.7827 | Avg L: 3.80
# RESULT 1BX7 | RMSD: 0.7827Å (SAVED)
# ----------------------------------------
# Mapping 1BYI...
#    [!] Skipping 1BYI (Length 238 > 80).
# Mapping 1C5A...
#    [!] Skipping 1C5A (Length 2665 > 80).
# Mapping 1C8C...
#    Step    0 | RMSD: 135.1288 | Avg L: 3.80
#    Step  500 | RMSD: 1.6325 | Avg L: 3.80
#    Step 1000 | RMSD: 1.1451 | Avg L: 3.80
#    Step 1500 | RMSD: 0.9436 | Avg L: 3.80
#    Step 2000 | RMSD: 0.8316 | Avg L: 3.80
#    Step 2500 | RMSD: 0.7572 | Avg L: 3.80
# RESULT 1C8C | RMSD: 0.7476Å (SAVED)
# ----------------------------------------
# Mapping 1C9O...
#    [!] Skipping 1C9O (Length 132 > 80).
# Mapping 1CAG...
#    Step    0 | RMSD: 37.3134 | Avg L: 3.80
#    Step  500 | RMSD: 6.1070 | Avg L: 3.80
#    Step 1000 | RMSD: 6.1348 | Avg L: 3.80
#    Step 1500 | RMSD: 6.1413 | Avg L: 3.80
#    Step 2000 | RMSD: 6.1155 | Avg L: 3.80
#    Step 2500 | RMSD: 6.1118 | Avg L: 3.80
#    --- RETRYING 1CAG WITH FRESH NOISE ---
#    Step    0 | RMSD: 35.6800 | Avg L: 3.80
#    Step  500 | RMSD: 6.1067 | Avg L: 3.80
#    Step 1000 | RMSD: 6.1070 | Avg L: 3.80
#    Step 1500 | RMSD: 6.1081 | Avg L: 3.80
#    Step 2000 | RMSD: 6.1167 | Avg L: 3.80
#    Step 2500 | RMSD: 6.1179 | Avg L: 3.80
# RESULT 1CAG | RMSD: 6.1059Å (DISCARDED)
# ----------------------------------------
# Mapping 1CC5...
#    [!] Skipping 1CC5 (Length 83 > 80).
# Mapping 1CC7...
#    Step    0 | RMSD: 130.3111 | Avg L: 3.80
#    Step  500 | RMSD: 2.7505 | Avg L: 3.80
#    Step 1000 | RMSD: 1.6069 | Avg L: 3.80
#    Step 1500 | RMSD: 1.2930 | Avg L: 3.80
#    Step 2000 | RMSD: 1.0962 | Avg L: 3.80
#    Step 2500 | RMSD: 0.9572 | Avg L: 3.80
# RESULT 1CC7 | RMSD: 0.9537Å (SAVED)
# ----------------------------------------
# Mapping 1CC8...
#    Step    0 | RMSD: 147.2812 | Avg L: 3.80
#    Step  500 | RMSD: 2.6964 | Avg L: 3.80
#    Step 1000 | RMSD: 1.8821 | Avg L: 3.80
#    Step 1500 | RMSD: 1.3138 | Avg L: 3.80
#    Step 2000 | RMSD: 1.0864 | Avg L: 3.80
#    Step 2500 | RMSD: 0.9450 | Avg L: 3.80
# RESULT 1CC8 | RMSD: 0.9313Å (SAVED)
# ----------------------------------------
# Mapping 1CCZ...
#    [!] Skipping 1CCZ (Length 171 > 80).
# Mapping 1CEI...
#    [!] Skipping 1CEI (Length 85 > 80).
# Mapping 1CFH...
#    [!] Skipping 1CFH (Length 705 > 80).
# Mapping 1CGI...
#    [!] Skipping 1CGI (Length 301 > 80).
# Mapping 1CHK...
#    [!] Skipping 1CHK (Length 476 > 80).
# Mapping 1CHL...
#    [!] Skipping 1CHL (Length 252 > 80).
# Mapping 1CJP...
#    [!] Skipping 1CJP (Length 948 > 80).
# Mapping 1CKA...
#    Step    0 | RMSD: 106.3147 | Avg L: 3.80
#    Step  500 | RMSD: 1.0813 | Avg L: 3.80
#    Step 1000 | RMSD: 0.7447 | Avg L: 3.80
#    Step 1500 | RMSD: 0.5675 | Avg L: 3.80
#    Step 2000 | RMSD: 0.4878 | Avg L: 3.80
#    Step 2500 | RMSD: 0.4817 | Avg L: 3.80
# RESULT 1CKA | RMSD: 0.3589Å (SAVED)
# ----------------------------------------
# Mapping 1CLB...
#    [!] Skipping 1CLB (Length 2475 > 80).
# Mapping 1CLM...
#    [!] Skipping 1CLM (Length 144 > 80).
# Mapping 1CMB...
#    [!] Skipping 1CMB (Length 208 > 80).
# Mapping 1COA...
# RESULT 1COA | RMSD: 99.0000Å (DISCARDED)
# ----------------------------------------
# Mapping 1CSP...
#    Step    0 | RMSD: 134.0118 | Avg L: 3.80
#    Step  500 | RMSD: 1.5244 | Avg L: 3.80
#    Step 1000 | RMSD: 1.0957 | Avg L: 3.80
#    Step 1500 | RMSD: 0.9128 | Avg L: 3.80
#    Step 2000 | RMSD: 0.8122 | Avg L: 3.80
#    Step 2500 | RMSD: 0.7338 | Avg L: 3.80
# RESULT 1CSP | RMSD: 0.7287Å (SAVED)
# ----------------------------------------
# Mapping 1CTF...
#    Step    0 | RMSD: 131.4606 | Avg L: 3.80
#    Step  500 | RMSD: 3.6285 | Avg L: 3.80
#    Step 1000 | RMSD: 1.7460 | Avg L: 3.80
#    Step 1500 | RMSD: 1.1705 | Avg L: 3.80
#    Step 2000 | RMSD: 0.9376 | Avg L: 3.80
#    Step 2500 | RMSD: 0.8085 | Avg L: 3.80
# RESULT 1CTF | RMSD: 0.8085Å (SAVED)
# ----------------------------------------
# Mapping 1CUK...
#    [!] Skipping 1CUK (Length 190 > 80).
# Mapping 1CVZ...
#    [!] Skipping 1CVZ (Length 212 > 80).
# Mapping 1CYO...
#    [!] Skipping 1CYO (Length 88 > 80).
# Mapping 1D2Z...
#    [!] Skipping 1D2Z (Length 516 > 80).
# Mapping 1D3Z...
#    [!] Skipping 1D3Z (Length 760 > 80).
# Mapping 1D4T...
#    [!] Skipping 1D4T (Length 115 > 80).
# Mapping 1D5T...
#    [!] Skipping 1D5T (Length 433 > 80).
# Mapping 1DAB...
#    [!] Skipping 1DAB (Length 539 > 80).
# Mapping 1DBW...
#    [!] Skipping 1DBW (Length 254 > 80).
# Mapping 1DCJ...
#    [!] Skipping 1DCJ (Length 1620 > 80).
# Mapping 1DD9...
#    [!] Skipping 1DD9 (Length 310 > 80).
# Mapping 1DF4...
#    Step    0 | RMSD: 104.0292 | Avg L: 3.80
#    Step  500 | RMSD: 3.9691 | Avg L: 3.80
#    Step 1000 | RMSD: 2.5884 | Avg L: 3.80
#    Step 1500 | RMSD: 1.8089 | Avg L: 3.80
#    Step 2000 | RMSD: 1.4550 | Avg L: 3.80
#    Step 2500 | RMSD: 1.2498 | Avg L: 3.80
#    --- RETRYING 1DF4 WITH FRESH NOISE ---
#    Step    0 | RMSD: 98.7106 | Avg L: 3.80
#    Step  500 | RMSD: 3.8378 | Avg L: 3.80
#    Step 1000 | RMSD: 2.6667 | Avg L: 3.80
#    Step 1500 | RMSD: 1.7873 | Avg L: 3.80
#    Step 2000 | RMSD: 1.4150 | Avg L: 3.80
#    Step 2500 | RMSD: 1.2299 | Avg L: 3.80
# RESULT 1DF4 | RMSD: 1.2129Å (DISCARDED)
# ----------------------------------------
# Mapping 1DGL...
#    [!] Skipping 1DGL (Length 474 > 80).
# Mapping 1DHN...
#    [!] Skipping 1DHN (Length 121 > 80).
# Mapping 1DIV...
#    [!] Skipping 1DIV (Length 149 > 80).
# Mapping 1DKT...
#    [!] Skipping 1DKT (Length 143 > 80).
# Mapping 1DLW...
#    [!] Skipping 1DLW (Length 116 > 80).
# Mapping 1DM9...
#    [!] Skipping 1DM9 (Length 211 > 80).
# Mapping 1DMB...
#    [!] Skipping 1DMB (Length 370 > 80).
# Mapping 1DOL...
#    Step    0 | RMSD: 145.8203 | Avg L: 3.80
#    Step  500 | RMSD: 2.1571 | Avg L: 3.80
#    Step 1000 | RMSD: 1.6732 | Avg L: 3.80
#    Step 1500 | RMSD: 1.3825 | Avg L: 3.80
#    Step 2000 | RMSD: 1.2183 | Avg L: 3.80
#    Step 2500 | RMSD: 1.0937 | Avg L: 3.80
#    --- RETRYING 1DOL WITH FRESH NOISE ---
#    Step    0 | RMSD: 134.7374 | Avg L: 3.80
#    Step  500 | RMSD: 2.2164 | Avg L: 3.80
#    Step 1000 | RMSD: 1.5279 | Avg L: 3.80
#    Step 1500 | RMSD: 1.3160 | Avg L: 3.80
#    Step 2000 | RMSD: 1.1648 | Avg L: 3.80
#    Step 2500 | RMSD: 1.0673 | Avg L: 3.80
# RESULT 1DOL | RMSD: 1.0481Å (DISCARDED)
# ----------------------------------------
# Mapping 1DSX...
#    [!] Skipping 1DSX (Length 696 > 80).
# Mapping 1DTP...
#    [!] Skipping 1DTP (Length 190 > 80).
# Mapping 1DUN...
#    [!] Skipping 1DUN (Length 121 > 80).
# Mapping 1DXJ...
#    [!] Skipping 1DXJ (Length 242 > 80).
# Mapping 1E0M...
#    [!] Skipping 1E0M (Length 370 > 80).
# Mapping 1E2A...
#    [!] Skipping 1E2A (Length 306 > 80).
# Mapping 1E4F...
#    [!] Skipping 1E4F (Length 378 > 80).
# Mapping 1E5K...
#    [!] Skipping 1E5K (Length 188 > 80).
# Mapping 1E6I...
#    [!] Skipping 1E6I (Length 114 > 80).
# Mapping 1E7L...
#    [!] Skipping 1E7L (Length 330 > 80).
# Mapping 1E9H...
#    [!] Skipping 1E9H (Length 1107 > 80).
# Mapping 1EA7...
#    [!] Skipping 1EA7 (Length 314 > 80).
# Mapping 1EB6...
#    [!] Skipping 1EB6 (Length 177 > 80).
# Mapping 1EDG...
#    [!] Skipping 1EDG (Length 380 > 80).
# Mapping 1EDM...
# RESULT 1EDM | RMSD: 99.0000Å (DISCARDED)
# ----------------------------------------
# Mapping 1EES...
#    [!] Skipping 1EES (Length 4480 > 80).
# Mapping 1EF1...
#    [!] Skipping 1EF1 (Length 752 > 80).
# Mapping 1EG3...
#    [!] Skipping 1EG3 (Length 260 > 80).
# Mapping 1EGN...
#    [!] Skipping 1EGN (Length 433 > 80).
# Mapping 1EHE...
#    [!] Skipping 1EHE (Length 399 > 80).
# Mapping 1EIG...
#    Step    0 | RMSD: 128.8490 | Avg L: 3.80
#    Step  500 | RMSD: 2.7232 | Avg L: 3.80
#    Step 1000 | RMSD: 1.9719 | Avg L: 3.80
#    Step 1500 | RMSD: 1.5125 | Avg L: 3.80
#    Step 2000 | RMSD: 1.2971 | Avg L: 3.80
#    Step 2500 | RMSD: 1.1575 | Avg L: 3.80
#    --- RETRYING 1EIG WITH FRESH NOISE ---
#    Step    0 | RMSD: 106.0666 | Avg L: 3.80
#    Step  500 | RMSD: 2.4601 | Avg L: 3.80
#    Step 1000 | RMSD: 1.6652 | Avg L: 3.80
#    Step 1500 | RMSD: 1.3683 | Avg L: 3.80
#    Step 2000 | RMSD: 1.1889 | Avg L: 3.80
#    Step 2500 | RMSD: 1.1067 | Avg L: 3.80
# RESULT 1EIG | RMSD: 1.0720Å (DISCARDED)
# ----------------------------------------
# Mapping 1EJ0...
#    [!] Skipping 1EJ0 (Length 180 > 80).
# Mapping 1EJG...
#    Step    0 | RMSD: 85.3530 | Avg L: 3.80
#    Step  500 | RMSD: 2.3134 | Avg L: 3.80
#    Step 1000 | RMSD: 1.1146 | Avg L: 3.80
#    Step 1500 | RMSD: 0.7273 | Avg L: 3.80
#    Step 2000 | RMSD: 0.5804 | Avg L: 3.80
#    Step 2500 | RMSD: 0.5002 | Avg L: 3.80
# RESULT 1EJG | RMSD: 0.4989Å (SAVED)
# ----------------------------------------
# Mapping 1EKI...
# RESULT 1EKI | RMSD: 99.0000Å (DISCARDED)
# ----------------------------------------
# Mapping 1ELU...
#    [!] Skipping 1ELU (Length 762 > 80).
# Mapping 1ELW...
#    [!] Skipping 1ELW (Length 248 > 80).
# Mapping 1EM7...
#    Step    0 | RMSD: 97.3871 | Avg L: 3.80
#    Step  500 | RMSD: 1.6943 | Avg L: 3.80
#    Step 1000 | RMSD: 0.9278 | Avg L: 3.80
#    Step 1500 | RMSD: 0.7246 | Avg L: 3.80
#    Step 2000 | RMSD: 0.6262 | Avg L: 3.80
#    Step 2500 | RMSD: 0.5474 | Avg L: 3.80
# RESULT 1EM7 | RMSD: 0.5474Å (SAVED)
# ----------------------------------------
# Mapping 1ENH...
#    Step    0 | RMSD: 111.5294 | Avg L: 3.80
#    Step  500 | RMSD: 2.7236 | Avg L: 3.80
#    Step 1000 | RMSD: 1.2132 | Avg L: 3.80
#    Step 1500 | RMSD: 0.7836 | Avg L: 3.80
#    Step 2000 | RMSD: 0.6262 | Avg L: 3.80
#    Step 2500 | RMSD: 0.5532 | Avg L: 3.80
# RESULT 1ENH | RMSD: 0.4961Å (SAVED)
# ----------------------------------------
# Mapping 1EO0...
#    [!] Skipping 1EO0 (Length 770 > 80).
# Mapping 1EP0...
#    [!] Skipping 1EP0 (Length 183 > 80).
# Mapping 1EQ6...
#    [!] Skipping 1EQ6 (Length 189 > 80).
# Mapping 1ERZ...
#    [!] Skipping 1ERZ (Length 606 > 80).
# Mapping 1ES5...
#    [!] Skipping 1ES5 (Length 260 > 80).
# Mapping 1ES9...
#    [!] Skipping 1ES9 (Length 212 > 80).
# Mapping 1ET1...
#    Step    0 | RMSD: 39.4720 | Avg L: 3.80
#    Step  500 | RMSD: 3.0388 | Avg L: 3.80
#    Step 1000 | RMSD: 1.5216 | Avg L: 3.80
#    Step 1500 | RMSD: 0.9837 | Avg L: 3.80
#    Step 2000 | RMSD: 0.7938 | Avg L: 3.80
#    Step 2500 | RMSD: 0.7074 | Avg L: 3.80
# RESULT 1ET1 | RMSD: 0.7046Å (SAVED)
# ----------------------------------------
# Mapping 1EUW...
#    [!] Skipping 1EUW (Length 147 > 80).
# Mapping 1EVT...
#    [!] Skipping 1EVT (Length 645 > 80).

# FINISH: 37 samples saved.
# (base) brendanlynch@Brendans-Laptop AI %  
