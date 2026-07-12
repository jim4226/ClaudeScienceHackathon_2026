# SKELETOME Idea Bakeoff - Full Catalog

*13 research-track ideas scored by an adversarial judge vs the rubric (Impact 25 / Claude Use 25 / Depth 20 / Demo 30), feasibility for a solo researcher in ~6 days, and bone/MSK/imaging domain fit. 2026-07-07.*

## Ranked scoreboard

| # | Idea | I | C | D | Dm | **Total** | Feas | Fit |
|---|------|:-:|:-:|:-:|:-:|:-:|:-:|:-:|
| 1 | **SKELETOME** | 22 | 23 | 18 | 26 | **89** | yellow | high |
| 2 | **BoneBase** | 22 | 21 | 18 | 25 | **86** | green | high |
| 3 | **OA-CausalBench** | 22 | 22 | 17 | 24 | **85** | green | high |
| 4 | **ALLELE-ORACLE** | 21 | 23 | 18 | 22 | **84** | green | medium |
| 5 | **COLLAPSE** | 19 | 20 | 18 | 26 | **83** | green | high |
| 6 | **CONSTRAINT-CLASH** | 19 | 21 | 19 | 23 | **82** | yellow | high |
| 7 | **JointShape-GWAS-Bridge** | 21 | 21 | 18 | 24 | **81** | yellow | high |
| 8 | **STABLE-BENCH-MSK** | 19 | 20 | 16 | 23 | **78** | yellow | high |
| 9 | **TissueClock-Audit** | 18 | 19 | 16 | 22 | **75** | green | high |
| 10 | **ChondroDriver** | 19 | 19 | 16 | 22 | **74** | yellow | high |
| 11 | **PerturbFloor** | 18 | 20 | 16 | 19 | **72** | yellow | low |
| 12 | **XR-DeepPhenotype-GWAS** | 19 | 19 | 16 | 24 | **71** | red | high |
| 13 | **RepertoireLie-Detector** | 17 | 19 | 15 | 21 | **70** | green | low |

---

## SKELETOME — 89/100 (yellow feas, high fit)
*Impact 22 · Claude 23 · Depth 18 · Demo 26*
> Quantitative wet-lab MPRA ground truth PLUS a blind GDF5 positive control PLUS two fresh 2025 results and an honest register — the only idea that scores near-top on all four axes at once; docked only for the fragile HAR/HAQER-vs-matched-control contrast and the AlphaGenome-key dependency.

*(Incumbent — full spec in PROJECT_CONTEXT.md / PROJECT_BRIEF.md.)*
---

## BoneBase — 86/100 (green feas, high fit)
*Impact 22 · Claude 21 · Depth 18 · Demo 25*
> Same blind-then-unseal calibration drama as SKELETOME but in the researcher's exact PhD wheelhouse (eBMD/fracture/GWAS), with an orthogonal FinnGen external benchmark and ZERO controlled-access dependency — the strongest challenger; only real risk is a possibly-weak eBMD-to-fracture signal, which is reportable honestly.

**Full title.** BoneBase: pinpointing the causal base at bone-mineral-density loci and predicting which will replicate in an orthogonal fracture GWAS

**Problem.** The UK Biobank/GEFOS heel-eBMD GWAS (Morris et al. 2019) found 1,362 independent signals at 899 loci, but eBMD is an imperfect proxy for real skeletal fragility; most loci have no resolved causal variant, and it is unknown which signals reflect true bone biology versus ultrasound-measurement artifacts. A researcher deciding which BMD gene to pursue for osteoporosis needs the causal base and confidence it translates to actual fracture risk.

**Biological question.** At high-confidence eBMD loci, which single non-coding variant is causal (by allele-specific effect on osteoblast/mesenchymal regulatory activity predicted from sequence), and can a sequence-model-derived causal/effect score predict which eBMD signals also carry a directionally-consistent, genome-wide-supported fracture signal, i.e. which loci are 'real bone' vs proxy noise?

**Discrete finding.** A reproducible table of causal-base nominations for the top eBMD loci with predicted regulatory mechanism, PLUS a calibration result: an ROC/precision-recall showing whether the sequence-derived score predicts orthogonal FinnGen fracture replication, yielding a ranked, triaged list of 'high-confidence bone-biology' loci for downstream osteoporosis follow-up.

**Demo moment.** Take a canonical BMD locus (e.g., WNT16 or ESR1), show AlphaGenome's accessibility track shifting at the pinpointed causal base in an osteoblast-like context, display the model's blinded prediction 'this locus WILL replicate in fracture,' then unseal FinnGen to confirm the directional fracture signal, and finish with the calibration curve over all tested loci showing the score separates replicating from non-replicating loci.

**Claude Science leverage.** Claude runs a fine-mapping-plus-mechanism loop autonomously: fetch each eBMD credible set, score every variant with AlphaGenome for allele-specific regulatory disruption in bone-relevant contexts, integrate gnomAD constraint + eQTL colocalization + Open Targets priors into a per-locus causal-base call, then generate a pre-registered prediction of each locus's fracture replication status, and finally unseal FinnGen fracture stats to test that prediction. Claude writes the per-locus mechanistic narrative and the honest calibration report. The scientific move (using a sequence model's confidence to triage proxy-phenotype loci) is a genuine judgment task, not scripting.

**Public datasets.**
- UKB/GEFOS heel eBMD + fracture GWAS summary statistics (Morris 2019, 899 loci) — `GEFOS data releases gefos.org (2018 release: eBMD + fracture); IEU OpenGWAS gwas.mrcieu.ac.uk (ebi-a/ukb-b eBMD, fracture); GWAS Catalog GCST006979/GCST006980`
- Independent fracture GWAS for orthogonal replication (FinnGen) — `FinnGen freeze results, r11/r12, e.g. M13_FRACTURE endpoints, finngen.fi/en/access_results (public summary stats)`
- AlphaGenome API (single-bp DNase / expression tracks; osteoblast, MSC, fibroblast contexts) — `github.com/google-deepmind/alphagenome; free non-commercial API key`
- eQTL Catalogue + GTEx (bone-adjacent tissues, MSC, adipose, fibroblast for coloc) — `ebi.ac.uk/eqtl REST API; GTEx v8/v10 via Open Targets`
- gnomAD (constraint, allele frequency for candidate-variant filtering) — `gnomad.broadinstitute.org v4 API`
- Open Targets (L2G, prior BMD/osteoporosis associations, drug-target evidence) — `platform.opentargets.org GraphQL (bio-research ot MCP)`

**Feasibility.** 5-6 days solo; day 1-2 pull eBMD credible sets + wire AlphaGenome and reproduce WNT16/ESR1, day 3 scale causal-base calls to top ~50-100 loci, day 4 pre-register fracture-replication predictions, day 5 unseal FinnGen + calibration, day 6 demo. A 40-locus subset is already a valid deliverable.

**Why it could win.** Directly in the researcher's PhD wheelhouse (BMD, skeletal imaging, GWAS) so Q&A is bulletproof; the proxy-vs-real-fragility question is a genuinely important, underexplored angle judges will find fresh (Depth); orthogonal FinnGen replication is a hard, honest external benchmark (Impact + trust); the blind-then-unseal calibration demo is dramatic and quantitative (Demo); triaging osteoporosis loci is 'advance the field' relevant (Gladstone award).

**Why it might lose.** eBMD-to-fracture translation is genuinely noisy, so the calibration signal could be weak and must be reported honestly even if near-null; AlphaGenome's bone/osteoblast track coverage may force reliance on proxy tissues, weakening causal-base confidence; slightly more moving parts (two GWAS + coloc + calibration) than idea 1, so scope discipline is essential to hit the 6-day window.
---

