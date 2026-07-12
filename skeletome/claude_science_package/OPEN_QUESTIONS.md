# SKELETOME — Open Questions (research backlog)

The 40 questions the package build surfaced, deduplicated and prioritized. This is the **"keep researching" list** for Claude Science. Work the BLOCKERS first — they gate whether the results can be trusted at all. Most are *live checks* (query the API, fetch the file), not literature reviews.

Legend: 🔴 BLOCKER · 🟠 freeze-before-scoring · 🟡 data-access verify · 🟢 stretch/mechanism

---

## 🔴 BLOCKERS — resolve before trusting any result

**B1. Does AlphaGenome actually expose a skeletal-lineage accessibility track?**
Enumerate `RECOMMENDED_VARIANT_SCORERS` / `output_metadata` on the live client. Confirm whether genuine embryonic-limb (UBERON:0002101), MSC (CL:0000134), or osteoblast/MG63 ATAC/DNASE tracks exist in AlphaGenome's output space — or whether the "skeletal" readout is a proxy tissue. **This decides whether `ag_atac_delta`/`ag_dnase_delta` can be labeled skeletal at all**, and whether the neural-vs-skeletal contrast is achievable on AlphaGenome alone (locked decision 1 requires the pipeline to be complete without ChromBPNet). If no skeletal track exists, either relabel to the literal track or promote ChromBPNet limb/MSC/MG63 to primary and revise decision 1.

**B2. Allele polarity — the sign of every downstream delta depends on it.**
Confirm the ancestral vs derived alleles for the control set against dbSNP + the primary papers: GDF5-GROW1 (rs4911178), GDF5-R4 (rs6060369), HACNS1. These are currently TODO placeholders. Capellini 2017 says the derived GROW1 allele *reduces* enhancer activity (~0.72×) → the frozen prediction is a **negative** delta for that row. Then verify the Whalen/Pollard GSE110760 table polarity row-by-row: for a human-specific fixed difference the hg19 reference base normally equals the human/derived allele, so ancestral = the chimp base — confirm this holds before trusting `ref_ancestral`→`alt_human`.

**B3. Freeze the `composite_score` formula and thresholds BEFORE looking at GDF5.**
Commit to disk, with zero free parameters fit on the controls: the composite weighting (constraint / skeletal effect size / skeletal-specificity / non-gBGC), `SKEL_EFFECT_MIN`, the `skeletal_specific` rule ("high skeletal AND muted neural" — absolute cutoff? skeletal-minus-neural contrast? ratio? quantile?), and `LAMBDA_NEURAL`. Circularity is the #1 validity attack — the GDF5 recovery is only meaningful if nothing was tuned to produce it. Report candidate-count sensitivity to each threshold.

**B4. Is GDF5-GROW1 actually inside the HAR substitution universe?**
Check whether the GROW1/R4 substitutions fall within a called zooHAR + the Whalen/Pollard human-specific substitution set. If a control is *not* in the natural universe, it can't be "re-discovered" by the same pipeline — you'd need a documented explicit spike-in path (which weakens the blind claim). Resolve the control-set design accordingly.

---

## 🟠 Method parameters to freeze (pre-register, then don't touch)

