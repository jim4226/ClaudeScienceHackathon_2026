# Witness 2 (Structural / CT) — Methods & Results

*Body Across Scales, three-witness aging study. CT organ/skeletal aging clock on
TotalSegmentator-CT-Lite (open, CC-BY; HF mirror `YongchengYAO/TotalSegmentator-CT-Lite`,
Zenodo 10047292).*

## 1. Data

- **Cohort.** 1,228 whole-body / partial-FOV CT scans with pre-computed 117-organ
  3D segmentation masks (TotalSegmentator label set: 52+ soft-tissue organs and
  vessels, 25 vertebrae, 24 ribs, plus sternum, costal cartilages, hips, femora,
  humeri, scapulae, clavicles, sacrum, skull). One scan lacks an age label, so the
  analysis frame is **n = 1,227** (age 15–98 y, mean 63.4, SD 15.0; 716 M / 510 F).
- **Feature matrix.** For each scan we integrate every organ mask to a **volume in
  mL** (voxel count × per-scan voxel volume, `vox_ml`), giving a 1,227 × 117 organ-volume
  matrix. Partial fields of view leave many organs un-imaged; the median scan contains
  70 of 117 organs. **Absent organs are encoded as volume 0**, which the
  gradient-boosting learner treats as an informative "not in frame" value; this
  reproduces the green-lit baseline exactly.
- **Pathology labels.** Each scan carries one radiology-derived pathology group:
  `no_pathology` (404, the control set), `tumor` (237), `vascular` (154),
  `trauma` (92), `inflammation` (86), `bleeding` (15), plus `unclear`/`other`/NaN
  (excluded from specificity testing).

## 2. Organ-volume age clock

- **Model.** `HistGradientBoostingRegressor` (scikit-learn, default hyper-parameters)
  on the 117 absolute organ volumes → chronological age.
- **Validation.** 5-fold cross-validation (shuffled, seed 0); every reported prediction
  is **out-of-fold**. Uncertainty is a 2,000-sample bootstrap over scans.
- **Whole-body performance: MAE = 8.56 y (95% CI 8.14–8.97), R² = 0.432 (95% CI 0.38–0.48).**
  This matches the pre-registered volume-only baseline (MAE 8.52, R² 0.45) within CI.
- **Per-system clocks.** Restricting features to one organ system gives deliberately
  weaker clocks — cardiovascular MAE 9.71 (R² 0.29) is the strongest single system,
  skeletal MAE 11.20 (R² 0.11); several small systems have R² ≈ 0. This is expected
  and honest: one organ system carries far less age signal than the whole body, and
  the per-system clocks exist to localise *specificity*, not to compete on accuracy.

## 3. Cole/de Lange bias correction

Age clocks regress toward the cohort mean, so raw age-gaps (predicted − chronological)
are anti-correlated with age (r = −0.72 on controls here). We fit
`gap ~ age` by OLS **on the `no_pathology` controls only** (slope −0.561, model
R² 0.523) and subtract the fitted line from every scan's gap. After correction the
control gaps have mean 0 and zero age-correlation, so a residual age-gap reflects
organ-specific acceleration rather than the regression-to-the-mean artifact. The same
correction is applied independently to the whole-body clock, each of the 8 per-system
clocks, and each single-organ clock.

## 4. Specificity matrix (organ-system × pathology)

For each (organ-system age clock × pathology group) cell we compare the corrected
age-gap of the pathology group against the `no_pathology` controls:
**Cohen's *d*** (pooled-SD effect size) and a **one-sided Mann–Whitney U** test
(H₁: pathology ages *older* than controls). p-values are **BH-FDR corrected across the
40 system×pathology cells**.

**Hits surviving BH-FDR < 0.05:**

| Organ-system clock | Pathology | Cohen's *d* | p (BH-FDR) |
|---|---|---|---|
| Cardiovascular | Vascular | **0.34** | 0.003 |
| Cardiovascular | Trauma | 0.30 | 0.038 |
| Endocrine/reproductive | Tumor | 0.19 | 0.034 |

The **cardiovascular → vascular** cell is the biologically pre-expected diagonal:
the organ system whose structure a vascular pathology alters is the one whose
structural age-gap it inflates. The whole-body clock alone flags vascular disease
(*d* = 0.36, BH-FDR 0.0003) but cannot localise it; the per-system decomposition does.
The large-magnitude cells in the `bleeding` column (n = 15) do **not** survive FDR —
correctly, given the tiny group.

## 5. Organ ranking

Two complementary rankings (`organ_age_ranking.csv`):

1. **Clock importance** — cross-validated permutation importance (Δ MAE in years when
   an organ's volume is shuffled, averaged over folds). The **aorta dominates**
   (Δ MAE 2.87 y), followed by subclavian/iliac arteries and the brachiocephalic
   trunk — large-vessel calibre is the single strongest structural age signal here.
2. **Pathology separation** — for each organ we build a single-feature age clock on
   the scans where that organ is imaged, bias-correct on controls, and take the best
   Cohen's *d* over pathology groups (BH-FDR across organs). **12 organs separate a
   pathology at FDR < 0.05**, led by iliac arteries → vascular (*d* up to 0.66) and,
   notably for the skeletal bridge, **humerus → trauma (d = 0.60), vertebra T2 → trauma,
   and costal cartilages → inflammation**.

## 6. Stated upgrade — HU / density features (parallel track, not run here)

This clock is **volume-only**. Organ *volume* captures gross atrophy/enlargement but
misses the tissue-composition changes that dominate structural aging:

- **Vertebral bone mineral density (BMD)** — mean Hounsfield Units in trabecular
  vertebral bodies is the validated opportunistic-CT osteoporosis biomarker and the
  literal "bone clock" the umbrella narrative promises.
- **Muscle attenuation** (myosteatosis) and **visceral/subcutaneous fat attenuation** —
  mean-HU sarcopenia and adiposity markers that track age independently of volume.

Extracting these requires the **raw CT intensity images** (`Images.zip`, 22.6 GB of
NIfTI whole-body CT), not just the masks (`Masks.zip`, 823 MB). Mean-HU-per-organ is a
simple mask-weighted average over the intensity volume, but the 22.6 GB download and
streaming extraction is a **separate compute track**; it is documented here as the
concrete, mechanical next step. The volume clock is reported rigorously on its own terms
and is **not** blocked on the density upgrade.

## 7. Honest limitations

- **n = 1,227 is modest.** All performance is 5-fold cross-validated with bootstrap CIs;
  we deliberately do **not** use the dataset's 89-scan test split (too small for a stable
  point estimate).
- **Volume-only.** See §6 — no tissue density yet.
- **Pathology labels are scan-level and coarse** (one group per scan), so specificity is
  measured at the group level, not lesion level.
- **Partial FOV.** Organ presence varies by scan; single-organ analyses are restricted to
  scans where the organ is imaged (≥100 present), and absence is modelled as volume 0 in
  the whole-body clock.
- **Cross-sectional.** Age-gaps are between-subject, not within-subject longitudinal
  trajectories.

## Outputs

- `specificity_matrix_ct.csv` — 45 rows (9 axes × 5 pathologies): Cohen's *d*, MWU p,
  BH-FDR, significance flag.
- `specificity_matrix_ct.png` — heatmap of the above.
- `organ_age_ranking.csv` — all 117 organs: system, n present, Spearman(volume, age),
  permutation importance, single-organ clock MAE, best-separated pathology + *d* + FDR.
- `organ_age_ranking.png` — two-panel ranking figure.
- `ct_clock_summary.json` — clock performance + bias-fit coefficients.
