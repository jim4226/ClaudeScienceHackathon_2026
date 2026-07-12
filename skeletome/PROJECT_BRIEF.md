# SKELETOME
### An In-Silico Skeletal Variant-Effect Screen for Human Accelerated Regions
*Built with Claude: Life Sciences — Research Track (Gladstone Institutes). Submission due Mon 2026-07-13, 9:00 PM ET.*

> Produced by a Claude Code research workflow (6 recon agents → design → 4-lens adversarial critique → hardened plan), run 2026-07-07.

---

## One-liner
The first in-silico skeletal screen of Human Accelerated Regions: we predict what every human-specific HAR substitution does to regulatory accessibility in **bone and cartilage cell contexts**, filter to bases mammals conserved for 100M years, flag the gBGC-confounded majority, and cross the genuinely skeletal-regulatory minority with osteoarthritis genetics — **blindly re-discovering the GDF5/GROW1 arthritis enhancer as the positive control.**

## Verdict: **GO — with changes**
The core thesis survived an adversarial prior-art sweep and is empirically true: **every published HAR-MPRA was run in neural cells; ENCODE contains zero skeletal ATAC-seq and only 3 legacy skeletal DNase experiments.** Every dataset has a verified public locator. There is a checkable positive control (GDF5/GROW1) that no sequence-to-function model has ever been shown to recover. Demo (30%) and Claude Use (25%) — 55% of the score — grade strong-to-excellent.

**The mandatory changes (all cheap inside the window):**
1. **Make gBGC a first-class headline arm.** ~19–33% of HARs are GC-biased gene conversion, not selection (Kostka 2012). This is the #1 reviewer kill-shot. Converting it into the discriminator ("most HARs are gBGC noise; here are the few that look genuinely skeletal-regulatory") turns the fatal flaw into the story.
2. **Rename "in-silico MPRA" → "in-silico variant-effect screen."** State in methods: it predicts model accessibility deltas, not measured transcription.
3. **Invert the engine order: AlphaGenome API is PRIMARY** (no GPU, sub-second, ~3k substitutions trivial). ChromBPNet is gated behind a 2-hour hour-1 smoke test.
4. **Replace n=1 GDF5 with a CONTROL SET** (GDF5-GROW1, GDF5-R4, HACNS1/GBX2) + negative controls; freeze GDF5's rank and effect-direction and report it **blind**.
5. **Demote the GWAS arm** to overlap-enrichment-vs-matched-background (not causality) unless a real skeletal eQTL is named for colocalization.
6. **Foreground Claude as an adversarial scientific collaborator** (self-red-teaming the positive control on camera; reasoning over motif internals), not glue.
7. **Cut from the critical path:** mouse-limb comparator, Enformer/Borzoi/gReLU, the Cactus MAF ancestral path.

*RECONSIDER only if no GPU AND AlphaGenome access both fail — but AlphaGenome alone ships the full demo, so this is not a realistic blocker.*

## Novelty claim (defensible, one sentence)
The first in-silico skeletal variant-effect screen for Human Accelerated Regions — predicting the regulatory impact of every human-specific HAR substitution in skeletal-lineage cell contexts with base-resolution sequence-to-function models, separating gBGC artifacts from candidate-adaptive changes via 241-mammal Zoonomia constraint plus a recombination-rate control, and cross-referencing the genuinely skeletal-regulatory minority with fine-mapped osteoarthritis/BMD/height credible sets — a lineage every prior HAR reporter assay (all neural) skipped, validated by unbiased blind re-discovery of the GDF5/GROW1 human-specific skeletal enhancer.

---

## The pipeline (6 phases)

**Phase 0 — Hour-1 go/no-go + positive-control wiring.** Decide the scoring engine within 2 hours. Run ONE GDF5 substitution (rs4911178, hg38 chr20:35,364,817) ref-vs-alt through AlphaGenome (guaranteed path) AND through one ENCODE ChromBPNet model via kundajelab/variant-scorer (2-hour hard gate). Hardcode GDF5/GROW1 + HACNS1/GBX2 as labeled control rows with an automated smoke test. Freeze the results-table TSV schema.

**Phase 1 — HAR set + human-specific substitutions (hg38).** Download zooHARs (Keough 2023, n=312, hg38) as the only critical-path HAR set. Enumerate human-specific substitutions by liftOver of the Whalen/Pollard 2023 hg19 human-chimp fixed-difference tables (GSE110760). Unit-test the substitution parser on GDF5 first. Spike GDF5/GROW1, GDF5/R4, HACNS1 as labeled control rows so they can't be silently gated out.

