# MotionVector — structure–function boundary test (NHANES 2005–06)

A prespecified **negative boundary test** for the "biological age is a direction"
thesis, one scale down from the electrical clocks. It asks whether skeletal-structural
aging (whole-body DXA) and 7-day movement (accelerometry) can be compressed into a
single "locomotor reserve" coordinate the way HeartVector compresses phase clocks into
A and D. **They cannot** — and *why* they cannot is the useful result.

## Cohort
NHANES 2005–06, the only cycle with same-person whole-body DXA **and** minute-level
accelerometry. `n = 2,891` (DXA ∩ accelerometry ∩ physical-function), ages 20–69, 378
with any lower-body limitation (13.1%). Keyed by public `SEQN`.

## Headline
- **PRIMARY (prespecified) — NULL.** Reserve contrast → lower-body limitation, beyond
  age+sex+BMI+shared axis: OR 1.10 per contrast-unit (95% CI 0.99–1.23), LRT p = 0.070.
  Fails the frozen criterion (p<0.05 **and** protective direction); the point estimate is
  non-protective.
- **The null is real, not underpower.** In the same n, raw steps/day predicts limitation
  at p ≈ 2×10⁻³³. The signal exists; the *age-clock transform discards and even inverts it*
  (more steps → clock says "older", r = +0.30). Testing the locomotor age-gap residual
  directly is R²-agnostic and even more decisively null (p = 0.96).
- **Interpretation.** Compressing movement into "how old does this look?" destroys the
  capacity/behaviour information raw movement carries. That *rejects* a universal
  "everything is an age clock" reading and motivates a mixed state-space
  (age + structure + movement + stress) — the HeartVector thesis one scale down.

Figure: `paper/figs_full/fig_s4_motionvector.pdf` (Supplementary Fig. S4 of the full
manuscript).

## Files
| file | contents |
|---|---|
| `MOTIONVECTOR_REPORT.md` | Full arm write-up: clock quality, primary/secondary/exploratory results, robustness of the null, honest verdict, protocol-adherence disclosure, caveats. |
| `motionvector_results.json` | Machine-readable result summary (cohort, clock R²/r, reserve definition, primary OR/CI/p, secondary + sanity tests). |
| `motionvector_geometry.json` | Frozen shared structure–function axis + reserve-contrast definition. |
| `MOTIONVECTOR_PROTOCOL_LOCK.json` | Prespecified protocol (frozen before outcome contact; `self_sha256` recorded). |
| `motionvector_repro.csv` | Per-subject (SEQN) age, sex, BMI, structural/locomotor gaps, shared axis, reserve contrast, and PFQ outcomes — reproduces the primary and exploratory logistic models. |
| `motionvector_scored.csv` | Clock scores per subject. |
| `motionvector_dxa_features.csv` | DXA-derived structural features (multiply-imputed, 5 replicates averaged). |
| `motionvector_locomotor_features.csv` | Accelerometry-derived locomotor features (implemented subset — see report's protocol-adherence disclosure). |

Fold assignments: `KFold(5, shuffle=True, random_state=20260711)` inside the cross-fit.

---
*Research result. Outcome is self-reported physical function (soft); accelerometry is the
predictor, not the outcome. DXA excludes ages 70+. Not for clinical use.*
