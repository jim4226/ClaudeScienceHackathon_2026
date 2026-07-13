# Signed perturbation directions in phase-age space: derivation and freeze

*Outcome-blind derivation and pre-registration of a covariance-scaled, signed
biological-age direction learned from a controlled human ion-channel
perturbation, for transport into an untouched external clinical cohort.*

## Methods

### Coordinate system

The frozen phase-age vector for an exam is
**z** = (z_P, z_AV, z_QRS, z_STT), where each z_k is the age- and
sex-adapted calibration z-score of the phase-specific ECG-age clock
(quadratic prediction adaptation `adapted_k = a·pred_k² + b·pred_k + c`,
followed by `z_k = (adapted_k − m_k)/σ_k` with
`m_k = X·β_mean`, `σ_k = exp(½ X·β_logvar)` floored at 0.25 and
`X = [1, (age−50)/10, ((age−50)/10)², sex, sex·(age−50)/10]`, sex coded
female = 1). All adaptation and calibration coefficients were inherited
bit-exact from the frozen disagreement definitions and were not re-fit.

The shared aging axis is **A** = **u**ᵀ**z** with **u** = ½(1,1,1,1); the
three-dimensional contrast coordinate is **q** = C**z**, where C has
orthonormal rows spanning the subspace orthogonal to **u**
(C**1** = **0**, CCᵀ = I). The unsigned disagreement radius is the
covariance-normalized Mahalanobis norm within this subspace,
D = √(**q**ᵀ Σ_q⁻¹ **q**). The contrast covariance Σ_q was the frozen
Ledoit–Wolf estimate on the calibration cohort (shrinkage 0.0177,
condition number 1.497); a reconstruction of the calibration contrast
covariance from the raw phase predictions reproduced the frozen Σ_q to
within 0.015 in every entry (residual equal to the frozen shrinkage), and
the calibration population reproducing the frozen D standardization
(one exam per patient, healthy, n = 9,887) matched the frozen
`n_calibration` exactly.

In whitened coordinates **û** = Σ_q⁻¹ᐟ² **q**, the radius is D = ‖**û**‖.
A signed perturbation score is the projection of **û** onto a fixed unit
axis, so it retains the direction that D discards; by construction
|S| ≤ D for every exam.

### Perturbation directions

For a controlled perturbation *k*, the contrast-subspace mean displacement
is **m**_k = E[C(**z**_post − **z**_baseline)], and the covariance-scaled
signed direction and its whitened representation are

  **w**_k = Σ_q⁻¹ **m**_k / √(**m**_kᵀ Σ_q⁻¹ **m**_k),
  **v̂**_k = Σ_q⁻¹ᐟ² **m**_k / ‖Σ_q⁻¹ᐟ² **m**_k‖,

with the scaling chosen so that **w**_kᵀ Σ_q **w**_k = 1 (verified to
< 10⁻⁴). The external patient score is S_k = **w**_kᵀ **q** = **v̂**_k · **û**.

**IKr blockade (ECGRDVQ).** For each participant, the phase-vector response
was the triplicate-averaged, baseline-corrected (pre-dose timepoint
−0.5 h), 0.5–8 h time-averaged (trapezoidal integral divided by 7.5 h)
paired dofetilide-minus-placebo contrast; at least two valid replicates
per treatment–period–timepoint were required (all cells had three).
**m**_IKr was the mean of these participant-level displacements
(n = 22 participants).

**Acute ischemia (STAFF-III).** Occlusion responses were the
inflation-minus-baseline contrast per occlusion (baseline coalesced,
linked recording preferred over within-file), averaged within patient
before pooling across patients (91 occlusions, 70 patients), so that
patients with multiple occlusions were not over-weighted.

### Stability gate

A direction was eligible for transport only if it satisfied all of:
pipeline yield ≥ 0.70; participant/patient-bootstrap median
covariance-aware cosine cos_Σ ≥ 0.80; lower 95% cosine bound > 0; sign
stable in ≥ 90% of bootstraps; and a treatment-label sign-flip permutation
test supporting a nonzero directional shift (p < 0.05). The
covariance-aware cosine was
cos_Σ(**a**,**b**) = **a**ᵀΣ_q⁻¹**b** / √((**a**ᵀΣ_q⁻¹**a**)(**b**ᵀΣ_q⁻¹**b**)).
The bootstrap resampling unit was the participant (ECGRDVQ) or patient
(STAFF), carrying all periods, timepoints and occlusions; the permutation
applied participant/patient-level sign flips of the contrast, with the
Mahalanobis norm ‖**m**‖_Σ as the test statistic; each bootstrap direction
was aligned to the full-sample direction (sign of cos_Σ) before computing
sign stability. All resampling used 10,000 replicates,
`numpy.random.default_rng`, seed 20260712.

