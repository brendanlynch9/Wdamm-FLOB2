(* ===================================================================== *)
(* PROOF-OF-RIGIDITY: DETERMINISTIC VALIDATION & INPUT EQUIVALENCE       *)
(* ===================================================================== *)

Require Import Reals.
Open Scope R_scope.

Parameter V : R.
Axiom V_pos : V > 0.

(* 1. The Reconstruction Function *)
Definition C_recon (K N sigma : R) : R :=
  K / (N * V * sigma).

(* 2. The Validation Function V: R^5 -> {0,1} *)
(* We use Rle_dec to constructively decide if the absolute difference is <= epsilon. *)
Definition Validation_Func (K N sigma T_f epsilon : R) : nat :=
  match Rle_dec (Rabs (C_recon K N sigma - T_f)) epsilon with
  | left _  => 1  (* State Accepted *)
  | right _ => 0  (* State Rejected *)
  end.

(* 3. Deterministic Validation (Input Equivalence) *)
(* In intuitionistic type theory, all functions are pure.
   Applying the same function to the same inputs always yields the same output. *)
Theorem Input_Equivalence :
  forall (K1 N1 sigma1 Tf1 eps1 K2 N2 sigma2 Tf2 eps2 : R),
  K1 = K2 -> N1 = N2 -> sigma1 = sigma2 -> Tf1 = Tf2 -> eps1 = eps2 ->
  Validation_Func K1 N1 sigma1 Tf1 eps1 = Validation_Func K2 N2 sigma2 Tf2 eps2.
Proof.
  intros K1 N1 sigma1 Tf1 eps1 K2 N2 sigma2 Tf2 eps2.
  intros HK HN Hsigma HTf Heps.
  (* Rewrite the variables based on the established equalities *)
  rewrite HK, HN, Hsigma, HTf, Heps.
  (* By definition of pure functions, equality is reflexive *)
  reflexivity.
Qed.

(* 4. State Tuple Equivalence *)
(* Proving S1=S2 -> V(S1)=V(S2) using Coq Records *)
Record StateTuple := mkState {
  state_K : R;
  state_N : R;
  state_sigma : R;
  state_Tf : R;
  state_eps : R
}.

Definition V_tuple (S : StateTuple) : nat :=
  Validation_Func (state_K S) (state_N S) (state_sigma S) (state_Tf S) (state_eps S).

Theorem Tuple_Equivalence :
  forall (S1 S2 : StateTuple),
  S1 = S2 -> V_tuple S1 = V_tuple S2.
Proof.
  intros S1 S2 Heq.
  rewrite Heq.
  reflexivity.
Qed.