## OA-CausalBench — 85/100 (green feas, high fit)
*Impact 22 · Claude 22 · Depth 17 · Demo 24*
> Blind scoring against the GO Consortium's own effector-gene calls across 100 OA loci is a real hit-rate benchmark judges can trust, risk-buffered (30-50 loci already presentable) and heavy on multi-source orchestration; capped slightly because recovery could be modest and it edges toward a standard V2G pipeline.

**Full title.** OA-CausalBench: sequence-first re-nomination of causal genes at the 100 osteoarthritis GWAS loci, blind-scored against the GO Consortium's own effector-gene calls

**Problem.** The GO Consortium's landmark osteoarthritis GWAS (Boer et al., Cell 2021; 826,690 individuals, 100 risk variants across 11 OA phenotypes) hand-curated high-confidence effector genes by integrating cartilage/bone functional genomics, but most loci still lack a single confidently-nominated causal gene and causal base. Clinicians and drug-hunters cannot act on a locus; they need a specific gene and the specific regulatory variant driving it.

**Biological question.** At each of the ~100 OA GWAS loci, which gene is the causal effector and which single non-coding variant most plausibly drives it, predicted from DNA sequence + regulatory context alone, and how well does a purely computational, blinded pipeline recover the GO Consortium's independently-derived effector genes?

**Discrete finding.** A reproducible per-locus table: nominated causal gene + single most-likely causal variant + predicted mechanism (accessibility/expression/splicing) for all ~100 OA loci, plus a confusion-matrix / precision-recall score of the blind pipeline against the GO Consortium effector genes, AND a shortlist of loci where the sequence model confidently nominates a DIFFERENT or previously-unnamed gene (novel, testable hypotheses).

**Demo moment.** Live pick a famous OA locus (e.g., GDF5/GROW1 or ALDH1A2) the model was blind to, show AlphaGenome's allele-specific accessibility track flip at the exact nominated base, then unseal the GO effector table to reveal the pipeline recovered the known gene, then show one locus where the model overrules the literature with an eQTL-backed alternative gene. Recovery-rate bar chart as the closer.

**Claude Science leverage.** Claude acts as an autonomous variant-to-gene scientist: for each locus it pulls the credible set, calls AlphaGenome on every candidate variant to predict allele-specific effects on chromatin accessibility / expression / splicing in cartilage-relevant contexts, cross-checks the predicted effector against the eQTL Catalogue and the 204-patient cartilage eQTL and the chondrocyte sQTL resource via colocalization-style logic, reasons over Open Targets evidence, and emits a ranked gene + causal-base call with a written mechanistic rationale per locus. Crucially it runs BLIND to the GO effector table, which is only unsealed at scoring time. This is judgment-heavy orchestration across five data sources per locus x100 loci, not glue.

**Public datasets.**
- GO Consortium OA GWAS summary statistics (Boer 2021, 11 OA phenotypes) — `Musculoskeletal Knowledge Portal / GO Consortium: msk.hugeamp.org (kp4cd.org/node/733); GWAS Catalog studies GCST007090-series; paper Cell 2021 PMC8459317`
- GO Consortium curated effector-gene table (the blinded ground truth) — `Boer et al. Cell 2021 Supplementary Tables (effector genes per locus), cell.com/cell/fulltext/S0092-8674(21)00941-7`
- Cartilage cis-eQTL resource, 204 OA patients (Kreitmaier et al. 2025) — `eBioMedicine 2025 PMC12278629; summary stats via listed repository / eQTL Catalogue`
- eQTL Catalogue (cartilage + synovium + 127 datasets) — `ftp://ftp.ebi.ac.uk/pub/databases/spot/eQTL/sumstats/ ; REST API ebi.ac.uk/eqtl; tabix_ftp_paths.tsv on GitHub eQTL-Catalogue/eQTL-Catalogue-resources`
- Response-splicing QTLs in primary human chondrocytes (orthogonal sQTL benchmark) — `Nat Commun 2025, s41467-025-63299-0 (GEO accession in data-availability section)`
- AlphaGenome API (single-bp DNase/RNA/splice/TF tracks incl. musculoskeletal cell types) — `github.com/google-deepmind/alphagenome; alphagenomedocs.com; free non-commercial API key`
- Open Targets Genetics/Platform (L2G, colocalization priors) — `platform.opentargets.org GraphQL API (available via bio-research ot MCP)`

**Feasibility.** 5-6 days solo; day 1-2 wire AlphaGenome + eQTL Catalogue + OT via MCP and reproduce 5 known loci, day 3-4 scale to all 100 loci, day 5 blind scoring + novel-locus shortlist, day 6 demo. Risk-buffered because a partial run (30-50 loci) is already a valid, presentable result.

**Why it could win.** Named disease (OA) the researcher owns; a real quantitative ground truth (GO effector genes) gives a trustworthy hit-rate number judges can believe; blind protocol reads as rigor (Depth); recovering a known enhancer live is a clean 3-min Demo; nominating novel effector genes for an untreatable disease is directly the Gladstone 'advance the field' angle (Impact); orchestration across 5 sources is strong Claude-Use.

**Why it might lose.** AlphaGenome cartilage/chondrocyte tracks may be sparse, so predictions lean on proxy tissues and correlation not accuracy; recovery rate could be modest (e.g., 40-60%) and must be framed honestly; overlaps conceptually with standard V2G pipelines, so the novelty must live in the sequence-first + blind-benchmark framing, not the components.
---

## ALLELE-ORACLE — 84/100 (green feas, medium fit)
*Impact 21 · Claude 23 · Depth 18 · Demo 22*
> Directional allele-preference accuracy on a pre-computed ADASTRA gold set is a calibration rule EVERY AlphaGenome user needs, the failure-mode stratification is genuine hypothesis-driven Claude-as-scientist, and no controlled data is needed — held back only by a medium MSK hook and a slightly plainer demo.

**Full title.** ALLELE-ORACLE: does AlphaGenome know which allele opens the chromatin?

**Problem.** AlphaGenome is benchmarked mostly on eQTL/expression and on relative track-correlation, not on the harder, directional, single-base question that regulatory-variant biology actually turns on: given a heterozygous SNP inside an open-chromatin peak, which of the two alleles is MORE accessible? This is exactly the signal a wet-lab allele-specific ATAC/ChIP experiment measures directly, and it is the signal you need before you ever trust a model to nominate a causal base. Nobody has cleanly reported AlphaGenome's DIRECTIONAL accuracy on a large gold-standard allele-specific accessibility/binding panel.

**Biological question.** For regulatory SNPs with experimentally measured allele-specific chromatin accessibility / TF binding, can a sequence-to-function model (AlphaGenome) predict the CORRECT preferred allele from sequence alone, how often, and where does it fail (which TF motifs, which accessibility levels, which conservation regimes)?

**Discrete finding.** A reproducible calibration report: AlphaGenome's directional allele-preference accuracy on N thousand gold-standard ASB SNPs (single headline number + AUROC), plus a confidence-threshold rule ('trust predictions only when |delta| > T and phyloP > C') and a ranked list of TF-motif contexts where it systematically fails. Ships as a notebook + a scored table others can reuse to filter their own AlphaGenome variant calls.

**Demo moment.** Live: paste a rs-ID of a known ASB SNP, AlphaGenome returns REF vs ALT accessibility tracks, the taller allele lights up = the experimentally preferred allele, checkmark. Then flip to the calibration curve: 'across 3,000 SNPs it's right 8X% of the time, and here's the exact confidence threshold above which it's right 9X% of the time' — a trustworthy accuracy number appearing in real time.

