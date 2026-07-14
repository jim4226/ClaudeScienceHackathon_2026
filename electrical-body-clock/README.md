# HumanVector electrical core

## Phase-resolved ECG age, controlled perturbations, and external transport

**[Read the canonical 54-page paper](paper/from_clocks_to_coordinates_full.pdf) | [Launch the public Atlas](https://jim4226.github.io/) | [Return to the project overview](../README.md)**

Jaron Mohammed | 2026

This directory contains the primary scientific experiment behind HumanVector.
It asks what a whole-ECG age model erases when four electrically distinct phases
of one heartbeat are represented separately.

Four disjoint age clocks cover:

- P: atrial depolarization;
- AV: the P-offset to QRS-onset conduction segment;
- QRS: ventricular depolarization;
- ST-T: ventricular repolarization.

Their standardized gaps form a state vector `z`. A shared projection `A`
summarizes movement common to the four clocks. A covariance-normalized radius
`D` summarizes magnitude inside the contrast subspace. Signed coordinates `q`,
and a fixed perturbation projection `S_IKr`, preserve orientation that `D`
discards. The shared direction and contrast subspace are orthogonal; the scalar
summaries `A` and `D` are not themselves two orthogonal axes.

## Read the evidence in this order

### 1. Confirmatory result: electrical D is null for mortality

On the single prespecified CODE-15 confirmatory test, adding `D` beyond age,
sex, `A`, and a whole-ECG age score did not improve mortality modeling:

```text
n = 74,715 complete cases
deaths = 2,583
HR(D) = 1.010 per SD
95% CI = 0.983 to 1.039
LRT p = 0.48
```

This is the strongest result because the geometry and model were hash-locked
before the outcome reveal. It is a negative result, not evidence that all
cardiac directions are uninformative.

### 2. Controlled perturbation recovers a signed direction

In the randomized ECGRDVQ crossover study, dofetilide displaced the ST-T clock
relative to placebo and defined a covariance-scaled IKr direction. The direction
was stable under participant bootstrapping. Its derivation remains exploratory
after correction across the two screened perturbations (Holm-adjusted
permutation p = 0.069). Quinidine provided within-cohort held-mechanism support;
ranolazine and verapamil projected more weakly with confidence intervals spanning
zero.

Acute ischemia in STAFF III moved primarily along the shared coordinate and did
not pass the contrast-direction stability gate. No substitute ischemia direction
was selected.

### 3. External phenotype transport is conditional

The frozen IKr coordinate was applied without outcome-driven redefinition to the
Chapman-Shaoxing/Ningbo cohort:

```text
n = 44,550
physician-assigned QT-extension cases = 386
fully adjusted OR = 1.225 per SD
95% CI = 1.10 to 1.364
LRT p = 1.92e-4
marginal OR = 1.00
```

The association emerges after adjustment and is therefore described as
conditional and potentially model-dependent. It does not establish that
`S_IKr` diagnoses QT prolongation or outperforms QTc clinically.

## Papers

| File | Role |
|---|---|
| [`from_clocks_to_coordinates_full.pdf`](paper/from_clocks_to_coordinates_full.pdf) | **Canonical submission paper, 54 pages** |
| [`from_clocks_to_coordinates_full.tex`](paper/from_clocks_to_coordinates_full.tex) | Matching canonical source |
| [`clocks_to_coordinates.pdf`](paper/clocks_to_coordinates.pdf) | Condensed six-page judge brief from an earlier revision |
| [`manuscript.pdf`](paper/manuscript.pdf) | Historical disease-localization manuscript |

When wording or scope differs, the canonical paper and
[`CLAIM_TO_ARTIFACT_LEDGER.md`](CLAIM_TO_ARTIFACT_LEDGER.md) govern the release.

## Repository layout

```text
electrical-body-clock/
|-- README.md
|-- CLAIM_TO_ARTIFACT_LEDGER.md
|-- RELEASE_MANIFEST.sha256
|-- environment.yml
|-- src/
|   |-- extraction/                  # phase-window and median-beat extraction
|   |-- training/                    # global and phase-specific age clocks
|   |-- analysis/                    # ECG analyses and controls
|   |-- nhanes/                      # secondary organ-system construction
|   `-- figures/                     # figure scripts
|-- results/
|   |-- act1_ecg/
|   |   |-- reveal/                  # confirmatory D result and reveal log
|   |   |-- perturbation/            # frozen IKr direction and verifier
|   |   `-- external_validation/     # Chapman transfer and phenotype test
|   |-- act2_nhanes/                 # survey-aware secondary BodyVector results
|   |-- brain_imaging/               # open LEMON derived views and sensitivity
|   `-- motionvector/                # exploratory structure-function boundary
|-- paper/                            # canonical source, PDF, and figures
|-- scripts/                          # public release and sensitivity scripts
|-- figures/                          # earlier publication figures
|-- demo/
|   |-- hf_space/                     # frozen CPU inference app
|   `-- electrical_body_clock_demo.html
`-- data/                              # download scripts, not source datasets
```

## Verify the released evidence

Run from the repository root:

```bash
make verify
make demo-smoke
make paper
```

`make verify` checks the frozen perturbation scorer, deterministic fixture,
ledger-referenced files, and both SHA-256 manifests. It does not retrain a clock
or access a controlled outcome.

## Full ECG pipeline

Full retraining requires the original datasets under their provider terms.
Create the environment and stage data locally:

```bash
conda env create -f electrical-body-clock/environment.yml
conda activate electrical-body-clock

python electrical-body-clock/src/extraction/download_ptbxl.py
python electrical-body-clock/src/extraction/subsystem_extractor.py
python electrical-body-clock/src/training/train_clocks_medianbeat.py
python electrical-body-clock/src/analysis/analyze_clocks.py
```

The median-beat 1D-CNN pipeline is canonical. A superseded full-strip training
script remains for historical reference and must not be mistaken for the frozen
demo checkpoints.

## Supporting analyses

The canonical paper also reports scale-appropriate supporting analyses across
NHANES blood systems, AABC and LEMON brain imaging, multi-region CT, movement,
and an exploratory genomic screen. These are not one person's data and are not
independent confirmations of the electrical perturbation result. See the root
[`README.md`](../README.md) and [`DATA_LICENSES.md`](../DATA_LICENSES.md).

## Demo

The public interactive companion is the
[HumanVector Atlas](https://jim4226.github.io/). The local CPU inference demo can
be run with:

```bash
cd electrical-body-clock/demo/hf_space
python -m pip install -r requirements.txt
python app.py
```

It includes frozen model checkpoints and three explicitly selected PTB-XL
example records under CC BY 4.0 with attribution. Nothing is refit at runtime.

## Data, citation, and license

Data and asset boundaries are documented in [`../DATA_LICENSES.md`](../DATA_LICENSES.md).
Code is released under the [MIT License](LICENSE). Third-party data and assets
remain under their source terms. Citation metadata are in [`CITATION.cff`](CITATION.cff).

*Research demonstration. Not for clinical use.*
