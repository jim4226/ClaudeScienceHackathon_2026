# SKELETOME — CHANGELOG

All notable changes to the SKELETOME research package. This project follows the
SKELETOME **canonical spine** as its source of truth; where a file disagrees with
the spine, the spine wins and the disagreement is logged here as a fix-forward item.

Format: newest first. Dates are ET. "Spine" = the canonical one-sentence-finding +
verified-facts brief that every agent aligns to.

---

## [v2] — 2026-07-07 — "Virtual skeletal MPRA, benchmarked against the real one"

### The pivot (one line)
SKELETOME changed from **a HAR-only in-silico *variant-effect screen*** (predict skeletal
accessibility deltas for human-specific HAR substitutions, validate blind on GDF5) to
**a virtual skeletal MPRA *benchmarked against a real one***: AlphaGenome's in-silico
human-vs-chimp DNase predictions are scored against the measured Okamoto/Capellini 2025
skeletal MPRA (GEO **GSE298093**), recovering the **HAQER-over-HAR** contrast and the
**polygenic** distribution of skeletal regulatory divergence, and — at base resolution —
nominating causal substitutions the region-level assay cannot resolve, blindly recovering
the GDF5/GROW1 human-specific skeletal enhancer.

### One-sentence finding (v2, canonical)
> AlphaGenome's in-silico human-vs-chimp DNase predictions reproduce the Okamoto/Capellini
> 2025 skeletal MPRA — recovering the HAQER-over-HAR contrast and the polygenic distribution
> of skeletal regulatory divergence from sequence alone — and, at base resolution, nominate
> the causal substitutions the region-level assay cannot resolve, blindly recovering the
> GDF5/GROW1 human-specific skeletal enhancer.

### Added
- **Benchmark spine** — Okamoto, Coveney, Ganapathee & Capellini 2025 skeletal MPRA
  (bioRxiv 2025.10.21.683789; GBE 10.1093/gbe/evag121), **GEO GSE298093** (19 samples),
  code `github.com/aokamoto-bio/human_skeletal_evolution_MPRA`. ~70k elements tested,
  30,736 active (45.2%), 11,542 differentially active (37.6% of active; |log2FC|>1 &
  Bonferroni p<0.01), hg38. This is now the validation target, not a mere precedent.
- **HAQER arm** — HAQERs (Mangan/Lowe 2022, n=**1,581** native hg38, BED5) added alongside
  HARs. Key MPRA result reproduced as the headline contrast: HAQER-overlapping active
  19/30 = 63% differential (Fisher OR 2.88, P<0.01, enriched vs chance); HAR-overlapping
  19/57 = 33% (P=0.58, not enriched); baseline 37.6%.
- **Dual-null honesty gate** — HAQER>HAR reported under BOTH the vs-chance Fisher test AND a
  sequence-feature-matched permutation null, always printed together, with the explicit
  caveat that against matched controls NEITHER HAR nor HAQER is significant (Fisher P>0.05).
- **`code/benchmark.py` (NEW)** — P3 concordance (AUROC / Spearman / top-decile precision-
  recall of predicted `|ag_dnase_delta|` vs measured `mpra_diff_active`), HAQER/HAR
  enrichment under both nulls, polygenicity (Gini, top-10% effect share, elements-for-50%),
  and the blind GDF5 line. MPRA input contract `MPRA_REQUIRED = [element_id, mpra_active,
  mpra_log2fc, mpra_bonferroni_p, mpra_diff_active, is_haqer, is_har]`.
- **Base-resolution causal nomination** — `score_alphagenome.py` now records the max-|delta|
  position (the causal substitution the region-level MPRA cannot resolve) into `notes`.
- **CAVEATS_AND_DEFENSES.md (v2)** — rewritten to 9 kill-shots for the benchmark framing +
  a paste-ready Limitations section; leads with the two ROBUST claims (concordance +
  polygenicity) and hedges HAQER>HAR as the vs-chance-only third result.

### Changed
- **Framing.** "In-silico variant-effect screen" → **"virtual skeletal MPRA, benchmarked
  against the real one."** The honesty invariant tightened: we predict DNase deltas and
  BENCHMARK them; we never say we "ran an MPRA."
- **Readout locked to DNase.** AlphaGenome's embryonic/fetal skeletal accessibility
  biosamples live in the DNASE panel (305 DNASE + 167 ATAC tracks; GTEx excluded), so DNase
  is the primary skeletal readout; ATAC is scored and passed through only.
