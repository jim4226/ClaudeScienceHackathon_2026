# Built with Claude: Life Sciences — 2026

## From Clocks to Coordinates — biological age is a direction, not a number

**Author:** Jaron Mohammed · University of Miami

This repository is a single research program built around one idea: **the
"biological age" a model reads off a physiological signal is better represented
as a direction in a state space than as a single number.** Biology routinely
compresses a complex system into one aggregate score — one "ECG-age" for the
whole heart, one organ-age gap, one undifferentiated set of "human accelerated
regions" assayed in a single cell type. That scalar is convenient, but it hides
*where* the signal comes from and throws away the part of it that carries
mechanism.

The method decomposes an aggregate age signal into a **shared aging axis A**
(how old the system looks overall), an orthogonal **disagreement radius D** (how
much its subsystems disagree with each other), and — when a controlled
perturbation is available — a **signed direction S** that the unsigned radius
discards. The anchor result is electrical: four subsystem ECG clocks resolved
into A/D geometry, where the radius is *null* on a pre-registered mortality test
but the discarded signed direction, recovered from a randomized ion-channel
blockade, transports to an external clinical cohort. The same shared-axis-versus-
disagreement *question* is then posed across other biological scales — a
whole-body CT skeleton, 220 real brain-MRI volumes, six blood-panel organ-system
clocks, and an in-silico genomic screen of human accelerated regions — as a
supporting multiscale atlas, and a movement boundary test marks exactly where
the "everything is an age clock" reading breaks down.

**One study, one geometry, read across scales** — with a live demo that runs the
frozen electrical clocks on any 12-lead ECG.

---

## The method

1. **Decompose** an aggregate age signal into the biologically distinct
   subsystems that generate it (ECG phases; organ-system panels; tissue/lineage
   contexts).
2. **Re-express** the subsystem gaps as a geometry: a shared aging axis **A**, an
   orthogonal disagreement radius **D**, and — where a controlled perturbation
   exists — a signed mechanism direction **S** (with |S| ≤ D by construction).
3. **Test** each coordinate against outcomes with the aggregate view as the
   baseline it must beat, freezing the geometry before any outcome is read.
4. **Validate** with a pre-registered outcome firewall, blind positive controls,
   and explicit negative / confound controls — and report the honest negatives
   (a null radius, a failed boundary test) as first-class results.

---

## Live demo · [`electrical-body-clock/demo/hf_space/`](electrical-body-clock/demo/hf_space/)

A deployable Gradio app (Hugging Face Space layout) runs the five *frozen*
subsystem phase-age clocks on CPU and reads out the A/D geometry live:

- **Live inference** — synthesize a physiologically-plausible 12-lead ECG (no
  patient data) or upload a WFDB / 12-column-CSV record; the app returns the
  subsystem age-gap fingerprint, the median beat with the four subsystem windows
  highlighted, and the record's position in the A–D plane.
- **Result explorer** — the frozen result figures: the perturbation compass,
  external Chapman transport, the multiscale organ atlas, brain-MRI disagreement,
  and the MotionVector structure–function boundary test.

Model weights and every standardization constant are frozen from the manuscript;
nothing is refit at runtime. `pip install -r requirements.txt && python app.py`.

---

## Arm I — the electrical anchor · [`electrical-body-clock/`](electrical-body-clock/)

*A phase-resolved ECG-age representation hides mechanism-aligned physiological
directions behind its scalar output — and a controlled human perturbation
recovers one of them.*

- **Decompose:** four disjoint 1D-CNN age clocks over the P wave, PR segment,
  QRS complex, and ST–T segment (21,373 adult PTB-XL ECGs), reframed as a
  *shared aging axis A* and an orthogonal *disagreement radius D*, with the
  geometry frozen on CODE-15 before any outcome was read.
- **Localize:** an FDR-controlled disease × subsystem matrix localizes
  single-substrate diseases to their canonical subsystem (bundle-branch block →
  QRS, ischemia → ST–T, AV block → PR); the same organ-age-gap principle carried
  to NHANES predicts all-cause mortality (hepatic HR 1.38, hematologic HR 1.36;
  C-index 0.817 → 0.845).
- **The central result:** the unsigned radius D was *null* on its single
  pre-registered CODE-15 mortality test (HR 1.01/SD, p = 0.48) — the honest
  negative that motivates a *signed* analysis. A randomized IKr blocker
  (dofetilide) displaces the ST–T repolarization clock, defining a
  covariance-scaled signed direction the radius discards; frozen and carried
  unchanged into an external cohort (Chapman–Shaoxing/Ningbo, n = 44,550), it
  adds conditional information about physician-assigned QT-interval extension.
- **Multiscale atlas (supporting):** the same A/D decomposition read at other
  scales — a whole-body CT skeleton clock, an image-derived disagreement
  coordinate from 220 real LEMON brain-MRI T1 volumes, and an in-silico genomic
  screen — as a visually rich companion, explicitly exploratory, not
  independent confirmation of the electrical result.
- **Validate:** pre-registered outcome firewall; negative controls (device/site
  confound, mask-shuffle leakage); an independent median-beat pipeline
  reproduces the ladder within noise.

Ships all source (`src/`), released result tables (`results/` — including the
external Chapman transport, NHANES organ-atlas robustness, brain-imaging
disagreement, and the `motionvector/` structure–function boundary test), figures,
the live demo (`demo/`), and three papers in `paper/`: the current 55-page
technical account (`from_clocks_to_coordinates_full`), its 6-page judge-cut
(`clocks_to_coordinates`), and the original reproducible disease-localization
write-up (`manuscript`). MIT.

---

## Arm II — the genomic scale · [`skeletome/`](skeletome/)

*The same substrate-resolution logic, one scale down: the first in-silico
skeletal variant-effect screen of Human Accelerated Regions (HARs) and HAQERs —
a virtual skeletal MPRA benchmarked against a real one. It is the deep-time,
sequence-level companion to the electrical anchor: resolve a monolithic signal
into the lineage that actually generates it, then validate the resolution
blind.*

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

This study was built with Claude as the scientific collaborator, not glue code:
designing the A/D geometry, writing the evaluation and control harnesses,
red-teaming its own positive controls, standing up the live demo, and drafting
the honest write-up — including the negatives.

---

## Data policy

This repository ships **code, result tables, figures, and papers only** — no
participant-level or restricted data. PTB-XL and NHANES (Arm I) and the
Okamoto/Capellini MPRA, Zoonomia, and GWAS summary statistics (Arm II) are
redistributed only through their original portals under their own licenses; run
each arm's `download_*` scripts to fetch them. The root and per-arm
`.gitignore` files block raw data, model checkpoints, and build artifacts.
