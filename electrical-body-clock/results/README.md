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

## `act1_ecg/external_validation/` - external cohort transfer (current paper)
| file | contents |
|---|---|
| `chapman_age_transfer.csv` | Chapman-Shaoxing/Ningbo (n = 44,595) clock-transfer metrics: raw and frozen-CODE-15-adapter-applied R2/MAE/calibration per clock, split by sex. Supports the external-validation claim in `clocks_to_coordinates`. |

> These tables report the **A/D (shared-axis / disagreement) framing** of the current
> manuscript. The `act1_ecg/` and `act2_nhanes/` tables above them report the original
> subsystem-clock and organ-gap analyses; both sets are released.

Re-running `src/nhanes/nhanes_organ_clocks.py` regenerates the Act II tables
plus `organ_gaps.parquet`, `surv.parquet`, `clock_stats.json`, and `ladder.json`
(the C-index ladder: 0.813 → 0.817 → 0.830 → 0.845, ΔC = +0.028).