**Claude Science leverage.** Claude autonomously runs the full loop as a scientist: pull the ADASTRA/UDACHA significant-ASB table, extract REF/ALT + preferred allele, batch-score every SNP through the AlphaGenome API (REF vs ALT accessibility/TF-binding delta), compute directional accuracy + AUROC of |delta| as a confidence score, then DIG: stratify failures by TF motif family, by BAD/ploidy, by peak height, and by phyloP constraint, forming and testing hypotheses ('AlphaGenome is directionally reliable only above delta threshold T and inside constrained bases') and writing the calibration curve. This is Claude-as-analyst forming mechanistic hypotheses, not glue code.

**Public datasets.**
- ADASTRA (allele-specific TF binding, ChIP-seq derived, ~thousands of significant ASB SNPs with directional preferred allele + FDR) — `adastra.autosome.org (latest 'Bill Cipher'/'soos' release); companion UDACHA release = allele-specific chromatin ACCESSIBILITY at SNPs (ATAC/DNase). Nat Commun 2021 s41467-021-23007-0`
- ENCODE allele-specific / ATAC-seq + phased genotypes (for an independent held-out accessibility replication set) — `encodeproject.org — ATAC-seq + DNase experiments with genotypes; filter to heterozygous SNPs in peaks`
- Zoonomia phyloP (241-way Cactus) single-base constraint, to stratify accuracy by evolutionary constraint — `hgdownload.cse.ucsc.edu/goldenpath/hg38/cactus241way/ (phyloP bigWig)`
- AlphaGenome hosted API (DNase/ATAC + TF-binding tracks, 1-bp resolution, no GPU) — `DeepMind AlphaGenome API (Avsec et al., Science 2026; biorxiv 2025.06.25.661532); REF/ALT scoring endpoint`

**Feasibility.** 3-4 days solo (API scoring is the main time cost; ADASTRA is a clean pre-computed table, no alignment needed). Tight but very achievable in the window.

**Why it could win.** Hits Claude-Use (autonomous benchmark + hypothesis-driven failure analysis), Impact (a calibration/confidence rule EVERY AlphaGenome user needs — directly reusable), and Depth (constraint- and motif-stratified failure modes push well past the first number). Gold-standard directional ground truth = trustworthy demo. Complements rather than competes with SKELETOME's region-level story: this is the base-level trust layer.

**Why it might lose.** Less evolutionarily 'sexy' than the human-vs-chimp HAQER narrative; weaker MSK/bone domain hook (medium, not high); depends on an AlphaGenome API key; ADASTRA is TF-binding-centric so the pure-accessibility (UDACHA/ENCODE) arm must be secured early or the accessibility framing softens.
---

## COLLAPSE — 83/100 (green feas, high fit)
*Impact 19 · Claude 20 · Depth 18 · Demo 26*
> The sharpest 'wow' narrative in the pool — the most confident variant model is blind to the solved collagen C-terminal lethality gradient — with real clinical ground truth and high domain credibility; the ~70-variant N caps it as a rigorous case study rather than a powered benchmark.

**Full title.** COLLAPSE — the collagen glycine-substitution paradox: why the best ddG models fail on the bone disease they should nail

**Problem.** Osteogenesis imperfecta (brittle bone disease) is overwhelmingly caused by missense substitution of glycine residues in the Gly-X-Y repeat of type I collagen (COL1A1/COL1A2). Clinically, nearly ALL triple-helical glycine substitutions are pathogenic, yet the severity is famously non-monotonic and position-dependent (a gradient toward the C-terminus, lethal 'regional clustering'). State-of-the-art structure-based stability predictors (ThermoMPNN, ESM, FoldX) were trained/benchmarked almost entirely on small globular domains (Megascale domains are 40–72 aa) and have essentially never been tested on a fibrous triple-helix. Whether these models can rank collagen Gly-substitution severity — the single most clinically actionable structural question in skeletal genetics — is unknown and untested.

**Biological question.** Can sequence/structure-based protein models predict the pathogenicity AND clinical severity gradient of glycine substitutions in the type I collagen triple helix, and where exactly do general-purpose stability/variant-effect predictors break on fibrillar collagen?

**Discrete finding.** A reproducible benchmark table + figure: (1) how well each predictor (AlphaMissense, ESM, ThermoMPNN, FoldX) separates pathogenic vs population Gly substitutions in collagen (AUROC), (2) whether ANY captures the C-terminal severity gradient (Spearman of score vs helical position / severity), and (3) a named failure mode — e.g. 'general stability models miss the register/position dependence unique to the triple helix' — packaged as a leaderboard others can extend to other fibrillar proteins.

**Demo moment.** Split-screen: left, the collagen triple helix with the pathogenic Gly positions lit up; right, a scatter of predictor score vs true C-terminal position. Claude presses run and narrates: 'AlphaMissense calls them all pathogenic — but watch the gradient. It's flat. The model knows THAT glycine matters, not WHERE.' The reveal that the single most confident model is blind to the clinical severity axis is the 3-minute punch.

**Claude Science leverage.** Claude acts as the scientist end-to-end: pulls and reconciles ClinVar/gnomAD/OI-database records (deduping HGVS, resolving triple-helical position from sequence), runs AlphaMissense + ESM pseudo-log-likelihood + a triple-helix-aware physical score in a notebook, and — the creative core — autonomously discovers WHERE the models fail by correlating residual error against biophysical covariates (helical position, X/Y register, imino-acid neighbor, distance to C-terminus) and writes up the mechanistic hypothesis. This is model-criticism-as-science, not glue.

**Public datasets.**
- ClinVar COL1A1/COL1A2 variants (pathogenic/benign missense, incl. triple-helical Gly substitutions) — `https://www.ncbi.nlm.nih.gov/clinvar/ — genes COL1A1 (NM_000088.4), COL1A2 (NM_000089.4); ~21 COL1A1 + ~49 COL1A2 triple-helical Gly substitutions classified P/LP`
- gnomAD v4 (population missense frequencies for COL1A1/COL1A2, benign/tolerated controls) — `https://gnomad.broadinstitute.org/ gene pages COL1A1, COL1A2`
- AlphaMissense precomputed pathogenicity scores (per-variant, all COL1A1/COL1A2 missense) — `https://alphamissense.hegelab.org / Zenodo AlphaMissense hg38 tables; UniProt P02452 (COL1A1), P08123 (COL1A2)`
- PDB collagen triple-helix structures for a physically grounded local model (Gly-X-Y peptides + fibril models) — `RCSB PDB 1CAG, 1CGD, 3HR2 (collagen microfibril); AlphaFold DB fragments for COL1A1 P02452`
- Curated OI severity/genotype–phenotype resource (position + clinical outcome, incl. lethal C-terminal gradient) — `OI Variant Database / Dalgleish COL1A1-COL1A2 mutation database (https://oi.gene.le.ac.uk) and Batkovskyte et al. 2025 AJMG-A structural-variant curation (doi:10.1002/ajmg.a.63935)`

**Feasibility.** 4-5 days solo. Data pull + HGVS/position parsing (1.5d), AlphaMissense/ESM scoring is precomputed or API/CPU (1d), benchmark + failure-mode analysis + figures (1.5d), demo polish (1d). Main risk-buffer: sample size is small (~70 pathogenic Gly variants), so framing is descriptive/mechanistic, not a big-N ML claim.

**Why it could win.** Unique fusion of the judge-facing 'wow' (state-of-the-art AI is blind to a solved clinical gradient) with genuine skeletal-biology domain credibility the researcher can defend live. Ground truth is real clinical pathogenicity, the finding is discrete and extensible (a fibrillar-protein leaderboard), and the story — 'the model that scores everything can't tell you which brittle-bone child is lethal' — is memorable and honest. Strong Impact + Depth + Demo.

