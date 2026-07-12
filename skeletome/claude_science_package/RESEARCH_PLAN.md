# SKELETOME — RESEARCH_PLAN.md (v2)

**A VIRTUAL skeletal MPRA, benchmarked against the real one.**
Research-track entry — "Build From the Bench," Built with Claude: Life Sciences. All-public-data, open-source, reproducible. Deliverable is a FINDING / reproducible ANALYSIS, not a builder tool.

> **One-sentence finding.** *AlphaGenome's in-silico human-vs-chimp DNase predictions reproduce the Okamoto/Capellini 2025 skeletal MPRA — recovering the HAQER-over-HAR contrast and the polygenic distribution of skeletal regulatory divergence from sequence alone — and, at base resolution, nominate the causal substitutions the region-level assay cannot resolve, blindly recovering the GDF5/GROW1 human-specific skeletal enhancer.*

> **Honest hook.** This is a **virtual** skeletal MPRA. We do **not** call our predictions "an MPRA" as if measured. We predict **DNase-accessibility deltas** (human/alt vs chimp/ref) with AlphaGenome and **BENCHMARK** them against the real wet-lab MPRA's differential-activity calls. The robust claims are (a) in-silico↔MPRA **concordance** and (b) recovery of the **polygenic distribution**; HAQER>HAR is reported under **both** nulls with the matched-control caveat stated in the open.

This is a **living backlog**. Each phase is an executable research TASK with Inputs → Steps → Outputs → Definition-of-Done (DoD) → Open Scientific Questions. Claude Science works these top-to-bottom. **P0 (track-locking) and the GDF5 control wiring are the hard gate:** nothing downstream is trusted until the benchmark engine returns numeric deltas on the GDF5 control and the hour-1 go/no-go passes.

