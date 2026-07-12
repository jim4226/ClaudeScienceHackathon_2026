# CANONICAL_SCHEMA.md — SKELETOME v2 per-ELEMENT results table

> The canonical output of the v2 pipeline is ONE tidy table: one row per tested regulatory element. This file defines every column exactly. Column names here are the source of truth — code, notebooks, and figures must use these names verbatim. Assembly is **hg38** throughout. All AlphaGenome values are **PREDICTED** (DNase-accessibility deltas), never measured; all `mpra_*` values are the **MEASURED** wet-lab ground truth from Okamoto/Capellini 2025 (GSE298093).

## Register reminder (applies to every row)

- `ag_*` columns = AlphaGenome **predictions** (DNase deltas). Not measured transcription.
- `mpra_*` columns = the **measured** MPRA calls we benchmark against.
- Skeletal signal is from the **DNase** panel (not ATAC).
- Element class uses the MPRA paper's **own** HAR/HAQER labels for benchmark rows.

## Table: `skeletome_v2_elements` (one row per element)

| # | Column | Type | Definition |
|---|--------|------|------------|
| 1 | `element_id` | string | Stable unique element identifier, keyed to the MPRA paper's element/oligo ID where the element is one of their ~70k tested (so rows join back to GSE298093 / their GitHub). Genome-wide-screen-only elements (standalone zooHAR/HAQER) get a `skel_`-prefixed ID. Primary key. |
| 2 | `chrom` | string | hg38 chromosome of the element (e.g. `chr20`). |
| 3 | `start` | int | hg38 element start, 0-based half-open (BED convention). |
| 4 | `end` | int | hg38 element end, 0-based half-open (BED convention). |
| 5 | `element_class` | enum {`HAR`,`HAQER`,`other`,`both`} | Acceleration class. For benchmark rows this uses the MPRA paper's OWN per-element HAR/HAQER labels (definitions must match theirs). `both` = labeled HAR and HAQER (rare; the sets are near-disjoint). `other` = tested element in neither class. |
| 6 | `human_seq` | string (ref) | The human (hg38) element sequence, or a reference/pointer to it if long. This is the AlphaGenome **alt** allele in the human-vs-chimp scoring. |
| 7 | `chimp_seq` | string (ref) | The chimpanzee element sequence (from the MPRA design / lifted), or a reference/pointer. This is the AlphaGenome **ref** allele. Human-vs-chimp = alt(human) vs ref(chimp). |
| 8 | `ag_dnase_diff_quantile` | float | PRIMARY predicted score: AlphaGenome human-vs-chimp DNase differential accessibility as the **quantile** score (CenterMaskScorer / quantile), aggregated across the skeletal DNase panel. Primary predictor benchmarked against `mpra_diff_active`. |
| 9 | `ag_dnase_diff_raw` | float | Predicted human-vs-chimp DNase differential accessibility as the **raw** (non-quantile) delta, aggregated across the skeletal DNase panel. Reported alongside the quantile score as a robustness readout. |
| 10 | `ag_skeletal_panel_tracks` | list[string] | The exact skeletal DNase track CURIEs / biosample IDs aggregated for this element (e.g. chondrocyte, embryonic femur, limb DNase). Locked via `output_metadata(HOMO_SAPIENS)` in P0. Documents provenance of the aggregate in cols 8-9. |
| 11 | `base_resolution_max_delta_pos` | int (hg38) | The single hg38 position within the element with the largest |base-resolution predicted DNase delta| — AlphaGenome's nomination of the most impactful base, which the region-level MPRA cannot resolve. |
| 12 | `mpra_active` | bool | MEASURED: element called ACTIVE in the MPRA (part of the 30,736 / 45.2%). Ground truth. |
| 13 | `mpra_diff_active` | bool | MEASURED: element called DIFFERENTIALLY active human vs chimp (|log2FC|>1 & Bonferroni p<0.01; part of the 11,542 / 37.6% of active). The primary benchmark label. |
| 14 | `mpra_log2fc` | float | MEASURED: human-vs-chimp log2 fold-change of MPRA activity for this element. Continuous ground truth (correlate against `ag_dnase_diff_quantile`). |
| 15 | `phylop_241` | float | Zoonomia 241-mammal phyloP score at the element / substitution (Sullivan/Christmas 2023). Used for the constraint filter. |
| 16 | `constrained` | bool | True if `phylop_241` >= 2.27 (5% FDR constraint threshold). Convenience flag derived from col 15. |
| 17 | `gbgc_class` | enum {`pure_gbgc`,`gbgc_influenced`,`selection`,`unknown`} | GC-biased-gene-conversion classification of the human-derived change(s) (Kostka 2012 framework). `pure_gbgc` ~ the ~19%-of-HARs bucket; `gbgc_influenced` ~ the ~29-33% bucket; `selection` = best explained by selection; `unknown` = not assessed. State which population/figure applies in `notes`. |
| 18 | `gbgc_flag` | bool | True if the element is gBGC-suspect (`pure_gbgc` or `gbgc_influenced`) — i.e. its human-vs-chimp signal may be a neutral GC-conversion artifact rather than adaptive. Used by the self-red-team gate before any gBGC-based dropping. |
| 19 | `oa_assoc_overlap` | bool | True if the element overlaps an osteoarthritis association (Hatzikotoulas 2025 Nature, 962 independent associations / GO 2.0 portal). BMD (Morris 2019) and height (Yengo 2022) overlaps, if computed, go in `notes` or parallel flags. |
| 20 | `causal_substitution_pos` | int (hg38) | The nominated causal human-derived substitution position (hg38) for this element — the base-resolution call reasoned from `base_resolution_max_delta_pos` plus constraint / GWAS context. For GDF5/GROW1 this should recover chr20:35,364,817 (rs4911178) blind. May equal `base_resolution_max_delta_pos` or be refined from it. |
| 21 | `is_control` | enum {`none`,`positive`,`negative_matched`,`negative_scramble`,`negative_nonskeletal`} | Control role. `positive` = GDF5/GROW1 and other known positives (recovered blind, not special-cased). `negative_matched` = sequence-feature-matched control from the MPRA's own set. `negative_scramble` / `negative_nonskeletal` = scrambled sequence / non-skeletal-track controls. `none` = ordinary tested element. |
| 22 | `notes` | string | Free text: liftOver caveats, which gBGC figure/population applies, BMD/height overlaps, self-red-team flags (e.g. "filter would drop this positive"), any per-row honesty caveats. |

## Notes on use

- **Join key back to the wet lab:** `element_id` must let any benchmark row rejoin the MPRA paper's per-element table (GSE298093 / their GitHub) so `mpra_active` / `mpra_diff_active` / `mpra_log2fc` are traceable, not re-derived.
- **Primary benchmark axes:** classification = `ag_dnase_diff_quantile` (col 8) vs `mpra_diff_active` (col 13, AUROC); regression = `ag_dnase_diff_quantile` vs `mpra_log2fc` (col 14, correlation). `ag_dnase_diff_raw` (col 9) is the robustness echo.
- **HAQER>HAR is computed from `element_class`** using the paper's own labels, reported under BOTH the vs-chance and vs-matched-control nulls (the latter via `is_control == negative_matched` rows), with the matched-control caveat attached.
- **Self-red-team gate lives in cols 15-18 + 21:** before applying any constraint/gBGC drop, verify no `is_control == positive` row (GDF5/GROW1) is removed by it; if it would be, set a flag in `notes` and do not drop silently.
- **Everything `ag_*` is predicted, everything `mpra_*` is measured.** Keep that distinction in every figure and caption.