**Why it might lose.** Small N of pathogenic collagen Gly variants makes statistical claims fragile (must be framed as a rigorously-scoped case study, not a benchmark with power). Collagen triple helix is out-of-distribution for structure models by design, so 'they fail' could read as expected rather than surprising unless the position-gradient analysis is sharp. Less flashy than a generative/design demo.
---

## CONSTRAINT-CLASH — 82/100 (yellow feas, high fit)
*Impact 19 · Claude 21 · Depth 19 · Demo 23*
> The coiled-spring divergence-x-constraint framing is the freshest Depth angle here and it has built-in MPRA ground truth, but a judge will read it as 'SKELETOME minus the blind control' i.e. strictly weaker than the incumbent, and the fragile HAQER-vs-control contrast plus 5-day tightness pull feasibility to yellow.

**Full title.** CONSTRAINT-CLASH: HAQERs sit in constrained neighborhoods — does the model predict their function is a coiled spring?

**Problem.** The 2025 T2T 'Consensus HAQER' paper (1,596 refined HAQERs) reports HAQERs carry signatures of ONGOING negative selection despite being the fastest-diverged regions — a paradox: rapidly evolved yet now constrained. And the Okamoto/Capellini 2025 skeletal MPRA shows HAQERs (not HARs) drive human-vs-chimp regulatory differences. No one has asked a sequence-to-function model whether the PREDICTED regulatory consequence of HAQER-vs-ancestral substitutions is systematically larger, and whether that predicted effect is concentrated in the bases that are now most mammalian-constrained.

**Biological question.** Across Consensus HAQERs, do the human-specific substitutions produce larger AlphaGenome-predicted regulatory-track changes than matched control substitutions, and is the predicted regulatory impact enriched at bases that are simultaneously human-diverged AND mammalian-constrained (phyloP) — i.e., is the 'coiled spring' (fast-diverged-but-now-constrained) signature also a functional-impact hotspot the model can see from sequence?

**Discrete finding.** A reproducible result: (1) effect-size distribution of AlphaGenome-predicted regulatory change for HAQER human-specific substitutions vs matched controls (with the honest matched-control caveat reported either way), (2) a per-base 'divergence x constraint x predicted-impact' map identifying the specific coiled-spring bases inside HAQERs, and (3) concordance of those predictions with the GSE298093 skeletal MPRA. Deliverable = ranked table of HAQER bases where fast divergence, mammalian constraint, and predicted function coincide.

**Demo moment.** A single HAQER shown three ways stacked: red ticks = human-specific substitutions, blue = mammalian phyloP constraint, and the AlphaGenome predicted-accessibility delta track spiking exactly where red and blue collide — 'the fastest-changed base is also the most-constrained base, and the model says that's where the regulatory switch flipped' — then the same base confirmed differentially active in the real skeletal MPRA.

**Claude Science leverage.** Claude runs the comparative pipeline end to end: polarize each HAQER substitution (human vs inferred ancestral), score human vs ancestral sequence through AlphaGenome for every element, build a MATCHED control set (GC/length/accessibility-matched non-HAQER regions — the exact rigor step that makes or breaks HAR/HAQER contrasts), overlay phyloP per base, then test the two nested hypotheses (HAQER>control effect; and effect enriched at diverged-AND-constrained bases). Critically, Claude cross-checks its own predictions against the GSE298093 MPRA to see whether predicted-high-impact HAQERs are the ones that were wet-lab differentially active. Autonomous hypothesis generation + built-in ground-truth validation + explicit control-matching rigor.

**Public datasets.**
- Consensus HAQERs (1,596 regions, T2T-refined, with divergence + negative-selection annotation) — `biorxiv 2025.10.20.683446 (PMC12633414) — supplementary HAQER coordinate/annotation tables`
- Okamoto/Capellini skeletal MPRA (human vs chimp, ~70k elements, HAQER>HAR differential-activity ground truth) — `GEO GSE298093; biorxiv 2025.10.21.683789`
- Zoonomia 241-way phyloP single-base constraint — `hgdownload.cse.ucsc.edu/goldenpath/hg38/cactus241way/ (phyloP bigWig) + zoonomiaproject.org/the-data`
- AlphaGenome hosted API (multi-track: DNase/ATAC, histone, TF binding, expression) — `DeepMind AlphaGenome API (Avsec et al. Science 2026)`
- hg38 + chimp (panTro6) / ancestral allele for polarizing human-specific substitutions — `UCSC hgdownload panTro6; Ensembl Compara ancestral sequences`

**Feasibility.** 4-5 days solo (control-matching + polarization + API scoring across ~1.6k regions is the real cost; MPRA concordance is the stretch arm). Feasible but leave a buffer.

**Why it could win.** Strong bone/MSK domain credibility via the skeletal MPRA (survives judge Q&A), rides THREE fresh 2025 results (Consensus HAQER, skeletal MPRA, AlphaGenome), and the constraint-x-divergence 'coiled spring' framing is a genuinely novel Depth angle judges won't have seen. Built-in ground truth (GSE298093) makes it trustworthy. Directly targets the Gladstone 'advance the field' award.

**Why it might lose.** This is the CLOSEST adjacent to SKELETOME and heavily overlaps its datasets/tools — a judge could see it as SKELETOME-minus-the-benchmark-blind-control, i.e., strictly weaker than the incumbent. The HAQER-vs-control contrast is fragile (same risk SKELETOME carries) and 5 days is the tighter end of the window.
---

## JointShape-GWAS-Bridge — 81/100 (yellow feas, high fit)
*Impact 21 · Claude 21 · Depth 18 · Demo 24*
> Two of the biggest MSK GWAS ever plus a novel mediation question and a built-in GDF5 blind control make it compelling, but the PRS-validation half depends on OAI individual genotypes (NDA/dbGaP DUA) that realistically will not clear in 6 days, so a chunk of the finding is at schedule risk.

**Full title.** JointShape-GWAS-Bridge: does the genetics of knee SHAPE encode OA risk before cartilage fails?

**Problem.** The 2025 OA GWAS found 962 loci but most act through opaque mechanisms, and clinical OA risk is diagnosed only after cartilage loss (Kellgren-Lawrence >=2). Meanwhile Kun 2023 showed knee/hip skeletal PROPORTIONS are highly heritable (145 loci) and polygenically linked to OA. Nobody has fused these two GWAS at the locus level to ask a structural-causal question: which OA risk loci act by shaping joint GEOMETRY (a measurable, pre-arthritic bone trait) versus by acting on cartilage/inflammation? A bone-shape-mediated OA locus is a fundamentally different (and more preventable/mechanically-actionable) drug/screening target than an inflammatory one.

**Biological question.** Of the ~962 OA-associated loci, which are colocalized with genetic determinants of knee/hip skeletal shape (i.e. OA risk is MEDIATED by inherited joint geometry), and does a joint-shape polygenic score predict incident radiographic OA in OAI knees independent of the standard OA PRS?

**Discrete finding.** A ranked, reproducible table of OA loci whose risk is colocalized with (mediated by) inherited knee/hip SHAPE — e.g. a shortlist of ~10-30 'structural OA' loci with coloc posterior probabilities — PLUS a trained joint-shape polygenic score with a reported hazard/odds ratio for incident knee OA in OAI, independent of the standard OA PRS. Others can immediately build on the locus list and the PRS.

