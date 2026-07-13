# MotionVector — Structure–Function Discordance (NHANES 2005-06)
*Prespecified per MOTIONVECTOR_PROTOCOL_LOCK.json (self_sha256 91b80634…), frozen before outcome contact. Result: **PRIMARY NULL** — a prespecified negative boundary test, reported in full.*

## What this is
A **boundary test**, not a headline: can skeletal-structural aging and 7-day movement be compressed into a
single "locomotor reserve" coordinate the way HeartVector compresses phase clocks into A/D? Two outcome-blind
cross-fitted age clocks in the same NHANES 2005-06 adults (the only cycle with both whole-body DXA and
minute-level accelerometry), plus a reserve contrast. n=2,891 same-person (DXA ∩ accelerometry ∩
physical-function), ages 20–69, 378 with any lower-body limitation (13.1%).

**Reserve definition (design change from the proposed plan, stated):** the plan defined reserve as a *ratio*
(structural gap ÷ locomotor gap), which is unstable near a zero denominator. I froze it instead as a
**calibration-orthogonal contrast** — the locomotor age-gap component orthogonal to the shared
structure-function axis estimated on the healthy calibration set. (Note: because the axis is fixed on the
calibration set, the contrast is orthogonal *there*, not globally — it correlates r≈−0.15 with the shared axis
on the full sample. It is a contrast, not a globally-orthogonal residual.)

## Clock quality (the crux)
| Clock | Out-of-fold R² | r(pred, age) | Interpretation |
|---|---|---|---|
| Structural (DXA) | **0.46** | 0.68 | reasonable age predictor |
| Locomotor (accelerometry) | **0.17** | 0.41 | **weak; counterintuitive** — in ages 20–69, steps barely track age (r=0.04), and the clock maps *more* steps → *older* |

The two age-**gaps** are **weakly correlated (r=0.07)** — structural and locomotor gap estimates carry largely
separate variation. (Stated as weak gap correlation, not "bone and movement age independently.")

## Results
- **PRIMARY (prespecified) — reserve → lower-body limitation, beyond age+sex+BMI+shared axis: NULL.**
  OR = **1.10 per +1 unit** of the reserve contrast (95% CI 0.99–1.23), LRT p = **0.070**. The contrast's
  sample SD is 1.13 (per-SD OR 1.12); the OR is reported per contrast-unit, **not** per SD. Fails the frozen
  criterion (p<0.05 AND protective direction) — and the point estimate is non-protective.
- **SECONDARY (prespecified) — load-bearing contrast:** load-bearing region BMD age-gap (legs/pelvis/lumbar
  spine/trunk) tracks objective locomotion slightly more than control regions (arms/ribs): r=−0.067 vs −0.010.
  Directionally as hypothesized, both weak.
- **SECONDARY (prespecified) — reserve → mortality:** NOT run (young DXA cohort ≤69 → few deaths; not worth
  the firewall exposure for an underpowered test under deadline).

### Exploratory / supporting (post-hoc — NOT prespecified)
- **Structural gap → limitation:** OR 1.14 per SD, p=0.019.
- **Raw steps/day → limitation:** OR 0.81 per 1,000 steps, p≈2×10⁻³³.
These were computed *after* the primary and are labeled exploratory. They show the underlying measurements
carry strong functional information even though the reserve contrast does not.

## Robustness of the null (R²-agnostic — the verdict does NOT rest on R²)
The verdict is the **prespecified outcome test** (logistic LRT), not a fit statistic. R² was diagnostic
context only. Three checks confirm the null is real and not an artifact of the weak clock's low R²:
- **The age-gap residual itself carries no function signal.** Testing `loco_gap` directly (beyond
  age+sex+BMI): OR 1.00, LRT **p=0.96** — a cleaner, even more decisive null than the reserve contrast
  (p=0.070). Testing the residual directly is R²-agnostic; it is null regardless of how well the clock fits age.
- **It is a TRUE null, not underpower.** In the *same* n=2,891, raw steps/day predicts limitation at
  **p=2×10⁻³³** — enormous power is present. The signal exists; the age-clock transform discards it.
- **The transform inverts the sign.** More steps correlates *positively* with locomotor age-gap (r=+0.30:
  more activity → clock says "older"), while more steps is strongly *protective* for function. So compressing
  movement into "how old does it look" doesn't just weaken the signal — it flips it. That is the mechanism
  behind the boundary finding.

## Honest verdict
The **prespecified reserve hypothesis failed** (OR 1.10, p=0.070). But structure and raw movement each carried
functional information (exploratory) — so the failure is specific: **compressing movement into a
chronological-age residual destroyed the information that raw movement carried.** This is the scientifically
useful boundary. It argues that biological state is *not* always best written as "how old does this modality
look?" — some systems carry age-like information; others carry capacity/state/behavior that an age clock throws
away. That result *rejects* a universal "everything is an age clock" reading and motivates a mixed state-space
(age + structure + movement + stress coordinates) — which is exactly the HeartVector thesis one scale down.

MotionVector does **not** change the HeartVector A-vs-D headline and does **not** touch the held CODE
confirmatory reveal. It is retained as a prespecified negative (audit evidence), one line in the master ledger,
full detail in this appendix.

## Protocol-adherence disclosure (deviation)
The locked protocol listed the locomotor clock's intended predictors as including **cadence distribution,
sustained walking-bout count/duration, transition-probability fragmentation, and cosinor circadian amplitude.**
The **implemented** locomotor feature set was a subset: mean daily steps, MVPA minutes, light minutes,
sedentary minutes, mean intensity, peak-1-minute intensity, day-to-day CV of steps and MVPA, sedentary
fraction, and active fraction. **Cadence distributions, walking bouts, transition-probability fragmentation,
and cosinor amplitude were NOT computed** — do not read the result as covering them. Because the primary
outcome is now unblinded, these features are deliberately **not** added post-hoc (that would be
outcome-informed feature selection); honoring the full feature list would require a fresh outcome-blind lock
and is out of scope. The null above rests on the implemented subset.

## Caveats
- Primary outcome is **self-reported** physical function (soft); accelerometry is the predictor, not the outcome.
- Ages 20–69 only (DXA excludes 70+) — the weak age–activity gradient is partly a range effect.
- n=2,891; DXA multiply-imputed (5 replicates averaged, per lock).
- The reserve is a calibration-orthogonal **contrast**, not a globally-orthogonal residual and not a per-SD unit.
- DXA and any CT observations are independent modalities/cohorts — phrase convergence as cross-modal, never causal.

## Reproducibility
`motionvector_repro.csv` adds the PFQ outcome (lb_limitation, any_lb_limit) and the scored covariates so the
primary and exploratory logistic models are reproducible; `motionvector_scored.csv` holds the clock scores;
feature tables are `motionvector_dxa_features.csv` / `motionvector_locomotor_features.csv`. Fold assignments
used KFold(5, shuffle=True, random_state=20260711) inside the cross-fit.