**Phase 2 — Constraint + gBGC control (the hardened arm).** Query `hg38.cactus241way.phyloP.bw` over substitution positions only (pyBigWig). Two tiers: phyloP>2.270 (5% FDR, primary) and >1.6 (sensitivity). Intersect with RoCCs mask. **gBGC arm:** classify each substitution weak→strong / strong→weak / neutral, join local recombination rate + hotspot proximity, report the W→S fraction of top movers vs background. Candidate = human-derived differs from ancestral AND phyloP>2.27 AND NOT W→S-in-hotspot. Assert GDF5/GROW1 survives.

**Phase 3 — Skeletal variant-effect scoring (the screen core).** PRIMARY: score all substitutions (ancestral vs derived) through AlphaGenome ATAC/DNASE — GPU-free, minutes. IF hour-1 passed: also score through ENCODE skeletal ChromBPNet models (embryonic limb, MSC, MG63) via variant-scorer (logFC + JSD). NEURAL COMPARATOR for skeletal-specificity. Every column labeled with the literal readout ("predicted DNase change in bulk limb / MG63 / H1-MSC" — never "chondrocyte").

**Phase 4 — Ranking + blind positive-control validation.** Pre-specify the testing unit. Build ONE recombination-matched permutation null; BH-FDR across the declared grid. **BLIND:** freeze thresholds + effect-direction rule before looking; report GDF5's blind rank and blind sign (expect derived allele reduces activity, matching Capellini ~0.72×). Report recovery across the control set + rejection of negative controls → genuine precision/recall (n>1). Claude self-red-teams at each stage.

**Phase 5 — GWAS supporting annotation (demoted, enrichment-tested).** Ingest GO 2.0 (Hatzikotoulas 2025) 962 precomputed SuSiE credible sets directly. Define a HAR-hit as a top non-gBGC skeletal mover overlapping a credible-set variant; compute an empirical overlap-enrichment p-value vs matched background. Explicitly "supporting annotation, not causality." Validate the coordinate chain on GDF5. Coloc against a named cartilage eQTL is stretch-only.

**Phase 6 — Demo assets, Claude-as-scientist moments, reproducibility.** Build the demo artifact against a MOCK 10-row TSV from Day 2; swap real numbers Day 4–5. Claude motif-reasoning arm: name TF motifs created/destroyed for top candidates, cross-reference To-2024 cell types, live literature check via bio-research MCP. Pre-run the full pipeline before scripting the demo. Ship README + run.sh + `git clone` reproduce.

---

## Day-by-day (real calendar)

| Day | Focus |
|---|---|
| **Wed 07-08** | Phase 0 + start Phase 1. Hour-1 go/no-go smoke tests (AlphaGenome + ChromBPNet in parallel). Stand up repo/env, API key, freeze schema. Person A: zooHAR download + liftOver + substitution caller unit-tested on GDF5. Person B: scaffold demo artifact + GWAS intersection against a MOCK 10-row TSV. |
| **Thu 07-09** | Finish Phase 1, complete Phase 2. Lock `hars_hg38.bed` + substitution BED with GDF5/HACNS1 spiked. Build constraint + gBGC arm. Assert control set survives all filters. Person B ingests GO 2.0 credible sets. |
| **Fri 07-10** | Phase 3 — the screen core. Score all substitutions through AlphaGenome (+ ChromBPNet skeletal models + neural comparator if hour-1 passed). Normalize to frozen schema. Rename outputs to "variant-effect screen." First informal look at whether GDF5 surfaces. |
| **Sat 07-11** | Phase 4 + 5. Permutation null, BH-FDR. **Blind validation:** GDF5 rank + sign, control-set recovery, negative-control rejection, precision/recall. Claude self-red-team. GWAS overlap-enrichment on OA credible sets. Novel-candidate shortlist. |
| **Sun 07-12** | Phase 6 build. Swap real numbers into demo. Claude motif-reasoning + live literature cross-check. Pre-run FULL pipeline to know GDF5's actual rank; script demo + recovery. Render hero figures. Attempt stretch arms only if core is done. |
| **Mon 07-13** | Finalize + submit before 9pm ET. Record 3-min demo against locked pipeline. Dated 24h prior-art sweep. README with attribution/licenses. Verify run.sh reproduces from clean clone. Submit with buffer. |

---

## Verified datasets & tools (real locators)