**Demo moment.** Live 3-panel reveal: (1) a Manhattan-style overlay lighting up the loci where OA and knee-shape signals coincide; (2) zoom to the top hit (expect GDF5/UQCC1 at 20q11 — a known joint-shape AND OA locus, serving as a blind positive control that validates the method); (3) a Kaplan-Meier curve in OAI where the top shape-PRS tertile visibly separates for incident OA years before diagnosis. The GDF5 recovery 'from two blind GWAS' is the goosebump beat.

**Claude Science leverage.** Claude orchestrates the full statistical-genetics pipeline autonomously: pulls both sets of summary stats, harmonizes builds/alleles, runs colocalization (coloc/PWCoCo-style posterior probabilities) across all 962 OA loci vs 23 shape phenotypes, ranks 'geometry-mediated' loci, then builds and validates a joint-shape PRS against incident radiographic OA in OAI — reasoning at each step about pleiotropy vs mediation, LD confounds, and multiple-testing. This is Claude-as-statistical-geneticist making judgment calls, not glue: it decides which colocalizations are credible, writes the mediation test, and interprets which loci are mechanically-actionable.

**Public datasets.**
- Translational genomics of osteoarthritis in 1,962,069 individuals (Hatzikotoulas 2025) — full GWAS summary statistics for 962 loci — `Nature 2025, DOI 10.1038/s41586-025-08771-z; summary stats via GWAS Catalog (search 'osteoarthritis Hatzikotoulas 2025') and the paper's data-availability (msk.hugeamp.org / Musculoskeletal Knowledge Portal)`
- Genetic architecture and evolution of the human skeletal form (Kun 2023) — 23 skeletal-proportion GWAS incl. hip width, femur, tibia, HAR/HAQER enrichment — `Science 2023, DOI 10.1126/science.adf8009; summary stats + phenotype defs in supplement and GWAS Catalog (Kun E 2023, skeletal proportions)`
- Osteoarthritis Initiative (OAI) — 4,796 subjects, longitudinal knee X-ray + MRI + KLG grades + incident-OA follow-up (individual level for PRS validation) — `NIMH Data Archive https://nda.nih.gov/oai (free, eRA Commons/Login.gov + click-through DUA); imaging + clinical + genotype substudy`
- GWAS Catalog / Open Targets Genetics for colocalization priors and eQTL overlap (GTEx cartilage/bone) — `https://www.ebi.ac.uk/gwas/ and Open Targets (accessible via ot MCP in Claude Science)`

**Feasibility.** 5-6 days solo. Summary-stat coloc + PRS is well-trodden; main risks are OAI access latency (start DUA day 1) and summary-stat harmonization. Achievable if OAI genotypes are gated — can fall back to UK Biobank-style external PRS weights and validate shape-PRS on OAI phenotypes only.

**Why it could win.** Rides two of the biggest-ever MSK GWAS (2025 Nature + 2023 Science), asks a genuinely novel mediation question a bone/imaging PhD can defend fluently in Q&A, has a built-in blind positive control (GDF5), and produces two reusable artifacts (locus list + PRS). Demo is visually clean and the 'shape encodes disease before cartilage fails' narrative is compelling and clinically resonant. Strong on Impact + Depth + Demo + Claude-Use simultaneously.

**Why it might lose.** Colocalization can be underpowered/ambiguous and honest results may yield fewer clean loci than hoped; OAI individual-level genotype access may not clear in time, weakening the PRS-validation half; coloc vs true mediation is a subtle claim judges' geneticists may probe. Mitigate by pre-registering GDF5 as the validation anchor and reporting negative loci honestly.
---

## STABLE-BENCH-MSK — 78/100 (yellow feas, high fit)
*Impact 19 · Claude 20 · Depth 16 · Demo 23*
> The reproduce-then-break arc and per-gene curator-actionable reliability map are strong, but 'toy-domain model is worse on real proteins' is a somewhat expected result that blunts the Depth surprise, and reproducing ThermoMPNN weights/env can eat the clock.

**Full title.** STABLE-BENCH-MSK — do stability predictors trained on toy domains generalize to real skeletal disease proteins? A held-out clinical audit anchored on Megascale

**Problem.** ThermoMPNN and peers report PCC ~0.75 on the Rocklin/Tsuboyama Megascale test set — but Megascale is 40–72 aa natural + de novo domains, a narrow slice of protein space. The field quietly assumes this generalizes to disease-relevant human proteins. For musculoskeletal disease this matters concretely: variant curators need to know whether a computed ddG is trustworthy for a SOST, GDF5, LRP5, RUNX2, or CTSK variant of uncertain significance. Nobody has done a clean out-of-distribution audit that (a) benchmarks the SOTA ddG model on Megascale to reproduce the headline number, then (b) tests the SAME model on a held-out set of clinically-annotated MSK-gene missense variants where pathogenicity is the label.

**Biological question.** Does a Megascale-trained SOTA stability predictor's accuracy transfer from toy folding domains to real skeletal/MSK disease proteins, and does predicted destabilization actually separate pathogenic from benign variants in bone-relevant genes?

**Discrete finding.** A reproducible 'transferability report': (1) reproduced Megascale PCC as a control, (2) per-gene AUROC of predicted destabilization vs clinical pathogenicity across the MSK panel, (3) a calibrated statement of WHERE ddG-based interpretation is safe vs unsafe for skeletal genes, released as a small notebook + table others can rerun and extend to new genes.

**Demo moment.** Claude first reproduces the famous ThermoMPNN Megascale scatter live (~0.75) — 'so far the model is exactly as advertised.' Then it swaps in the real bone-disease proteins and the AUROC bars drop unevenly across genes. The camera lands on one gene where destabilization cleanly predicts pathogenicity and one where it's near-random, with Claude's one-line verdict on which VUS calls a curator should and shouldn't trust.

**Claude Science leverage.** Claude runs the full experimental pipeline autonomously: reproduces the published Megascale ThermoMPNN number (the trust-building control), then folds/loads AlphaFold structures for the MSK panel, runs ThermoMPNN inference on every ClinVar missense, and evaluates whether |ddG| separates pathogenic vs benign (AUROC, calibration). It reasons about failure — e.g. which structural contexts (surface vs core, disulfide-rich SOST, propeptide vs mature GDF5) degrade transfer — and proposes a per-gene reliability flag. Claude designs and defends the OOD experiment, not just plots it.

**Public datasets.**
- Megascale / Tsuboyama-Rocklin 2023 folding-stability dataset (~800k high-quality ddG, ~250k-mutant standard test split) — `Zenodo https://zenodo.org/records/7992926 ; HuggingFace RosettaCommons/MegaScale ; Nature 2023 620:434-444`
- ThermoMPNN trained model + inference code (SOTA single-mutation ddG) — `GitHub Kuhlman-Lab/ThermoMPNN (PNAS 2024, doi:10.1073/pnas.2314853121)`
- AlphaFold DB structures for MSK disease proteins (inference inputs) — `https://alphafold.ebi.ac.uk/ — SOST (Q9BQB4), GDF5 (P43026), LRP5 (O75197), CTSK (P43235), RUNX2 (Q13950)`
- ClinVar pathogenic/benign missense for the MSK gene panel (held-out clinical labels) — `https://www.ncbi.nlm.nih.gov/clinvar/ filtered to SOST, GDF5, LRP5, CTSK, RUNX2, ALPL, COMP`
- ProteinGym clinical + DMS substitution benchmarks (external cross-check of variant-effect ranking) — `https://proteingym.org/ (217 DMS assays, ~2.7M variants; clinical ClinVar substitution benchmark)`

