# Built with Claude: Life Sciences — 2026 Hackathon

Two independent entries built during the *Built with Claude: Life Sciences*
hackathon (2026). Each entry is a self-contained research package in its own
top-level folder.

**Author:** Jaron Mar · University of Miami

---

## Entries

### 1. [`electrical-body-clock/`](electrical-body-clock/) — Body Clock (main track)

**Subsystem-resolved ECG aging clocks localize disease to its electrical
substrate, and the same organ-resolved principle predicts mortality.**

Rather than estimating one "ECG-age" for the whole heart, this project
decomposes cardiac age into four electrically distinct subsystems and shows the
resulting fingerprint localizes disease — then demonstrates the same
organ-resolved-aging idea predicts all-cause mortality in an independent cohort.

- **Act I — PTB-XL.** Four disjoint 1D-CNN age clocks over the P wave, PR
  segment, QRS complex, and ST–T segment of 21,373 adult ECGs. Full-strip test
  R2: QRS 0.54, ST-T 0.39, P 0.38, PR 0.24 — each weaker than a whole-strip
  global clock (R2 = 0.63, MAE 8.1 y), so no single subsystem holds all cardiac
  age information. An FDR-controlled disease x subsystem specificity matrix
  localizes single-substrate diseases to their canonical subsystem
  (bundle-branch block -> QRS, ischemia -> ST-T, AV block -> PR), with two
  negative controls confirming the signal is physiological.
- **Act II — NHANES.** Organ-age-gap mortality: hepatic HR 1.38, hematologic
  HR 1.36; C-index ladder 0.817 -> 0.845 (delta-C +0.028).

Ships: all source (`src/`), released result tables (`results/`), seven figures,
a self-contained interactive demo (`demo/`), and the compiled paper
(`paper/manuscript.{tex,pdf,docx}` + `references.bib`). **License:** MIT (see
`electrical-body-clock/LICENSE`).

### 2. [`skeletome/`](skeletome/) — SKELETOME (research track, Gladstone)

**The first in-silico skeletal variant-effect screen of Human Accelerated
Regions (HARs) and HAQERs — a virtual skeletal MPRA benchmarked against a real
one.**

Every published HAR reporter assay was run in neural cells; ENCODE contains
essentially no skeletal chromatin-accessibility data. SKELETOME predicts
human-vs-chimp DNase deltas for HAR and HAQER elements with AlphaGenome
(GPU-free API), benchmarks them against the Okamoto/Capellini 2025 skeletal MPRA
(GEO GSE298093), separates gBGC artifacts from candidate-adaptive changes via
241-mammal Zoonomia constraint plus a recombination-rate control, crosses the
genuinely skeletal-regulatory minority with osteoarthritis / BMD / height
genetics, and **blindly re-discovers the GDF5/GROW1 skeletal enhancer** as a
positive control.

The offline benchmark (`code/benchmark.py`) runs exit-0 with a mock AUROC of
0.84, reproduces HAQER 63% vs HAR 33% enrichment, and recovers GDF5/GROW1 blind
at the top 0.9%. See `skeletome/claude_science_package/START_HERE.md` to
continue the work in Claude Science.

---

## Data policy

This repository ships **code, result tables, figures, and papers only**. No
participant-level or restricted data is committed. The datasets used
(PTB-XL and NHANES for the Body Clock; the Okamoto/Capellini MPRA, Zoonomia,
and GWAS summary statistics for SKELETOME) are redistributed only through their
original portals under their own licenses — run the `download_*` scripts in each
entry to fetch them. The root and per-entry `.gitignore` files block raw data,
model checkpoints, and build artifacts.
