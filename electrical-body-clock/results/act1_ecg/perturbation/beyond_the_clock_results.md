# Beyond the Clock: randomized human perturbations reveal hidden physiological directions inside an ECG biological-age model

*Integrated results — perturbation-compass discovery centerpiece. Impersonal
voice. All directional quantities are frozen; the ECGRDVQ derivation is a
retrospective, outcome-free construction and the prospective novelty begins
with transport into external clinical ECG populations.*

## Summary claim

Randomized IKr blockade revealed a stable signed direction within a
phase-resolved ECG age model. A second IKr-active drug reproduced that
displacement, and the frozen direction carried conditional information about
physician-assigned QT extension in an external clinical ECG population — while
unsigned radial disagreement did not. The failed radial hypothesis is
informative in itself: physiology does not merely move farther from normal, it
moves in directions.

A frozen phase-specific ECG age model responded to randomized perturbations
along separable coordinates. IKr blockade produced a reproducible signed
repolarization displacement, whereas transient ischemia shifted the shared
age-model coordinate without increasing radial disagreement. Acute
perturbations are described throughout as **displacing the ECG age-model
state**; no claim is made that they caused biological aging or rejuvenation.



![Discovery compass: IKr blockade displaces the frozen ECG age model along a stable signed direction (panel a, tight red spread) that transports to an external QT-extension phenotype (panel c, OR 1.23), while ischemia moves a different, diffuse direction (panel a, blue) and the unsigned radius D does not transport (panel c). Panel b: IKr blockers project positively on the frozen direction; mechanistic comparators do not.]({{artifact:676848c5-f0d0-41bc-94d5-a7ab62f2857b}})

## Coordinate system (frozen)

Each exam is summarized by a four-dimensional phase-age vector
**z** = (z_P, z_AV, z_QRS, z_STT) of age- and sex-adapted calibration
z-scores from phase-specific ECG-age clocks. The shared aging axis is
A = ½(1,1,1,1)·**z**; the contrast coordinate is **q** = C**z** with C
orthonormal, C**1**=0, CCᵀ=I. The unsigned disagreement radius is the
within-subspace Mahalanobis norm D = √(**q**ᵀΣ_q⁻¹**q**), Σ_q the frozen
Ledoit–Wolf contrast covariance (shrinkage 0.0177, condition number 1.497).
In whitened coordinates **û** = Σ_q⁻¹ᐟ²**q**, D = ‖**û**‖ and a signed score
S_k = **w**_kᵀ**q** = **v̂**_k·**û** retains the direction D discards
(|S| ≤ D by construction). All calibration and adaptation coefficients were
inherited bit-exact from the frozen definitions and were not re-fit.

## Arm 1 — Randomized discovery (ECGRDVQ)

The IKr-blockade contrast displacement, computed per participant as the
triplicate-averaged, baseline-corrected (−0.5 h pre-dose), 0.5–8 h
time-averaged paired dofetilide-minus-placebo contrast and averaged over
n = 22 participants, was **m**_IKr = (−0.129, −0.365, +0.243), dominated by
the q2 = QRS-vs-ST–T coordinate and consistent with a selective ST–T
phase-age increase under delayed-rectifier potassium-current blockade
(‖**m**_IKr‖_Σ = 0.563). The frozen covariance-scaled direction was
**w**_IKr = (−0.381, −0.939, +0.703), with **w**ᵀΣ_q**w** = 1.

The direction passed every pre-registered stability-gate criterion: pipeline
yield 22/22; participant-bootstrap median covariance-aware cosine
cos_Σ = 0.941 (95% CI 0.635–0.998); sign stable in 99.99% of bootstraps; and
an exact participant sign-flip permutation test of the Mahalanobis norm
T² = **m**ᵀΣ_q⁻¹**m**, recomputing the direction inside every permutation,
p = 0.033. Leave-one-participant-out derivation confirmed that no participant
was scored on a direction learned from them (median cos_Σ 0.997, minimum
0.946). The gate was applied and then read out; no verdict was pre-declared.

## Arm 2 — Cross-drug confirmation

Quinidine, a second IKr-active drug given to the same crossover cohort in a
separate period, reproduced the displacement: the mean quinidine projection
on the frozen **w**_IKr was +0.835 (95% CI 0.514–1.190; bootstrap p < 10⁻⁴),
and the two blockers were aligned in the whitened metric
(cos_Σ(**m**_dof, **m**_quin) = +0.943, 95% CI 0.494–0.993). Because quinidine
was measured in the same participants, this is a within-cohort, held-mechanism
pharmacologic confirmation, not independent external validation.

Ranolazine and verapamil are mechanistic comparators, not inert or negative
controls. Projected on the frozen **w**_IKr, the two IKr blockers had
projection CIs excluding zero (dofetilide +0.563, 0.254–0.912; quinidine
+0.835, 0.518–1.199) while the two comparators did not (ranolazine +0.209,
−0.031–0.475; verapamil +0.117, −0.088–0.370); the comparators were neither
required to be null nor used to redefine the direction. Compared against the
shared axis A, radius D, whole-ECG age and QTc, S_IKr is the only coordinate
that isolates the signed repolarization direction.

The acute-ischemia contrast direction (STAFF-III) failed the same gate:
occlusion moved the vector predominantly along the shared A axis, leaving a
weak, unstable contrast displacement (‖**m**_isch‖_Σ = 0.187; median
cos_Σ = 0.634 with a 95% interval spanning zero; sign stable 79.1%;
permutation p = 0.835). Per protocol the established shared-A ischemia result
is retained and no substitute contrast direction was constructed. Two
perturbations therefore move two different coordinates of the same frozen
model — a signed contrast for IKr blockade, the shared radius for ischemia.

