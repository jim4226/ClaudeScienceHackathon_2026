# Built with Claude: Life Sciences — 2026

## From Clocks to Coordinates — biological age is a direction, not a number

[![CI](https://github.com/jim4226/ClaudeScienceHackathon_2026/actions/workflows/ci.yml/badge.svg)](https://github.com/jim4226/ClaudeScienceHackathon_2026/actions/workflows/ci.yml)

**Author:** Jaron Mohammed 

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

> **Prospective methods prototype; no biological discovery is claimed.** This arm
> is a *bounded, forward-looking* companion to the electrical anchor, not a
> validated result. Read it as a screening method and a pre-registered analysis
> plan — the honest negative it already produces (below) is the point.

*The same substrate-resolution logic, one scale down: an in-silico screen that
scores Human Accelerated Region (HAR) substitutions for a predicted
skeletal-lineage regulatory effect — the lineage prior HAR functional work
(concentrated on neural contexts) has skipped.*

- **Decompose:** score each of the 1,955 human-specific substitutions in the 312
  Zoonomia HARs (Keough 2023) for a skeletal-minus-neural predicted
  chromatin-accessibility contrast with an open sequence-to-coverage model. This
  is a variant-effect *screen* (model-predicted accessibility), not a reporter
  assay — no transcription is measured, and candidates are prioritised hypotheses
  awaiting experimental validation.
- **Filter:** two first-class filters separate candidates from the confounded
  majority — 241-mammal phyloP constraint (61.8% of substitutions at phyloP > 2.27)
  and a GC-biased gene-conversion (gBGC) discriminator (48% weak→strong, flagged as
  likely recombination artefacts). Requiring both leaves 722 candidate
  substitutions; crossing them with osteoarthritis/BMD GWAS credible sets surfaces
  10 proximal HARs.
- **Honest negative:** the 10 GWAS-proximal HARs are **not** significantly more
  skeletal-specific than matched non-proximal HARs (matched permutation null,
  50,000 draws, p = 0.24), and no substitution overlaps a credible-set variant
  exactly (0 exact-base overlaps). A **blind GDF5 filter control** — pass/reject
  calls on the constraint+gBGC filters, frozen before scoring — recovers the two
  constrained strong→weak GDF5 variants and rejects the gBGC-favoured promoter
  variant, as pre-specified.

The `code/` benchmark and demo-input scripts run **offline against mock element
tables** (deterministic, seeded) so the interface can be demonstrated without a
model API key — those mock benchmark numbers are illustrative and are **not**
reported as findings here or in the manuscript. See
[`skeletome/README.md`](skeletome/README.md) and
[`skeletome/claude_science_package/START_HERE.md`](skeletome/claude_science_package/START_HERE.md)
to run the real pipeline.

---

## Built with Claude

This study was built with Claude as the scientific collaborator, not glue code:
designing the A/D geometry, writing the evaluation and control harnesses,
red-teaming its own positive controls, standing up the live demo, and drafting
the honest write-up — including the negatives.

---

## Data policy

**No raw waveforms, images, identifiable records, or restricted participant-level
data are redistributed.** Selected *derived* records from openly licensed datasets
**are** included: pseudonymous, participant-level derived feature/score tables
keyed by each source's own public accession — the LEMON brain-imaging feature
table (`sub-0100xx` subject IDs) and the MotionVector NHANES DXA/accelerometry
score tables (public `SEQN` IDs). These are model-derived summaries of public,
consented, de-identified research datasets, released under the source licenses;
no raw signal, image, or genotype is committed.

Everything else is redistributed only through its original portal under its own
license — PTB-XL and NHANES raw data (Arm I), and the Okamoto/Capellini MPRA,
Zoonomia alignment, and GWAS summary statistics (Arm II); run each arm's
`download_*` scripts to fetch them. The root and per-arm `.gitignore` files block
raw waveforms, images, and model checkpoints.

Every dataset — source, version, license, attribution, and exactly which derived
files are committed — is mapped in [`DATA_LICENSES.md`](DATA_LICENSES.md).
