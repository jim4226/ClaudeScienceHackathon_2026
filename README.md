# Built with Claude: Life Sciences — 2026

## Substrate-Resolved Biology — one method, two systems

**Author:** Jaron Mar · University of Miami

This repository is a single hackathon research program built around one
computational-biology method, applied to two very different systems. Biology
routinely compresses a complex system into a single aggregate score — one
"ECG-age" for the whole heart, one undifferentiated set of "human accelerated
regions" assayed in a single cell type. That compression is convenient, but it
hides *where* a signal actually comes from, and it makes a real biological
effect hard to separate from a confound. The goal here is the opposite: take
the monolithic signal apart into the distinct biological substrates that
generate it, model each one on its own, and then show the resolution is both
real and useful.

Applied to the **aging heart**, the method decomposes a single ECG "age" into
four separate subsystem clocks — atria, conduction axis, ventricle, and
repolarization — and shows the resulting fingerprint localizes disease to its
correct electrical substrate, while the same organ-age-gap idea, carried to a
national cohort, predicts all-cause mortality. Applied to the **evolving
genome**, the same recipe produces the first in-silico skeletal variant-effect
screen of human accelerated regions: it resolves their regulatory effect to
bone- and cartilage-relevant cell contexts — a lineage every prior HAR reporter
assay skipped — separates the majority that are evolutionary noise from the
genuinely skeletal-regulatory minority, and validates itself by blindly
re-discovering a known human skeletal enhancer. **The novelty is the method** —
substrate resolution plus blind-control validation — shown to hold across two
organ systems, two data modalities, and two populations; each arm also lands a
concrete first in its own field.

---

## The method

The field routinely collapses a biological system into a single aggregate
number — one "ECG-age" for the whole heart, one monolithic set of "human
accelerated regions" assayed in a single cell type. This program does the
opposite. In each arm:

1. **Decompose** the monolithic signal into the biologically distinct
   substrates that actually generate it.
2. **Predict** each substrate independently with a purpose-built
   sequence/signal model.
3. **Localize** — ask what each substrate's signal maps onto (a disease, a
   tissue, an outcome), with the aggregate view as the baseline it must beat.
4. **Validate** that the resolution is real, not artifact, with a *blind
   positive control* plus explicit negative / confound controls.

The claim in both arms is a **recipe, not a single model** — and it reproduces
across two organ systems, two data modalities, and two populations.

---

## Arm I — the aging heart · [`electrical-body-clock/`](electrical-body-clock/)

*Subsystem-resolved ECG aging clocks localize disease to its electrical
substrate, and the same organ-resolved principle predicts mortality.*

- **Decompose:** four disjoint 1D-CNN age clocks over the P wave, PR segment,
  QRS complex, and ST–T segment of 21,373 adult PTB-XL ECGs.
- **Localize (Act I — PTB-XL):** each subsystem carries a genuine but partial
  age signal (test R²: QRS 0.54, ST–T 0.39, P 0.38, PR 0.24) — weaker than a
  whole-strip global clock (R² 0.63, MAE 8.1 y), so no single subsystem holds
  all cardiac age information. An FDR-controlled disease × subsystem matrix
  localizes single-substrate diseases to their canonical subsystem:
  bundle-branch block → QRS, ischemia → ST–T, AV block → PR.
- **Localize (Act II — NHANES):** the same organ-age-gap principle predicts
  all-cause mortality — hepatic HR 1.38, hematologic HR 1.36; C-index ladder
  0.817 → 0.845 (ΔC +0.028).
- **Validate:** two negative controls (device/site confound, mask-shuffle
  leakage); an independent median-beat pipeline reproduces the ladder within
  noise.

Ships all source (`src/`), released result tables (`results/`), seven figures,
a self-contained interactive demo (`demo/`), and the compiled paper
(`paper/manuscript.{tex,pdf,docx}`). MIT.

---

## Arm II — the evolving genome · [`skeletome/`](skeletome/)

*The first in-silico skeletal variant-effect screen of Human Accelerated
Regions (HARs) and HAQERs — a virtual skeletal MPRA benchmarked against a real
one.*

- **Decompose:** resolve HAR and HAQER regulatory effects to *skeletal* cell
  contexts — the lineage every prior HAR reporter assay (all neural) skipped —
  using AlphaGenome (GPU-free API).
- **Localize:** predict human-vs-chimp DNase deltas per element; separate the
  gBGC-confounded majority from the genuinely skeletal-regulatory minority
  (241-mammal Zoonomia constraint + recombination-rate control); cross the
  minority with osteoarthritis / BMD / height genetics.
- **Validate:** benchmark against the real Okamoto/Capellini 2025 skeletal MPRA
  (GEO GSE298093) and **blind-recover the GDF5/GROW1 skeletal enhancer** as a
  positive control. The offline benchmark runs exit-0: mock AUROC 0.84
  in-silico↔MPRA concordance, HAQER 63% vs HAR 33% enrichment, GDF5/GROW1
  recovered blind at the top 0.9%.

Research package + runnable code; see
[`skeletome/claude_science_package/START_HERE.md`](skeletome/claude_science_package/START_HERE.md)
to continue the work in Claude Science.

---

## Built with Claude

Both arms were built with Claude as the scientific collaborator, not glue code:
designing the decomposition, writing the evaluation and control harnesses,
red-teaming its own positive controls, and drafting the honest write-up.

---

## Data policy

This repository ships **code, result tables, figures, and papers only** — no
participant-level or restricted data. PTB-XL and NHANES (Arm I) and the
Okamoto/Capellini MPRA, Zoonomia, and GWAS summary statistics (Arm II) are
redistributed only through their original portals under their own licenses; run
each arm's `download_*` scripts to fetch them. The root and per-arm
`.gitignore` files block raw data, model checkpoints, and build artifacts.
