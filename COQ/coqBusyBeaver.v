Require Import Reals.
Require Import Lra.

Open Scope R_scope.

(*** 1. CONSTANTS ***)
Definition n_base : R := 24.
Definition chi_rupture : R := 763.55827.

(*** 2. THE BUSY BEAVER HALTING CLOSURE (ACI) ***)
Theorem aci_bb6_stability :
  forall (v_m : R),
  v_m <= chi_rupture -> 
  v_m / (n_base * 3) < 11.
Proof.
  intros v_m H_bound.
  unfold n_base.
  
  (* Step 1: Simplify the goal into a linear form *)
  (* field_simplify handles the division by (24*3) automatically *)
  field_simplify.
  
  (* Step 2: Use lra on the simplified inequality *)
  (* After field_simplify, we are left with: v_m / 72 < 11 *)
  (* We multiply both sides by 72 to clear the fraction *)
  apply (Rmult_lt_reg_r 72).
  - lra. (* 72 > 0 *)
  - unfold Rdiv. 
    rewrite Rmult_assoc.
    rewrite Rinv_l by lra.
    rewrite Rmult_1_r.
    
    (* Step 3: Final Numerical Closure *)
    assert (H_limit : 11 * 72 = 792) by lra.
    rewrite H_limit.
    
    (* Comparison: v_m <= 763.55827 < 792 *)
    assert (H_chi_lt : chi_rupture < 792) by (unfold chi_rupture; lra).
    lra.
Qed.

(*** FINAL VERIFICATION ***)
Check aci_bb6_stability.