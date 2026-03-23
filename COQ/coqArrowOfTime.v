Require Import Reals.
Require Import Lra.

Open Scope R_scope.

(*** RESOLUTION 33: AXIOMATIC DERIVATION OF THE ARROW OF TIME ***)

Parameter PI : R.
Axiom PI_pos : PI > 0.

Definition Omega_u : R := 2073045 / 10000000000.
Definition Phi_u : R := 2 * PI * Omega_u.

Parameter SpectralDensity : R -> R.

Definition is_stable (phi : R) : Prop :=
  exists (Integrable : Prop), Integrable /\ (forall t, SpectralDensity (phi * t) <= 1.0 / Omega_u).

Axiom t_symmetry_divergence : 
  forall (phi : R), phi = 0 -> ~ is_stable phi.

Axiom hopf_stability : is_stable Phi_u.

Theorem arrow_of_time_necessity :
  exists (phi : R), is_stable phi /\ phi <> 0.
Proof.
  exists Phi_u.
  split.
  - apply hopf_stability.
  - unfold Phi_u, Omega_u.
    (* Explicitly convert 'greater than' to 'not equal' for the solver *)
    assert (H_nz : PI <> 0).
    { apply Rgt_not_eq. exact PI_pos. }
    lra.
Qed.