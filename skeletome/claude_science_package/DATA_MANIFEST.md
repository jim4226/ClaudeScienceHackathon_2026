# SKELETOME — DATA MANIFEST (v2)

**A virtual skeletal MPRA, benchmarked against the real one.**
This manifest is the single source of truth for every external dataset the pipeline consumes: exact URL/accession, file format, genome build, approximate size, license/attribution, and a concrete **LOAD RECIPE**.

- **Last verified:** 2026-07-07 (locators per the verified SPINE; see per-row "Checked" notes).
- **Reference build for the whole project:** **hg38 / GRCh38.** Everything is hg38-native; liftOver only if a source is hg19.
- **Companion script:** `code/download.sh` holds the actual `curl`/`wget` commands, guarded so the 9 GB phyloP bigWig is *never* fully downloaded — it is streamed by position via HTTP range reads (pyBigWig over a URL).
- **Canonical outputs:** `results/elements.tsv` (row per MPRA element — the benchmark unit) and `results/substitutions.tsv` (row per human-specific substitution — base-resolution). This manifest covers *inputs* only.

> **Verification honesty:** rows are tagged **[VERIFIED — SPINE]** (primary-source-checked this session per the canonical spine), **[VERIFIED META]** (existence/format confirmed via landing page/search), or **[TODO]** (exact download URL/column to confirm first thing in Claude Science). bioRxiv **HTML 403s** — use the **PDF + GEO + GitHub** for the benchmark paper.

---

## 0. Credentials & registration (read first)

| Resource | Needs | How |
|---|---|---|
| **AlphaGenome API** (PRIMARY engine) | **API key** (free, non-commercial) | `pip install alphagenome`; register at https://deepmind.google.com/science/alphagenome → "Get API key". Export `ALPHA_GENOME_API_KEY`; passed to `dna_client.create(API_KEY)`. **No key → no scoring.** Non-commercial license. hg38/GRCh38.p13. Batch politely. |
| **GEO GSE298093** (benchmark MPRA) | none | Public FTP/HTTPS. |
| **aokamoto-bio GitHub** (benchmark calls + labels) | none | Public git clone. |
| ENCODE files | none | Public; download URLs 307-redirect to signed S3 — follow with `curl -L`. |
| UCSC goldenPath (phyloP, chains, bigZips) | none | Public HTTP, range-request friendly. |
| Zoonomia RoCCs / track hub | none | Public HTTP (`cgl.gi.ucsc.edu`). |
| Lowe-lab HAQER BED | none | Public (GitHub/lab site). |
| GWAS Catalog / GO 2.0 OA / GIANT | none | Public FTP/HTTPS. |

Nothing here is controlled-access (no dbGaP/EGA).

---

## 1. Okamoto/Capellini 2025 skeletal MPRA — THE BENCHMARK (Phase 1 spine, Phase 3 ground truth)

This is the real wet-lab measurement our in-silico predictions are benchmarked against. It supplies per-element **differential-activity calls**, the paper's **HAR/HAQER labels**, hg38 element coordinates, and human/chimp element sequences.

- **What:** Massively parallel reporter assay (MPRA) of ~**70,000** elements testing human vs chimpanzee regulatory activity in postcranial skeletal development.
- **Paper (verified — SPINE):** Okamoto, Coveney, Ganapathee & Capellini 2025, *"Massively parallel functional screen identifies thousands of regulatory differences in human vs chimpanzee postcranial skeletal development."* **bioRxiv 2025.10.21.683789**; *Genome Biology and Evolution* **10.1093/gbe/evag121**.
  - **[VERIFIED — SPINE]** **bioRxiv HTML 403s to automated fetch — use the PDF, the GEO record, and the GitHub repo instead.**
- **Benchmark GEO record:** **GSE298093** — https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE298093
  - **[VERIFIED — SPINE]** Public; **19 samples**: TC28a2 + CHON002 chondrocyte lines + K562 bone-marrow lymphoblast + plasmid. hg38.
- **Code / per-element calls + labels:** **github.com/aokamoto-bio/human_skeletal_evolution_MPRA**
  - **[VERIFIED — SPINE]** Holds the analysis code and the per-element differential-activity tables with the paper's HAR/HAQER labels and hg38 coords.
