# Results

Released prediction tables and analysis outputs. Every figure and table in the
paper regenerates from these files, so the headline numbers can be checked
without re-training.

## `act1_ecg/` — the electrical body clock (PTB-XL)
| file | contents |
|---|---|
| `ladder_full.csv` | Added-value ladder (full-strip pipeline): chrono-null / interval-biomarker / deep-global MAE & R², and per-subsystem R². Drives Table 1 and Fig 1. |
| `clock_performance.csv` | Median-beat reproducibility pipeline: whole-beat + subsystem MAE/R² (robustness check). |
| `ladder_baselines.csv` | Chronological-null and handcrafted interval-biomarker baselines. |
| `specificity_matrix_bootstrap.parquet` | Double-centered disease × subsystem interaction + within-patient contrast, with 1000-resample patient-cluster bootstrap CIs. Drives Fig 2b, Fig 3. |
| `substrate_matrix_d.csv` | Raw (pre-correction) disease × subsystem age-gap matrix (Cohen's d). Fig 2a. |
| `specificity_test.csv` | Raw argmax "which subsystem is oldest" readout (2/6 clean) — the pre-correction view. |
| `substrate_pure_summary.csv` | Substrate-pure sensitivity: interaction on patients carrying exactly one disease label. Fig 4. |

## `act2_nhanes/` — whole-body organ clocks (NHANES)
| file | contents |
|---|---|
| `nhanes_cox_results.csv` | Per-organ Cox HRs (age/sex-adjusted) + mutually-adjusted joint model, per +1 SD organ-age gap. Table 2, Fig 6a. |
| `nhanes_smoking_attribution.csv` | Organ-age gap by smoking status (never/former/current) with effect sizes. Fig 7. |

### `act2_nhanes/robustness/` — mortality-model robustness (current paper)
| file | contents |
|---|---|
| `nhanes_cv_cindex_ladder.csv` | 10-fold cross-validated C-index ladder (B0 age/sex 0.813 -> B1 +A 0.826 -> B2 +D 0.830), the CV counterpart to the in-sample ladder. |
| `nhanes_cv_cindex_folds.csv` | Per-fold C-index for each ladder rung (the 10 folds behind the means above). |
| `nhanes_leave_one_system_out.csv` | Leave-one-organ-system-out hazard ratios for the disagreement score D - the D->mortality signal survives dropping any single organ clock (max design-t p = 0.0032, dropping Cardiovascular). |
| `nhanes_robustness_addons.json` | Machine-readable summary of the leave-one-out analysis with the correct design-df p-values and interpretation. |

## `act1_ecg/perturbation/` — controlled-perturbation signed direction (current paper)
| file | contents |
|---|---|
| `PERTURBATION_TRANSPORT_LOCK.json` | Frozen protocol lock for the signed IKr direction: the covariance-scaled `w_IKr` vector, the stability gate (bootstrap median cos_Σ, sign-stability, multiplicity-corrected permutation p), and the outcome-blind derivation provenance. Drives the compass figure. |
| `perturbation_direction_gate.csv` | Per-direction gate results (IKr passes as a stable exploratory direction; acute ischemia is diffuse and fails the gate). |
| `shuffled_control_comparison.csv` | Sign-flipped / random-direction negative controls (diagnostic only; cannot redefine the direction or gate the conclusion). |
| `perturbation_direction_verifier.py` | Standalone verifier that re-checks the frozen direction against the gate constants. |
| `perturbation_transport_methods_results.md` | Methods + results narrative for the perturbation-transport arm. |
| `beyond_the_clock_results.md` | Summary of the full "beyond the clock" evidence chain (derivation → quinidine confirmation → external QT-extension transport). |

## `act1_ecg/external_validation/` - external cohort transfer (current paper)
| file | contents |
|---|---|
| `chapman_age_transfer.csv` | Chapman-Shaoxing/Ningbo (n = 44,595) clock-transfer metrics: raw and frozen-CODE-15-adapter-applied R2/MAE/calibration per clock, split by sex. Supports the external-validation claim in `clocks_to_coordinates`. |
| `chapman_phenotype_test.{json,csv}` | Chapman-Shaoxing/Ningbo QT-interval-extension phenotype test (SNOMED 111975006; n = 44,550, 386 cases). The frozen signed IKr direction added conditional information beyond age/sex, conventional intervals, A and D: adjustment ladder from marginal null (OR 1.00) to fully adjusted OR 1.23 (p = 1.9e-4); per-site replication (Ningbo confirms, Chapman-Shaoxing underpowered); and the rhythm-context sensitivity (null when excluding both atrial flutter/fibrillation and sinus bradycardia, 86 cases) reported as a limitation. Drives the Chapman transport figure. |

## `brain_imaging/` — image-derived disagreement (LEMON, supporting multiscale atlas)
| file | contents |
|---|---|
| `lemon_imaging_feature_table.csv` | 220 real LEMON T1 (MP2RAGE) volumes processed end-to-end via ANTsPyNet into four structural-aging views, per-view cohort z-scores, and `D_std`. Derived features are keyed by public BIDS ID; the GWDG BIDS metadata declares CC0 and the official INDI distribution lists PDDL. |
| `lemon_disagreement_result.json` | Primary result + controls: older > young image-derived disagreement (D 0.34 → 0.52, Cohen's d = 0.84, Mann–Whitney p = 4.3e-8), surviving permutation, leave-one-view-out, extremity-adjusted OLS, and a within-older step (not gradient). Backs the brain-MRI panel of the multiscale atlas. |
| `lemon_balanced_sensitivity.json` | Equal-weight, balanced-subsample, young-reference, linear-residual, and within-group-scaling diagnostics. The between-group contrast persists but attenuates under balanced sampling; within-group scaling does not support universal excess dysregulation. |

### `brain_imaging/aabc_aggregates/` - controlled-access AABC, aggregate release only

| file | contents |
|---|---|
| `brain_channel_clock_metrics.csv` | Held-out chronological-age performance for the structural, myelin, perfusion, and functional MRI-derived channels. |
| `neuromotionvector_primary_result.csv` | Prespecified longitudinal and cross-sectional gait models. The longitudinal primary result is null and is reported with its confidence interval. |
| `neuromotionvector_{secondaries,sensitivities}.csv` | Disclosure-checked secondary and sensitivity estimates. |
| `GEOMETRY_FROZEN.json` | Frozen AABC shared/disagreement geometry and content hash. |
| `NEUROMOTIONVECTOR_PROTOCOL_LOCK.json`, `run_log_real.json` | Outcome-independent protocol and aggregate execution receipt. |

No AABC participant IDs, per-visit scores, source spreadsheets, or images are
included. Reproducible source code is in `src/brain_imaging/aabc/`.

## `ct_atlas/` - TotalSegmentator structural atlas, aggregate release

| file | contents |
|---|---|
| `ct_clock_summary.json` | Five-fold out-of-fold whole-body and per-system volume-clock performance for n = 1,227 examinations. |
| `specificity_matrix_ct.{csv,png}` | Aggregate system-by-pathology effect sizes and multiplicity-adjusted results. |
| `organ_age_ranking.{csv,png}` | Organ-level age associations, importance, and aggregate pathology-separation summaries. |
| `ct_methods.md`, `ct_handoff_summary.json` | Methods, limitations, and Claude Science artifact provenance. |

Raw CT images, masks, scan identifiers, and scan-level feature rows are not
distributed. This is a cross-sectional, volume-only exploratory atlas.

> These tables report the **A/D (shared-axis / disagreement) framing** of the current
> manuscript. The `act1_ecg/` and `act2_nhanes/` tables above them report the original
> subsystem-clock and organ-gap analyses; both sets are released. The `perturbation/`,
> `external_validation/chapman_phenotype_test.*`, and `brain_imaging/` tables back the
> controlled-perturbation result and the supporting multiscale atlas in
> `from_clocks_to_coordinates_full` and `clocks_to_coordinates`.

Re-running `src/nhanes/nhanes_organ_clocks.py` regenerates the original Act II
tables. The current manuscript's prediction ladder is the cross-validated
`robustness/nhanes_cv_cindex_ladder.csv`; the older in-sample exploratory ladder
is not used as headline evidence.
