# Data licenses & provenance

Every external dataset this project uses, with its source, version, license, the
attribution it requires, and **exactly which derived files (if any) are committed
to this repository**. No raw waveforms, images, genotypes, or identifiable records
are redistributed here. Where a table is committed, it is a *model-derived summary*
keyed by the source's own already-public/de-identified accession.

> Licenses are summarized in good faith and can change at the source portal. The
> authoritative license for each dataset is the one on its linked portal at the
> time you download it — confirm there before redistribution or commercial use.

## Arm I — electrical / physiological

| Dataset | Version | Source / portal | License | Committed here? |
|---|---|---|---|---|
| **PTB-XL** (12-lead ECG) | 1.0.3 | PhysioNet `ptb-xl` | CC-BY 4.0 | No raw signal. A few **curated example records** are bundled with the live demo under CC-BY 4.0 **with attribution** (see `demo/hf_space/`). Derived clock scores only in `results/`. |
| **Chapman–Shaoxing / Ningbo** (ECG arrhythmia) | `ecg-arrhythmia` 1.0.0 | PhysioNet | CC-BY 4.0 | **Aggregate only** — the QT-extension transport table `results/act1_ecg/external_validation/chapman_*.csv` (per-analysis OR/CI/p rows; no participant records). |
| **NHANES** (2005–2006 examination + Linked Mortality File) | 2005–2006 cycle; NCHS LMF | CDC / NCHS | U.S. Government public domain (open; cite NCHS) | Derived organ-clock Cox/robustness aggregates in `results/act2_nhanes/`; **participant-level derived score tables** keyed by public `SEQN` in `results/motionvector/` (DXA + accelerometry gaps/scores — no raw accelerometry, no DXA images). |
| **LEMON** (MPI-Leipzig Mind-Brain-Body, T1 MP2RAGE) | OpenNeuro `ds000221` | OpenNeuro / MPI-CBS; T1 volumes fetched from the GWDG open mirror | Open-access, de-identified (BIDS IDs `sub-0100xx`); **confirm exact terms on the OpenNeuro portal** (default CC0; some INDI mirrors state non-commercial + attribution) | **No raw images.** Only the **derived per-subject feature table** `results/brain_imaging/lemon_imaging_feature_table.csv` (brain-age, tissue volumes) keyed by the public de-identified `sub-0100xx` ID. |
| **CODE-15%** (ECG + mortality) | Zenodo 4916206 | Zenodo | CC-BY 4.0 | No raw data. Confirmatory result is custodian-held behind an outcome firewall; only the released summary is described in the manuscript. |
| **SaMi-Trop** (Chagas ECG cohort) | Zenodo 4905618 | Zenodo | CC-BY 4.0 | No raw data committed. |

## Arm II — genomic (prospective prototype)

| Dataset | Version | Source / portal | License | Committed here? |
|---|---|---|---|---|
| **Human Accelerated Regions** (hars312) | Keough 2023 call set | UCSC Genome Browser track / Keough et al. 2023 (doi:10.1126/science.abm1696) | Open (UCSC data-use; cite Keough 2023) | Derived substitution catalogue + scores in `skeletome/` result tables (positions, phyloP, gBGC class, predicted contrast). |
| **Zoonomia 241-way** Cactus alignment / phyloP | cactus241way | UCSC / Zoonomia Consortium (Christmas et al. 2023) | Open (cite Zoonomia) | No raw alignment. Per-base phyloP values enter the committed constraint summary only. |
| **Okamoto/Capellini skeletal MPRA** | GEO GSE298093 | NCBI GEO | Per GEO submitter terms (public) | **Not committed.** The offline `benchmark.py` runs against a **deterministic mock table**, not this MPRA (see `skeletome/README.md`). |
| **Osteoarthritis GWAS** credible sets | Genetics of Osteoarthritis (GO) consortium | Consortium portal / GWAS Catalog | Per consortium terms (summary statistics) | Only overlap counts / proximity flags enter committed summaries. |
| **Bone-mineral-density GWAS** credible sets | GEFOS / UK Biobank (Morris et al. 2019) | Consortium portal / GWAS Catalog | Per consortium terms (summary statistics) | Only overlap counts / proximity flags enter committed summaries. |

## Models

| Model | Role | Source | License |
|---|---|---|---|
| Frozen subsystem ECG clocks (this work) | Arm I inference + demo | this repo (`demo/hf_space/hv_bundle/models/`) | MIT (with the repo) |
| Borzoi / AlphaGenome (sequence→coverage) | Arm II predicted accessibility | Calico / Google DeepMind | Per model provider's terms; weights **not** redistributed here |

## Summary of what is redistributed

- **Committed:** source code, model-derived result tables (aggregate and some
  pseudonymous participant-level, keyed by public accessions), figures, papers, the
  frozen demo clock weights, and a few CC-BY PTB-XL example records (with attribution).
- **Never committed:** raw ECG waveforms, raw MRI/DXA images, raw accelerometry,
  genotypes, identifiable records, or any restricted-access data.
