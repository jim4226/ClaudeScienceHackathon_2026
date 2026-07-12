# PROJECT_CONTEXT.md — SKELETOME v2 (standing project knowledge for Claude Science)

> This is the source-of-truth briefing doc. Every agent and every session aligns to this. If something here conflicts with an older note, this wins. TRACK: **Research ("Build From the Bench")** — the deliverable is a **FINDING / reproducible ANALYSIS**, not a builder tool or app. Foreground the biological question, the public datasets/tools, the discrete reproducible result, and HOW CLAUDE SCIENCE GOT US THERE.

---

## 1. The v2 thesis (one paragraph)

Humans and chimpanzees differ in postcranial skeletal form (limb proportions, joint shape, pelvis/gait). Okamoto, Coveney, Ganapathee & Capellini (2025) ran a **real massively parallel reporter assay (MPRA)** in human vs chimpanzee skeletal cell contexts and measured **thousands** of regulatory differences — and reported that human accelerated regions (HARs) were **not** especially predictive of differential activity, while the story is broadly **polygenic**. We ask whether a **sequence-only deep-learning model of regulatory activity — AlphaGenome (DeepMind, Nature 28 Jan 2026)** — can, from the human and chimp sequences ALONE, reproduce that wet-lab benchmark: predict per-element **DNase-accessibility deltas** (human vs chimp) across a fetal-skeletal DNase panel and recover (a) the concordance with the measured differential-activity calls, (b) the polygenic distribution, and (c) the HAQER-over-HAR contrast. Then, where the region-level MPRA cannot resolve WHICH base drives a difference, we use AlphaGenome at **base resolution** to nominate the single causal substitution — and validate the whole pipeline **blind** by recovering the known GDF5/GROW1 human-specific skeletal enhancer.

## 2. One-sentence finding (the hero)

> "AlphaGenome's in-silico human-vs-chimp DNase predictions reproduce the Okamoto/Capellini 2025 skeletal MPRA — recovering the HAQER-over-HAR contrast and the polygenic distribution of skeletal regulatory divergence from sequence alone — and, at base resolution, nominate the causal substitutions the region-level assay cannot resolve, blindly recovering the GDF5/GROW1 human-specific skeletal enhancer."

**HOOK (honest):** a **VIRTUAL skeletal MPRA, validated against the real one.** We never call our predictions "an MPRA" as if measured. We predict DNase-accessibility deltas and **benchmark** them against the real wet-lab MPRA differential-activity calls.

## 3. The biological question

What regulatory DNA changes reshaped the human postcranial skeleton relative to our closest living relative? Concretely: across the elements the Capellini group functionally tested, can differential regulatory activity be predicted from human vs chimp sequence alone; is the signal concentrated in named acceleration classes (HARs, HAQERs) or spread polygenically; and at the elements that matter most, which specific human-derived substitution is causal?

## 4. Why the benchmark framing (turning "HARs aren't predictive" into our validation set + spine)

The Capellini 2025 result is often read as a **negative** for HARs. We invert it into an **asset**: their ~70k tested elements with per-element **measured** active / differentially-active calls and human+chimp sequences form a large, quantitative, public **ground-truth benchmark**. A sequence-only model that reproduces those calls has demonstrated real predictive skill on primate skeletal regulatory divergence — and can then go *beyond* the region-level assay to base resolution. So the MPRA is not our competitor; it is our **labeled test set and our spine**. Their "HARs not especially predictive / it's polygenic" becomes a **specific, falsifiable target** we try to reproduce in silico.

## 5. The honest register (non-negotiable framing rules)

State these plainly in the repo, the write-up, and the demo. They make the work credible, not weaker.

- **Predicted, not measured.** We output AlphaGenome **DNase-accessibility deltas**, not transcriptional output. We do not claim to have measured enhancer activity. We benchmark predictions against the real assay's calls.
- **DNase, not ATAC.** AlphaGenome exposes 305 human DNase + 167 ATAC tracks (ENCODE-derived; GTEx excluded). Fetal skeletal accessibility lives in the **DNase** panel. Use DNase for skeletal context; ATAC is at most a robustness check.
- **Correlation / enrichment, not absolute accuracy.** The AlphaGenome model card warns it is not fully optimized for cell/tissue-specific patterns. We frame the benchmark as **concordance / correlation / enrichment**, never as absolute per-element accuracy.
- **Use THEIR HAR/HAQER labels.** For the benchmark, use the MPRA paper's own per-element HAR/HAQER labels (from their GitHub) so definitions match theirs exactly. Use the standalone zooHAR-312 / HAQER-1581 BEDs only for the broader genome-wide screen.
- **The matched-control caveat (must state).** Versus sequence-feature-MATCHED controls, NEITHER HAR nor HAQER reached significance (Fisher P>0.05). The HAQER>HAR headline rests on the **vs-chance** test. Therefore our ROBUST claims are (a) in-silico <-> MPRA concordance and (b) the polygenic distribution. HAQER>HAR is reported under **BOTH** nulls (vs-chance AND vs-matched-control), with the caveat attached.