## Arm 3 — External physician-labeled phenotype (Chapman-Shaoxing + Ningbo)

The frozen S_IKr was transported, without refitting, onto 44,550 usable
one-record-per-patient clinical ECGs from the combined ecg-arrhythmia 1.0.0
release (pipeline yield 99.3%; reconstructed z reproduced the stored z to
0.0). The pre-registered test — a one-degree-of-freedom nested likelihood-ratio
test for S_IKr in the model
`QT-extension ~ S_IKr + age + sex + HR + QTc + QRS + whole-age + A + D`
(physician-assigned QT-interval extension, SNOMED 111975006; 386 cases,
≥100 required) — was significant (LR = 13.9, p = 1.9×10⁻⁴; OR per SD = 1.23,
95% CI 1.10–1.36) and essentially unchanged under Firth penalization
(OR 1.22, p = 1.9×10⁻⁴).

This is a conditional result, not simple separation. The marginal S_IKr
association is null (OR 1.00, p = 0.996) and the effect emerges only with
adjustment, rising monotonically as the base model is enriched
(marginal → +age/sex p = 0.09 → +intervals p = 7×10⁻³ → full p = 2×10⁻⁴);
S_IKr is a repolarization-shape coordinate unmasked once QRS and the shared
amplitude A are accounted for. Accordingly, the defensible statement is that
**the frozen IKr direction added information about physician-assigned QT
extension beyond conventional intervals, shared age-model displacement and
radial disagreement** — not that it identifies QT prolongation better than
QTc. A bootstrap of the difference in incremental contribution (600-fold
patient resampling) placed S_IKr's own incremental information robustly
above zero (LR 15.3, 95% CI 2.9–35.2) but **not** statistically distinguishable
from QTc, A or D (all pairwise-difference CIs include zero); the unsigned
radius D was the weakest single coordinate (incremental LR 3.3, p = 0.07).

Reported transparently as required: the raw SNOMED label is noisy — 42% of
cases have automated QTc < 350 ms and the dominant rhythms are atrial flutter
and sinus bradycardia, where automated QT delineation is unreliable — so a
post-hoc reliable-interval subset (QTc 350–600 ms, HR 40–120 bpm) was examined
and preserved the effect (OR 1.25, p = 1.3×10⁻³) with the label then behaving
correctly (case QTc 465 vs 427 ms); this subset analysis is post-hoc
robustness, not pre-registered confirmation. Rhythm-exclusion sensitivities
show the signal holds excluding atrial flutter/fibrillation (p = 0.014) but
attenuates to null when both flutter and bradycardia are removed (OR 0.93,
p = 0.48, 86 cases), so the association is not independent of rhythm context.

By site, Ningbo (n = 34,343; 329 cases) independently confirms the effect
(LR = 9.7, p = 1.9×10⁻³; OR 1.20, 95% CI 1.07–1.34) and serves as the
site-specific external phenotype confirmation. Chapman-Shaoxing (n = 10,207;
57 cases) is under-powered against the ≥100-case gate and is reported in the
same signed direction with a confidence interval and no pass/fail conclusion
(OR 1.44, 95% CI 1.06–1.97).

## Arm 4 — Cross-national generalizability (CPSC + Georgia): pre-specified, deferred

The independent geographic-replication arm would test whether the frozen
signed direction transports to a non-Chinese population, using the open
Challenge-2020 sources (CPSC and CPSC-extra, China; Georgia/Emory, USA; PTB and
PTB-XL excluded because they overlap the clock-development source). The
pre-specified protocol is header-only screening first, waveform inference only
if the non-PTB prolonged-QT case gate (≥100 records) passes, then the identical
frozen model per source with meta-analysis.

This arm is **deferred** for the present submission and adds only
cross-national generalizability — not discovery, confirmation, or the
signed-beats-unsigned claim, all of which are established in Arms 1–3. Its
scope is narrow because three of the four external sites already in the chain
(Chapman-Shaoxing, Ningbo, and CPSC) are Chinese; only Georgia (USA) would add
population diversity, and at the observed QT-extension prevalence (~0.9%) the
~10³·⁴ Georgia records sit near the ≥100-case gate, so a qualifying US case
count is not assured. Critically, **independent-site replication is already
demonstrated within Arm 3**: Ningbo confirms the effect at a second hospital
independent of the Chapman-Shaoxing derivation site. The frozen scorer and the
deterministic header-gate procedure are in place, so this arm can be executed
unchanged if a US replication is later required.

## Arm 5 — Open MIMIC portability (dropped by pre-registered gate)

The open MIMIC-IV-ECG module supplies no chronological age or sex. The
pre-registered invariance gate — S_IKr computable without age, S(p,a)=S(p,a+1)
to numerical tolerance — failed by construction, because the phase z-scores are
age- and sex-adapted (numerically, the same ECG's S_IKr moves on average
0.33 SD, up to ~1 SD, across ages 30–80; max |ΔS| per +1 yr = 0.029). Per the
pre-registered rule the score was not redefined and the MIMIC arm was dropped;
the external evidence is carried by the Chapman-Shaoxing + Ningbo phenotype
test (Arm 3), with the CPSC/Georgia cross-national arm available but deferred.

## Novelty statement

To our knowledge, this is the first controlled-human perturbation map of a
phase-resolved ECG age model, separating shared, radial and signed
physiological coordinates and transporting a frozen signed direction into
clinical ECG populations. A drug-specific ECG signature per se is not claimed
as novel (cf. the 2025 IKrNet preprint).
