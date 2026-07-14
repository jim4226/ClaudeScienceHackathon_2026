# HumanVector

## From Clocks to Coordinates

**Turning biological age from one number into a directional state space.**

[![CI](https://github.com/jim4226/ClaudeScienceHackathon_2026/actions/workflows/ci.yml/badge.svg)](https://github.com/jim4226/ClaudeScienceHackathon_2026/actions/workflows/ci.yml)
[![Paper: 54 pages](https://img.shields.io/badge/paper-54%20pages-8b1e3f)](electrical-body-clock/paper/from_clocks_to_coordinates_full.pdf)
[![License: MIT](https://img.shields.io/badge/code-MIT-2f6f66)](LICENSE)

**[Read the full paper](electrical-body-clock/paper/from_clocks_to_coordinates_full.pdf) | [Launch the HumanVector Atlas](https://jim4226.github.io/) | [Open presentation mode](https://jim4226.github.io/?present=1) | [Verify the evidence](#reproduce-and-verify)**

**Built with Claude: Life Sciences 2026 | Researcher Track**
**Jaron Mohammed**

HumanVector asks what biological-age models erase when they compress a complex
system into one number. The anchor experiment trains separate age clocks for the
P, AV, QRS and ST-T phases of a heartbeat, then represents their outputs as a
shared coordinate, an unsigned disagreement radius, and, when a controlled
perturbation is available, a signed physiological direction.

The prespecified mortality test for electrical disagreement was null. That
negative result exposed the central insight: magnitude alone can discard
mechanism. Randomized IKr blockade revealed a stable repolarization direction; a
second IKr-active drug moved in the same direction; and the frozen coordinate
carried adjustment-dependent information about physician-assigned QT extension
in a geographically distinct cohort. Its marginal association was null, so the
transport result is conditional and potentially model-dependent.

Brain MRI, blood biomarkers, multi-region CT, movement, and evolutionary genomics
form a supporting cross-scale atlas. They use related, scale-appropriate
constructions. They are not observations from one person and do not independently
confirm the electrical result.

> **HumanVector is a cross-cohort evidence atlas and research framework. It is
> not a clinical device, diagnostic system, or whole-person digital twin.**

## Start here

| Artifact | Purpose |
|---|---|
| [Full 54-page paper](electrical-body-clock/paper/from_clocks_to_coordinates_full.pdf) | Canonical scientific account and submission paper |
| [HumanVector Atlas](https://jim4226.github.io/) | Public interactive anatomy and results companion |
| [Guided presentation](https://jim4226.github.io/?present=1) | Presentation-mode camera and narrative flow |
| [Claim-to-artifact ledger](electrical-body-clock/CLAIM_TO_ARTIFACT_LEDGER.md) | Maps released claims to committed evidence |
| [Submission brief](SUBMISSION.md) | Judge-facing links and project summary |
| [Reproducibility guide](REPRODUCE.md) | Fresh-clone verification and build commands |
| [Data and license map](DATA_LICENSES.md) | Source, access, redistribution, and attribution boundaries |

The PDF above has SHA-256
`c1cb1807f852be288d89966abba1676179622403559cf094482206f1edc77bc0`.
The other manuscripts in `electrical-body-clock/paper/` are retained as a
condensed judge brief and a historical earlier analysis. They are not the
canonical submission paper.

## The primary discovery

Four non-overlapping phase clocks produce a standardized state vector

```text
z = [P, AV, QRS, ST-T]
```

HumanVector reads that state in three ways:

- **A, shared movement:** how strongly the phase clocks move together.
- **D, disagreement magnitude:** the covariance-normalized radius inside the
  contrast subspace. The shared direction and contrast subspace are orthogonal;
  the scalar summaries A and D are not themselves two orthogonal axes.
- **S, signed direction:** a fixed projection learned outcome-blind from a
  controlled perturbation, preserving which way the system moved.

The evidence chain is deliberately asymmetric:

| Test | Result | Evidential role |
|---|---|---|
| CODE-15 mortality, n = 74,715 and 2,583 deaths | D was null: HR 1.010 per SD, 95% CI 0.983 to 1.039, LRT p = 0.48 | Single prespecified confirmatory test |
| Dofetilide vs placebo, randomized crossover | Stable IKr-aligned direction; derivation Holm-adjusted permutation p = 0.069 | Exploratory, outcome-free direction derivation |
| Quinidine | Positive projection on the frozen direction, mean +0.84 | Within-cohort held-mechanism support |
| Chapman-Shaoxing/Ningbo, n = 44,550 | Fully adjusted OR 1.225 per SD, 95% CI 1.10 to 1.364; marginal OR 1.00 | External phenotype test with adjustment-dependent support |

The conclusion is not that every disagreement score is predictive. It is that a
scalar age and an unsigned radius can erase physiologically meaningful
orientation, and that controlled perturbations provide a principled way to
recover a frozen direction.

## Cross-scale atlas

| Scale | Dataset and construction | What the study found | Status |
|---|---|---|---|
| Blood systems | Six cross-fitted NHANES organ-system clocks | Shared and disagreement summaries were mortality-associated in survey-weighted secondary analyses | Secondary; outcome had been inspected previously |
| Brain, multimodal | AABC/HCP-Aging structural, myelin, perfusion, and functional clocks | Four held-out age clocks were viable; prespecified disagreement-to-walk-change test was null | Controlled-access prospective boundary test |
| Brain, open T1 | 220 LEMON scans and four correlated structural views | Older participants had greater pooled cross-view dispersion; the contrast remained positive in 5,000 balanced resamples | Separate open-data sensitivity, not validation of AABC D |
| Anatomy | TotalSegmentator v2 multi-region volume features, n = 1,227 | Cross-validated MAE 8.56 years; cardiovascular volumes were the strongest system-level estimate | Exploratory volume-only localization atlas |
| Structure-function | NHANES DXA plus accelerometry | Prespecified reserve-to-limitation test did not reach significance and has acknowledged processing limitations | Exploratory boundary analysis |
| Deep time | 1,955 substitutions in 312 Zoonomia HARs | No matched enrichment near skeletal GWAS loci, p = 0.24 | Hypothesis screen, not functional validation |

The Atlas makes these scales explorable while keeping their cohort boundaries
visible. Reference anatomy is never presented as a reconstruction of an ECG
participant.

## Live demo

The public [HumanVector Atlas](https://jim4226.github.io/) provides:

- interactive heart MRI, brain MRI, skeleton CT, and whole-body CT reference
  anatomy;
- a participant view using explicitly licensed PTB-XL examples;
- a six-slide results deck for the locked null, perturbation direction, external
  transport, atlas, and boundary analyses;
- visible evidence-status and cohort-boundary language throughout.

The local CPU demo in
[`electrical-body-clock/demo/hf_space/`](electrical-body-clock/demo/hf_space/)
runs the five frozen ECG clocks on a synthetic ECG or an eligible local upload.
Nothing is refit at runtime.

## Repository map

```text
.
|-- README.md                         # this judge-facing entry point
|-- SUBMISSION.md                     # canonical submission links
|-- REPRODUCE.md                      # fresh-clone verification
|-- HACKATHON_PROVENANCE.md           # work and artifact provenance
|-- CLAUDE_SCIENCE_METHODS.md         # how Claude changed the research workflow
|-- DATA_LICENSES.md                  # source-by-source governance map
|-- electrical-body-clock/
|   |-- paper/                        # canonical PDF, TeX, figures, references
|   |-- results/                      # released aggregate and derived results
|   |-- src/                          # extraction, training, and analysis code
|   |-- scripts/                      # release verifiers and sensitivity analyses
|   `-- demo/                         # static and CPU inference demos
`-- skeletome/                        # bounded exploratory genomic screen
```

## Reproduce and verify

From a fresh Ubuntu clone, no controlled-access data are needed for the release
checks:

```bash
make verify        # scorer fixture, claim ledger, and SHA-256 manifests
make demo-smoke    # CPU end-to-end demo smoke test
make paper         # compile canonical, condensed, and historical manuscripts
```

For environment details, expected outputs, and a Windows note, see
[`REPRODUCE.md`](REPRODUCE.md). Full retraining requires the original datasets
under their provider terms; the release checks do not.

## How Claude Science changed the workflow

Claude was used as a scientific collaborator and adversarial reviewer: to help
formalize the geometry, build outcome firewalls and protocol locks, generate and
test analysis code, surface contradictory claims, maintain the claim-to-artifact
ledger, and reproduce headline outputs from frozen artifacts. The division of
labor, safeguards, failures, and corrections are documented in
[`CLAUDE_SCIENCE_METHODS.md`](CLAUDE_SCIENCE_METHODS.md).

## Data governance

No raw controlled-access AABC data, restricted clinical records, raw MRI/CT
volumes, or identifiable participant data are committed. Three explicitly
selected PTB-XL example waveforms are included in the local demo under CC BY 4.0
with attribution, along with the frozen model checkpoints needed for CPU
inference. The repository also contains disclosed derived tables from open,
de-identified sources. Exact boundaries and licenses are listed in
[`DATA_LICENSES.md`](DATA_LICENSES.md).

Code is released under the [MIT License](LICENSE). Data and third-party assets
remain under their original terms.

## Citation

See [`CITATION.cff`](CITATION.cff). The canonical paper is:

> Jaron Mohammed. *From Clocks to Coordinates: Controlled Human Perturbations
> Reveal Hidden Directions in ECG Biological Age.* 2026.

---

*Research demonstration. Not for clinical use.*
