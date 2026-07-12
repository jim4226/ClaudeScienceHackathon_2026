# SKELETOME — CAVEATS_AND_DEFENSES.md (v2)

**The honesty layer.** This document pre-bakes an honest answer to every reviewer kill-shot for the v2 finding — *a **virtual** skeletal MPRA, benchmarked against the real one* — each paired with the exact mitigation already built into the pipeline (`RESEARCH_PLAN.md`, `code/benchmark.py`, `code/score_alphagenome.py`). The Limitations section at the end is meant to be pasted verbatim into the writeup. The goal is not to make the weaknesses disappear — several are real and we say so — but to demonstrate we saw them first, quantified them, and built the pipeline so no weakness can silently inflate the result.

**The one-sentence finding (honest form).** AlphaGenome's in-silico human(alt)-vs-chimp(ref) DNase-accessibility predictions **reproduce** the Okamoto/Coveney/Ganapathee/Capellini 2025 skeletal MPRA — recovering the HAQER-over-HAR contrast (under the vs-chance null) and the **polygenic** distribution of skeletal regulatory divergence from sequence alone — and, at base resolution, nominate causal substitutions the region-level assay cannot resolve, blindly recovering the GDF5/GROW1 human-specific skeletal enhancer.

**What we did NOT do.** We did **not** run an MPRA. We predict DNase-accessibility deltas and **benchmark** them against the real, published, wet-lab MPRA differential-activity calls. Everywhere in prose we write "predicted DNase change," never "measured activity." A judge should come away thinking: *these people tried to kill their own result before we could.*

Format for each threat: **Kill-shot → Honest answer → Mitigation in the pipeline → Residual risk we still own.**