### Scoring engines
- **AlphaGenome SDK + hosted API** — PRIMARY, GPU-free. https://github.com/google-deepmind/alphagenome · https://deepmind.google.com/science/alphagenome *(document API/non-commercial caveat; keep MIT ChromBPNet as the reproducible core)*
- **ENCODE ChromBPNet skeletal models** (gated behind hour-1 smoke test):
  - Embryonic **limb** — https://www.encodeproject.org/annotations/ENCSR138OCE/ + https://www.encodeproject.org/annotations/ENCSR858EVI/ *(highest priority — developing limb mesenchyme)*
  - **MSC** — https://www.encodeproject.org/files/ENCFF640AVL/@@download/ENCFF640AVL.tar.gz (720 MB)
  - **MG63** osteoblast-like — https://www.encodeproject.org/files/ENCFF841SWM/@@download/ENCFF841SWM.tar.gz (510 MB)
- **ChromBPNet + variant-scorer** (Kundaje, MIT) — https://github.com/kundajelab/chrombpnet · https://github.com/kundajelab/variant-scorer · Docker `kundajelab/chrombpnet:latest`

### HARs, substitutions, constraint
- **zooHARs** (Keough 2023, n=312, hg38) — Science doi:10.1126/science.abm1696 Table S1 · pipeline https://github.com/keoughkath/AcceleratedRegionsNF (Zenodo 7478724)
- **zooHAR MPRA data (neural)** — https://datadryad.org/dataset/doi:10.7272/Q6057D5N *(evidence of the neural-only gap — demo cold-open)*
- **Whalen & Pollard 2023 human-chimp fixed-difference tables** (hg19) — GEO GSE110760 · https://pmc.ncbi.nlm.nih.gov/articles/PMC10023452/
- **liftOver + hg19ToHg38 chain** — https://hgdownload.soe.ucsc.edu/goldenPath/hg19/liftOver/hg19ToHg38.over.chain.gz
- **Zoonomia 241-way phyloP** (hg38, 9.0 GB) — https://hgdownload.soe.ucsc.edu/goldenPath/hg38/cactus241way/hg38.cactus241way.phyloP.bw *(query positions only)*
- **Zoonomia RoCCs mask** — https://cgl.gi.ucsc.edu/data/cactus/zoonomia-2021-track-hub/hg38/RoCCs.bed.gz
- **1000G Phase 3 recombination / LD (EUR)** — https://ftp.1000genomes.ebi.ac.uk/vol1/ftp/release/20130502/

### GWAS
- **GO 2.0 OA + 962 SuSiE credible sets** (Hatzikotoulas 2025) — https://www.genetics-osteoarthritis.com · code https://github.com/hmgu-itg/Genetics-of-Osteoarthritis-2.0
- **GO 1.0 OA** (Boer 2021, 11 phenotypes) — https://kp4cd.org/node/733
- **Morris 2019 eBMD** (harmonised GRCh38) — https://www.ebi.ac.uk/gwas/studies/GCST006979
- **Yengo 2022 height** (GIANT) — https://giant-consortium.web.broadinstitute.org/GIANT_consortium_data_files *(tertiary sanity only — hyper-polygenic)*

### Reference atlas & controls
- **To 2024 embryonic skeletal multiome** (E-MTAB-14385) — https://www.ebi.ac.uk/biostudies/studies/E-MTAB-14385 · portal https://developmental.cellatlas.io/skeleton-development · code https://github.com/Teichlab/skeletal_dev_atlas
- **GDF5 positive control (hg38):** GDF5 chr20:35,433,347–35,454,754 (ENSG00000125965); rs4911178 chr20:35,364,817 (GROW1, hip); rs6060369 chr20:35,319,358 (R4, knee); rs143384 chr20:35,437,976

### Stack
Claude Code · Python (pyBigWig, pandas/numpy, matplotlib/plotly) · bedtools + UCSC liftOver · AlphaGenome SDK · kundajelab/chrombpnet + variant-scorer · TF-MODISCO (ships with ENCODE bundles) · susieR/coloc (stretch) · bio-research MCP (pubmed/biorxiv/consensus) · Artifact + screen-capture for the demo.

---

## Deliverables
1. A ranked, FDR-controlled, **gBGC-flagged** table of human-specific HAR substitutions predicted to change skeletal-context accessibility — each annotated with phyloP constraint, gBGC status, per-engine skeletal effect, skeletal-vs-neural specificity, and OA/BMD/height credible-set overlap.
2. The **GDF5/GROW1 blind re-discovery report** — rank + effect-direction frozen before looking; validated across a control set + negative controls; genuine precision/recall (n>1).
3. A shortlist of **NEW candidate skeletal-acting HARs** (≥4/5 pre-registered criteria), each a labeled hypothesis with a named target gene cross-referenced to To-2024 cell types, gBGC status disclosed.
4. An open, one-command-reproducible pipeline (repo + run.sh + Docker) on public data + open models, full attribution, MIT ChromBPNet path as the reproducible core.
5. An interactive HTML artifact + **3-minute demo video** walking one HAR from human-specific mutation → skeletal accessibility delta → deep constraint → gBGC filter → arthritis credible set, climaxing on the blind GDF5 re-discovery.
6. A methods writeup framing SKELETOME as the first in-silico skeletal HAR variant-effect screen (NOT an MPRA), distinguished head-on from Kun 2023 (enrichment-only) and Whalen/Pollard 2023 (neural-only).

