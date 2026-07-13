# Skeletome — prospective methods prototype

> **Prospective methods prototype; no biological discovery is claimed.**
> This is a screening *method* plus a pre-registered analysis plan and a
> partial real run — not a validated result. Nothing here should be read as a
> demonstrated skeletal-regulatory finding.

Skeletome is the genomic-scale companion to the electrical anchor of
*From Clocks to Coordinates*. It asks one focused question: of the human-specific
substitutions inside Human Accelerated Regions (HARs), which are plausibly
**skeletal-lineage regulatory** changes rather than evolutionary noise? Prior HAR
functional work has concentrated on neural contexts; the skeleton — the bridge
organ of the parent study — has not been screened at the level of individual HAR
substitutions.

## What is real vs. illustrative

**Real (committed result tables, from public reference data):**
- The **substitution catalogue** — 1,955 human-specific substitutions across the
  312 Zoonomia HARs (UCSC `hars312`, Keough 2023, doi:10.1126/science.abm1696).
- **Constraint** from the 241-mammal Zoonomia Cactus alignment phyloP
  (61.8% at phyloP > 2.27; 74.8% at > 1.6).
- The **gBGC discriminator** (48% weak→strong, 35% strong→weak, 17% neutral).
- **GWAS proximity** to osteoarthritis / bone-mineral-density credible sets
  (10 HARs within 25 kb; 0 exact-base overlaps).
- The predicted **skeletal-minus-neural accessibility contrast** per candidate
  (`skeletome_top_candidates.csv`), spanning −2.45 to 4.69.
- The **honest negative:** the 10 GWAS-proximal HARs are not significantly more
  skeletal-specific than matched controls (matched permutation null, 50,000 draws,
  p = 0.24).
- The **blind GDF5 filter control:** pass/reject calls on the constraint+gBGC
  filters, frozen before scoring; the two constrained strong→weak GDF5 variants
  are retained and the gBGC-favoured promoter variant rejected, as pre-specified.

**Illustrative only (do not cite as findings):**
- `code/benchmark.py` and `code/make_demo_input.py` run **offline against a
  deterministic, seeded MOCK element table** so the interface and report can be
  demonstrated without a model API key. The mock benchmark's AUROC / enrichment /
  rank numbers are **not** biological results and are **not** reported in the
  manuscript. The mock table deliberately spikes the GDF5 controls purely so the
  end-to-end demo path is exercised.

## Layout

```
skeletome/
├── README.md                     # this file
├── PROJECT_BRIEF.md              # original hackathon plan (historical)
├── IDEA_BAKEOFF.md               # idea selection (historical)
├── skeletome_onepager.html       # one-page overview
├── DEMO_PRODUCTION_PLAN.html     # demo plan (historical)
└── claude_science_package/
    ├── START_HERE.md             # how to run the real pipeline
    ├── code/                     # scoring, constraint, gBGC, GWAS, benchmark
    ├── tests/                    # test_gdf5.py — filter-control unit test
    ├── requirements.txt
    └── *.md                      # schema, caveats, open questions, changelog
```

## Running the real pipeline

The real screen needs the public reference inputs (HAR call set, 241-way phyloP,
GWAS credible sets) and a sequence-to-coverage model; see
[`claude_science_package/START_HERE.md`](claude_science_package/START_HERE.md) and
[`claude_science_package/DATA_MANIFEST.md`](claude_science_package/DATA_MANIFEST.md).
`OPEN_QUESTIONS.md` lists the allele-polarity items still to confirm before any
candidate is treated as more than a hypothesis.

---
*Prospective prototype. No claim is made that any HAR substitution causes an
age-related skeletal phenotype.*