- **Recombination map for the gBGC null.** deCODE/Halldorsson 2019 pedigree map (current recombination) vs an LD-based population map (historical average that actually drove ancestral gBGC). The historical map is arguably more appropriate for classifying *fixed* substitutions. Test `gbgc_flag` sensitivity to the choice. Add the chosen map to the manifest (it's a not-yet-listed download).
- **`gbgc_flag` thresholds.** Recombination-rate percentile cutoff + hotspot-proximity window (defaults: 10 cM/Mb, 1 kb). Run a P4 sensitivity sweep: candidate count vs threshold. Confirm GDF5 itself is not in a high-recombination window that would flag it.
- **Permutation-null granularity.** `N_RECOMB_BINS=10` with qcut may leave sparse strata at real n (~3k). Verify bins are well-populated; decide whether to additionally match on GC content / baseline accessibility, not just recombination rate.
- **ATAC vs DNASE as primary readout.** Which better matches reporter-enhancer behavior at GDF5-GROW1? One track, the max, or a weighted combination? Calibrate against controls.
- **Neural comparator choice.** Which neural biosample(s) represent the historical HAR-assay context (fetal brain / neural crest / NPC)? Single tissue or aggregate? This sets `skeletal_specific`.
- **Multi-engine combination.** When AlphaGenome + ChromBPNet both present, current composite takes max magnitude. Consider requiring **concordant sign** across engines, or reporting per-engine agreement as a confidence field (esp. GDF5-GROW1, where both should reproduce the ~0.72× reduction).
- **AlphaGenome mechanics (first `--full` run):** confirm the `AggregationType` member for a REF→ALT delta; confirm `score_variant` `raw_score` sign is ALT-minus-REF (the blind check depends on it); confirm the interval-resize width/constant for the installed package version; confirm whether `score_variant` accepts `ontology_terms` to restrict tracks (else neural vs skeletal use the same tracks and the contrast is meaningless → switch to `predict_variant` + manual REF/ALT track diffing).
- **HACNS1 canonical row.** Replace the placeholder hg38 coordinate (chr2:235,865,331, correct GBX2 locus) with the exact human-specific substitution from zooHARs Table S1 / liftOver of Prabhakar 2008. Decide: single most-accelerated site, or multiple rows?

## 🟡 Data-access loose ends (verify locators)

- **zooHARs Table S1:** canonical redistributable source — the paywalled science.org supplementary file vs the open **Zenodo 7478724** archive. Use Zenodo for `har.bed`.
- **Whalen/Pollard GSE110760:** which TSV inside `GSE110760_RAW.tar` enumerates substitutions with chrom/pos/ref/alt **and** an explicit ancestral allele?
- **GO 2.0 OA credible sets:** the `genetics-osteoarthritis.com` portal path 404'd — find the real download (GWAS Catalog GCST + FTP, the paper's Data Availability/Zenodo, or the `hmgu-itg/Genetics-of-Osteoarthritis-2.0` GitHub). Confirm the 962 SuSiE sets and the credible-set TSV columns for the membership join.
- **Morris 2019 eBMD:** GCST006979 showed "Full Summary Statistics: Not available" — confirm the right accession for harmonised GRCh38 sumstats, or pull from **GEFOS** (gefos.org).
- **ENCODE limb ChromBPNet model:** ENCSR138OCE's annotation page listed no downloadable files — locate the actual `chrombpnet_nobias.h5` (under source experiment ENCSR818JGZ, a sibling file accession, or ENCSR858EVI).
- **pandas version:** package tested on pandas 3.0; if Claude Science runs 2.x, re-run tests (object-dtype `.map` / `is_bool_dtype` differ). Consider pinning `pandas>=2.1`.

## 🟢 The central empirical question + mechanism stretch

- **★ The headline question:** After controlling for gBGC (recombination-matched null + `gbgc_flag` exclusion), is there **any residual skeletal-regulatory signal** in the WtoS-in-hotspot HAR subset — or does the apparent acceleration collapse to conversion artifact? This determines whether the story is *"we found N candidates"* or *"the field's HARs are overwhelmingly gBGC."* Both are publishable; know which one you have.
- **Robustness:** does the candidate list survive three null constructions (matched-permutation, parametric, empirical-Bayes local-FDR)?
- **Cartilage eQTL for real colocalization:** GTEx has no cartilage. Find a chondrocyte/cartilage eQTL resource (GO 2.0 companion? a published chondrocyte eQTL study?) to upgrade the GWAS arm from enrichment to coloc for headline hits.
- **Cell-type-specific modeling (To-2024, E-MTAB-14385):** does training on the embryonic skeletal multiome recover growth-plate chondrocyte signal that the bulk limb track dilutes? Which bulk biosample least-badly proxies chondrocytes?
- **AlphaGenome determinism:** are hosted-API scores byte-stable across calls so `run.sh` can claim reproducible regeneration, or must you pin a tolerance and cache raw responses as the canonical artifact?