---

## 3-minute demo script (the detective story)
1. **[0:00–0:25] COLD OPEN — visceral gap.** Live terminal queries ENCODE on camera; count returns **ZERO** skeletal ATAC-seq next to a stack of neural HAR-MPRA papers. Cut to a physical skeleton/joint. VO: *"Every experiment asking what makes the human genome human was run in brain cells. Nobody asked the skeleton."* One sentence defining HARs.
2. **[0:25–1:00] METHOD via ONE base-flip.** Animate a single substitution (ancestral G → human A) through three gates: a conservation bar filling ("mammals kept this base 100 million years"), a gBGC checkpoint stamping "not a recombination artifact," a skeletal-accessibility needle moving. Full pipeline flashes 3s as background texture — never narrated box-by-box.
3. **[1:00–1:45] THE BLIND LINE-UP.** Ranked list sorts live with gene names blurred. Claude prints in-transcript: *"positive control GDF5 still surfaces ✓"* — a real self-red-teaming moment. Top row locks in.
4. **[1:45–2:15] THE REVEAL (only music swell).** Unblur the top row: **GDF5.** Split-screen — SKELETOME's blind-predicted direction (derived allele reduces activity) next to Capellini 2017's transgenic-mouse result showing the same. On screen: *"We never told it about this gene."*
5. **[2:15–2:45] THE NEW SUSPECTS.** Scroll the novel-candidate shortlist (3–5 rows, named target genes), labeled HYPOTHESES. Caption: *"predicted, not measured — and gBGC-filtered."* Show the real `ranked_movers.tsv` opening.
6. **[2:45–3:00] CLOSE.** `git clone && ./run.sh` shot for reproducibility. Return to the skeleton/joint image. One line naming the single candidate we'd hand a wet lab to test first, and why.

---

## Top risks → mitigations
| Risk | Mitigation |
|---|---|
| **gBGC confound** (19–33% of HARs; #1 kill-shot) | Make gBGC a first-class headline arm; recombination-matched null; frame as the discriminator. |
| **ChromBPNet build/GPU hell** burns days | AlphaGenome primary (GPU-free) ships the demo alone; ChromBPNet gated behind a hard 2-hour smoke test. |
| **GDF5 re-discovery circularity** (n=1, tuned-until-it-surfaces) | Freeze thresholds + direction before looking; control SET + negative controls; report precision/recall. |
| **"In-silico MPRA" over-claim** | Rename to "variant-effect screen"; methods state predicted accessibility deltas, not transcription. |
| **GWAS overlap is coincidence-prone** | Demote to enrichment annotation with empirical p-value vs matched background; credible-set membership, not lead-SNP proximity. |
| **Cell-type over-claim** (bulk limb / MG63 / H1-MSC ≠ chondrocyte) | Label every column with the literal readout; reserve "chondrocyte" for the To-2024 training stretch only. |
| **"Claude Use" scored as generic wrapper** | Foreground Claude as adversarial collaborator on camera: authors/unit-tests the caller against GDF5, self-red-teams a silent filter, reasons over motif deltas + live literature. |
| **Demo hinges on one stochastic result** | Pre-run full pipeline; if GDF5 is top-N not #1, reframe as "top 0.5% of all substitutions"; build against mocks from Day 2; keep the contribution-track footprint as backup hero. |

---

## Judge-score read (adversarial panel)
- **Skeptical genomics reviewer:** viable. Impact 18–20/25, Claude Use 22–24/25, Depth 13–16/20, Demo 25–28/30. *"Can medal on presentation + orchestration alone; the gBGC/MPRA/n=1/GWAS fixes are what make it a contender to win."*
- **Hackathon judge:** viable. *"Podium-contender. Highest-leverage change: reframe Claude from orchestration layer to adversarial scientific collaborator — that's the 25% axis where it's most below potential."*
- **Feasibility engineer:** viable. *"Fate decided in the first 4 hours. AlphaGenome primary + ChromBPNet gated + cut the stretch clutter + mock-data demo from Day 2 = a complete winning story with slack."*
- **Demo director:** viable. *"One editorial decision from top-tier: make the blind GDF5 re-discovery the SINGLE climax; demote everything else to 3–5s supporting shots. Most life-sci entries structurally can't produce a ground-truth re-discovery — that's the unfair advantage."*