## 6. The verified anchor facts (do not drift from these)

**Benchmark data.** Okamoto, Coveney, Ganapathee & Capellini 2025, "Massively parallel functional screen identifies thousands of regulatory differences in human vs chimpanzee postcranial skeletal development." bioRxiv 2025.10.21.683789; Genome Biology and Evolution, doi 10.1093/gbe/evag121. GEO **GSE298093** (public; 19 samples: TC28a2 + CHON002 chondrocyte lines + K562 bone-marrow lymphoblast + plasmid). Code: github.com/aokamoto-bio/human_skeletal_evolution_MPRA. ~70k elements tested; **30,736 active (45.2%)**; **11,542 differentially active (37.6% of active)**; threshold |log2FC|>1 & Bonferroni p<0.01. Assembly **hg38**.

**Key MPRA result.** HAQER-overlapping active regions **19/30 = 63%** differential (Fisher OR **2.88**, P<0.01, ENRICHED vs chance). HAR-overlapping **19/57 = 33%** (P=0.58, NOT enriched). Baseline **37.6%**. Polygenic ("thousands of elements, not a few loci"). Caveat as in §5: vs matched controls neither class is significant.

**Engine.** AlphaGenome (Google DeepMind; Nature 28 Jan 2026, doi 10.1038/s41586-025-10014-0). Peer-reviewed. Hosted no-GPU API (`pip install alphagenome`; `dna_client.create(API_KEY)`). Predicts 1-bp ATAC & DNase; ref-vs-alt variant scoring (CenterMaskScorer; quantile score primary). Non-commercial license. hg38/GRCh38.p13.

**Track availability (B1 — RESOLVED, YES).** AlphaGenome outputs 305 human DNASE + 167 ATAC tracks (ENCODE-derived; GTEx excluded). Skeletal biosamples present: chondrocyte (ENCSR970DQR), osteoblast (ENCSR000ELJ), MSC (H1-derived), embryonic femur (ENCSR805XIF), embryonic limb/forelimb/hindlimb DNase. **Use DNASE, not ATAC.** FIRST CODE STEP: `output_metadata(HOMO_SAPIENS)` -> grep `.dnase` biosample_name / ontology_curie for chondrocyte|osteoblast|mesenchymal|limb|femur to lock exact CURIEs. **Aggregate a small skeletal DNase panel** (chondrocyte + embryonic femur + limb) rather than a single track.

**Acceleration sets.** HARs: zooHARs n=312 (Keough 2023, Science). HAQERs: 1,581 native hg38 (Mangan et al., Cell 2022; Lowe lab `haqer.hg38.bed` BED5). Almost disjoint from HARs (6/2,733 overlap). Benchmark uses the MPRA paper's own labels; genome-wide screen uses the standalone BEDs.

**Constraint / gBGC.** Zoonomia 241-mammal phyloP >= 2.27 = 5% FDR (Sullivan/Christmas 2023, Science). gBGC: ~19% of HARs best explained by pure gBGC (76% selection); ~29-33% gBGC-influenced (Kostka 2012) — always state which figure you mean.

**GDF5 positive control (hg38, GRCh38.p14).** GDF5 chr20:35,433,347-35,454,749 (end is ...749, NOT ...754). rs4911178 GROW1 chr20:35,364,817 (derived allele 0.72x enhancer activity, shorter bone, higher OA; Capellini 2017, Nat Genet). rs6060369 = R4 enhancer (knee). GDF5-GROW1 is the HAR-exception positive control we recover BLIND.

**GWAS overlays.** OA = Hatzikotoulas 2025, NATURE — **962 independent associations** (not "credible sets"; 513 novel; 700 effector genes) + GO 2.0 portal genetics-osteoarthritis.com. BMD = Morris 2019 eBMD, 518 loci. Height = Yengo 2022 GIANT, 12,111 SNPs / 7,209 loci. Precedents to cite: Whalen & Pollard 2023 (neural HAR-MPRA, GEO GSE110760); Kun 2023 (skeletal-proportion loci HAR-enriched, enrichment-only). Optional base-resolution cross-check: ENCODE ChromBPNet DNase-seq skeletal models (limb ENCSR138OCE/ENCSR858EVI; MSC ENCFF640AVL; MG63 ENCFF841SWM).

