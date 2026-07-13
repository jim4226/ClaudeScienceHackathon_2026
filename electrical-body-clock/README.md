# The Electrical Body Clock

**Subsystem-resolved ECG aging clocks localize disease to its electrical substrate,
and the same organ-resolved principle predicts mortality.**

Jaron Mohammed · University of Miami · 2026

---

Deep-learning "ECG-age" models estimate a single biological age for the whole heart,
discarding the fact that the heart is an assembly of electrically distinct subsystems —
the atria, the AV conduction axis, the ventricular myocardium, and the repolarization
apparatus — that can age at different rates and fail independently. This project
**decomposes** ECG age into four subsystem clocks, shows the resulting fingerprint
localizes disease to its electrical substrate, and then demonstrates that the *same*
organ-resolved-aging principle predicts all-cause mortality in an independent national
cohort.

The scientific claim is a **method**, not a single model: *train per-system age
predictors in healthy people, read out the bias-corrected age-gap, and ask what it
localizes to and what it predicts.* That recipe reproduces across two measurement
modalities and two populations.

> **Manuscripts.** This arm ships three papers in [`paper/`](paper/), reflecting how the
> science evolved:
>
> 1. [`from_clocks_to_coordinates_full.pdf`](paper/from_clocks_to_coordinates_full.pdf)
>    (55 pp) — the **current, complete technical account**. It reframes the four subsystem
>    clocks as a *shared aging axis A* and an orthogonal *disagreement radius D*, reports
>    the pre-registered CODE-15 mortality test for D (null, HR 1.01/SD), and builds the
>    central result on a controlled human perturbation: a randomized IKr blocker
>    (dofetilide) displaces the ST–T repolarization clock, defining a signed direction the
>    unsigned radius discards, which then transports to an independent external cohort
>    (Chapman–Shaoxing/Ningbo) as conditional information about physician-assigned
>    QT-interval extension. A supporting **multiscale atlas** (whole-body CT skeleton, real
>    brain MRI from 220 LEMON T1 volumes, and an in-silico genomic screen) shows the same
>    decomposition recurring across scales.
> 2. [`clocks_to_coordinates.pdf`](paper/clocks_to_coordinates.pdf) (6 pp) — a **condensed
>    judge-cut** of the same result: perturbation discovery first, the external-transport
>    (Chapman) figure promoted to a full panel, and the multiscale atlas closing the
>    account. Every number is lifted verbatim from the full manuscript; nothing new is
>    asserted.
> 3. [`manuscript.pdf`](paper/manuscript.pdf) — the **original disease-localization
>    write-up** whose numbers the `src/`, `figures/`, and `results/` tables below directly
>    reproduce.
>
> Read `from_clocks_to_coordinates_full` (or the 6-page `clocks_to_coordinates`) for the
> current science; read `manuscript` for the fully-reproducible ladder + specificity
> results. The external clock-transfer metrics are in
> [`results/act1_ecg/external_validation/`](results/act1_ecg/external_validation/)
> (Chapman age-transfer table, n = 44,595).

## The two acts

### Act I — the heart's electrical subsystems (PTB-XL)
Four disjoint 1D-CNN age clocks over the **P wave, PR segment, QRS complex, and ST–T
segment** of 21,373 adult PTB-XL ECGs.

- Each subsystem carries a genuine but partial age signal (full-strip pipeline test R²:
  QRS 0.54, ST–T 0.39, P 0.38, PR 0.24), weaker than a whole-strip global clock
  (R² = 0.63, MAE 8.1 y) — no single subsystem holds all cardiac age information. An
  independent median-beat pipeline reproduces the ladder within noise (QRS 0.56, PR 0.20).
- A disease × subsystem **specificity matrix** (age/sex-adjusted, FDR-controlled,
  patient-cluster bootstrap) shows single-substrate diseases localize to their canonical
  subsystem: **bundle-branch block → QRS** (+0.090 SD, top-ranked in 85% of resamples),
  **ischemia → ST–T** (+0.071 SD, 60%), **AV block → PR** (+0.30 SD within-patient).
- Two negative controls (device/site confound, mask-shuffle leakage) confirm the signal
  is physiological, not artifactual.

### Act II — the same principle, whole-body (NHANES)
Six organ-system age clocks (cardiovascular, metabolic, renal, hepatic, immune,
hematologic) from routine labs in 15,844 NHANES adults linked to the NCHS mortality file
(2,002 deaths).

- Four of six organ-age gaps predict all-cause mortality (hepatic HR 1.38, hematologic
  1.36, metabolic 1.20, renal 1.19, per +1 SD).
- The multi-system profile improves mortality prediction over chronological age:
  **C-index 0.817 → 0.845 (ΔC = +0.028)**.
- Smoking, a modifiable exposure, accelerates exactly the two clocks with the largest
  mortality hazard (hepatic, hematologic) — the divergence points at its cause.

> **Act II is a parallel demonstration, not an external validation.** NHANES and PTB-XL
> are different cohorts, and NHANES contains no ECG waveforms. No Act I model is reused;
> no NHANES participant contributes an ECG. Act II shows the *method* generalizes.

## Repository layout