**Language discipline (LOCKED):**
- This is a **predicted** differential-accessibility screen benchmarked against a measured MPRA. Never "we ran an MPRA." Always "predicted DNase delta" vs "measured MPRA differential activity."
- Frame the benchmark as **correlation / enrichment / concordance**, NOT absolute accuracy — the AlphaGenome model card warns it is not fully optimized for cell/tissue-specific patterns.
- Report skeletal readouts by their **literal DNase biosample** (chondrocyte / embryonic femur / embryonic limb), never a generic "chondrocyte" unless the track literally is.
- **DNase, not ATAC**, is the skeletal readout (fetal skeletal accessibility is in AlphaGenome's DNase panel; see P0).

**Canonical output.** Every phase writes into ONE row-per-element TSV (`results/elements.tsv`) whose columns are frozen. Do not add, rename, or reorder columns without updating every consumer. The unit of analysis is the **MPRA-tested element** (its measured call is the ground truth we benchmark against); a second, base-resolution table (`results/substitutions.tsv`) holds the per-substitution deltas used in P5.

---

## Benchmark ground-truth summary (the number we are reproducing)

From **Okamoto, Coveney, Ganapathee & Capellini 2025** ("Massively parallel functional screen identifies thousands of regulatory differences in human vs chimpanzee postcranial skeletal development," bioRxiv 2025.10.21.683789; *Genome Biology and Evolution* 10.1093/gbe/evag121; GEO **GSE298093**; code github.com/aokamoto-bio/human_skeletal_evolution_MPRA; **hg38**):
- ~**70,000** elements tested; **30,736 active** (45.2%); **11,542 differentially active** (37.6% of active). Threshold: **|log2FC| > 1 & Bonferroni p < 0.01**.
- **HAQER**-overlapping active regions: **19/30 = 63% differential** (Fisher OR **2.88**, P < 0.01, ENRICHED vs chance).
- **HAR**-overlapping active regions: **19/57 = 33% differential** (P = 0.58, NOT enriched vs chance). Baseline = 37.6%.
- **Polygenic**: "thousands of elements, not a few loci."
- **HONESTY CAVEAT (must state):** vs sequence-feature-**matched** controls, NEITHER HAR nor HAQER was significant (Fisher P > 0.05). The HAQER>HAR headline rests on the **vs-chance** test. So our robust claims = concordance + polygenic distribution; HAQER>HAR is reported under BOTH nulls.

---

## Phase 0 — Lock the skeletal DNase tracks + wire the GDF5 control + hour-1 go/no-go

**Goal.** Prove the benchmark engine works end-to-end on a single known variant before investing in the full screen, lock the exact skeletal DNase track CURIEs, and hard-wire the GDF5 positive control so it rides through every subsequent filter.

**Inputs.**
- AlphaGenome SDK (hosted, GPU-free). `pip install alphagenome`; `dna_client.create(API_KEY)`. Docs https://www.alphagenomedocs.com/ ; repo https://github.com/google-deepmind/alphagenome. (Avsec et al., *Nature* 28 Jan 2026, 10.1038/s41586-025-10014-0. Non-commercial license. hg38/GRCh38.p13.)
- GDF5 control coordinates (hg38, GRCh38.p14): **GDF5 gene chr20:35,433,347–35,454,749** (end is ...749, NOT ...754). **GROW1 rs4911178 chr20:35,364,817** (derived allele 0.72× enhancer activity, shorter bone, higher OA; Capellini 2017 Nat Genet). **R4 rs6060369** = knee enhancer. GDF5-GROW1 = the HAR-exception positive control to be recovered **blind**.
- Confirmed skeletal DNase biosamples present in AlphaGenome (B1 RESOLVED, YES): chondrocyte (**ENCSR970DQR**), osteoblast (**ENCSR000ELJ**), MSC (H1-derived), embryonic femur (**ENCSR805XIF**), embryonic limb/forelimb/hindlimb DNase.

**Steps.**
1. `pip install alphagenome`; `dna_model = dna_client.create(API_KEY)`.
2. **FIRST CODE STEP — lock tracks.** Call `dna_model.output_metadata(organism=dna_client.Organism.HOMO_SAPIENS)`. AlphaGenome outputs **305 human DNASE + 167 ATAC** tracks (ENCODE-derived; GTEx excluded). Grep the **.dnase** track `biosample_name` / `ontology_curie` for `chondrocyte | osteoblast | mesenchymal | limb | femur`. **Persist matched CURIEs + track names to `config/skeletal_tracks.yaml`** — this is a scientific decision, not a constant. **Aggregate a small skeletal DNase PANEL** (chondrocyte + embryonic femur + limb) rather than one track.
3. Score **GROW1 (rs4911178)** as `genome.Variant(chromosome='chr20', position=35364817, reference_bases=<ancestral>, alternate_bases=<derived>)`; build interval via `variant.reference_interval.resize(dna_client.SUPPORTED_SEQUENCE_LENGTHS['SEQUENCE_LENGTH_1MB'])`; call `dna_model.score_variant(interval, variant, variant_scorers=[CenterMaskScorer over the DNASE panel])`; flatten with `variant_scorers.tidy_scores(...)`. **Primary metric = quantile score; keep raw too.**
   - **Polarity check:** ancestral = REF, derived = ALT ⇒ `ag_dnase_delta` is ancestral→derived. Capellini 2017 measured the derived GROW1 allele at ~**0.72×** activity ⇒ we EXPECT a **negative** delta. A strong positive delta means our ancestral/derived assignment is flipped — stop and fix.
4. Seed the schema with `is_control` = `GDF5-GROW1 | GDF5-R4 | negative | none` plus a handful of `negative` controls (matched non-HAR/HAQER common variants in gene deserts / housekeeping promoters expected to show ~0 skeletal delta).
5. **Claude-science-as-method (capture the artifact):** record the `output_metadata` grep, the chosen CURIEs, and the GROW1 polarity reasoning as a captured reasoning artifact in the run log — this is the "how Claude Science got us there" evidence, not narration.

**Outputs.** `config/skeletal_tracks.yaml` (locked DNASE CURIEs + literal biosample labels); `results/p0_control_smoke.tsv` (GROW1 + R4 + negatives, canonical columns, AG columns only); go/no-go verdict + captured reasoning in run log.

**Definition of Done.**
- AlphaGenome returns a numeric `ag_dnase_delta` (quantile + raw) for GROW1 in ≥1 locked skeletal DNase track.
- GROW1 delta sign is **negative** (derived reduces accessibility), matching Capellini 2017 — OR a documented, understood reason it isn't (flag loudly).
- `config/skeletal_tracks.yaml` lists ≥1 explicitly-named skeletal DNASE track with its literal biosample label and CURIE; a multi-track skeletal panel is defined.
- Go/no-go verdict recorded within hour 1.

**Open Scientific Questions.**
1. **Panel aggregation.** Mean, max, or per-track-then-combine across chondrocyte + femur + limb? Which aggregation best tracks the GROW1 direction+magnitude — freeze it before the screen.
2. **Which skeletal biosample is least-bad?** None are primary growth-plate chondrocytes; rank chondrocyte (ENCSR970DQR) vs embryonic femur (ENCSR805XIF) vs limb by fidelity to GROW1 and to the MPRA calls in P3.
3. **Ancestral allele definition.** Alignment-inferred primate base vs human-major allele — polarity of every delta depends on it. Standardize on the MPRA paper's own human/chimp sequence pair (§P1) so definitions match theirs; reconcile with dbSNP REF.
4. **Quantile vs raw score.** Which correlates better with measured MPRA log2FC at the controls?

---

## Phase 1 — Assemble the benchmark elements (MPRA elements + genome-wide HAR/HAQER)

**Goal.** Build the master element table: every MPRA-tested/active element with **the paper's own HAR/HAQER labels** and its **human + chimp sequences**, in hg38 — the spine of `results/elements.tsv`. Add the standalone zooHAR-312 + HAQER-1581 sets for the broader genome-wide screen.

**Inputs.**
- **Benchmark (primary):** Okamoto/Capellini 2025 — GEO **GSE298093** (19 samples: TC28a2 + CHON002 chondrocyte lines + K562 + plasmid) and code **github.com/aokamoto-bio/human_skeletal_evolution_MPRA**. Provides per-element differential-activity calls (log2FC, Bonferroni p, active/differential flags), the paper's per-element **HAR/HAQER labels**, hg38 element coords, and human/chimp element sequences. (bioRxiv **HTML 403s**; use the PDF + GEO + GitHub.)
- **Genome-wide HAR set:** zooHARs **n=312** (Keough 2023, Science; hg38).
- **Genome-wide HAQER set:** **1,581** native hg38 (Mangan et al. Cell 2022; Lowe-lab **haqer.hg38.bed**, BED5). Almost disjoint from HARs (6/2,733 overlap).
- liftOver chain hg19→hg38 (only if any source is hg19).

**Steps.**
1. From the aokamoto-bio GitHub + GSE298093 supplement, load the **per-element table**: `element_id`, hg38 `chrom/start/end`, `human_seq`, `chimp_seq`, measured `mpra_log2fc`, `mpra_bonf_p`, `mpra_active` (bool), `mpra_differential` (bool, |log2FC|>1 & Bonferroni p<0.01), and the paper's `har_label` / `haqer_label`.
2. **Sanity-reproduce the ground-truth counts** from the loaded table: ~70k tested, **30,736 active**, **11,542 differential**; HAQER 19/30=63%, HAR 19/57=33%. If these don't reproduce from the file, STOP — we are reading the wrong column/definition.
3. For the broader genome-wide screen, load zooHAR-312 and haqer.hg38.bed (1,581) as standalone interval sets with provenance flags (`har_source`, `haqer_source`). Use the paper's labels for the benchmark; the standalone BEDs only for the genome-wide extension.
4. Emit the human(alt) and chimp(ref) sequence pair per element for AlphaGenome scoring (P2). Where the paper gives only element intervals, extract sequences from hg38 with the paper's variant list applied to derive the chimp allele.
5. Confirm the **GDF5/GROW1** control lands in the element table (natural or injected as a flagged control row) so P6 blind validation has a target.

**Outputs.** `results/elements.tsv` (canonical: `element_id, chrom, start_hg38, end_hg38, har_label, haqer_label, har_source, haqer_source, mpra_log2fc, mpra_bonf_p, mpra_active, mpra_differential, is_control`); `results/element_sequences.tsv` (human_seq, chimp_seq per element); liftOver QC log if used.

**Definition of Done.**
- The three headline ground-truth numbers (30,736 active; 11,542 differential; 37.6%) **reproduce** from the loaded file.
- HAQER 19/30 and HAR 19/57 subsets reproduce from the paper's own labels.
- 100% of benchmark rows have hg38 coords + a human/chimp sequence pair + a measured call.
- GDF5 control present (flagged).

**Open Scientific Questions.**
1. **Element sequence source.** Use the paper's exact oligo sequences (best — matches what they measured) or reconstruct from hg38 + variants? Prefer the paper's sequences to keep the benchmark honest.
2. **Paper labels vs standalone BEDs.** Do the paper's HAR/HAQER element labels match zooHAR-312 / haqer.hg38.bed on overlap? Report the concordance; use the paper's labels for the benchmark.
3. **Active-set definition.** Benchmark against all tested, or only the 30,736 active? (Differential is defined on active.) Freeze the tested set before scoring.

---

## Phase 2 — AlphaGenome scoring: human(alt) vs chimp(ref) DNase across the skeletal panel

**Goal.** For every benchmark element, predict the human-vs-chimp differential DNase accessibility from **sequence alone**, at both region level (to benchmark against the MPRA call) and base resolution (for P5 causal nomination).

**Inputs.** `config/skeletal_tracks.yaml` (P0 locked panel); `results/element_sequences.tsv` (human/chimp pairs); AlphaGenome client.

**Steps.**
1. For each element, score **human(alt) vs chimp(ref)** through AlphaGenome CenterMaskScorer over the locked skeletal DNase panel → per-element `ag_dnase_delta_quantile` (primary) + `ag_dnase_delta_raw`, aggregated across the panel per the P0-frozen rule.
2. Also capture **base-resolution DNase deltas** across each element (the per-position ancestral→derived accessibility track) → store the max|delta| position and value per element for P5.
3. Batch politely (non-commercial hosted API); cache all raw responses so the benchmark is reproducible without re-hitting the API.
4. **Claude self-red-team (capture artifact):** re-run the GDF5 control through the exact P1→P2 code path; confirm the control's element still scores and retains its expected negative, skeletal-biased DNase signature. A code path that drops the control is a bug.

**Outputs.** `results/elements.tsv` extended with `ag_dnase_delta_quantile, ag_dnase_delta_raw, ag_max_abs_base_delta, ag_max_abs_base_pos`; cached raw AlphaGenome responses in `cache/`.

**Definition of Done.**
- Every benchmark element has a predicted `ag_dnase_delta_quantile` (+ raw) over the skeletal panel.
- Base-resolution max|delta| + position captured for every element.
- GDF5 control survives the path with expected negative skeletal-biased delta (self-red-team passed, artifact captured).

**Open Scientific Questions.**
1. **Region-level vs base-level for the benchmark.** Does the center-mask region score or the summed base-resolution delta correlate better with measured MPRA log2FC?
2. **Panel disagreement.** Do chondrocyte, femur, and limb DNase tracks agree on direction per element? Where they disagree, which tracks the MPRA?
3. **Sequence-context length.** Is the 1 Mb interval necessary, or does a shorter context change the deltas at short MPRA elements?
4. **Model-card caveat in practice.** How much does the "not fully tissue-specific" warning bite — is skeletal DNase delta distinguishable from a generic-accessibility delta at these elements?

---

## Phase 3 — BENCHMARK: predicted vs measured concordance, HAQER>HAR, polygenic distribution

**Goal.** The core FINDING. Quantify how well the predicted differential-accessibility deltas reproduce the measured MPRA differential-activity calls; recover HAQER>HAR under both nulls; recover the polygenic distribution.

**Inputs.** Fully-scored `results/elements.tsv` (measured MPRA calls + predicted AG deltas).

**Steps.**
1. **Concordance (headline robust claim).** Across all ~30k active elements: (a) **AUROC** of |predicted delta| discriminating `mpra_differential` (1) vs non-differential active (0); (b) **Spearman/Pearson correlation** of `ag_dnase_delta` vs measured `mpra_log2fc` (signed). Report both with CIs. This is correlation/enrichment, **not** accuracy.
2. **HAQER>HAR — vs-chance null.** Within the paper's labeled subsets, compute predicted-differential rate for HAQER vs HAR vs baseline; reproduce the direction (HAQER > baseline > HAR) and test with Fisher/permutation. Compare to measured 63% / 37.6% / 33%.
3. **HAQER>HAR — vs-matched-control null.** Repeat against sequence-feature-matched control elements (GC, length, conservation). **State up front** that in the real MPRA neither HAR nor HAQER was significant under this null; report our in-silico result under BOTH nulls with the same caveat.
4. **Polygenic distribution (headline robust claim).** Show the predicted differential signal is spread across thousands of elements, not concentrated in a few loci — cumulative-contribution / Lorenz-style curve of predicted deltas vs measured, demonstrating the same polygenic shape.
5. **Claude-science artifact:** capture the reasoning that chooses the concordance metric and the two nulls, and the self-check that the benchmark isn't leaking labels (predictions are sequence-only, blind to the measured call).

**Outputs.** `results/benchmark.json` (AUROC, correlations + CIs, HAQER/HAR/baseline rates under both nulls, polygenic curve stats); benchmark figures (ROC, predicted-vs-measured scatter, HAQER>HAR bars under both nulls, polygenic curve).

**Definition of Done.**
- AUROC + signed correlation of predicted vs measured reported with CIs.
- HAQER>HAR direction reported under **both** the vs-chance and vs-matched nulls, with the matched-null caveat stated.
- Polygenic distribution demonstrated (predicted mirrors measured spread).
- No label leakage: predictions confirmed sequence-only.

**Open Scientific Questions.**
1. **Best concordance metric.** AUROC vs correlation vs top-decile precision — which most fairly states "the virtual MPRA reproduces the real one"?
2. **Where does concordance break?** Which element classes (short, low-conservation, gBGC-suspect) drive prediction/measurement disagreement?
3. **HAQER small-n.** 19/30 and 19/57 are tiny; how stable is the recovered contrast under bootstrap? Frame honestly.
4. **Direction vs magnitude.** Does AlphaGenome get the sign of divergence right more often than the magnitude?

---

## Phase 4 — Constraint + gBGC on human-specific substitutions in top elements

**Goal.** Annotate the human-specific substitutions inside the top-concordant / top-differential elements with deep mammalian constraint and gBGC status, so the story separates genuine skeletal-regulatory divergence from GC-biased-gene-conversion artifact.

**Inputs.**
- Zoonomia 241-way phyloP (hg38 bigWig, 9.0 GB — stream by position). Constraint cutoff **phyloP ≥ 2.27 = 5% FDR** (Sullivan/Christmas 2023 Science).
- Zoonomia RoCCs mask.
- Recombination map (deCODE/Halldorsson 2019) for gBGC context.
- gBGC framing: ~**19%** of HARs best explained by **pure gBGC**, **76%** selection; ~**29–33%** gBGC-influenced (Kostka 2012) — state which figure is meant in each sentence.

**Steps.**
1. Extract the per-substitution list inside top elements → `results/substitutions.tsv` (`element_id, chrom, pos_hg38, ref_ancestral, alt_human`).
2. Query phyloP at each `pos_hg38` → `phylop_241`; `constrained = phylop_241 >= 2.27`. Intersect RoCCs → `rocc`.
3. gBGC classification from ancestral→derived: Weak(A/T)→Strong(G/C)=`WtoS`; Strong→Weak=`StoW`; else `neutral` → `gbgc_class`. Join local recombination → `recomb_rate_cMperMb`; `gbgc_flag = WtoS AND elevated recombination`.
4. Report the WtoS fraction and how much of the top-element signal is gBGC-suspect vs constrained-and-non-gBGC.

**Outputs.** `results/substitutions.tsv` extended with `phylop_241, constrained, rocc, gbgc_class, recomb_rate_cMperMb, gbgc_flag`.

**Definition of Done.**
- phyloP + gBGC populated for ≥95% of top-element substitutions (assembly-gap NAs logged).
- WtoS fraction reported with the correct Kostka figure cited (pure-gBGC 19% vs influenced 29–33%).
- Constrained-and-non-gBGC subset of top elements enumerated.

**Open Scientific Questions.**
1. **Which gBGC figure applies here** — pure-gBGC (19%) or gBGC-influenced (29–33%) for our top-element subset?
2. **phyloP 2.27 for regulatory elements** — right operating point (5% FDR is genome-wide) or report at multiple thresholds?
3. **Does gBGC explain the HAQER>HAR contrast** or survive it? Test whether HAQER differential elements are less gBGC-suspect than HAR ones.
4. **Recombination map choice** — current (deCODE) vs historical LD-based — for classifying fixed substitutions.

---

## Phase 5 — Base-resolution causal substitution + OA/BMD/height GWAS intersection

**Goal.** Use AlphaGenome's base resolution to nominate the **causal substitution** the region-level MPRA cannot resolve (max|base delta| within an element), and intersect with skeletal GWAS for supporting annotation (enrichment, not causality).

**Inputs.**
- `results/elements.tsv` + base-resolution deltas (P2); `results/substitutions.tsv` (P4).
- **OA:** Hatzikotoulas 2025 **Nature** — **962 independent associations** (513 novel; 700 effector genes) + GO 2.0 portal genetics-osteoarthritis.com.
- **BMD:** Morris 2019 eBMD, 518 loci. **Height:** Yengo 2022 GIANT, 12,111 SNPs / 7,209 loci.

**Steps.**
1. For each top differential element, take the **max|base delta| position** (P2) as the nominated causal substitution; record `nominated_causal_pos`, `nominated_causal_delta`.
2. Intersect nominated causal substitutions with the OA **962 independent associations** / credible sets, eBMD loci, and height loci → `oa_overlap`, `bmd_overlap`, `height_overlap` + set IDs.
3. Empirical enrichment: nominated-causal overlap rate vs a matched background (MAF/LD/recomb/distance-to-gene); permutation → `gwas_enrich_p`. Report as **enrichment**, not per-variant causality.
4. **Base-resolution win:** show, at ≥1 element (ideally GDF5/GROW1), that the region-level MPRA calls the element differential but only the base-resolution AlphaGenome delta pinpoints WHICH substitution drives it — the resolution the assay lacks.

**Outputs.** `results/substitutions.tsv` extended with `nominated_causal_pos, nominated_causal_delta, oa_overlap, bmd_overlap, height_overlap, gwas_enrich_p`; a causal-nomination summary.

**Definition of Done.**
- Each top differential element has a nominated causal substitution (max|base delta|).
- Nominated set tested for OA/BMD/height enrichment with a single empirical `gwas_enrich_p` each, matched-background scheme documented.
- At least one worked example where base resolution adds information the region-level MPRA cannot (causal substitution pinpointed).

**Open Scientific Questions.**
1. **Causal criterion.** Single max|delta| base, or a contiguous high-delta window? Multi-substitution elements may need joint scoring.
2. **Which GWAS is the right target** — OA (developmentally relevant), eBMD, or height? Report all three.
3. **Which cartilage eQTL enables real coloc** (GTEx has no cartilage) if we want to go beyond enrichment to a mechanistic statement?
4. **Matched-background sensitivity** of `gwas_enrich_p` to the covariate set.

---

## Phase 6 — BLIND GDF5 validation + Claude self-red-team + demo + one-command reproduce

**Goal.** Package the virtual-MPRA benchmark into a judge-ready, reproducible artifact, and validate the whole pipeline by **blind re-discovery of the GDF5/GROW1** human-specific skeletal enhancer.

**Inputs.** Final `results/elements.tsv` + `results/substitutions.tsv` + `results/benchmark.json`; the GDF5 control anchors.

**Steps.**
1. **BLIND validation.** BEFORE inspecting the control's rank, FREEZE (with timestamp) the predicted differential rank + effect direction of GDF5/GROW1 (and negatives). Then reveal: confirm GROW1 ranks high among predicted-differential elements with the expected **negative** DNase direction, recovering it BLIND — the HAR-exception positive control.
2. **Claude self-red-team (capture artifact):** re-run the constraint/gBGC filter (P4) and confirm it does NOT silently drop the GDF5 positive control; if it would, that is a filter bug to fix and document. Capture this as a reasoning artifact.
3. **Claude motif/base reasoning:** for GDF5 and the top nominated causal substitutions, reason over the base-resolution deltas (which motif is created/destroyed), generate a per-candidate mechanistic hypothesis, and **cross-check each against live literature** (PubMed/consensus); tag any with no support as speculative.
4. **Reproduce.** `run.sh` runs P0→P5 end-to-end from public data on a fresh machine (pinned versions, cached AlphaGenome responses + the small MPRA/label files, API-key env var; phyloB bigWig streamed, never fully downloaded).
5. **Deliverables:** 3-min demo video; open repo/notebook; **100–200 word summary**; figures (predicted-vs-measured concordance, HAQER>HAR under both nulls, polygenic curve, GDF5 blind-recovery). Writeup states the honesty caveats verbatim (predicted-not-measured; matched-control; correlation-not-accuracy).

**Outputs.** `run.sh`; `figures/`; `results/control_validation.json` (frozen predictions + revealed rank/direction + freeze timestamp); motif-hypothesis table with citations; 100–200 word summary; README; 3-min demo.

**Definition of Done.**
- `run.sh` runs clean on a fresh checkout with only an API key + public downloads.
- GDF5/GROW1 recovered BLIND: top-ranked among predicted-differential with correct (negative) direction; freeze timestamp makes blindness auditable.
- Self-red-team confirms no filter drops the control.
- Every top nominated causal substitution has a motif-level hypothesis with a literature citation or an explicit "speculative" tag.
- Submission bundle complete (video + repo + 100–200 word summary), honesty caveats stated.

**Open Scientific Questions.**
1. **Blind-set size.** GDF5 is n≈1–2 trusted positives; can we expand with other validated human-specific skeletal enhancers to make blind precision/recall less noisy?
2. **Headline framing.** If concordance is strong, the hero is "virtual MPRA reproduces the real one + adds base resolution"; if HAQER>HAR is fragile under the matched null, lead with concordance + polygenic + GDF5. Decide from the actual numbers.
3. **Generalization.** Does swapping `skeletal_tracks.yaml` re-run the benchmark on a non-skeletal tissue, showing this is a general in-silico-vs-MPRA framework, not a GDF5-overfit demo?

---

## Cross-cutting invariants (every phase)
- **Predicted, not measured.** We predict DNase deltas and BENCHMARK them against the real MPRA; never "we ran an MPRA."
- **Correlation/enrichment, not accuracy** — the AlphaGenome model card caveat is stated wherever a benchmark number appears.
- **DNase, not ATAC**, for skeletal context.
- **HAQER>HAR reported under BOTH nulls** with the matched-control caveat (neither significant vs matched controls in the real MPRA).
- **Robust claims = concordance + polygenic distribution.**
- The **GDF5 control** must survive every filter; a filter that drops it is a bug; its rank/direction are frozen before looking.
- **Claude-science-as-method** artifacts (track-locking grep, polarity reasoning, self-red-team, causal/motif reasoning) are captured, not narrated.
- Canonical TSV columns are frozen; all code reads/writes exactly those names. hg38 throughout.
