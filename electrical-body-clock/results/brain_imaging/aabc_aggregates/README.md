# AABC NeuroMotionVector aggregate release

This directory contains disclosure-checked, group-level outputs from the
NeuroMotionVector analysis of AABC / HCP-Aging Release 2. The source data are
controlled-access and governed by the AABC data-use agreement.

## What is included

- `NEUROMOTIONVECTOR_PROTOCOL_LOCK.json`: the outcome-blind protocol and
  frozen analysis definitions.
- `GEOMETRY_FROZEN.json`: the frozen four-channel geometry hash and held-out
  channel-clock metrics.
- `aabc_data_inventory.csv`: event-level availability counts.
- `brain_channel_clock_metrics.csv`: aggregate held-out clock metrics.
- `neuromotionvector_primary_result.csv`: longitudinal and cross-sectional
  primary model summaries.
- `neuromotionvector_secondaries.csv`: prespecified secondary model summaries.
- `neuromotionvector_sensitivities.csv`: aggregate sensitivity summaries.
- `run_log_real.json`: disclosure-safe run metadata, cohort counts, metrics,
  and group-level results.
- `AABC_REAL_DATA_RUNBOOK.md` and `NEUROMOTIONVECTOR_REPORT.md`: execution and
  interpretation records.

The corresponding public analysis code is in
`../../../src/brain_imaging/aabc/`.

## What is deliberately excluded

No AABC participant identifier, participant-level row, per-visit score,
participant manifest, MRI-derived feature matrix, gait record, or raw imaging
file is distributed here. In particular,
`aabc_participant_visit_manifest.parquet` and
`neuromotionvector_scores.parquet` remain inside the approved controlled
environment. The protocol may name those private execution artifacts, but they
are not part of this release.

These aggregate files are provided for claim verification and methodological
review. They are not a substitute for obtaining authorized AABC access.