```
electrical-body-clock/
├── README.md
├── LICENSE                 # MIT
├── CITATION.cff
├── environment.yml         # conda env: electrical-body-clock
├── src/
│   ├── extraction/         # ECG subsystem-window extraction (P/PR/QRS/ST-T masks)
│   ├── training/           # 1D-CNN subsystem + global age clocks
│   ├── analysis/           # specificity matrix, negative controls, figures
│   ├── nhanes/             # Act II organ clocks + Cox mortality analysis
│   └── figures/            # figure-generation scripts
├── results/
│   ├── act1_ecg/           # clock performance, specificity, bootstrap CIs (CSV/parquet)
│   │   └── external_validation/  # Chapman–Shaoxing/Ningbo clock-transfer metrics
│   └── act2_nhanes/        # Cox HRs, C-index ladder, smoking attribution
│       └── robustness/     # cross-validated C-index folds, leave-one-system-out D
├── figures/                # publication figures (PNG) — Fig 1–7
├── demo/                   # static fingerprint demo + hf_space/ (deployable live-inference app)
├── paper/                  # from_clocks_to_coordinates_full.{tex,pdf} (55 pp, current)
│                           #   + clocks_to_coordinates.{tex,pdf} (6 pp judge-cut)
│                           #   + manuscript.{tex,pdf,docx} (original reproducible paper)
│                           #   figs_full/ = full-manuscript figures, figs_c2c/ = judge-cut,
│                           #   figs/ = original paper; references_c2c.bib + references.bib
└── data/                   # download scripts ONLY (no data redistributed)
```

## Reproducing the results

**Runs from a fresh clone, no restricted data** (from the repository root):

```bash
make verify        # frozen IKr scorer + fixture, ledger files, SHA-256 manifest
make demo-smoke    # end-to-end test of the live demo (no server launched)
make paper         # compile all three manuscripts with tectonic
```

`make verify` re-runs the independent perturbation verifier against the committed
protocol lock and scorer fixture and checks that every result file named in
[`CLAIM_TO_ARTIFACT_LEDGER.md`](CLAIM_TO_ARTIFACT_LEDGER.md) is present and matches
the SHA-256 [`RELEASE_MANIFEST.sha256`](RELEASE_MANIFEST.sha256).

**Full retraining pipeline** (needs the source data fetched and staged — see
[`../DATA_LICENSES.md`](../DATA_LICENSES.md); the ECG clocks are the *frozen
median-beat 1D-CNN* pipeline, `train_clocks_medianbeat.py`, which is canonical —
`train_clock.py` is a superseded full-strip ResNet kept for reference only):

```bash
conda env create -f environment.yml && conda activate electrical-body-clock

# 1. Fetch data (respects PhysioNet / NHANES data-use agreements)
python src/extraction/download_ptbxl.py        # PTB-XL v1.0.3
python data/download_nhanes.py                 # NHANES 2005-2010 + mortality

# 2. Act I — ECG subsystem clocks (median-beat pipeline is canonical)
python src/extraction/subsystem_extractor.py   # P/AV/QRS/ST-T windows + median beats
python src/training/train_clocks_medianbeat.py # 5 clocks (global + 4 subsystems)
python src/analysis/analyze_clocks.py          # specificity matrix + controls

# 3. Act II — NHANES organ clocks + mortality
python src/nhanes/build_master.py              # assemble NHANES master table
python src/nhanes/nhanes_organ_clocks.py       # 6 organ clocks, survey Cox, C-index ladder

# 4. Figures
python src/figures/make_figures.py             # regenerate figures from results/
```

> Training and extraction scripts read their inputs from a local staging directory
> (`drive_staging/…`); set those paths for your environment before running. The
> `make` targets above need none of this.

The headline numbers can be checked without re-training: every quantity in the
paper is mapped to the committed result file it was read from in
[`CLAIM_TO_ARTIFACT_LEDGER.md`](CLAIM_TO_ARTIFACT_LEDGER.md), and the figures that
depend only on those released tables regenerate from them. Figures that also need
raw waveforms or images (which are not redistributed — see
[`../DATA_LICENSES.md`](../DATA_LICENSES.md)) require first fetching the source data
through its portal.

## Live demo

[`demo/hf_space/`](demo/hf_space/) is a deployable Gradio app (Hugging Face Space
layout) that runs the five *frozen* subsystem phase-age clocks on CPU and reads out
the A/D geometry live — synthesize or upload a 12-lead ECG and see the subsystem
age-gap fingerprint, the windowed median beat, and the record's A–D position, plus a
result explorer over the frozen figures. Model weights and standardization constants
ship inside the folder; nothing is refit at runtime.

```bash
cd demo/hf_space
pip install -r requirements.txt
python app.py                                  # or push the folder to a Hugging Face Space
```

## Data availability

This project redistributes **no** participant-level data. Both datasets are openly
available under their own data-use agreements:

- **PTB-XL v1.0.3** — PhysioNet, <https://physionet.org/content/ptb-xl/>
- **NHANES 2005–2010** — CDC, <https://wwwn.cdc.gov/nchs/nhanes/>, linked to the
  **NCHS Public-Use Linked Mortality File (2019)**,
  <https://www.cdc.gov/nchs/data-linkage/mortality-public.htm>

The scripts in `data/` download and preprocess these sources locally.

## Citation

See [`CITATION.cff`](CITATION.cff). If you use this work, please cite the paper in
[`paper/`](paper/).

## License

Code released under the [MIT License](LICENSE). Data remain under their respective
providers' terms.

---

*Research demonstration; not for clinical use.*
