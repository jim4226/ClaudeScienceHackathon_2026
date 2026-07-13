# Response to Reviewer Blocker #1 — the genomic (Skeletome) arm

*Prepared for the reviewer who wrote: "Both papers still present an 'in-silico
genomic screen,' including broad novelty claims. The repository indicates this arm
uses a mock/prototype pipeline. Remove it from the abstract, conclusion, Figure 5,
Part III, and 'first screen' claims."*

We thank the reviewer for this catch. It exposed a **real packaging defect on our
side**, and we want to separate that defect — which we have now fixed — from the
question of whether the screen used real data. **The screen is real.** The
impression that it was a mock came from an artifact of what we committed to the
repository, not from how the reported numbers were produced.

---

## 1. What was actually wrong (and is now fixed)

At the time of review, the repository shipped the Skeletome **code** — including an
offline demonstration harness (`code/benchmark.py`) that runs against a seeded
**mock** element table so the pipeline can be exercised with no model API key and no
data download — but it did **not** ship the **real result tables** that the
manuscript's numbers were read from. A reviewer inspecting the repo therefore saw
scoring code, a mock, and `run.sh` defaulting to mock mode, and reasonably concluded
"prototype/mock pipeline."

That was a genuine reproducibility gap. We have now committed the real run's outputs
and the real scoring engine:

| File (now in repo) | What it is |
|---|---|
| `skeletome/results/borzoi_scores_full.csv` | The full scored catalogue — all **1,958** substitutions (1,955 HAR + 3 GDF5 controls), with real per-variant skeletal and neural accessibility deltas. |
| `skeletome/results/skeletome_top_candidates.csv` | The top-ranked candidate substitutions. |
| `skeletome/results/skeletome_pipeline_summary.json` | The provenance-stamped run summary (source URLs, counts, GDF5 control calls, permutation p-value). |
| `skeletome/claude_science_package/code/borzoi_score.py` | The **real** scoring engine that produced the numbers: `Borzoi.from_pretrained("johahi/borzoi-replicate-0")`, 524,288-bp hg38 windows, ref-vs-alt one-hot, skeletal-vs-neural track contrast. |

Every numeric value in Part III now regenerates from these committed files.

---

## 2. Why the numbers were never the mock — schema-level proof

The mock and the real pipeline emit **disjoint columns**. They cannot be confused,
and the manuscript's numbers can only have come from one of them:

- **Mock** (`benchmark.py::make_mock`, seed `20260707`) emits:
  `element_id, element_class, ag_dnase_diff, mpra_active, mpra_diff_active,
  mpra_log2fc, is_control` — and deliberately *spikes* the GDF5 controls so the demo
  path lights up.
- **Real** (`borzoi_score.py` → `borzoi_scores_full.csv`) emits:
  `har_id, chrom, pos_hg38, ref, alt, phylop_241way, gbgc_class, candidate_flag,
  skel_delta, skel_log2r, neural_delta, neural_log2r, skel_minus_neural`.

The manuscript reports the **`skel_minus_neural`** contrast (range −2.45 to 4.69).
That column exists **only** in the real table. `make_mock` never produces it. The
mock is referenced in exactly one file (`benchmark.py`) and is imported by **none**
of the real pipeline stages (`score_alphagenome.py`, `comparator.py`,
`aggregate.py`). The manuscript's reported quantities are structurally incapable of
originating from the mock.

The manuscript's numbers reconcile to the committed real table to the digit:

| Manuscript claim | `borzoi_scores_full.csv` | Match |
|---|---|---|
| `skel_minus_neural` spans −2.45 to 4.69 | −2.4489 to 4.6900 | ✓ |
| 722 candidate substitutions (constraint + non-artefactual gBGC) | 724 candidate-flagged, minus the 2 retained GDF5 controls = 722 | ✓ |
| 1,955 HAR substitutions (+3 controls = 1,958) | 1,958 rows | ✓ |