## 7. Pipeline phases (v2)

- **P0** — `output_metadata()` -> lock skeletal DNase track CURIEs + wire GDF5 control + hour-1 go/no-go.
- **P1** — Assemble elements: MPRA ~30k tested/active with their HAR/HAQER labels + human/chimp sequences from GSE298093 / GitHub; plus standalone zooHAR-312 + HAQER-1581 for the genome-wide screen. hg38; liftOver as needed.
- **P2** — AlphaGenome score human(alt) vs chimp(ref) DNASE across the skeletal panel -> per-element predicted differential accessibility (quantile + raw) + base-resolution deltas.
- **P3** — BENCHMARK: concordance of predicted vs measured differential activity (AUROC / correlation across ~30k elements); recover HAQER>HAR under vs-chance AND vs-matched-control nulls; recover the polygenic distribution.
- **P4** — Constraint + gBGC on human-specific substitutions in top elements.
- **P5** — Base-resolution causal substitution (max|delta|) + OA/BMD/height GWAS intersection.
- **P6** — BLIND GDF5/control validation + Claude self-red-team + demo + one-command reproduce.

## 8. The Research-track deliverable + Claude-Science-as-method

**Deliverable (Research track).** A FINDING backed by a reproducible analysis via Claude Science: a **3-min demo video** + an **open repo/notebook/write-up** + a **100-200 word summary**. Due **2026-07-13, 9pm ET**. The FINDING is the hero throughout. Never pitch this as an app, tool, or product.

**Claude-Science-as-method (the 25% Claude Use axis + the Research-track "show how Claude Science got you there" ask).** Claude discovers the datasets, writes and unit-tests the code, runs `output_metadata` to lock the tracks, executes the benchmark, and **self-red-teams** the constraint/gBGC filter that would silently drop its own GDF5 positive control — then reasons over base-resolution deltas to nominate causal variants cross-checked against live literature. Surface these as **captured reasoning artifacts** (saved logs, decision notes, the red-team writeup), not as narration.

## 9. Judging map (Impact 25 / ClaudeUse 25 / Depth 20 / Demo 30)

- **Impact (25):** primate skeletal evolution + human-disease relevance (OA/BMD/height); a reusable in-silico-vs-wet-lab benchmarking recipe.
- **Claude Use (25):** Claude Science as the method — dataset discovery, code+tests, metadata locking, benchmark execution, self-red-team, causal-variant reasoning, all as captured artifacts.
- **Depth (20):** ~30k-element concordance benchmark under two nulls; base-resolution causal nomination; constraint/gBGC analysis; blind positive-control recovery.
- **Demo (30):** the virtual-MPRA-validated-against-the-real-one narrative, ending on the blind GDF5/GROW1 recovery; honest register on screen.

## 10. Positive / negative control policy

- **Positive control (blind):** GDF5/GROW1 human-specific skeletal enhancer (chr20 coords in §6). Must be recovered by the pipeline WITHOUT being special-cased. It is a HAR-exception, so it also stress-tests any HAR-only assumption.
- **Negative controls:** sequence-feature-matched control elements (the MPRA's own matched set) and scrambled / non-skeletal DNase tracks. Predicted deltas should NOT concentrate there.
- **Self-red-team gate:** before trusting any constraint/gBGC filter, verify it does not silently drop GDF5/GROW1 or other known positives. A filter that removes its own positive control is rejected or flagged, not applied silently.

## 11. How to behave while iterating

- Match the SPINE facts, numbers, and column names EXACTLY. If a number here differs from memory, the SPINE wins; do not "round" or paraphrase coordinates (GDF5 end is ...749).
- Keep the honest register in every artifact: predicted-not-measured, DNase-not-ATAC, correlation-not-accuracy, their-labels-for-the-benchmark, the matched-control caveat.
- The FINDING is the hero. Never drift into tool/app/product framing.
- Prefer a small aggregated skeletal DNase panel over a single track; report both quantile and raw deltas.
- Report HAQER>HAR under BOTH nulls with the caveat; lead with the two robust claims (concordance, polygenic).
- Capture reasoning as artifacts (logs, decision notes, red-team writeup) rather than narrating after the fact.
- One-command reproduce is a first-class requirement, not a nicety.
- When a filter, threshold, or definition could drop a known positive, self-red-team first.
