# Data licenses, access classes, and public-release boundaries

This file enumerates every external data source used in the submitted
HumanVector study and states exactly what this repository redistributes.
Licenses and access terms remain governed by the source portals. Users must
accept and follow those terms before downloading source data.

The repository is intentionally mixed:

- most cohorts are represented by aggregate statistics, code, hashes, or
  figures only;
- three explicitly attributed PTB-XL example records are redistributed under
  CC BY 4.0 for the interactive demo;
- public-use participant-level derived tables are present for NHANES and LEMON;
- no AABC or EchoNext participant-level data are redistributed;
- frozen model state dictionaries are included so the demo can run offline.

## Electrical and physiological data

| Dataset | Version and source | Access and license | Public files in this repository |
|---|---|---|---|
| **PTB-XL** | 1.0.3, [PhysioNet](https://physionet.org/content/ptb-xl/1.0.3/) | Open, CC BY 4.0 | Three unmodified waveform pairs (`00176_hr`, `00233_hr`, `00420_hr`) in `electrical-body-clock/demo/hf_space/examples/`, their manifest and attribution, model-derived result tables, 13 public-record report examples in `demo/claude_extract_demo.json`, and frozen clock checkpoints. |
| **CODE-15%** | Zenodo record 4916206 | Open, CC BY 4.0 | No raw waveforms or row-level outcome data. The public release contains the frozen reveal script, protocol receipts, hashes, and aggregate confirmatory statistics under `results/act1_ecg/reveal/`. |
| **SaMi-Trop** | Zenodo record 4905618 | Open, CC BY 4.0 | No raw records. Manuscript-level aggregate signed-contrast results only. |
| **Chapman-Shaoxing and Ningbo** | `ecg-arrhythmia` 1.0.0, [PhysioNet](https://physionet.org/content/ecg-arrhythmia/1.0.0/) | Open, CC BY 4.0 | Aggregate transport, sensitivity, and site-stratified rows under `results/act1_ecg/external_validation/`; no waveforms. |
| **ECGRDVQ** | 1.0.0, [PhysioNet](https://physionet.org/content/ecgrdvq/1.0.0/) | Open, Open Data Commons Attribution License v1.0 | No raw ECGs or clinical rows. The signed-direction lock, deterministic fixture, scorer, gate summaries, and aggregate drug projections are under `results/act1_ecg/perturbation/`. |
| **STAFF III** | 1.0.0, [PhysioNet](https://physionet.org/content/staffiii/1.0.0/) | Open, Open Data Commons Attribution License v1.0 | No raw ECGs or patient rows. Aggregate ischemia gate statistics and figures only. |
| **EchoNext** | 1.1.1, [PhysioNet](https://physionet.org/content/echonext/1.1.1/) | Restricted; PhysioNet Restricted Health Data License and DUA 1.5.0 | No waveform, tabular, label, or participant-level derivative is redistributed. Only disclosure-safe aggregate statements and figures appear in the paper. |

PTB-XL, ECGRDVQ, STAFF III, Chapman-Shaoxing/Ningbo, CODE-15%, and
SaMi-Trop should also be cited using the source publications listed by their
repositories. The bundled PTB-XL records have an additional local attribution
file at `electrical-body-clock/demo/hf_space/examples/ATTRIBUTION.md`.

## Whole-body and imaging data

| Dataset | Version and source | Access and license | Public files in this repository |
|---|---|---|---|
| **NHANES with Linked Mortality** | 2005-2010 cycles and public-use mortality linkage, CDC/NCHS | U.S. Government public-use data; cite CDC/NCHS | Aggregate organ-clock and survey-Cox outputs in `results/act2_nhanes/`. The exploratory MotionVector folder also contains participant-level derived public-use tables keyed by `SEQN`, including selected DXA, demographic, survey, outcome, and locomotor variables. No images or raw accelerometer streams are included. |
| **AABC / HCP-Aging Release 2** | Release 2, [BALSA / Human Connectome Project](https://www.humanconnectome.org/study/hcp-lifespan-aging/data-releases) | Registered academic access under the [AABC Consortium Data Use Terms](https://www.humanconnectome.org/study/hcp-lifespan-aging/data-use-terms); redistribution outside the approved institution is restricted | No participant IDs, per-visit scores, source spreadsheets, or imaging data. Only disclosure-checked cohort-level tables, the geometry lock, run log, methods/report, and source code under `results/brain_imaging/aabc_aggregates/` and `src/brain_imaging/aabc/`. |
| **MPI LEMON** | MPI Leipzig Mind-Brain-Body MRI collection | Open. The GWDG BIDS metadata declares CC0; the official INDI distribution lists PDDL | No raw NIfTI scans. The repo contains a 220-row derived table keyed by the source's public BIDS IDs, cohort-level JSON results, balanced sensitivities, and derived visualization panels. |
| **TotalSegmentator CT** | Dataset v2.0.1, [Zenodo 10047292](https://zenodo.org/records/10047292) | Open, CC BY 4.0 | No raw CT volumes, masks, or patient-level feature matrix. Disclosure-safe aggregate performance/ranking tables, methods, summaries, and figures are under `results/ct_atlas/`. |

For AABC, public outputs must not associate participant IDs with measurements.
All participant-level AABC material remains in the approved controlled
environment. The required AABC acknowledgment is included in the manuscript.

## Genomic prototype

| Dataset | Source | Access and license | Public files in this repository |
|---|---|---|---|
| **Human Accelerated Regions** | Keough et al. 2023 call set and UCSC Genome Browser | Open source tables; cite Keough et al. and UCSC | Derived substitution catalogue and model scores under `skeletome/`. |
| **Zoonomia 241-way alignment and phyloP** | UCSC and Zoonomia Consortium | Open source tables; cite Zoonomia | No raw alignment. Derived constraint summaries only. |
| **Skeletal MPRA** | GEO GSE298093 | Public per GEO submitter terms | Not redistributed. The offline benchmark uses a deterministic mock table. |
| **Osteoarthritis and BMD GWAS summaries** | GO Consortium, GWAS Catalog, and GEFOS | Public summary-statistic terms vary by source | Only overlap counts and proximity flags in derived summaries. |

## Models and software

| Asset | Public location | Terms |
|---|---|---|
| Frozen subsystem ECG clock state dictionaries | `electrical-body-clock/demo/hf_space/hv_bundle/models/` | Released with this repository under MIT; intended for research demonstration, not clinically validated. |
| HumanVector analysis and verification code | This repository | MIT. |
| Third-party sequence models such as Borzoi or AlphaGenome | Provider repositories | Provider terms apply; weights are not redistributed here. |

## Privacy and clinical-use boundary

All source cohorts are de-identified or public-use research resources. Nothing
in this repository is intended for diagnosis, treatment, or clinical decision
making. Do not upload private, identifiable, restricted, or protected health
data to the hosted demo. The repository's MIT license applies to original code
and documentation, not to third-party data or assets, whose source licenses
remain controlling.