The gate was applied and then read out; no verdict was pre-declared.

### Confirmation, standardization and controls

Confirmation of the IKr direction used quinidine, a second IKr blocker
administered to the same crossover cohort in a separate period; it is
therefore a within-cohort, held-mechanism pharmacologic confirmation, not
independent external validation. Pre-defined confirmation required a
positive mean quinidine projection on the frozen **w**_IKr with a
participant-bootstrap 95% CI excluding zero, a positive
cos_Σ(**m**_dof, **m**_quin) with bootstrap CI, and a
leave-one-participant-out check (direction re-derived on N−1 dofetilide
participants, the held-out participant's quinidine response projected on
it). Ranolazine and verapamil were projected as secondary active-drug
specificity controls; they were neither required to be null nor used to
redefine the direction.

The score was standardized on the frozen calibration cohort (the same
healthy, one-exam-per-patient population that defines D),
S_IKr,std = (**w**_IKrᵀ**q** − μ_S,cal)/σ_S,cal, with μ_S,cal and σ_S,cal
recorded; any external-cohort SD scaling is reserved as a sensitivity.
Negative controls — the sign-flipped direction, a frozen set of
treatment-sign-flip realizations, and 200 random Σ_q-normalized directions
in q-space — were frozen as diagnostic empirical nulls only: they cannot be
searched for a better direction, redefine **w**, change the endpoint, or
gate the primary conclusion. The scorer, its fixture, and an independent
verifier (asserting C**1** = 0, CCᵀ = I, Σ_q symmetric positive-definite,
**w**ᵀΣ_q**w** = 1, exact fixture reproduction, and that no outcome column
is ever loaded) were frozen alongside the protocol lock, which carries a
canonical content self-hash and the SHA-256 hashes of C, Σ_q, the input
feature tables and the scorer.

## Results

The IKr-blockade contrast displacement was
**m**_IKr = (−0.129, −0.365, +0.243) (q1, q2, q3; time-averaged units),
dominated by the q2 = QRS-vs-ST–T coordinate — consistent with the
selective ST–T phase-age increase produced by delayed-rectifier potassium
current blockade — with Mahalanobis norm ‖**m**_IKr‖_Σ = 0.563. The
resulting frozen direction was **w**_IKr = (−0.381, −0.939, +0.703).

This direction passed every gate criterion: pipeline yield 1.00 (22/22),
bootstrap median cos_Σ = 0.941 (95% CI 0.635–0.998), sign stable in 99.99%
of bootstraps, and sign-flip permutation p = 0.033. Quinidine confirmed the
direction: the mean quinidine projection on the frozen **w**_IKr was
+0.835 (95% CI 0.514–1.190, bootstrap p < 10⁻⁴), the two IKr blockers were
aligned in the whitened metric (cos_Σ(**m**_dof, **m**_quin) = +0.943, 95%
CI 0.494–0.993), and the leave-one-participant-out directions were highly
stable (median cos_Σ 0.997, minimum 0.946, all > 0.90) with the held-out
quinidine response projecting positive in 90.5% of participants. The two
IKr blockers had projection CIs excluding zero (dofetilide +0.563,
0.254–0.912; quinidine +0.835, 0.518–1.199), whereas the non-IKr active
comparators did not (ranolazine +0.209, −0.031–0.475; verapamil +0.117,
−0.088–0.370).

The acute-ischemia contrast direction failed the gate. Occlusion moved the
phase-age vector predominantly along the shared A axis (all four phase
clocks shifted coherently upward during late inflation), leaving a weak and
unstable contrast-subspace displacement (‖**m**_isch‖_Σ = 0.187; bootstrap
median cos_Σ = 0.634 with a 95% interval spanning zero, −0.844 to 0.987;
sign stable in only 79.1% of bootstraps; permutation p = 0.835). Per
protocol, the established shared-A ischemia result is retained and no
substitute contrast direction was constructed; ischemia does not enter the
transport family.

Because only the IKr direction passed, the transport family contains a
single frozen direction (k = 1), and the pre-registered external test is a
one-degree-of-freedom likelihood-ratio comparison of a base survival model
(age, sex, HR, PR, QRS, QTc, whole-ECG age, A, D) against the same model
augmented by S_IKr,std. The score is standardized on the frozen calibration
cohort (μ_S,cal = 0.008, σ_S,cal = 1.011; the unit variance follows from
**w**ᵀΣ_q**w** = 1). All external endpoints, alignment windows, censoring,
tie handling, and negative controls were frozen before any outcome was
accessed.

The ECGRDVQ fingerprint that anchors this direction has already been
observed; the derivation reported here is a retrospective, outcome-free
construction of a fixed scoring axis. The prospective novelty begins only
with the frozen external transport test in the independent cohort.
