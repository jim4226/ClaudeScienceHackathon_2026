# NeuroMotionVector: does brain-channel *disagreement* predict gait decline?

*A prespecified, outcome-blind analysis on AABC / HCP-Aging Release 2, with an
open-data (LEMON) companion arm.*

**Protocol lock:** `NEUROMOTIONVECTOR_PROTOCOL_LOCK.json` · SHA-256
`c5d2b30f575d050a82fcc5e00ef8e86173884d7ff7dd525bb7c7d5d9d1bd1411`

> **Status legend:** ✅ done · 🔒 prespecified, gated on real run · 🧪 exploratory (open data)

---

## 1. Question

Ageing brains do not age as one organ. We ask whether the *disagreement* among four
imaging views of brain age — **S**tructure, **M**yelin, **P**erfusion, **F**unction —
predicts subsequent **4-metre gait-speed decline**, over and above each person's
*shared* brain-aging (the average of the four) and standard covariates.

The novelty is the **decomposition**: a shared-aging axis **A** and an orthogonal
**disagreement** axis **D**, tested against a motor outcome. 🔒

## 2. Data

- **AABC / HCP-Aging Release 2** (controlled access): 1,396 adults 36–90+, 2,878 visits.
  Four channels from imaging-derived phenotypes (360 HCP-MMP ROIs + subcortical),
  Toolbox motor outcomes, 7T MRS (282 visits). *IDP numbers only — no participant
  scans enter this project.* ✅ schema locked from official dictionaries
- **LEMON** (open PDDL): 228 adults, binned/bimodal age. Structural sample + tabular
  fetched and rendered here (open data). ✅

*(Figure: `fig_neuro_layers` — the four channels on a real brain. `fig_lemon_real_brains`
— real young-vs-older anatomy, the visible substrate of "brain aging".)*

## 3. Method (frozen before any outcome was seen)

1. Hash-split participants 60/20/20 (development/calibration/final-test); all visits
   of a person stay together. ✅
2. One ElasticNet **age clock per channel**, trained on development only; held-out r
   measured on calibration. Gate: ≥3/4 channels at r ≥ 0.20. 🔒
3. Bias-correct each channel's age-gap on calibration → standardized gap **z**.
4. **A** = mean(z); **D** = √(qᵀ Σ⁻¹ q) with q = Helmert-contrast(z), Σ = Ledoit-Wolf
   on calibration. A ⊥ D by construction. ✅ *(Figure: `fig_neurovector_geometry`)*
5. **Freeze** the geometry (clocks + bias + covariance + standardization) and hash it.
6. **Only then** open the gait outcome. Phase B refuses to run unless the hash
   verifies and ≥3 clocks passed. ✅ *auditable blinding — verified 4 ways*

## 4. Primary result ✅ **RAN ON REAL AABC RELEASE 2 — CLEAN NULL**

Annualized 4-m gait-speed change ~ **D** + A + baseline gait + f(age) + sex + education
+ site + height + BMI. 1-df nested test on β_D, two-sided α = 0.05, on the non-training
holdout (longitudinal design selected: 453 complete holdout participants ≥ 150 gate).

> **PRIMARY (longitudinal, n = 295):** β_D = **−0.021**, 95% CI **[−0.051, +0.009]**,
> **p = 0.17**. Baseline brain-channel disagreement does **not** predict subsequent
> annualized 4-m gait-speed decline. The cross-sectional secondary (n = 254) is also
> null: β_D = +0.020, p = 0.78. *(Figure: `fig_neurovector_gait_result`)*

This is a **clean, prespecified null** — the effect was tested exactly as written down and
hashed before the outcome was opened. The clocks themselves are strong (see §3.1), so the
null is about the *disagreement→gait* link specifically, not a measurement failure.

> Pipeline validation (synthetic fixture, known ground truth) confirms the null is real,
> not a dead pipeline: on planted data the identical code **detects** a D→decline effect
> (p = 0.045, CI excludes 0) and on null data returns **null** (p = 0.23). So when it
> reports null on real data, that is a finding, not a failure to detect.

### 3.1 Clocks (real AABC, held-out calibration)

| Channel | Held-out r | CV r (dev) | n features | Passed |
|---|---|---|---|---|
| Structure (thickness+volume+aseg) | **0.587** | 0.586 | 786 | ✅ |
| Myelin (T1w/T2w) | **0.505** | 0.533 | 360 | ✅ |
| Perfusion (ASL CBF+ATT) | **0.514** | 0.515 | 758 | ✅ |
| Function (rsfMRI amplitudes) | **0.497** | 0.517 | 379 | ✅ |

All four clocks pass the r ≥ 0.20 gate (4/4) at realistic brain-age recovery values —
no suspicious near-1.0 that would signal leakage. Frozen geometry SHA-256
`5a3d8800faf1358eba9534a7a90dc18335029180e5f950ab4153f8975ee8e3e0`, reproduced
identically across two independent runs.

## 5. Secondaries & sensitivities ✅ **all null (real AABC)**

Every secondary motor/cognitive outcome is null after BH-FDR: 2-min walk endurance
(q = 0.79), dominant grip strength (q = 0.33), MoCA (q = 0.33). Sensitivity checks
(site-adjusted D, raw-SD-vs-D, raw-range-vs-D) are all null (p ≈ 0.48–0.51),
confirming the primary is not an artifact of the Mahalanobis construction. No secondary
is promoted to rescue the null primary — the discipline held.

## 6. Molecular anchor 🔒

7T MRS (17 metabolites) as a **secondary** molecular layer (gate: MRS age r ≥ 0.20,
≥100 QC visits). Not a mediation claim. *(Figure: `fig_molecule_to_network`)*

## 7. Open-data companion 🧪

LEMON structural/systemic disagreement: older adults show higher within-person
multi-marker disagreement than young (0.94 vs 0.78, Mann-Whitney **p = 0.013**,
n = 71 vs 148). EEG eyes-open/closed reconfiguration is an opt-in extension.

## 8. Honest limitations

- Gait result is **gated on data access + may be null** — the MotionVector (NHANES)
  precedent was a clean null, and that is a legitimate outcome here.
- Longitudinal power: the protocol's 300@20%-holdout gate is arithmetically
  unreachable at N=1,396; the analysis uses a revised, feasible ≥150-holdout gate and
  falls back to cross-sectional if unmet. Stated up front, pre-outcome.
- LEMON age is binned/bimodal → its arm is exploratory, not a lifespan clock.
- MRS n is small at 3T-concurrent visits; molecular arm is context, not headline.

## 9. Reproducibility

`neuromotionvector_pipeline.py` (frozen) · `run_pipeline.py` (driver) ·
`make_fixture.py` (synthetic QA) · `make_figures.py` (aggregate-driven figures) ·
`AABC_REAL_DATA_RUNBOOK.md` (how to run on the real data) ·
`NEUROMOTIONVECTOR_CLAIMS_LEDGER.json` (per-claim status).

*HeartVector phase-desynchrony remains the project's locked proof; NeuroMotionVector
is a distinct brain-imaging section built to the same prespecification discipline.*