- **Skeletal panel via `output_metadata()`** — aggregate a small skeletal DNASE panel
  (chondrocyte ENCSR970DQR, osteoblast ENCSR000ELJ, embryonic femur ENCSR805XIF, limb)
  rather than trusting one track.
- **Engine.** AlphaGenome pinned to the peer-reviewed Nature paper (28 Jan 2026,
  10.1038/s41586-025-10014-0), hosted no-GPU API. Remains PRIMARY; ChromBPNet stays optional.
- **`code/score_alphagenome.py` (v2)** — human(alt)-vs-chimp(ref) DNase scoring across the
  panel, CenterMaskScorer width=501 with quantile_score primary, DIFF_MEAN aggregation,
  base-resolution max-|delta| position.

### Corrected (facts brought into line with the spine)
- **GDF5 gene-body end coordinate:** should be **chr20:35,433,347–35,454,749** (end `...749`,
  GRCh38.p14), NOT `...35,454,754`.
- **Osteoarthritis GWAS:** Hatzikotoulas 2025 **Nature** = **962 independent associations**
  (513 novel; 700 effector genes), NOT "962 SuSiE credible sets." GWAS arm intersects
  independent associations / fine-mapped signals, framed as supporting annotation.
- **HAQER count:** **1,581** native hg38 (Mangan/Lowe 2022); near-disjoint from HARs
  (6/2,733 overlap). zooHARs **n=312** (Keough 2023).
- **Constraint:** Zoonomia 241-mammal phyloP **≥ 2.27 = 5% FDR** (Sullivan/Christmas 2023).
- **gBGC:** ~19% of HARs best explained by pure gBGC (76% selection); ~29–33% gBGC-influenced
  (Kostka 2012) — state which figure is meant.

### Deprecated / de-emphasized
- **"Every HAR assay was neural / ENCODE has zero skeletal ATAC" as the headline gap.** Still
  true and citable, but no longer the thesis — Whalen/Pollard 2023 (GSE110760, neural
  HAR-MPRA) and Kun 2023 (enrichment-only) are now **precedents we cite ourselves**, not the
  benchmark. The benchmark is the real skeletal MPRA (GSE298093).
- **ChromBPNet as a co-primary** — remains an OPTIONAL base-resolution / robustness
  cross-check (limb ENCSR138OCE/ENCSR858EVI; MSC ENCFF640AVL; MG63 ENCFF841SWM).

### KNOWN INCONSISTENCY (fix-forward — several v1 docs still on disk)
The v2 rewrite landed in `CAVEATS_AND_DEFENSES.md`, `code/benchmark.py`, and
`code/score_alphagenome.py`. The following files are **still the v1 (HAR-only, neural-gap,
"never an MPRA") text on disk** and must be re-synced to the v2 spine before submission:
`PROJECT_CONTEXT.md`, `CANONICAL_SCHEMA.md`, `RESEARCH_PLAN.md`, `DATA_MANIFEST.md`,
`PROJECT_BRIEF.md`, `START_HERE.md`, `OPEN_QUESTIONS.md`, `PROMPT_PACK.md`, and the code
schema/harness (`code/schema.py` and any module reading the old column set). See the
consistency-audit findings below for the specific contradictions.

---

## [v1] — 2026-07-07 — Initial research package (HAR-only skeletal variant-effect screen)

### Added
- Full Claude-Science package: `PROJECT_CONTEXT.md` (7 locked decisions + honest register),
  `CANONICAL_SCHEMA.md` (one-row-per-substitution TSV contract), `RESEARCH_PLAN.md` (P0–P6),
  `DATA_MANIFEST.md`, `PROMPT_PACK.md`, `OPEN_QUESTIONS.md` (40 questions), `PROJECT_BRIEF.md`,
  `START_HERE.md`, and a runnable mock-by-default `code/` pipeline (schema, substitutions,
  constraint, gbgc, score_alphagenome, score_chrombpnet, comparator, aggregate) + tests.
- Thesis: first in-silico **skeletal** variant-effect screen for HARs — every published HAR
  reporter assay was neural; ENCODE has no skeletal ATAC-seq. Score human-specific HAR
  substitutions for predicted skeletal accessibility change, filter by Zoonomia constraint,
  separate gBGC, intersect OA/BMD/height GWAS, blind-validate on GDF5/GROW1.
- Locked decisions: AlphaGenome PRIMARY (ChromBPNet optional); gBGC a first-class arm;
  "variant-effect screen" not "in-silico MPRA"; GDF5 a frozen-blind control SET; GWAS =
  enrichment-not-causality; Claude as adversarial collaborator; literal cell-type labels only.
