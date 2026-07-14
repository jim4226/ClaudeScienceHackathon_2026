# NeuroMotionVector — AABC Real-Data Runbook

**Purpose:** run the frozen, fixture-validated pipeline on the real AABC Release 2
data in your approved environment. The code is identical to what was validated on
the synthetic fixture — only the input paths change.

**Governance (READ FIRST).** AABC is controlled-access under the HCP-Lifespan DUT.
Per the DUA ruling recorded for this project:
- Participant-level AABC data (IDP CSVs, Toolbox scores) runs ONLY in your approved
  environment (Modal under your UM login). It is NOT pulled into the Claude Science
  sandbox and NOT staged to the hackathon Drive.
- Only AGGREGATE outputs (clock metrics, A/D scores summaries, primary/secondary
  result tables, figures driven by aggregates) leave that environment.
- A UM *login link* on Modal is not the same as UM data-governance *approval* of
  that project for controlled human-subjects data. You own that call as data owner;
  confirm your IBC/data-steward is comfortable before the first real run.
- No participant IDs in any public output; no re-identification; no rendering of
  identifiable AABC scans (figure exemplars are synthetic/LEMON per protocol §8).

---

## 0. The one missing input

Four predictor channels + outcomes are already in hand. The pipeline additionally
needs **chronological age + covariates**, which are NOT in any imaging or Toolbox
file. Download from the BALSA AABC Release 2 **Files** tab:

    AABC_Release2_Non-imaging_Data-XL.csv   (or the non-imaging dictionary export)

It must provide, keyed by `id_event`:

| column | role |
|---|---|
| `age_open` | **clock target** (required) |
| `sex`, `site`, `education`, `height_inches`, `bmi` | primary-model covariates |
| `days_from_V1` | longitudinal Δt |

Rename its key column to `id_event` and its columns to the names above if they differ
(a small adapter cell is included in §3).

---

## 1. Environment

```bash
pip install numpy pandas scipy scikit-learn pyarrow    # versions validated:
#   numpy 2.4.x, pandas 2.3.x, scipy 1.17.x, scikit-learn 1.9.x
```

The pipeline is pinned to scikit-learn 1.9 API (ElasticNetCV `alphas=` int,
group-CV via pre-split iterators). If you use an older sklearn, `n_alphas=` and a
`groups=` fit kwarg are the equivalents.

## 2. Files to stage in the run folder

Unzip the four predictor archives so the folder contains (real Release-2 names):

    Cortical_Areal_Thicknesses.csv   Cortical_Areal_Volumes.csv   asegstats.csv
    Cortical_Areal_Myelin.csv
    PVEc_ASL_CBF.csv   PVEc_ASL_ATT.csv
    rfMRI_REST_FullAmplitudes.csv
    <demographics from the non-imaging file, saved as>  demographics.csv
    AABC_Release2_NIH-Toolbox-Scores.csv   # SEALED — passed separately, opened last

All key on `x___` (== `id_event`). The loader renames `x___`→`id_event` automatically.

## 3. Build demographics.csv from the non-imaging file

```python
import pandas as pd
nid = pd.read_csv("AABC_Release2_Non-imaging_Data-XL.csv")
# adapt these names to the actual columns if they differ:
demo = nid.rename(columns={"<key>":"id_event","<age>":"age_open","<sex>":"sex",
    "<site>":"site","<educ>":"education","<height>":"height_inches","<bmi>":"bmi",
    "<days>":"days_from_V1"})
demo["id"]    = demo["id_event"].str.replace(r"_(V\d+)$","",regex=True)
demo["event"] = demo["id_event"].str.extract(r"_(V\d+)$")[0].fillna("V1")
demo = demo[["id_event","id","event","age_open","sex","site","scanner" if "scanner" in demo else "site",
             "education","height_inches","bmi","days_from_V1"]]
demo.to_csv("demographics.csv", index=False)
```

## 4. Run — Phase A (outcome-blind) then Phase B (sealed)

```bash
python run_pipeline.py \
    --data      /path/to/run_folder \
    --out       /path/to/outputs \
    --sealed-outcome /path/to/run_folder/AABC_Release2_NIH-Toolbox-Scores.csv
```

**Do NOT pass `--fast` for the real run** — that flag is a coarse grid for fixture
QA only. The default full grid (50 alphas × 3 l1_ratios × 5 grouped folds) is the
frozen specification.

**What happens, in order:**
1. Loads the 4 channels, builds the participant-visit manifest + `aabc_data_inventory.csv`.
2. Hash-splits participants 60/20/20 (dev/calibration/final-test), all visits together.
3. Trains the 4 age clocks on **development only**; measures held-out r on calibration.
4. **Stop-rule #3/#10 gate:** needs ≥3/4 clocks with r ≥ 0.20. If <3 pass, the run
   writes `GEOMETRY_FROZEN.json` with the failure and Phase B REFUSES — report a
   technical-failure result, do not fish for a positive.
5. Fits bias correction + Ledoit-Wolf covariance + A/D standardization on calibration.
6. Freezes geometry and writes its SHA-256 hash.
7. **Only then** opens the Toolbox outcomes and runs the primary + secondaries +
   sensitivities. If the geometry hash does not verify, Phase B raises and stops.

## 5. Expected runtime

- Full grid: ≈ **1 minute per channel** on ~1,100 development visits × 733 features
  (measured on the fixture at this scale). Four channels ≈ 4–6 min + geometry + tests.
- Memory: < 4 GB. No GPU needed. A single Modal CPU container is ample.

## 6. Outputs to bring back (aggregate-only)

    aabc_data_inventory.csv
    aabc_participant_visit_manifest.parquet     # aggregate; check no ID leaves scope
    brain_channel_clock_metrics.csv
    neuromotionvector_scores.parquet            # A/D/z per visit (de-identified if shared)
    GEOMETRY_FROZEN.json                        # the frozen hash — record it
    neuromotionvector_primary_result.csv
    neuromotionvector_secondaries.csv
    neuromotionvector_sensitivities.csv
    run_log.json

The figures (`make_figures.py`) regenerate from these aggregates — run it against
the real `outputs/` to produce the real-data versions of all four figures.

## 7. Primary-endpoint reminder (locked, pre-outcome)

- **Primary:** annualized 4-m gait-speed change ~ D + A + baseline gait + f(age) +
  sex + education + site + height + BMI; 1-df nested test on β_D, two-sided α = 0.05.
- Tested on the **40% non-training holdout** (calibration + final-test). Longitudinal
  runs if ≥150 complete holdout participants; else cross-sectional on final-test is
  promoted (this is the revised, arithmetic-feasible gate — the protocol's original
  300@20% ceiling is unreachable at N=1,396).
- Report effect + 95% CI **regardless of significance**. Never promote a secondary
  to rescue a null primary. The MotionVector precedent (NHANES) was a clean null and
  that is a legitimate, publishable outcome here too.

## 8. If a clock fails the gate

Stop-rule #10 is not a nuisance — a channel clock with r < 0.20 means that modality
does not carry a usable age signal in this release, and forcing it into the geometry
would inject noise into D. Report which channels passed, freeze on the passing set
(≥3), and note the dropped channel in the claims ledger. If <3 pass, the honest
result is "technical failure: brain-age clocks did not validate," full stop.
