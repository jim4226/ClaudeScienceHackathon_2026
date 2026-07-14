# CT structural atlas aggregate release

This directory contains aggregate outputs from the volume-only
TotalSegmentator-CT-Lite structural-age analysis. Raw CT images, segmentation
masks, scan identifiers, and scan-level feature rows are not distributed here.

## Files

- `ct_clock_summary.json`: five-fold out-of-fold whole-body and per-system
  clock performance.
- `specificity_matrix_ct.csv` and `.png`: aggregate system-by-pathology effect
  sizes and multiplicity-adjusted results.
- `organ_age_ranking.csv` and `.png`: organ-level age associations,
  permutation importance, and aggregate pathology-separation summaries.
- `ct_methods.md`: data, modeling, validation, scope, and limitations.
- `ct_handoff_summary.json`: aggregate execution handoff and Claude Science
  artifact provenance. UUIDs in this file identify generated artifacts, not
  participants.

The analysis is cross-sectional and volume-only. It does not include CT
density, Hounsfield-unit, or bone-mineral-density features. The pathology
labels are coarse scan-level groups, and the results should be interpreted as
an exploratory structural atlas rather than clinical validation.
