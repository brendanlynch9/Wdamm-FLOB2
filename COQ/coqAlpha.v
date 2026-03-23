Require Import Reals.
Require Import Lra.

Open Scope R_scope.

(*** 1. CONSTANTS ***)
Definition e8_roots : R := 240.
Definition delta_e8 : R := 1 / e8_roots.
Definition alpha_inv_target : R := 137.03599.

(*** 2. THE E8 SPECTRAL CORRECTION ***)

Theorem alpha_e8_correction_integrity :
  (alpha_inv_target * (1 + delta_e8)) > alpha_inv_target.
Proof.
  unfold alpha_inv_target, delta_e8, e8_roots.
  
  (* Step 1: Explicitly prove 1/240 > 0 by reconciling notations *)
  assert (H_pos : 1 / 240 > 0).
  {
    unfold Rdiv.
    rewrite Rmult_1_l. (* Changes 1 * / 240 into / 240 *)
    apply Rinv_0_lt_compat.
    lra. (* Proves 240 > 0 *)
  }
  
  (* Step 2: Use lra to close the scaling inequality *)
  (* Since alpha_inv > 0 and 1/240 > 0, the product must be > alpha_inv *)
  lra.
Qed.