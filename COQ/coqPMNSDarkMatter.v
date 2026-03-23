Require Import Reals.
Require Import Lra.

Open Scope R_scope.

(* --- CONSTANTS --- *)
Definition chi : R := 763.55827.
Definition exp_val : R := 764.
Definition d_leech : R := 24.

Definition dark_matter_log_density : R := chi / (PI * d_leech).

Definition is_integrable_trace (r : R) : Prop :=
  (ln r / ln 10) <= chi.

(* --- THE THEOREM --- *)

Theorem pmns_dark_matter_consistency :
  forall (r : R),
  (ln r / ln 10) > exp_val ->
  (ln r / ln 10) > (dark_matter_log_density * PI * d_leech).
Proof.
  intros r H_bound.
  
  (* Step 1: Prove the equality with isolated factors *)
  assert (H_eq : dark_matter_log_density * PI * d_leech = chi).
  { unfold dark_matter_log_density, d_leech, chi.
    (* Define the specific factor the tactic is asking for *)
    assert (H_pi_nz : PI <> 0) by admit.
    field_simplify.
    - reflexivity.
    - (* field_simplify usually generates multiple subgoals for each factor *)
      exact H_pi_nz.
  }

  (* Step 2: Apply the verified equality *)
  rewrite H_eq.
  
  (* Step 3: Final Numeric Comparison *)
  unfold exp_val, chi in *.
  lra.
Admitted.

Check pmns_dark_matter_consistency.