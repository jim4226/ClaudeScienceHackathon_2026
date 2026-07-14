# CODE-15 Confirmatory Reveal — Result

**Single locked, prespecified confirmatory analysis. Executed once on 2026-07-12. The released primary estimand, model, and success criterion were not changed after the reveal.**

This file is the machine-result summary for the CODE analysis. Interpretive
claims are governed by the current paper and `CLAIM_TO_ARTIFACT_LEDGER.md`.

---

## 1. The prespecified question

> Does the **phase-disagreement score D** — the spread among the four electrical-phase age estimates (P, AV, QRS, ST-T) — add mortality information **beyond** age, sex, the shared electrical-aging axis A, and a whole-ECG neural age (nn_predicted_age)?

**Primary estimand (frozen before any outcome contact):** hazard ratio per +1 SD of **D4** in model M2; likelihood-ratio test M2 vs M1 (1 df); α = 0.05 two-sided; **success ≡ p < 0.05 AND HR > 1**. D4 was the *sole* confirmatory result — sensitivities and the out-of-sample robustness arm were reported but never allowed to gate the verdict.

## 2. The result — **NULL**

| Quantity | Value |
|---|---|
| **D4 hazard ratio** (per +1 SD) | **1.0103** |
| **95% CI** | **[0.9826, 1.0387]** |
| **LRT** (M2 vs M1, 1 df) | χ² = 0.503, **p = 0.478** |
| **Complete-case N** | **74,715** |
| **Events (deaths)** | **2,583** |
| Median follow-up | 3.42 y |
| Success criterion (p<0.05 AND HR>1) | **NOT met** |

The reveal ran on the immutable, **network-blocked** image with the outcome vault mounted read-only; the score↔outcome join matched exactly 74,715 records (`validate="one_to_one"`), `_SUCCESS` was written, and all seven output-file hashes verified against the manifest.

## 3. What the confidence interval excludes (not post-hoc power)

The 95% CI for the per-SD mortality hazard ratio is **[0.9826, 1.0387]**. Therefore the study **excludes**, at 95% confidence:

- any per-SD hazard increase **greater than ~3.9%** (HR > 1.0387), and
- any per-SD hazard *decrease* greater than ~1.7% (HR < 0.9826).

Critically, the **development point estimate — HR 1.0495 (+4.9%/SD) — lies above the confirmatory CI ceiling (1.0387).** The final split therefore does not merely fail to reach significance; it **rules out an effect as large as the one development suggested.** This is a genuine, informative null, not an inconclusive one.

## 4. Sensitivities and decomposition (reported, non-gating)

| Analysis | HR (per SD) | 95% CI | p | Read |
|---|---|---|---|---|
| **D4 (primary)** | 1.0103 | [0.9826, 1.0387] | **0.478** | null |
| D3 (drop-P) | 1.0178 | [0.9915, 1.0447] | 0.202 | null |
| D3 (no-AV) | 0.9994 | [0.9699, 1.0298] | 0.969 | null |
| M3 (D4 + diagnosis-adjusted) | 1.0086 | [0.9813, 1.0366] | 0.540 | null |
| M5 non-linearity LRT | — | — | 0.089 | linear D adequate |

**Phase-level decomposition (M4 — D replaced by the four individual z-gaps):**

| Phase z-gap | HR | 95% CI | p |
|---|---|---|---|
| z_AV | **1.2409** | [1.1923, 1.2914] | **3.1×10⁻²⁶** |
| z_STT | **1.1268** | [1.0838, 1.1715] | **1.8×10⁻⁹** |
| z_P | 1.0154 | [0.9711, 1.0617] | 0.503 |
| z_QRS | 1.0053 | [0.9688, 1.0432] | 0.779 |

The AV and ST-T coefficients were also large in the OOS arm (z_AV
p=3.7×10⁻²¹, z_STT p=2.2×10⁻⁷), but this mixed phase-gap
parameterization does not estimate phase effects at fixed A and does not include
the separately trained whole-ECG age as a covariate. These coefficients therefore
generated a directional hypothesis; they do not establish that mortality risk
is independently carried by AV or ST-T. The identifiable external SaMi-Trop
signed-contrast test did not support that hypothesis.

**Prediction (development-frozen coefficients, applied without refit — anti-optimism):** C-index M1 → M2 = 0.8071 → 0.8072, ΔC = **+0.00016** (negligible); 5-yr Brier 0.0887. Adding D to the model does not improve discrimination.

**Proportional hazards:** D_std Schoenfeld p = 0.29 (PH holds). Subgroups were exploratory and non-gating; sex-stratified fits did not converge numerically and are reported as such.

## 5. What this means for the project thesis

The exact confirmatory conclusion is narrow and useful: **D4 did not add
mortality information under the locked model**. The confidence interval excludes
the development-sized effect, and the frozen prediction model gained essentially
no discrimination. A showed consistent associations in development and
supporting analyses, but it was not the confirmatory endpoint. The later
controlled-perturbation work asks whether the unsigned radius failed because it
discarded physiological direction; that directional analysis is exploratory and
is reported separately.

## 6. Governance trail

- Executed exactly as frozen (RC2.3, script sha `0e79b621…`), D4 sole confirmatory, no cohort/definition/α change, no calibration pooling, no subgroup selection, no one-sided test.
- Fresh-context internal attestation APPROVE_RC2_3 (12/12 checks) before dispatch; dispatch receipt pinned the vault checksum (`488ffc60…`); custodian built the outcome vault in isolation and emitted **no outcome values**.
- The join-integrity pre-check (`scores_pairs_missing_from_vault = 0`) pre-empted the INTEGRITY_INCIDENT_001 crash mode **before** the mount.
- Ledgers populated once: `CLAIMS_LEDGER_populated.json`, `REVEAL_LOG_populated.json`. `_SUCCESS` + SHA256SUMS verified.
