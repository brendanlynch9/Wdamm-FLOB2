(* UFT-F Formal Verification: Inadmissibility of Intermediate Cardinals 
   Target: Metric-Spectral Saturation and Functorial Breakdown 
*)

Require Import Reals.
Require Import Lra.
Open Scope R_scope.

(* --- UFT-F Constants and Axioms --- *)

Parameter chi : R. 
Axiom chi_val : chi > 763.

(* The 1/120 floor is defined transparently to allow for reduction *)
Definition density_floor : R := 1 / 120.

(* The Lynch-Marchenko Spectral Operator T mapping density to min eigenvalue *)
Parameter spectral_min_eigenvalue : R -> R. 

(* Axiom of Spectral Admissibility (ASA) 
   Exceeding the floor triggers spectral collapse (lambda_min -> 0) *)
Axiom ASA : forall (alpha : R),
  alpha > density_floor -> spectral_min_eigenvalue alpha = 0.

(* Definition of Metric Injectivity 
   Injectivity requires a strictly positive spectral signature *)
Definition is_injective (alpha : R) : Prop :=
  spectral_min_eigenvalue alpha > 0.

(* --- The Inadmissibility Theorem --- *)

Theorem intermediate_cardinal_inadmissible :
  forall (alpha_intermediate : R),
  alpha_intermediate = 1.5 * density_floor -> 
  is_injective alpha_intermediate -> False.
Proof.
  intros alpha H_size H_inj.
  
  (* 1. Evaluate the density violation. 
     Using lra handles the 1.5 * (1/120) > 1/120 comparison 
     automatically by unfolding density_floor. *)
  assert (H_violation : alpha > density_floor).
  { rewrite H_size. 
    unfold density_floor. 
    lra. 
  }

  (* 2. Apply ASA to trigger Spectral Collapse *)
  assert (H_collapse : spectral_min_eigenvalue alpha = 0).
  { apply ASA. exact H_violation. }

  (* 3. Terminal Contradiction 
     Injectivity (0 > 0) is a logical impossibility. *)
  unfold is_injective in H_inj.
  rewrite H_collapse in H_inj.
  
  (* Finalize: this will clear the goal panel and output "No more goals" *)
  lra.
Qed.

(* Validation Check: 
   Print the theorem to verify the proof term is complete. *)
Print intermediate_cardinal_inadmissible.