---

## 3. What is real in this arm (all from public reference data)

Every input is a public, versioned reference source, and every headline number is
computed, not asserted:

- **HAR call set:** the 312 Zoonomia HARs from UCSC track `hars312` (Keough et al.
  2023, *Science*, doi:10.1126/science.abm1696), contributing 1,955 human-specific
  substitutions.
- **Evolutionary constraint:** per-base phyloP from the Zoonomia 241-mammal Cactus
  alignment (`hgdownload.soe.ucsc.edu/goldenPath/hg38/cactus241way`). 61.8% of
  substitutions fall at phyloP > 2.27; 74.8% at phyloP > 1.6.
- **gBGC discriminator:** allelic-direction classification — 936 weak→strong (48%),
  688 strong→weak (35%), 331 neutral (17%) — used to flag substitutions whose HAR
  excess can be explained by GC-biased gene conversion rather than selection.
- **Accessibility scoring:** a real Borzoi run over 16 skeletal-lineage and 81
  neural accessibility tracks, giving the per-variant skeletal-minus-neural contrast.
- **GWAS proximity:** intersection with osteoarthritis (936) and bone-mineral-density
  (903) credible-set variants; 10 HARs within 25 kb, **0 exact-base overlaps**.
- **The honest negative — this is the point:** the 10 GWAS-proximal HARs are **not**
  significantly more skeletal-specific than size- and substitution-matched controls
  (matched permutation null, 50,000 draws, mean 0.220 vs matched-null 0.179,
  **p = 0.24**). We report a null, not an enrichment.
- **Blind GDF5 filter control:** three GDF5-locus substitutions were frozen with
  pre-specified pass/reject calls before scoring. The two constrained strong→weak
  variants (GROW1 enhancer rs4911178, phyloP 7.04; GDF5 5′UTR rs143384, phyloP 4.96)
  were retained; the unconstrained, gBGC-favoured promoter variant rs6060369 was
  rejected — exactly as pre-specified. The frozen quantity is the filter outcome,
  not any signed effect direction.

This is an evolutionary-genomics screen that **prioritises hypotheses** and reports
its own strongest test as a null. It is not, and never claimed to be, a validated
skeletal-regulatory discovery.

---

## 4. Where we nonetheless agree with the reviewer

Two of the reviewer's underlying concerns are correct and we adopt them regardless of
the mock misunderstanding:

1. **The arm is supporting, not confirmatory.** Part III shares "a theme and a
   method, never a fitted causal path," with the electrical result and "is not
   independent confirmation." The manuscript already states this; we are happy to
   make it even more prominent.
2. **The novelty claim should be narrow.** We will keep only the defensible,
   falsifiable statement — that to our knowledge this is the first in-silico
   variant-effect screen to score the *complete* HAR substitution catalogue for
   skeletal-lineage regulatory effect (prior HAR functional work having concentrated
   on neural contexts) — and drop any language that could read as a biological
   discovery.

---

## 5. Proposed resolution

We ask the reviewer to consider **retain-with-honest-framing** rather than removal,
now that the real results are in the repository and verifiable. Concretely, we will:

- Keep Part III as an explicitly labelled **supporting in-silico screen that
  reports a null**, with the "prospective methods prototype" framing already in
  `skeletome/README.md`.
- Retain only the narrow catalogue-completeness novelty statement; remove any
  "discovery"/"first result" phrasing beyond it.
- Ensure the abstract and Figure 5 language describe the genomic scale as a
  supporting atlas that poses a related coordinate-based question, not as
  confirmation of the electrical finding.

If the reviewer prefers removal despite the real provenance, we will instead reduce
the arm to a single prospective-extension sentence, per their suggested wording:

> A prospective genomic extension was designed but is not included as an empirical
> finding.

Either way, no biological discovery is claimed, and the reported quantities are now
fully reproducible from the committed `skeletome/results/` tables.