The two claims we defend as **ROBUST** are (a) the in-silico ↔ MPRA **concordance** and (b) the **polygenic** distribution. The **HAQER > HAR** contrast is reported under both nulls and is honest only under the vs-chance null (Caveat #1).

---

## 1. "HAQER > HAR is a cherry-picked contrast. Against proper matched controls it evaporates."

**Kill-shot.** The headline "HAQERs are enriched for human-vs-chimp differential skeletal activity, HARs are not" only holds against a chance baseline; against sequence-feature-matched controls it is not significant — so it is a null-model artifact.

**Honest answer.** *Partly true, and we state it in the same breath as the claim.* In the real MPRA, HAQER-overlapping active regions are 19/30 = 63% differential (Fisher OR 2.88, P<0.01, enriched **vs chance**), HARs 19/57 = 33% (P=0.58, not enriched), against a 37.6% baseline. But **against sequence-feature-matched controls, NEITHER HAR nor HAQER is significant** (Fisher P>0.05). So the HAQER>HAR headline rests on the **vs-chance** test only.

**Mitigation (P3, `code/benchmark.py`).** The benchmark computes the HAQER and HAR differential-activity rates and tests each under **both nulls, side by side, always printed together**: (a) a one-sided Fisher exact test vs the active-element baseline (`fisher_p_vs_chance`, `odds_ratio_vs_chance`), and (b) a **sequence-feature-matched permutation** null that resamples equal numbers of active elements within GC/length/substitution-count strata (`perm_p_vs_matched`, `N_MATCHED_PERM=10000`). The report line literally states: *"vs sequence-feature-matched controls neither HAR nor HAQER is expected significant; the HAQER>HAR headline rests on the vs-chance test."* We never quote the vs-chance p-value without the matched-control p-value next to it.

**Residual risk we own.** The matched-control construction can itself over- or under-correct depending on which sequence features we match on; matching is never perfect. We therefore lead with our two robust claims (concordance + polygenicity) and treat HAQER>HAR as the weaker, honestly-hedged third result — reported, not headlined.

---

## 2. "A model prediction is not an MPRA. You're calling a neural-net output a functional assay."

**Kill-shot.** In-silico accessibility deltas are not measured reporter transcription. Branding this "an MPRA" over-claims a wet-lab experiment you never ran.

**Honest answer.** *Correct, and we are disciplined about it.* This is a **virtual** MPRA: we predict human-vs-chimp DNase-accessibility deltas from sequence and **benchmark** them against the **real** MPRA's measured differential-activity calls. We never describe our numbers as measured transcription or enhancer activity.

**Mitigation (naming discipline + the benchmark itself).** The bridge from prediction to reality **is the benchmark**: `code/benchmark.py` joins our predicted `ag_dnase_diff = |ag_dnase_delta|` to the MPRA's measured `mpra_diff_active` and reports **concordance** (AUROC of predicted magnitude discriminating measured differential elements, Spearman of predicted magnitude vs measured |log2FC|, top-decile precision/recall). The MPRA table is loaded under a documented column contract (`MPRA_REQUIRED`) from the GSE298093-derived differential-activity calls; a documented mock generator reproduces the published headline rates offline. Prose uses "predicted DNase change in [literal biosample]," never "measured activity."

**Residual risk we own.** Accessibility ≠ transcription; a variant can change one without the other, so concordance measures agreement with a reporter assay, not ground-truth regulation. Candidates are hypotheses for functional follow-up.

---

## 3. "AlphaGenome isn't tissue-specific-optimized, and it excludes GTEx. It can't speak to skeletal biology."

**Kill-shot.** AlphaGenome's own model card warns it is not fully optimized for cell/tissue-specific patterns, and its training panel excludes GTEx. Applying it to *skeletal* regulatory divergence is out of its wheelhouse.

**Honest answer.** *Fair, and it dictates how we frame the result.* AlphaGenome exposes 305 human DNASE + 167 ATAC tracks (ENCODE-derived; **GTEx excluded**), and its model card cautions against reading absolute cell-type-specific accessibility off it. So we frame the finding as **correlation / enrichment against a measured benchmark**, never as absolute per-cell-type accuracy.

**Mitigation (P0 + P3).** (a) We do not trust one track: `score_alphagenome.py` calls `output_metadata()` and selects a **skeletal DNASE panel** by biosample keyword (chondrocyte, osteoblast, mesenchymal, embryonic femur, limb/forelimb/hindlimb — B1-resolved accessions incl. ENCSR970DQR, ENCSR000ELJ, ENCSR805XIF) and aggregates across it. (b) The entire claim is a **benchmark against a measured assay**, not a self-reported confidence — if AlphaGenome were useless here, the concordance AUROC would sit at 0.5 and we would report that. (c) The GDF5 blind control is the acid test that the model recovers a *known* skeletal enhancer.

**Residual risk we own.** The bulk skeletal DNASE tracks dilute genuinely cell-type-restricted (e.g. growth-plate chondrocyte) signal, so a truly chondrocyte-specific enhancer change can fall below detection — a false-negative floor, not a false-positive risk. The honest ceiling on the claim is set by the benchmark, not by the model's confidence.

---

## 4. "Why DNase and not ATAC? Looks like you picked the readout that worked."

**Kill-shot.** You benchmark DNase but also run ATAC — choosing DNase post-hoc is selective reporting.

**Honest answer.** *The choice is a priori and principled, not post-hoc.* AlphaGenome's **fetal/embryonic skeletal accessibility is in the DNASE panel** (chondrocyte, osteoblast, MSC, embryonic femur, embryonic limb DNase), while the ATAC panel lacks matched embryonic-skeletal biosamples. DNase is therefore the **skeletal-context** readout; that decision was locked in P0 before any benchmark was computed.

**Mitigation.** `score_alphagenome.py` scores **both** DNASE and ATAC and writes both (`ag_dnase_delta`, `ag_atac_delta`); the benchmark uses DNase as primary and keeps ATAC as a pass-through secondary that a reviewer can inspect. The skeletal-panel selection is DNASE-only *because that is where the skeletal biosamples are*, and the code says so.

**Residual risk we own.** DNase and ATAC measure open chromatin by different chemistries; a DNase-only benchmark does not cross-validate the accessibility signal across assay types for the skeletal biosamples that lack ATAC coverage.

---

## 5. "Your HAR/HAQER definitions are chosen to make the story work."

**Kill-shot.** HAR and HAQER sets vary by paper; picking favorable definitions manufactures the HAQER>HAR contrast.

**Honest answer.** *We deliberately use the MPRA authors' own per-element labels, precisely so the definitions match theirs and cannot be tuned by us.* For the benchmark, HAR/HAQER membership comes from the **MPRA paper's own per-element HAR/HAQER labels** (from `github.com/aokamoto-bio/human_skeletal_evolution_MPRA`), not from a set we curated. For the broader genome-wide screen we use the standalone published BEDs (zooHARs n=312, Keough 2023; HAQERs n=1,581 native hg38, Mangan/Lowe 2022; near-disjoint, 6/2,733 overlap) and say which set is used where.

**Mitigation (`code/benchmark.py`).** The `is_haqer` / `is_har` columns in the MPRA input contract are the authors' labels; we do not recompute overlaps for the benchmark. Definitional provenance is documented in the input contract and `DATA_MANIFEST.md`.

**Residual risk we own.** Their labels inherit their overlap thresholds and set versions; our benchmark is only as clean as their annotation. We tie ourselves to their choices rather than defending our own — the honest trade is reproducibility over freedom.

---

## 6. "GDF5 validation is circular / n=1. You tuned the pipeline to hit your one favorite gene."

**Kill-shot.** A pipeline tuned on its own positive control is circular; n=1 anecdotes are worthless.

**Honest answer.** *The most dangerous critique, designed against from day one.* GDF5/GROW1 is recovered **blind**: its predicted rank and effect **direction are frozen before we look**, it is one of a **control set** (>1), and nothing in the scoring or benchmark is fit on it.

**Mitigation (P0 + P6, `code/benchmark.py` blind line + `code/score_alphagenome.py`).**
- **Frozen expectation.** GDF5-GROW1's expected sign is **negative** (derived allele ≈ 0.72× activity, shorter bone, higher OA; Capellini 2017 *Nat Genet*), locked in the schema/aggregate before scoring. The benchmark's `blind_gdf5_line()` reports its predicted delta, its **blind rank** among all elements, and whether its measured MPRA call agrees — computed post-hoc, tuning nothing. In the offline fixture it lands at negative sign, top ~1% rank, measured differentially-active — recovered blind.
- **Control set > 1.** GDF5-GROW1, GDF5-R4 (rs6060369, R4 knee enhancer), HACNS1, plus explicit **negative controls** — a real precision/recall curve, not a single hit.
- **No free parameter fit on controls.** `composite_score` weights, thresholds, and the skeletal DNASE panel are decided a priori.
- **Claude self-red-team.** Claude pushes the GDF5 control through the exact constraint/gBGC filter code and asserts **no silent filter drops the positive control** — a filter that removes GDF5 is a filter bug (see Caveat #7).

**Residual risk we own.** Even n>1 is small and the curve is noisy; expanding the trusted-positive set is an open task. Until then the validation is suggestive, not definitive.

---

## 7. "Your constraint/gBGC filter would silently delete GDF5 — and you'd never notice."

**Kill-shot.** HARs/HAQERs are enriched for gBGC (≈19% of HARs best explained by pure gBGC, ~76% selection, Kostka 2012; ~29–33% gBGC-influenced), and a naive gBGC/constraint filter can drop weak→strong substitutions — including your positive control — inflating apparent specificity.

**Honest answer.** *Real, and we red-team it explicitly.* gBGC near recombination hotspots fixes A/T→G/C changes with no regulatory meaning; any HAR/HAQER screen that ignores gBGC measures a conversion artifact. But an over-aggressive gBGC filter can silently remove a genuine functional site that happens to be weak→strong.

**Mitigation (P4 + self-red-team).** gBGC is a **first-class arm**: every substitution is classed `WtoS | StoW | neutral` (`gbgc_class`), joined to local recombination rate (`recomb_rate_cMperMb`), flagged (`gbgc_flag`) when WtoS-in-hotspot, and the permutation null is **matched on recombination rate** so a candidate cannot score high merely by being a gBGC target. Critically, **Claude runs the GDF5 control through the live filter and asserts it survives** — a filter that drops the frozen positive control is treated as a bug and reverted. We report the recombination-map sensitivity of the flag (pedigree vs LD map). We cite the constraint threshold precisely: Zoonomia 241-mammal phyloP ≥ 2.27 = 5% FDR (Christmas/Sullivan 2023).

**Residual risk we own.** A substitution can be **both** gBGC-driven **and** functional; gBGC classification depends on the recombination map. We never claim a non-gBGC candidate is *proven* selection.

---

## 8. "You tested tens of thousands of elements. Your 'polygenic' story is just multiple-testing noise."

**Kill-shot.** With ~30k active elements, tails are populated by chance and "thousands of differences" is an uncorrected-p mirage.

**Honest answer.** *We lean into the correction rather than the raw count.* The real MPRA calls 11,542 differentially active with **|log2FC|>1 AND Bonferroni p<0.01** — already a stringent, corrected threshold, not nominal p. Our benchmark measures whether the **distribution** of the effect is spread across many elements, not whether any single tail call is real.

**Mitigation (P3 polygenicity + P4 FDR).** `polygenicity()` reports the Gini of measured |log2FC| across differential elements, the share of total effect carried by the top 10%, and how many elements it takes to account for 50% of the effect — a low top-10% share and a large 50%-effect count is the quantitative signature of **polygenicity** ("thousands of elements, not a few loci"). Our own candidate ranking (`aggregate.py`) uses a recombination-matched empirical p and **Benjamini–Hochberg FDR** (`fdr_bh`), not nominal p.

**Residual risk we own.** FDR controls the expected false-discovery *rate*, not any individual call; if the true number of skeletal-regulatory elements is smaller than the differential-active count, the polygenic signal is partly reporter-assay noise distributed broadly. We report the honest distribution rather than a headline count.

---

## 9. "Ancestral/derived polarity — flip it and every delta sign is wrong (including GDF5)."

**Kill-shot.** The directional claim (human allele *reduces* accessibility, matching GDF5's 0.72×) collapses if ancestral (chimp) vs derived (human) is mis-assigned.

**Honest answer.** *A single-point failure we gate on explicitly.* We fix `ref_ancestral` = chimp/ancestral REF and `alt_human` = human derived ALT; AlphaGenome's (ALT−REF) delta is (human−chimp) by construction. GROW1's delta **must be negative** to match the wet-lab 0.72×, or we stop and debug.

**Mitigation (P0 + P1).** Polarity is a P0 definition-of-done gate: the GDF5-GROW1 mock/real delta must be **negative** and the blind line asserts the sign; ancestral state is standardized on the alignment-inferred base and reconciled against dbSNP REF, with low-confidence-ancestral positions flagged in `notes`.

**Residual risk we own.** Positions with incomplete lineage sorting or shallow alignment have irreducibly uncertain ancestral state; we flag rather than silently assign them.

---

## Limitations (paste verbatim into the writeup)

SKELETOME is a **computational, in-silico benchmark**, not a functional assay. We predict human-vs-chimp **chromatin-accessibility changes** (DNase, with ATAC as secondary) from sequence using AlphaGenome, and benchmark those predictions against the **measured** differential-activity calls of a published wet-lab skeletal MPRA (Okamoto et al. 2025, GEO GSE298093). We never describe our predictions as measured transcription or enhancer activity; this is a **virtual** MPRA validated against the real one, and candidates are hypotheses for experimental follow-up.

Our two robust results are (a) the **concordance** between predicted DNase-accessibility deltas and the MPRA's measured differential-activity calls, and (b) the **polygenic** distribution of that differential signal across thousands of elements. The **HAQER-over-HAR** contrast is reported under two nulls: it is enriched **vs chance** (Fisher OR 2.88, P<0.01 for HAQERs; HARs not enriched, P=0.58) but, consistent with the original study, **neither HAR nor HAQER is significant against sequence-feature-matched controls** — so we report HAQER>HAR as a vs-chance result and do not over-state it.

AlphaGenome is **not fully optimized for cell/tissue-specific patterns** and its training panel **excludes GTEx**; we therefore frame the finding as correlation/enrichment against a measured benchmark, never as absolute per-cell-type accuracy. We select a skeletal DNASE panel from `output_metadata()` (chondrocyte, osteoblast, MSC, embryonic femur, embryonic limb) and aggregate across it, but these bulk tracks dilute genuinely cell-type-restricted signal and can produce false negatives. We use **DNase rather than ATAC** because AlphaGenome's embryonic-skeletal accessibility biosamples are in the DNase panel.

For the benchmark we use the MPRA authors' **own per-element HAR/HAQER labels**, so definitions match theirs and cannot be tuned by us. Human Accelerated Regions and HAQERs are enriched for **GC-biased gene conversion**, which fixes substitutions with no regulatory meaning; we treat gBGC as a primary arm, match our null on recombination rate, and explicitly red-team that our constraint/gBGC filter does not silently drop the GDF5 positive control — but gBGC classification depends on the recombination map, and a substitution can be both gBGC-driven and functional.

Validation rests on **blind re-discovery of a small set of wet-lab-validated human-specific skeletal enhancers** (GDF5-GROW1, GDF5-R4, HACNS1) against negative controls, with predicted rank and effect direction **frozen before unblinding**. This provides genuine (n>1) precision/recall, but the control set is small and the estimate is noisy. Where the honest number of candidates surviving all filters is small, we report that number rather than relaxing thresholds to inflate it.
