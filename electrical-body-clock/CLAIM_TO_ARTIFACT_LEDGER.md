# Claim-to-artifact ledger

Each headline quantity in *From Clocks to Coordinates* mapped to the exact
committed result file it was read from, with the value as it appears in that file.
Paths are relative to `electrical-body-clock/`. Every value below was read back
from the committed table at the time this ledger was written — not transcribed
from the manuscript.

## Evidence hierarchy (read this first)

The claims below are **not** all the same strength. In descending order of
evidential weight:

1. **Locked confirmatory null (strongest).** The composite phase-disagreement
   scalar **D4** adds no mortality information beyond age, sex, the shared axis A,
   and a whole-ECG clock in a single prespecified, hash-locked,
   firewall-protected CODE-15 reveal. The exact confirmatory conclusion is that
   **D4 did not add mortality information under the locked model**. A was not the
   confirmatory endpoint.
2. **Same-cohort held-mechanism support.** The signed IKr perturbation direction
   (dofetilide derivation arm) with quinidine as a within-cohort held-mechanism
   confirmation; the *direction* result is **exploratory** (Holm-adjusted
   p = 0.069).
3. **External, adjustment-dependent support.** The Chapman–Shaoxing/Ningbo
   QT-extension phenotype transport — a positive larger-site estimate that is
   **conditional** (emerges only after covariate adjustment; marginal p = 0.996).
4. **Supporting multiscale atlas (weakest, supporting only).** NHANES organ-system,
   whole-body CT, brain MRI (LEMON), and the in-silico genomic prototype pose the
   *same question* at other scales; none is a confirmatory test of the electrical
   result, and the genomic arm is a prospective prototype (see `../skeletome/`).

## Ledger

| Manuscript claim | Value (as committed) | Source file |
|---|---|---|
| **Confirmatory D4 null** (mortality beyond A) | HR 1.01, 95% CI [0.983, 1.039], Wald p = 0.471, LRT p = 0.478, `success=false` | `results/act1_ecg/reveal/reveal_result.json` |
| Reveal executed once, hash-locked script | RC2.3, sha256 `0e79b621…`, n=74,715, 2,583 deaths | `results/act1_ecg/reveal/CODE_CONFIRMATORY_RESULT.md`, `reveal_final_cox_RC2_3.py` |
| AV / ST-T generated a directional hypothesis in a mixed phase-gap model | z_AV p = 3.7×10⁻²¹, z_STT p = 2.2×10⁻⁷; these are not effects at fixed A or beyond the separately trained whole-ECG clock | `results/act1_ecg/reveal/CODE_CONFIRMATORY_RESULT.md` |
| Shared axis A mortality (CODE development) | HR 1.22 / SD, p = 1.4×10⁻²⁰ | `results/act1_ecg/reveal/CODE_CONFIRMATORY_RESULT.md` |
| Signed IKr direction (exploratory) | Holm-adjusted p = 0.069; quinidine held-mechanism mean S = 0.835 | `results/act1_ecg/perturbation/PERTURBATION_TRANSPORT_LOCK.json` |
| IKr scorer + deterministic fixture + verifier | S_IKr = wᵀq identity; verifier asserts exact match | `results/act1_ecg/perturbation/s_ikr_scorer.py`, `scorer_fixture.json`, `perturbation_direction_verifier.py` |
| Chapman QT-extension primary (full adjustment) | OR 1.225 / SD, 95% CI [1.10, 1.364], LRT p = 1.92×10⁻⁴, N = 44,550, 386 cases | `results/act1_ecg/external_validation/chapman_phenotype_test.csv` |
| Chapman marginal (unadjusted) | OR 1.00, p = 0.996 | `results/act1_ecg/external_validation/chapman_phenotype_test.csv` |
| Chapman rhythm-exclusion (both) | OR 0.931, p = 0.481, 86 cases (post-hoc) | `results/act1_ecg/external_validation/chapman_phenotype_test.csv` |
| Ningbo site (part of pooled primary) | OR 1.198, p = 1.88×10⁻³, 329 cases | `results/act1_ecg/external_validation/chapman_phenotype_test.csv` |
| NHANES shared body axis A_body | HR 1.206 / SD, 95% CI [1.130, 1.287] | `results/act2_nhanes/` (canonical svycoxph table) |
| NHANES body disagreement D_body | HR 1.213 / SD, 95% CI [1.108, 1.328], p = 3.1×10⁻⁵ | `results/act2_nhanes/` (canonical svycoxph table) |
| NHANES C-index ladder (age+sex → +A → +D) | 0.8127 → 0.8262 → 0.8304 (ΔC = +0.0042) | `results/act2_nhanes/robustness/nhanes_cv_cindex_ladder.csv` |
| LEMON brain disagreement (older > young) | D_young 0.340, D_older 0.517, diff +0.177 (95% CI [0.112, 0.242]), MW p = 4.3×10⁻⁸, Cohen's d = 0.844, n = 220 | `results/brain_imaging/lemon_disagreement_result.json` |
| LEMON balanced-group sensitivity | 5,000 balanced 69-vs-69 draws, median d = 0.602, 95% interval [0.444, 0.784], all draws positive; within-group scaling reverses the contrast | `results/brain_imaging/lemon_balanced_sensitivity.json` |
| AABC four channel clocks | Held-out r = 0.587 structure, 0.505 myelin, 0.514 perfusion, 0.497 function | `results/brain_imaging/aabc_aggregates/brain_channel_clock_metrics.csv` |
| AABC longitudinal gait test | beta = -0.0208, 95% CI [-0.0507, 0.00918], p = 0.166, n = 295 (null) | `results/brain_imaging/aabc_aggregates/neuromotionvector_primary_result.csv` |
| CT whole-body volume clock | Five-fold OOF MAE = 8.56 years, R2 = 0.432, n = 1,227 | `results/ct_atlas/ct_clock_summary.json` |
| CT system ranking | Cardiovascular R2 = 0.288; skeletal R2 = 0.111; all other system R2 values at or below 0.107 | `results/ct_atlas/ct_clock_summary.json` |
| MotionVector prespecified negative | reserve→limitation OR 1.10 (95% CI 0.99–1.23), LRT p = 0.070 (NULL); raw steps p ≈ 2×10⁻³³ | `results/motionvector/motionvector_results.json`, `MOTIONVECTOR_PROTOCOL_LOCK.json` |
| Skeletome (prospective prototype) | 312 HARs, 1,955 substitutions; GWAS-proximal enrichment null (permutation p = 0.24); blind GDF5 filter control | `../skeletome/` result tables; `../skeletome/README.md` |

## Note on the D_body confidence interval

The D_body interval **[1.108, 1.328]** is the **design-based survey Cox** value
(`svycoxph`, `WTMEC2YR/3` weights over 3 cycles, robust SE, design df = 47) — the
canonical model for NHANES with the Linked Mortality File. This is the interval
reported in the manuscript and it matches the committed canonical Cox table
exactly. A narrower interval computed under a naïve (non-survey) Cox model is not
canonical here and is not reported.