**Feasibility.** 5 days solo. ThermoMPNN setup + Megascale reproduction (1.5d, main technical risk = environment/weights), AlphaFold structure fetch + ClinVar panel assembly (1d), inference + AUROC/calibration analysis (1.5d), demo + writeup (1d). CPU-feasible; no wet lab.

**Why it could win.** Hits all four criteria cleanly: a real reproduced benchmark (trust), an honest OOD stress test (Depth), a curator-actionable output (Impact — a reliability map for MSK variant interpretation others can build on), and a demo with a built-in 'reproduce-then-break' arc. Domain credibility lets the researcher pick the right gene panel and survive Q&A on collagenopathies/sclerosteosis. Complements Idea 1 (collagen-specific) as the broader-panel sibling.

**Why it might lose.** Less conceptually novel than the collagen-gradient story — 'model trained on toy domains is worse on real proteins' is a somewhat expected result, so the win hinges on the per-gene actionability and a crisp calibration finding rather than a shock. Reproducing ThermoMPNN exactly can eat time if weights/env are finicky. ClinVar labels carry annotation noise that must be handled honestly.
---

## TissueClock-Audit — 75/100 (green feas, high fit)
*Impact 18 · Claude 19 · Depth 16 · Demo 22*
> Hard ground-truth ages, no API keys, and a fresh skeletal-muscle-ages-faster angle in the researcher's wheelhouse — but epigenetic clocks are a crowded field so the audit reads incremental, and the muscle-acceleration effect may be small at n~100/tissue.

**Full title.** TissueClock-Audit: where do epigenetic aging clocks break, and does skeletal muscle age faster?

**Problem.** Epigenetic 'aging clocks' (Horvath, PhenoAge, DunedinPACE) are trained mostly on blood and assumed to transfer across tissues, but a January 2025 GTEx benchmark showed they behave very differently by tissue. No one has produced a clean, reproducible, per-tissue error+bias audit that a downstream researcher can drop a new sample into and know which clock to trust — and whether musculoskeletal tissue (skeletal muscle) shows accelerated epigenetic aging vs other tissues, which matters directly for sarcopenia/osteoporosis biology.

**Biological question.** Across human tissues, which epigenetic clocks are accurate vs biased, and does load-bearing/musculoskeletal tissue (skeletal muscle) show measurably faster epigenetic aging than non-MSK tissues from the same donors?

**Discrete finding.** A reproducible per-tissue clock-accuracy scorecard (MAE + directional bias for each clock x tissue) PLUS a within-donor test result: does skeletal muscle show a positive epigenetic age acceleration relative to the donor's other tissues, with effect size and CI. Ships as a notebook + CSV others can extend.

**Demo moment.** Live: a heatmap of clock x tissue error lights up, one cell flashing red where a widely-cited clock is badly biased in muscle; then a single paired-difference plot showing skeletal muscle sitting above the diagonal — 'muscle reads older than the same person's other tissues' — quantified with a p-value, all recomputed from raw betas on screen.

**Claude Science leverage.** Claude Science acts as the analyst end-to-end: pull GSE213478 beta matrix + donor age metadata, autonomously reimplement 3-4 clocks from published CpG coefficients (handling probe-ID liftover and missing-CpG imputation — a real methodological trap it must reason through), compute per-tissue MAE/median-error/age-acceleration with matched within-donor contrasts, run the skeletal-muscle-vs-rest paired test, and self-critique (e.g. flag that EPIC-vs-450K probe dropout inflates certain clocks). It writes the reproducible notebook and interprets biology, not just runs a script.

**Public datasets.**
- GTEx multi-tissue DNA methylation (Infinium MethylationEPIC v1, ~1000 samples, 9 tissues incl. skeletal muscle, 424 donors, 866,895 CpGs) — `GEO GSE213478`
- Horvath 2013 353-CpG multi-tissue clock coefficients (ground-truth clock to reimplement) — `Genome Biology 2013 14:R115, supplementary coefficient table; also methylclock/dnaMethyAge R packages on Bioconductor/GitHub`
- Independent replication cohort of aging-associated CpGs across GTEx tissues — `GEO GSE213478-linked EWAS (PMC11308253) reporting 162,002 hyper/90,626 hypo age-CpGs across 8 tissues`

**Feasibility.** 3-4 days solo; core benchmark by day 2, muscle-acceleration contrast + robustness by day 3.5. Main risk is CpG-coefficient/probe wrangling, which is bounded and exactly what Claude is good at.

**Why it could win.** Ground-truth ages give a hard quantitative benchmark (Impact + Depth), the skeletal-muscle angle is genuinely novel and squarely in the researcher's MSK wheelhouse so they survive judge Q&A, and the finding is a resource others build on. No API keys, purely public data, fully reproducible.

**Why it might lose.** Aging clocks are a crowded field so the accuracy-audit half can read as incremental; the muscle-acceleration effect could be small or noisy in n~100/tissue, and it competes with Skeletome on freshness/wow-factor rather than beating it on demo spectacle.
---

