# SKELETOME — PROMPT_PACK.md

Ready-to-paste prompts for driving **Claude Science** through each SKELETOME iteration.
Paste ONE fenced prompt per step. Each is self-contained: it names exact inputs, outputs,
files, and an explicit **Definition of Done (DoD)** with **acceptance criteria**.

**How to use.** Paste `META` first (it stays in force for the whole session). Then run
steps `0 → 7` in order. Do not skip step 0 (the go/no-go gate). Every prompt writes into
the package repo and updates `results/skeletome_results.tsv` with the **canonical columns**
(see `PROJECT_CONTEXT.md`); never rename or reorder those columns.

Verified API facts baked into these prompts (do not let the model re-invent them):
- AlphaGenome: `from alphagenome.models import dna_client, variant_scorers`,
  `from alphagenome.data import genome`; client `dna_client.create(API_KEY)`;
  score with `model.score_variant(interval=, variant=, variant_scorers=[...])`;
  tidy with `variant_scorers.tidy_scores(scores)` → pandas with columns incl.
  `raw_score`, `quantile_score`, `output_type`, `biosample_name`. `API_KEY` from env
  `ALPHA_GENOME_API_KEY`. Interval is built from the variant and resized to the model
  sequence length (1 Mb max; use the width AlphaGenome's helper returns, do not hardcode).
- ChromBPNet variant-scorer: `python src/variant_scoring.py -l variants.tsv -g genome.fa
  -m chrombpnet_nobias.h5 -o out_prefix -s hg38.chrom.sizes`; chrombpnet input schema
  columns `['chr','pos','allele1','allele2','variant_id']` (pos is 1-indexed); output
  columns include `logfc`, `abs_logfc`, `jsd`, `active_allele_quantile`.

---

## META — paste first, keep in force all session

```
You are the SKELETOME research engine inside Claude Science. Project knowledge in this
package (PROJECT_CONTEXT.md, DATA_SOURCES.md, code/) is authoritative. SKELETOME is a
variant-effect SCREEN (predicted model accessibility deltas), NEVER an "in-silico MPRA"
and never a transcription/causality claim. All skeletal readouts must be labeled by their
LITERAL source ("predicted DNase change in bulk embryonic limb / MG63 osteosarcoma /
H1-MSC"), never "chondrocyte".

Standing rules for every task you run:
1. CONTROL-SET GUARDRAIL. The control set (GDF5-GROW1, GDF5-R4, HACNS1) and the negative
   controls must be present in the working table at every stage. After ANY filter, join,
   dedup, liftOver, or subset, print a one-line audit: how many of the 3 positive controls
   and N negatives survived, with their current row values. If a positive control is
   dropped, STOP and report which line of code removed it and why — treat that as a bug in
   the pipeline, not an expected outcome.
2. SILENT-FILTER FLAG. Any operation that can reduce row count (dropna, merge how='inner',
   dtype coercion, threshold, liftOver failure) must log rows-in vs rows-out and the reason
   for every dropped row. No silent drops.
3. ADVERSARIAL SELF-REVIEW. After writing code, red-team it: name the one filter or join
   most likely to silently drop the GDF5 positive control, and prove with a printed check
   that it does not.
4. CANONICAL SCHEMA. Read/write results/skeletome_results.tsv with EXACTLY the canonical
   columns in PROJECT_CONTEXT.md. Never rename/reorder/drop columns; add new info as new
   canonical-named columns only.
5. PROVENANCE. Print the source URL/accession and retrieval date for every external file.
   If an API signature or file format is uncertain, verify it live before coding; if truly
   unverifiable, write a clearly-marked stub with a TODO and the exact doc URL.
6. REPRODUCIBILITY. Every step is a script under code/ runnable from run.sh, deterministic
   (fixed seeds), with inputs/outputs stated in a docstring.

Acknowledge these rules once, then wait for the step prompt.
```

---

## STEP 0 — Hour-1 AlphaGenome + ChromBPNet go/no-go smoke test (GDF5)

```
GOAL: One-hour go/no-go. Prove AlphaGenome can score a single skeletal variant end to end,
and run the ChromBPNet 2-hour smoke check in parallel. This gates the whole project.

INPUTS:
- Control variant rs143384 (GDF5 5'UTR), hg38 chr20:35,437,976, and the GDF5-GROW1 variant
  rs4911178 hg38 chr20:35,364,817. Ancestral vs derived alleles: determine from the
  substitution table in PROJECT_CONTEXT (if not yet built, hardcode ref/alt for this smoke
  test and note it as provisional).
- AlphaGenome API key in env ALPHA_GENOME_API_KEY.
- ChromBPNet: model kundajelab/chrombpnet Docker or pip; MSC weights ENCFF640AVL,
  MG63 weights ENCFF841SWM (see DATA_SOURCES.md); variant-scorer repo kundajelab/variant-scorer.

TASKS:
A) AlphaGenome path (PRIMARY, must pass):
   from alphagenome.models import dna_client, variant_scorers
   from alphagenome.data import genome
   model = dna_client.create(os.environ['ALPHA_GENOME_API_KEY'])
   variant  = genome.Variant(chromosome='chr20', position=35437976,
                             reference_bases=REF, alternate_bases=ALT)
   interval = variant.reference_interval.resize(dna_client.SEQUENCE_LENGTH_1MB)  # verify the
             # exact constant/helper name against the installed package; do not guess a number
   scores = model.score_variant(interval=interval, variant=variant,
             variant_scorers=list(variant_scorers.RECOMMENDED_VARIANT_SCORERS.values()))
   df = variant_scorers.tidy_scores(scores)
   Filter df to ATAC and DNASE output_type rows; print raw_score + quantile_score for the
   most skeletal-relevant biosamples available (limb/osteoblast/MSC/bone if present, else
   report what biosamples exist). Save code/smoke_alphagenome.py + results/smoke_ag.tsv.
B) ChromBPNet path (OPTIONAL, 2-hour box): write the same variant into a chrombpnet-schema
   TSV with columns ['chr','pos','allele1','allele2','variant_id'] (pos 1-indexed), then run
   python src/variant_scoring.py -l gdf5.tsv -g hg38.fa -m <MSC chrombpnet_nobias.h5>
   -o results/smoke_cbp -s hg38.chrom.sizes. Save code/smoke_chrombpnet.sh + the output TSV.

DEFINITION OF DONE / ACCEPTANCE CRITERIA:
- GO if AlphaGenome returns finite ATAC and DNASE raw_score + quantile_score for the GDF5
  variant with no exception, and the tidy dataframe has the documented columns.
- Record the predicted effect DIRECTION for the derived allele (expect REDUCED activity per
  Capellini 2017 ~0.72x; do NOT tune anything to hit this — just record and compare later).
- ChromBPNet smoke: GO-enrichment if variant_scoring.py runs to completion and emits logfc +
  jsd within 2h wall-clock; otherwise mark ChromBPNet as OPTIONAL/DEFERRED and proceed with
  AlphaGenome alone (this is an allowed outcome, not a failure).
- OUTPUT a one-paragraph GO / NO-GO verdict naming which engines passed. If AlphaGenome
  fails, NO-GO: report the exact error and the doc URL to check before any further steps.
```

---

## STEP 1 — Build the hg38 substitution table with controls spiked in

```
GOAL: Produce the master substitution table: one row per human-specific single-base
substitution inside a HAR, in hg38, with the control set spiked and clearly labeled.

INPUTS (see DATA_SOURCES.md for URLs/accessions):
- zooHARs (Keough 2023, n=312, hg38) Table S1 — HAR coordinates.
- Whalen & Pollard 2023 human–chimp fixed-difference substitution tables (hg19; GEO
  GSE110760 / PMC10023452).
- liftOver chain hg19ToHg38.over.chain.gz + UCSC liftOver (or pyliftover).
- Control coordinates (hg38) from PROJECT_CONTEXT: GDF5-GROW1 rs4911178 chr20:35,364,817;
  GDF5-R4 rs6060369 chr20:35,319,358; rs143384 chr20:35,437,976; HACNS1/GBX2. Negative
  controls: pick >=20 substitutions that are NOT in any HAR and NOT near a skeletal gene
  (document selection rule and seed).

TASKS:
1. Load HARs; load Whalen/Pollard human-specific fixed differences; keep only substitutions
   whose hg19 position lifts cleanly to hg38 AND falls inside a HAR interval. Log every
   liftOver failure (unmapped/split) with reason.
2. For each substitution set ref_ancestral (chimp/inferred ancestral) and alt_human. State
   the ancestral-inference source explicitly; if only human/chimp is available, label the
   chimp allele as the ancestral proxy in `notes`.
3. Assemble the canonical table results/skeletome_results.tsv with columns:
   har_id, chrom, pos_hg38, ref_ancestral, alt_human, target_gene_hypothesis
   (nearest/regulatory-target gene; method noted), is_control
   (GDF5-GROW1|GDF5-R4|HACNS1|negative|none), notes. Leave all downstream scoring columns
   present but empty/NA for now.
4. Spike the control + negative rows in with correct is_control labels. GDF5 controls may or
   may not sit inside a zooHAR — if they do not, add them anyway flagged in notes as
   "control, not HAR-derived".

DEFINITION OF DONE / ACCEPTANCE CRITERIA:
- results/skeletome_results.tsv exists with exactly the canonical column names (extra
  not-yet-filled canonical columns allowed as NA).
- Row-count audit printed: HARs in, substitutions in (hg19), lifted to hg38, inside-HAR
  retained, dropped-with-reason tally.
- CONTROL AUDIT: all 3 positive controls + all negatives present with correct is_control and
  hg38 coordinates matching PROJECT_CONTEXT to the base pair. If any positive control is
  absent, STOP and explain.
- A 5-row sample and total N printed. Save the builder as code/build_substitutions.py.
```

---

## STEP 2 — Constraint (phyloP) + gBGC arm

```
GOAL: Annotate every substitution with 241-way phyloP constraint and a first-class gBGC
classification, so we can later separate genuine skeletal-regulatory HARs from gBGC noise.

INPUTS:
- results/skeletome_results.tsv from Step 1.
- Zoonomia 241-way phyloP bigWig (hg38) + RoCCs mask BED (see DATA_SOURCES.md).
- A recombination-rate map (deCODE/HapMap hg38) + known hotspot intervals (document source).

TASKS:
1. phyloP: query the bigWig at each pos_hg38 (bigWigAverageOverBed or pyBigWig). Fill
   phylop_241 (float), constrained = phylop_241 > 2.27 (bool), rocc = pos in RoCCs (bool).
2. gBGC: classify each ref_ancestral->alt_human substitution:
   - WtoS  (weak A/T -> strong G/C)
   - StoW  (strong G/C -> weak A/T)
   - neutral (A<->T or G<->C)
   Fill gbgc_class. Join local recomb_rate_cMperMb at the site. Set gbgc_flag = True for
   WtoS substitutions in elevated-recombination / hotspot-proximal regions (state the exact
   rule + thresholds in notes; keep it a documented, tunable constant).
3. Report the WtoS fraction across all HAR substitutions and note whether it exceeds the
   genome-wide expectation (the "most HARs are gBGC noise" framing).

DEFINITION OF DONE / ACCEPTANCE CRITERIA:
- Columns phylop_241, constrained, rocc, gbgc_class, recomb_rate_cMperMb, gbgc_flag filled
  for every row (NA only where the bigWig/recomb map genuinely lacks coverage — log those).
- Sanity: constrained rows are a minority; gbgc_class in {WtoS,StoW,neutral} for 100% of rows.
- CONTROL AUDIT: print phyloP, constrained, gbgc_class, gbgc_flag for the 3 positive controls.
  Flag loudly if a positive control is gbgc_flag=True (it may be — that is a finding, not a
  bug — but it must be visible before scoring).
- Save code/annotate_constraint_gbgc.py. No positive control silently dropped.
```

---

## STEP 3 — Skeletal scoring (AlphaGenome primary) + neural comparator

```
GOAL: Score every substitution for predicted skeletal-lineage accessibility change with
AlphaGenome (primary), optionally enrich with ChromBPNet, and add a neural comparator so we
can isolate skeletal-SPECIFIC effects.

INPUTS:
- results/skeletome_results.tsv (Steps 1-2).
- AlphaGenome key in ALPHA_GENOME_API_KEY.
- (Optional) ChromBPNet limb/MSC/MG63 models (ENCSR138OCE/ENCSR858EVI, ENCFF640AVL,
  ENCFF841SWM) + variant-scorer, only if Step 0 marked ChromBPNet GO.

TASKS:
1. AlphaGenome (PRIMARY): for each row build genome.Variant + resized interval and call
   model.score_variant(..., variant_scorers=list(
     variant_scorers.RECOMMENDED_VARIANT_SCORERS.values())); tidy_scores -> pandas.
   From the tidy frame take the ancestral->derived delta:
   - ag_atac_delta  = ATAC raw_score for the most skeletal-relevant biosample(s) available
   - ag_dnase_delta = DNASE raw_score likewise
   Select biosamples by LITERAL skeletal relevance (limb/osteoblast/MSC/bone/chondro-adjacent
   if present); record exactly which biosample_name(s) you used in notes. Batch calls and
   cache raw responses to disk so reruns are free.
2. Neural comparator: from the SAME tidy output pick a neural biosample (e.g. brain/neural
   DNASE-ATAC) and store its delta as neural_delta. This is the comparator, not a target.
3. (Optional) ChromBPNet: run variant_scoring.py per model; map logfc into cbp_limb_logfc,
   cbp_msc_logfc, cbp_mg63_logfc and jsd into cbp_jsd. If ChromBPNet is DEFERRED, leave these
   NA and say so.
4. Derive skeletal_specific (bool): TRUE when the skeletal effect is strong AND the neural
   effect is muted (state the exact rule, e.g. |ag_atac_delta or ag_dnase_delta| >= tS and
   |neural_delta| <= tN; keep tS/tN as documented constants).

DEFINITION OF DONE / ACCEPTANCE CRITERIA:
- ag_atac_delta, ag_dnase_delta, neural_delta filled for all rows; cbp_* filled or explicitly
  NA/deferred; skeletal_specific set for all rows.
- Direction check: for the GDF5 controls, report predicted direction and compare to the
  frozen expectation (derived allele REDUCES activity, ~0.72x). Report agreement WITHOUT
  changing any threshold to force it.
- CONTROL AUDIT: table of all controls with ag_atac_delta, ag_dnase_delta, neural_delta,
  skeletal_specific. Confirm none dropped by batching/caching/join.
- Save code/score_alphagenome.py (+ code/score_chrombpnet.sh if used). Raw API responses
  cached under cache/ and git-ignored.
```

---

## STEP 4 — Permutation null + BH-FDR + BLIND GDF5 / control-set validation

```
GOAL: Turn deltas into calibrated significance with a recombination-matched permutation null,
BH-FDR, and a BLIND validation of the frozen control set. Freeze predictions BEFORE looking.

INPUTS:
- results/skeletome_results.tsv (Steps 1-3), with a FROZEN pre-registration file
  code/frozen_expectations.yaml stating, for each control, its expected rank tier and
  expected effect direction, committed BEFORE this step reads any score.

TASKS:
1. Composite score: combine skeletal effect magnitude, skeletal_specific, and constraint into
   composite_score (state the formula; keep weights documented + fixed). Do NOT let gBGC-
   flagged or unconstrained rows inflate the score (they are handled by the candidate filter,
   not by silently zeroing them here — keep them in the table).
2. Permutation null: build an empirical null by permuting labels/positions while MATCHING on
   recomb_rate_cMperMb (bin-matched resampling; fixed seed; >=10k permutations). Compute
   empirical_p per substitution as the fraction of matched null draws with |score| >= observed.
3. Multiple testing: fdr_bh = Benjamini-Hochberg over empirical_p.
4. candidate (bool) = constrained AND NOT gbgc_flag AND skeletal effect (skeletal_specific or
   passing the effect threshold) — exactly per PROJECT_CONTEXT definition.
5. BLIND validation: only AFTER 1-4 are computed and written, open code/frozen_expectations.yaml
   and compute genuine precision/recall over the control set (positives should rank high /
   be candidates; negatives should not). Report n, precision, recall, and per-control
   hit/miss with predicted vs frozen direction.

DEFINITION OF DONE / ACCEPTANCE CRITERIA:
- Columns composite_score, empirical_p, fdr_bh, candidate filled for all rows.
- The permutation null is recomb-matched (show the matching diagnostic: null vs observed
  recomb-rate distributions overlap).
- BLIND validation reports precision/recall with n>1 and a per-control table; GDF5-GROW1 and
  GDF5-R4 should surface as candidates with the expected reduced-activity direction, and
  negatives should be non-candidates. Report the result honestly even if a control misses —
  do NOT retro-fit thresholds.
- CONTROL/SILENT-FILTER AUDIT: confirm the candidate filter did not drop a positive control
  for a reason other than a real gbgc_flag/constraint fail; if it did, surface it as the
  headline caveat. Save code/permute_fdr_validate.py + results/validation_report.md.
```

---

## STEP 5 — OA credible-set enrichment (supporting annotation)

```
GOAL: Test whether candidate skeletal-regulatory HAR substitutions are enriched in
osteoarthritis GWAS credible sets, as SUPPORTING annotation (overlap enrichment), NOT a
causality claim.

INPUTS:
- results/skeletome_results.tsv (Steps 1-4).
- GO 2.0 OA GWAS + 962 SuSiE credible sets (Hatzikotoulas 2025; genetics-osteoarthritis.com).
- Optional: eBMD (Morris 2019, GCST006979) and height (Yengo 2022) for secondary overlap.

TASKS:
1. Membership: for each substitution, oa_credible_overlap (bool) = pos_hg38 falls within a
   SuSiE credible-set variant set (credible-set MEMBERSHIP, not lead-SNP proximity). Record
   oa_credible_set_id.
2. Enrichment: compute gwas_enrich_p = empirical overlap-enrichment p-value for CANDIDATE
   substitutions vs a matched background (match on the same covariates as the Step-4 null,
   incl. recomb rate and constraint; fixed seed; >=10k draws).
3. Optional colocalization ONLY IF a named cartilage/skeletal eQTL enables it; otherwise state
   that no colocalization is claimed.

DEFINITION OF DONE / ACCEPTANCE CRITERIA:
- Columns oa_credible_overlap, oa_credible_set_id, gwas_enrich_p filled for all rows.
- Enrichment reported as: k candidates overlap credible sets vs expected under matched
  background, with gwas_enrich_p and the background-matching diagnostic. Framed as annotation.
- CONTROL AUDIT: report OA overlap status for GDF5 controls (GDF5 is a known OA/skeletal locus
  — note whether the controls land in an OA credible set as an external sanity check).
- Save code/gwas_enrichment.py + results/gwas_enrichment_report.md. No causality language.
```

---

## STEP 6 — TF-MODISCO motif reasoning + live-literature cross-check + shortlist

```
GOAL: For the top candidates, use motif-contribution deltas to generate mechanistic
hypotheses (which TF binding is gained/lost), cross-check each against LIVE literature, and
produce a novel-candidate shortlist. This is the adversarial-collaborator showcase.

INPUTS:
- results/skeletome_results.tsv (candidate==True, ranked by composite_score).
- Motif/contribution deltas: ChromBPNet contribution scores + TF-MODISCO motifs if ChromBPNet
  was run; otherwise AlphaGenome contribution/attribution outputs for the same windows. State
  which source you used.
- Web/literature access for cross-checking (name each source + date).

TASKS:
1. For the top ~10-20 candidates, compute ancestral vs derived motif-contribution deltas and
   name the specific TF motif(s) gained or lost (e.g. SOX9, RUNX2, HOX). Tie each to the
   target_gene_hypothesis and the skeletal cell context (LITERAL: limb/MSC/MG63).
2. For each hypothesis, do a live-literature cross-check: is this TF known in skeletal/
   chondrocyte/osteoblast biology at this locus? Cite the paper. Mark hypotheses as
   supported / novel / contradicted.
3. Red-team each top candidate: could the signal be a gBGC artifact, a phyloP-mask edge, or a
   biosample mislabel? Only keep candidates that survive.
4. Emit results/novel_candidates.md: ranked shortlist with har_id, target_gene_hypothesis,
   TF motif change, predicted direction, OA overlap, literature status, and confidence.

DEFINITION OF DONE / ACCEPTANCE CRITERIA:
- >=1 mechanistic hypothesis per top candidate, each with a named TF motif delta and a cited
  live reference (or an explicit "no prior literature — novel" with the searches you ran).
- GDF5 control appears in the reasoning as a positive anchor: the pipeline's motif reasoning
  should recover a plausible mechanism at GDF5 (blind re-discovery narrative).
- Shortlist separates gBGC-suspect from clean candidates; nothing gbgc_flag=True is presented
  as a headline novel hit without a caveat.
- Save code/motif_reasoning.md (method) + results/novel_candidates.md (deliverable).
```

---

## STEP 7 — Demo assets (3-min script, figures) + reproducibility

```
GOAL: Produce the hackathon deliverables: a 3-minute demo script, the key figures, and a
one-command reproduction path.

INPUTS: everything in results/ + code/ from Steps 0-6.

TASKS:
1. Figures (save to figures/, each with a caption stating the LITERAL data source):
   - F1 pipeline schematic (HARs -> substitutions -> constraint/gBGC -> AlphaGenome skeletal
     scoring + neural comparator -> permutation/FDR -> OA enrichment -> motif reasoning).
   - F2 volcano/scatter: composite_score vs -log10(empirical_p), controls highlighted,
     gbgc_flag styled distinctly, candidates labeled.
   - F3 GDF5 blind-validation panel: predicted derived-allele direction vs frozen expectation.
   - F4 novel-candidate shortlist table.
2. 3-minute script (docs/DEMO_SCRIPT.md): the gap ("every HAR reporter assay was neural;
   ENCODE has zero skeletal ATAC — we fill it computationally"), the method as a variant-
   effect SCREEN (not an MPRA), the blind GDF5 re-discovery, the gBGC-noise separation, and
   the top novel candidate. Time-boxed to ~3 min.
3. run.sh: from a clean checkout, sets env, fetches public data (or points to DATA_SOURCES.md),
   and runs code/ Steps 1-6 to regenerate results/skeletome_results.tsv + reports + figures.
   Deterministic (fixed seeds). Document the AlphaGenome key + optional ChromBPNet toggle.

DEFINITION OF DONE / ACCEPTANCE CRITERIA:
- run.sh regenerates results/skeletome_results.tsv byte-stable (or numerically within a
  stated tolerance) on a clean run; a fresh reader can reproduce from README + DATA_SOURCES.
- All figures carry LITERAL source labels; no figure says "chondrocyte" or "MPRA".
- Demo script explicitly frames the work as predicted accessibility deltas, states the control-
  set precision/recall, and names the gBGC caveat.
- FINAL CONTROL AUDIT: the demo asserts the control set survived end to end (controls present
  in the final TSV with expected direction) and lists any silent-filter caveat found in the run.
```

---

### Reusable one-liner to append to ANY step if you want an extra guardrail pass

```
Before you finish: re-print the CONTROL AUDIT (3 positive + negatives, current row values),
list every row-reducing operation in this step with rows-in/rows-out, and name the single
filter most likely to have silently dropped the GDF5 positive control — then prove it did not.
```