- **Ground-truth numbers to reproduce (frozen):**
  - ~**70,000** tested; **30,736 active** (45.2%); **11,542 differentially active** (37.6% of active).
  - Threshold: **|log2FC| > 1 & Bonferroni p < 0.01**.
  - **HAQER**: **19/30 = 63%** differential (Fisher OR **2.88**, P < 0.01, ENRICHED vs chance).
  - **HAR**: **19/57 = 33%** differential (P = 0.58, NOT enriched vs chance). Baseline 37.6%.
  - **Caveat (must state):** vs sequence-feature-**matched** controls, NEITHER HAR nor HAQER significant (Fisher P > 0.05). HAQER>HAR rests on the vs-chance test.
- **Format:** GEO supplementary TSV/CSV (per-element calls) + GitHub tables; hg38.
- **Size:** small for the call/label tables (MBs); raw sequencing counts larger (not needed for the benchmark).
- **License:** public GEO + open GitHub; cite Okamoto et al. 2025 (GBE 10.1093/gbe/evag121) + GSE298093.
- **LOAD RECIPE:**
  1. `git clone https://github.com/aokamoto-bio/human_skeletal_evolution_MPRA` and pull the per-element differential-activity table (log2FC, Bonferroni p, active/differential flags, HAR/HAQER labels, hg38 coords). If not in the repo, pull the supplementary TSV from **GSE298093**.
  2. `pandas.read_csv(..., sep=...)`; **inspect the header — do NOT assume column names.** Map to canonical: `element_id, chrom, start_hg38, end_hg38, har_label, haqer_label, mpra_log2fc, mpra_bonf_p, mpra_active, mpra_differential`.
  3. **Sanity gate:** reproduce **30,736 active / 11,542 differential / 37.6%** and **HAQER 19/30, HAR 19/57** from the loaded file. If they don't reproduce, you are reading the wrong column/definition — STOP and fix.
  4. Extract the human(alt) + chimp(ref) element sequences (prefer the paper's exact oligo sequences) → `results/element_sequences.tsv` for AlphaGenome scoring (Phase 2).

---

## 2. AlphaGenome SDK + track-locking — THE ENGINE (Phase 0 lock, Phase 2 scoring)

- **What:** AlphaGenome (Google DeepMind) — sequence-to-function model predicting 1-bp ATAC & DNase and ref-vs-alt variant scores. **We use DNASE (not ATAC)** for skeletal context.
- **Paper (verified — SPINE):** Avsec et al., *Nature* **28 Jan 2026**, **10.1038/s41586-025-10014-0**. Peer-reviewed. hg38/GRCh38.p13. Non-commercial license.
- **SDK:** `pip install alphagenome`; `dna_client.create(API_KEY)`. Docs https://www.alphagenomedocs.com/ ; repo https://github.com/google-deepmind/alphagenome. Hosted, **GPU-free**.
- **Track inventory (B1 RESOLVED — SPINE):** AlphaGenome outputs **305 human DNASE + 167 ATAC** tracks (ENCODE-derived; **GTEx excluded**). Confirmed skeletal DNase biosamples present: **chondrocyte ENCSR970DQR**, **osteoblast ENCSR000ELJ**, **MSC (H1-derived)**, **embryonic femur ENCSR805XIF**, embryonic **limb/forelimb/hindlimb** DNase.
- **FIRST CODE STEP — lock the tracks:**
  ```python
  from alphagenome.models import dna_client
  dna_model = dna_client.create(API_KEY)
  meta = dna_model.output_metadata(organism=dna_client.Organism.HOMO_SAPIENS)
  # grep the .dnase tracks by biosample_name / ontology_curie:
  #   chondrocyte | osteoblast | mesenchymal | limb | femur
  # persist matched CURIEs + track names to config/skeletal_tracks.yaml
  ```
  - **Aggregate a small skeletal DNase PANEL** (chondrocyte + embryonic femur + limb), not one track.
  - **CAVEAT (must carry):** the AlphaGenome model card warns it is **not fully optimized for cell/tissue-specific patterns** — frame every benchmark number as **correlation/enrichment, not absolute accuracy.**
- **Variant scoring (Phase 2):**
  ```python
  from alphagenome.data import genome
  variant = genome.Variant(chromosome='chr20', position=35364817,
                           reference_bases=ANC, alternate_bases=DER)  # ancestral=REF, derived=ALT
  interval = variant.reference_interval.resize(
      dna_client.SUPPORTED_SEQUENCE_LENGTHS['SEQUENCE_LENGTH_1MB'])
  scores = dna_model.score_variant(interval, variant,
                                   variant_scorers=[<CenterMaskScorer over the DNASE panel>])
  # variant_scorers.tidy_scores(scores) -> flat table; QUANTILE score primary, keep raw.
  ```
  - `ag_dnase_delta` is ancestral→derived. Cache all raw responses in `cache/` for reproducibility.
- **License:** non-commercial; cite Avsec et al. Nature 2026 (10.1038/s41586-025-10014-0).

---

## 3. Genome-wide HAR set — zooHARs (Phase 1 genome-wide extension)

- **What:** **312** zooHARs (Zoonomia 241-way). Standalone HAR interval set for the broader genome-wide screen; for the benchmark, use the MPRA paper's own HAR labels (§1).
- **Source (verified — SPINE):** Keough et al., **Science 2023**, doi:**10.1126/science.abm1696**; coordinates in Table S1. Pipeline https://github.com/keoughkath/AcceleratedRegionsNF (Zenodo 7478724).
- **Format:** supplementary table → BED; **hg38**. Size < 1 MB.
- **License:** AAAS/Science supplement — cite the paper + Zoonomia.
- **LOAD RECIPE:** read Table S1 with `pandas.read_excel`; emit `chrom start end har_id` BED; UCSC-style `chr20`; `sort -k1,1 -k2,2n`. **Almost disjoint from HAQERs (6/2,733 overlap).**

---

## 4. Genome-wide HAQER set — Lowe-lab haqer.hg38.bed (Phase 1 genome-wide extension)

- **What:** **1,581** native-hg38 Human Ancestor Quickly Evolved Regions (HAQERs). The class the MPRA found ENRICHED for differential activity (19/30 = 63%).
- **Source (verified — SPINE):** Mangan et al., **Cell 2022** (Lowe lab). File **haqer.hg38.bed**, **BED5**, **1,581** intervals, hg38-native.
- **Format:** BED5 (`chrom start end name score`), hg38. Size < 1 MB.
- **License:** open; cite Mangan et al. Cell 2022 + Lowe lab.
- **LOAD RECIPE:**
  ```bash
  # haqer.hg38.bed (Lowe-lab); 1,581 native-hg38 intervals, BED5
  sort -k1,1 -k2,2n haqer.hg38.bed > haqer.hg38.sorted.bed
  wc -l haqer.hg38.sorted.bed   # expect 1581
  ```
  Use for the genome-wide extension; for the benchmark, defer to the paper's per-element HAQER labels (§1). **[TODO: confirm the exact Lowe-lab download path for haqer.hg38.bed at first use.]**

---

## 5. Zoonomia 241-way phyloP — deep mammalian constraint (Phase 4)

- **[VERIFIED — SPINE]** URL: https://hgdownload.soe.ucsc.edu/goldenPath/hg38/cactus241way/hg38.cactus241way.phyloP.bw (directory `.../cactus241way/`, file `cactus241way.phyloP.bw`, **9.0 G**).
- **Format:** **bigWig** (per-base phyloP, hg38). **Size: 9.0 GB — DO NOT fully download; stream by position.**
- **Constraint threshold (frozen):** **`constrained = phylop_241 >= 2.27`** = **5% FDR** (Sullivan/Christmas 2023 Science).
- **License:** UCSC/Zoonomia public; cite Zoonomia + UCSC.
- **LOAD RECIPE (position-only):**
  ```python
  import pyBigWig
  bw = pyBigWig.open("https://hgdownload.soe.ucsc.edu/goldenPath/hg38/cactus241way/hg38.cactus241way.phyloP.bw")
  val = bw.values("chr20", p, p+1)[0]     # single-base phyloP over HTTP range read; no full download
  ```
  Write `phylop_241` (float) and `constrained = phylop_241 >= 2.27` (bool). Fall back to a local copy only if remote range reads are blocked.

---

## 6. Zoonomia RoCCs + recombination map + gBGC framing (Phase 4)

- **RoCCs mask [VERIFIED — SPINE]:** https://cgl.gi.ucsc.edu/data/cactus/zoonomia-2021-track-hub/hg38/RoCCs.bed.gz — gzipped **BED** (hg38), ~4.7 MB. Canonical `rocc` (bool).
  ```bash
  zcat RoCCs.bed.gz | sort -k1,1 -k2,2n > roccs.sorted.bed
  bedtools intersect -a substitutions.hg38.bed -b roccs.sorted.bed -c | awk '{print $0"\t"($NF>0)}'
  ```
- **Recombination map:** deCODE/Halldorsson 2019, **Science doi:10.1126/science.aau1043** (hg38 UCSC `recombRate2`/`recombAvg`). For `recomb_rate_cMperMb` + hotspot proximity → `gbgc_flag = WtoS AND elevated recombination`.
- **gBGC framing (cite the right figure):** ~**19%** of HARs best explained by **pure gBGC** (76% selection); ~**29–33%** gBGC-influenced (Kostka 2012). State which is meant in each sentence.
- **License:** Zoonomia/UCSC + deCODE public; cite accordingly.

---

## 7. liftOver chain hg19 → hg38 (Phase 1, only if a source is hg19)

- **[VERIFIED — SPINE]** https://hgdownload.soe.ucsc.edu/goldenPath/hg19/liftOver/hg19ToHg38.over.chain.gz — gzipped UCSC chain, ~222 KB.
- **Note:** the benchmark MPRA, zooHARs, and haqer.hg38.bed are all **hg38-native** — liftOver is only needed if a specific supplementary file turns out to be hg19. Confirm each file's build from its header first.
- **LOAD RECIPE:** UCSC `liftOver in.bed hg19ToHg38.over.chain.gz out.bed unmapped.bed`, or `pyliftover`. Drop + LOG any coordinate that fails to lift or maps multiply; re-confirm the GDF5 control survives.

---

## 8. OA / BMD / height GWAS — supporting annotation (Phase 5)

### 8a. Osteoarthritis — Hatzikotoulas 2025 (PRIMARY skeletal GWAS)
- **What:** OA GWAS with **962 INDEPENDENT ASSOCIATIONS** (**513 novel**; **700 effector genes**) — NOT "credible sets" as a count. Portal **genetics-osteoarthritis.com** (GO 2.0).
- **Paper (verified — SPINE):** Hatzikotoulas et al., **Nature 2025**.
  - **[VERIFIED META]** portal + paper confirmed; code https://github.com/hmgu-itg/Genetics-of-Osteoarthritis-2.0.
- **[TODO] exact download URL** for the 962 associations / credible-set table — resolve via: (1) GWAS Catalog (search "osteoarthritis Hatzikotoulas 2025" → GCST accession → FTP `.../summary_statistics/GCST<xxx>/`); (2) the Nature paper's Data Availability; (3) the GitHub repo.
- **Expected format:** per-association / credible-set TSV — **[TODO: confirm real column names from the header before coding the join.]** GRCh38.
- **License:** GOGO/consortium open summary stats; cite Hatzikotoulas et al. Nature 2025.
- **LOAD RECIPE:** `pandas.read_csv(..., sep='\t')`; build a BED of association/credible-set SNPs; `oa_overlap` (bool) + set id; `gwas_enrich_p` = empirical enrichment of nominated causal substitutions vs a matched background.

### 8b. Bone mineral density + height (supporting)
| Trait | Source (verified — SPINE) | Notes |
|---|---|---|
| **eBMD** | Morris 2019 eBMD, **518 loci** (GWAS Catalog / GEFOS http://www.gefos.org) | GRCh38 harmonised sumstats `*.h.tsv.gz` (`hm_chrom, hm_pos, hm_other_allele, hm_effect_allele, beta, se, p_value, ...`). **[TODO: confirm the correct GCST accession for Morris 2019 eBMD.]** |
| **Height** | Yengo 2022 (GIANT), **12,111 SNPs / 7,209 loci** | https://giant-consortium.web.broadinstitute.org/GIANT_consortium_data_files — bulk TSV; liftOver if GRCh37. |

### 8c. Precedents to cite ourselves
- **Whalen & Pollard 2023** — neural HAR-MPRA (GEO **GSE110760**): the prior HAR-MPRA was run in **neural** cells; our benchmark is the first **skeletal** one. Cite as precedent/contrast, not as our benchmark.
- **Kun 2023** — skeletal-proportion loci HAR-enriched (enrichment-only). Cite as precedent for HAR–skeletal enrichment framing.

---

## 9. GDF5 control locus — BLIND validation set (Phase 0 wiring, Phase 6 validation)

Hard-coded coordinates, **hg38 (GRCh38.p14)**. Not downloads — frozen control/validation anchors. Rank + predicted direction FROZEN (timestamped) before looking.

| Control | hg38 locus | `is_control` | Expectation |
|---|---|---|---|
| GDF5 gene body | **chr20:35,433,347–35,454,749** (end is ...749, corrected) | (context gene) | target region |
| **GROW1** rs4911178 | **chr20:35,364,817** | `GDF5-GROW1` | derived allele **reduces** enhancer activity (**0.72×**; shorter bone, higher OA; Capellini 2017 Nat Genet) — expect **negative** DNase delta; recovered BLIND (the HAR-exception positive control) |
| **R4** rs6060369 | knee enhancer | `GDF5-R4` | derived reduces activity |
| negative controls | matched non-HAR/HAQER neutral | `negative` | expect ~no skeletal effect |

- **LOAD RECIPE:** hard-code a small `controls.tsv` (same schema as the element/substitution tables) checked into the repo. In Phase 0 confirm the caller emits the GROW1 row with the expected negative delta; in Phase 6 freeze then reveal the rank/direction for genuine blind validation. Self-red-team: assert no filter drops these before the reveal.
- **Reference FASTA for allele lookups:** hg38 (§10).

---

## 10. Reference genome & housekeeping

| File | URL | Format | Size |
|---|---|---|---|
| hg38 FASTA | https://hgdownload.soe.ucsc.edu/goldenPath/hg38/bigZips/hg38.fa.gz | gzip FASTA | ~940 MB |
| hg38 chrom sizes | https://hgdownload.soe.ucsc.edu/goldenPath/hg38/bigZips/hg38.chrom.sizes | TSV | ~11 KB |

- **[VERIFIED META]** standard UCSC bigZips paths. Needed for allele lookups + any local scoring.

---

## Provenance summary (cite these)

- **Benchmark MPRA:** Okamoto, Coveney, Ganapathee & Capellini 2025, *GBE* 10.1093/gbe/evag121 (bioRxiv 2025.10.21.683789); GEO **GSE298093**; github.com/aokamoto-bio/human_skeletal_evolution_MPRA. hg38.
- **Engine:** AlphaGenome — Avsec et al., *Nature* 2026, 10.1038/s41586-025-10014-0; DeepMind hosted API (DNASE panel; 305 DNASE / 167 ATAC tracks).
- **HAR set:** zooHARs, Keough et al. Science 2023 (10.1126/science.abm1696), n=312.
- **HAQER set:** Mangan et al. Cell 2022 (Lowe lab), haqer.hg38.bed, n=1,581.
- **Constraint:** Zoonomia phyloP 241-way + RoCCs (Sullivan/Christmas 2023 Science; phyloP ≥ 2.27 = 5% FDR); gBGC (Kostka 2012: 19% pure-gBGC / 29–33% influenced).
- **Recombination:** deCODE/Halldorsson 2019 Science (10.1126/science.aau1043).
- **GWAS:** OA Hatzikotoulas 2025 Nature (962 independent associations; portal genetics-osteoarthritis.com); eBMD Morris 2019 (518 loci); height Yengo 2022 GIANT (12,111 SNPs / 7,209 loci).
- **Precedents cited:** Whalen & Pollard 2023 neural HAR-MPRA (GSE110760); Kun 2023 skeletal-proportion HAR enrichment.
- **Optional cross-check:** ENCODE ChromBPNet DNase skeletal models (limb ENCSR138OCE/ENCSR858EVI; MSC ENCFF640AVL; MG63 ENCFF841SWM) — base-resolution / robustness only.
- UCSC Genome Browser (liftOver chain, hg38 bigZips, goldenPath).

## Open TODOs carried forward (resolve first in Claude Science)
1. Exact **GSE298093 / GitHub** per-element table + header names for differential-activity calls and HAR/HAQER labels (bioRxiv HTML 403s — use PDF/GEO/GitHub).
2. Confirm the **Lowe-lab haqer.hg38.bed** download path (1,581 intervals, BED5).
3. Real download URL + column header for the **Hatzikotoulas 2025 OA** 962-association / credible-set table.
4. Correct **Morris 2019 eBMD** GCST accession (518 loci) — GEFOS fallback.
5. Confirm skeletal **DNASE CURIEs** from `output_metadata` and freeze `config/skeletal_tracks.yaml` (chondrocyte ENCSR970DQR, embryonic femur ENCSR805XIF, limb).