## ChondroDriver — 74/100 (yellow feas, high fit)
*Impact 19 · Claude 19 · Depth 16 · Demo 22*
> A genetically-anchored, wet-lab-actionable OA driver nomination with a memorable state-reversion demo, but the causal claim rests on GEARS running out-of-distribution on chondrocytes (a shakiness this very idea-set's own finding exposes), so it leans on convergent circumstantial evidence rather than a hard benchmark number.

**Full title.** ChondroDriver — nominate and in-silico-validate a cell-type-specific driver of the osteoarthritis chondrocyte transition, cross-checked against BMD/OA GWAS

**Problem.** Single-cell OA atlases have catalogued a pathological MMP13+/RUNX2+ 'hypertrophic/detrimental' chondrocyte state, but which transcription factor actually DRIVES the healthy→detrimental transition is largely descriptive. There is no cheap way to prioritize a causal driver whose perturbation would revert the state — and whether any nominated driver is human-genetically supported by OA/BMD GWAS is rarely checked in the same analysis. A discrete, ranked, genetically-anchored driver nomination is something an OA cell-biology lab could take straight to a wet-lab knockdown.

**Biological question.** Which transcription factor, if silenced in the detrimental OA chondrocyte subpopulation, is predicted to shift its transcriptome back toward the healthy chondrocyte state — and is that TF (or its targets) supported by OA/BMD/height GWAS as a bona fide skeletal effector?

**Discrete finding.** A short ranked list (top ~5) of candidate driver TFs of the OA detrimental-chondrocyte state, each with: regulon/DE evidence, an in-silico knockdown 'reversion score', and a GWAS/Open-Targets genetic-support flag — delivered as a reproducible notebook. The headline is one nominated, genetically-anchored driver with a falsifiable wet-lab prediction.

**Demo moment.** A UMAP of chondrocytes with the detrimental state highlighted; Claude clicks 'knock down TF-X in silico' and the predicted cells visibly slide back toward the healthy cluster, while a side panel lights up 'OA GWAS: supported (Open Targets L2G 0.4)'. The state-reversion animation + genetic check in one view is memorable and clearly biological.

**Claude Science leverage.** Claude runs the full nomination pipeline autonomously: load the atlas, define the detrimental-vs-healthy chondrocyte contrast, infer candidate regulators (SCENIC-style regulon activity + differential TF expression), then use a perturbation model (GEARS) to SIMULATE knocking down each top TF and score which simulated knockdown most moves the cell toward the healthy centroid. It then queries Open Targets / GWAS Catalog (via the bio-research OT MCP it already has) to test whether the top drivers are human-genetically supported, and adjudicates conflicts. Claude is making the scientific chain of inference — descriptive state -> causal candidate -> in-silico intervention -> genetic validation — not just plotting.

**Public datasets.**
- Multi-tissue human knee single-cell atlas (cartilage, meniscus, synovium, subchondral bone; OA vs healthy) — `Nature Comms Biology 2025 s42003-025-08586-8; processed objects in its GEO super-series / Zenodo (linked in Data Availability)`
- Human OA articular-cartilage scRNA-seq (7 chondrocyte states incl. MMP13+/RUNX2+) — `GEO GSE152805 (Ji et al.); plus GSE104782 (Ji 2019 progression)`
- GEARS / scGPT perturbation-response models for in-silico TF knockdown — `github.com/snap-stanford/GEARS (trained on Norman/Replogle); scGPT perturbation module`
- OA and eBMD GWAS summary statistics for genetic anchoring — `GWAS Catalog: Boer et al. 2021 OA (GCST90129000-series); Morris/Kemp eBMD UK Biobank (GCST006979); Open Targets Genetics for L2G scores`

**Feasibility.** 4-6 days solo; main risk is GEARS transfer to primary chondrocytes (out-of-distribution). Mitigate by also reporting a model-free reversion score (does silencing the TF's regulon move DE genes toward healthy) so the finding stands even if the deep model is weak.

**Why it could win.** Direct MSK/skeletal-biology domain fit — the researcher survives Q&A and adds credibility. Chains four methods into a real translational nomination (Depth), produces an artifact an OA lab can act on and Gladstone would value (Impact + 'most potential to advance the field'), and the state-reversion animation is a strong 3-min demo. Genetic anchoring makes it trustworthy.

**Why it might lose.** In-silico perturbation models are known-shaky (see idea 1's own finding) and chondrocytes are out-of-distribution for GEARS, so the causal claim is softer than Skeletome's benchmarked ground truth. No wet-lab confirmation possible in the window, so it rests on convergent circumstantial evidence rather than a single hard benchmark number.
---

## PerturbFloor — 72/100 (yellow feas, low fit)
*Impact 18 · Claude 20 · Depth 16 · Demo 19*
> Maximally rigorous, leakage-audited, and uses a genuinely post-training dataset, but low domain fit weakens Q&A, the contrarian 'billion-param model ties the mean' result may already be familiar to judges from Nat Methods 2025, the demo is visually plain, and scFoundation inference carries GPU risk.

**Full title.** PerturbFloor — does a foundation cell model actually beat the boring baseline on a brand-new held-out Perturb-seq?

**Problem.** Deep 'virtual cell' foundation models (scGPT, scFoundation, GEARS) are marketed as able to predict the transcriptome after an unseen genetic perturbation, but two 2025 papers (Ahlmann-Eltze/Huber, Nat Methods 2025; Wu et al., BMC Genomics 2025) showed they often fail to beat a trivial 'predict the training mean' or linear baseline on the classic Adamson/Norman/Replogle datasets. Those benchmarks are now saturated and partly in the models' training corpora, so nobody knows the honest floor on genuinely fresh data. A clean, leakage-free re-benchmark on a dataset published AFTER the models were trained is a reproducible finding the whole field can build on.

**Biological question.** When we perturb a gene never seen during training, can any current model predict the resulting single-cell expression shift better than a linear/train-mean baseline — and if so, for which classes of genes (TFs vs signaling vs metabolic) does the model add real biology?

**Discrete finding.** A reproducible leaderboard + notebook: for each model, delta-Pearson / E-distance vs. the train-mean and ridge-linear baselines on the fresh CD4 Perturb-seq, broken down by gene functional class, with an explicit statement of which (if any) model beats the floor and by how much — plus the leakage audit that makes the comparison trustworthy.

**Demo moment.** One slide, one scatter: predicted vs. true expression shift for a held-out perturbation, with the foundation model's points and the dumb-baseline's points overlaid — and the R lines nearly identical. Claude narrates live: 'the billion-parameter model ties the mean.' Then a bar chart of the gene classes where the model DOES add signal. Punchy, contrarian, trustworthy.

**Claude Science leverage.** Claude acts as the autonomous ML scientist: it writes the leakage-audit (checks which perturbed genes overlap the model's pretraining vocabulary/corpus), builds the evaluation harness (Pearson-delta on top differentially-expressed genes, E-distance, held-out-gene split), runs baseline vs. foundation model, and — critically — reads each model's tokenizer/config to decide what a fair zero-shot split even is. It then reasons about WHY failures cluster (e.g., low-expression targets, non-monotone effects) and drafts the honest write-up. This is Claude-as-experimentalist making judgment calls, not glue code.

**Public datasets.**
- Genome-scale Perturb-seq in primary human CD4+ T cells (fresh held-out; published Dec 2025, post-dates model training) — `bioRxiv 2025.12.23.696273 (Marson lab); also on CZI Virtual Cells Platform 'genome-scale-tcell-perturb-seq'`
- Replogle 2022 genome-scale + essential Perturb-seq (K562, RPE1) — canonical benchmark — `Figshare+ 10.25452/figshare.plus.20029387 (K562_essential_raw_singlecell_01.h5ad etc.); loader pertpy.data.replogle_2022_k562_gwps()`
- Norman 2019 (dual-gene, epistasis) and Adamson 2016 (UPR) Perturb-seq — `pertpy.data.norman_2019() / adamson_2016(); GEO GSE133344, GSE90546`
- scGPT / scFoundation / GEARS pretrained weights — `github.com/bowang-lab/scGPT (Zenodo weights), github.com/biomap-research/scFoundation, github.com/snap-stanford/GEARS`

**Feasibility.** 4-5 days solo; risk is GPU for scFoundation inference (mitigate by using GEARS + scGPT zero-shot which run on modest hardware, and precomputed embeddings).

**Why it could win.** Rides two hot 2025 results, is maximally rigorous/honest (Depth + Claude-Use), and produces a genuinely reusable community artifact (Impact). Contrarian 'emperor has no clothes' demos land well with judges. Uses a dataset that literally could not have leaked into the models.

**Why it might lose.** Low domain fit for a bone researcher — weaker on judge Q&A and less differentiated (perturbation benchmarking is a crowded space; a judge may have seen the Nature Methods paper). Demo is intellectually cool but visually plain; needs strong narration to beat Skeletome's blind-validation drama.
---

## XR-DeepPhenotype-GWAS — 71/100 (red feas, high fit)
*Impact 19 · Claude 19 · Depth 16 · Demo 24*
> Highest demo ceiling in MSK (an X-ray auto-measuring itself) and dead-center domain fit, but it stacks two hard dependencies — a reliable imaging-extraction pipeline AND controlled-access dbGaP OAI genotypes — that together make the full genetic finding implausible to land in 6 days.

**Full title.** XR-DeepPhenotype-GWAS: mining a hidden OA endophenotype from OAI knee X-rays that the KL grade throws away

**Problem.** Kellgren-Lawrence grading collapses rich radiographic biology (osteophyte size, joint-space-width asymmetry, subchondral sclerosis, tibial-plateau geometry) into a single 0-4 ordinal that is coarse, subjective, and reader-variable. Because everyone GWASes KL grade or 'OA yes/no', the genetics of the SPECIFIC structural features — the actual failing mechanics — are largely uncharted. A continuous, automatically-extracted radiographic endophenotype is both a better disease axis and a more heritable GWAS target than the lumped KL label.

**Biological question.** If we extract a continuous, quantitative knee-structure phenotype directly from OAI radiographs (e.g. minimum medial joint-space width and osteophyte burden) with an automated imaging pipeline, does it define a distinct genetic architecture — do known OA/shape loci (GDF5, ASTN2, COL11A1) load onto specific features, and does the continuous phenotype recover signal that binary KL misses?

**Discrete finding.** A reproducible continuous radiographic endophenotype (medial JSW + osteophyte burden) extracted for the OAI cohort, WITH a demonstrated genetic association result: known OA/shape loci (anchored by GDF5) associate more strongly with the continuous phenotype than with binary KL, quantifying how much genetic signal the KL grade discards. Deliverable = the phenotype table + the loci-to-feature map + effect-size comparison.

**Demo moment.** Split-screen: left, the pipeline auto-annotating a knee X-ray (landmarks snapping onto the joint margin, JSW arrow drawn, osteophyte highlighted) — visually satisfying and trustworthy; right, a bar chart showing the GDF5 (and COL11A1) effect size on the continuous phenotype rising sharply above its washed-out effect on binary KL grade. The one-liner: 'the KL grade was hiding the genetics — here it is.'

**Claude Science leverage.** Claude runs the whole imaging-to-genetics loop: applies/wraps a pretrained landmark/JSW extractor to OAI radiographs to produce a continuous phenotype, QCs it against OARSI ground-truth sub-scores (reporting agreement), then autonomously runs the GWAS/association or PRS-projection against known loci, and reasons about heritability, reader-noise reduction, and which loci map to which structural feature. Claude is doing quantitative imaging science + statistical genetics end to end and making the calls on QC thresholds and confounders (age, sex, BMI, side).

**Public datasets.**
- Osteoarthritis Initiative (OAI) — full-resolution bilateral knee radiographs (~4,796 subjects, multiple timepoints) with central KLG readings, JSW measurements, and OARSI osteophyte/JSN sub-scores as ground truth — `NIMH Data Archive https://nda.nih.gov/oai — imaging release + 'kXR_SQ' semi-quant reading tables and JSW quantitative tables (free click-through DUA)`
- OAI genotype substudy (imputed genome-wide genotypes on the OAI cohort) for the GWAS/PRS association step — `OAI genetics data via dbGaP (study accession phs001019 / OAI GWAS) and NDA; standard controlled-access request`
- Kun 2023 skeletal-form loci + Hatzikotoulas 2025 OA loci as the prior/annotation set to interpret which features are genetically driven — `Science 2023 DOI 10.1126/science.adf8009; Nature 2025 DOI 10.1038/s41586-025-08771-z; loci via GWAS Catalog`
- Pretrained open KL-grading / JSW CNN weights (OAI-trained) to bootstrap the imaging extractor without training from scratch — `Public OAI-trained models e.g. Chen/Tiulpin OARSI KL models on GitHub (search 'OAI KL grading CNN github') and Nature Sci Rep 2023 ensemble (DOI 10.1038/s41598-023-50210-4)`

**Feasibility.** 6 days solo, tighter. Imaging extraction on OAI is the time sink and OAI genotype (dbGaP) access is the schedule risk. De-risk by (a) using OAI's already-published quantitative JSW tables as the phenotype instead of re-deriving it, and (b) if genotypes don't clear, projecting published GDF5/COL11A1 weights onto the continuous phenotype via family/known-carrier proxies or reporting the phenotype-vs-KL information gain alone as the finding.

**Why it could win.** This is squarely the person's home turf (bone imaging + KL/JSW + stats) so Q&A survival is near-certain, and the demo of an X-ray being auto-measured is the most visually 'cool to watch' beat available in MSK. Novel framing (genetics of the discarded endophenotype) scores Depth; reusable phenotype + loci-map scores Impact; imaging+genetics fusion scores Claude-Use.

**Why it might lose.** Two hard dependencies stacked (imaging pipeline reliability + controlled-access OAI genotypes) make it the riskier of the two on a 6-day clock; if genotypes don't arrive, the genetic 'finding' shrinks to an association-with-known-loci or an information-gain argument, which is weaker than a fresh GWAS. Imaging extraction noise could blunt the effect. Higher execution risk than JointShape-GWAS-Bridge, though higher demo ceiling.
---

## RepertoireLie-Detector — 70/100 (green feas, low fit)
*Impact 17 · Claude 19 · Depth 15 · Demo 21*
> Clean keyless public data and a fun interactive real-vs-fake demo with honest OOD self-critique, but it sits outside the researcher's domain (weak Q&A) and naturalness classification risks looking trivial/unsurprising unless the decoys are genuinely hard, with no binding-relevant readout to anchor impact.

**Full title.** RepertoireLie-Detector: can a foundation model tell a real human antibody from a plausible fake?

**Problem.** Antibody language models and generative design tools are exploding, but there is no simple, trustworthy public benchmark for whether a model actually captures the rules of real human immune repertoires vs merely producing sequences that 'look' antibody-shaped. A discrete, reproducible naturalness benchmark — real OAS sequences vs germline-shuffled/model-generated decoys — is a tool the whole antibody-ML community can build on.

**Biological question.** What sequence-level features (CDR3 length distribution, positional amino-acid usage, V/J pairing, somatic hypermutation patterns) distinguish genuine human antibodies from realistic decoys, and can a classifier trained purely on these separate real from fake with quantified accuracy?

**Discrete finding.** A reproducible 'antibody naturalness' benchmark: a trained classifier + its ROC-AUC on donor-blocked and study-OOD splits, plus a ranked list of the sequence features that most betray a fake (e.g. CDR3-length tails, specific positional biases). Released as dataset split + model + feature report others can benchmark generative models against.

**Demo moment.** Live: paste in a handful of sequences — some pulled from real OAS, some freshly germline-shuffled decoys — and the model scores each 0-1 for 'human-real,' correctly flagging the fakes, with a SHAP-style bar showing the CDR3 feature that gave one away. Then the OOD twist: show accuracy drop on a held-out disease cohort, an honest limitation on screen.

**Claude Science leverage.** Claude Science runs the full scientific loop autonomously: download and parse OAS, engineer a decoy generator from IMGT germline recombination + shuffling (reasoning about what makes a decoy 'hard'), build interpretable features, train and cross-validate a classifier with donor-blocked splits to avoid leakage, and — the creative part — probe WHICH features it relies on and stress-test with an OOD study hold-out, honestly reporting where naturalness detection fails. It designs the benchmark, not just fits a model.

**Public datasets.**
- Observed Antibody Space (OAS) — paired human heavy/light sequences (~1.8M pairs) and unpaired (~2.4B), fully downloadable with 97 annotation columns incl. germline + SHM — `https://opig.stats.ox.ac.uk/webapps/oas/ (Olsen et al., Protein Science 2022, PMC8740823)`
- IMGT/human germline V/D/J reference (to build biologically-honest germline-recombination decoys) — `https://www.imgt.org/vquest/refseqh.html`
- Held-out OAS study/donor split for out-of-distribution generalization test — `OAS per-study metadata (e.g. hold out SARS-CoV-2 vs Memory-B-Cell subsets within Paired OAS)`

**Feasibility.** 4-5 days solo; data + decoy generator by day 2, classifier + donor-blocked eval by day 3, OOD stress-test + feature interpretation by day 4.5. Risk: making decoys hard-enough to be interesting rather than trivially separable.

**Why it could win.** Very demo-friendly (interactive real-vs-fake guessing game is fun to watch), strong Claude-as-scientist story (it designs the benchmark and self-critiques via OOD), clean public data with no keys, and a genuinely useful community artifact given the antibody-generation hype.

**Why it might lose.** Outside the researcher's domain, so weaker on judge Q&A depth and credibility; naturalness classification can look easy/unsurprising if decoys are too simple, and immunogenomics judges may want a wet-lab or binding-relevant readout the sequence-only benchmark can't provide.
---
