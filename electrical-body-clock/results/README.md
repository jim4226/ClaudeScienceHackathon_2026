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

Re-running `src/nhanes/nhanes_organ_clocks.py` regenerates the Act II tables
plus `organ_gaps.parquet`, `surv.parquet`, `clock_stats.json`, and `ladder.json`
(the C-index ladder: 0.813 → 0.817 → 0.830 → 0.845, ΔC = +0.028).
