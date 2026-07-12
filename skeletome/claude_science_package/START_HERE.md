# SKELETOME — START HERE
### A portable research package for continuing in Claude Science

This folder is a self-contained, **fact-checked** research package (**v2**). Drop it into Claude Science and keep iterating — the benchmark already runs and the blind positive-control machinery already works.

> ⚠️ **v2 — read `CHANGELOG.md` first.** The project pivoted (2026-07-07) after a deep-research pass found the **Okamoto/Capellini 2025 skeletal MPRA** (GEO GSE298093): HARs are *not* enriched for skeletal regulatory divergence — **HAQERs are** — and a skeletal MPRA now exists. We turned that into the spine: their 70k-element MPRA is our public **ground-truth benchmark**. `PROJECT_CONTEXT.md` is the v2 source of truth.

> **SKELETOME v2** = a **virtual skeletal MPRA, benchmarked against the real one.** Using AlphaGenome (DeepMind, Nature 2026; hosted no-GPU API; verified to expose skeletal DNase tracks) we predict human-vs-chimp DNase deltas for HAR **and HAQER** elements, **benchmark against the Okamoto/Capellini MPRA** (concordance + HAQER>HAR + polygenic), add Zoonomia constraint + gBGC + OA/BMD/height GWAS, pinpoint the **causal base** the region-level assay can't, and **blind-recover GDF5/GROW1** (the HAR exception). Research track — the deliverable is the *finding*, not a tool.

---

## ✅ Verified before shipping (2026-07-07)
- **`python code/benchmark.py`** (the v2 hero) runs **offline, exit 0** — mock AUROC **0.84** in-silico↔MPRA concordance; reproduces **HAQER 63% vs HAR 33%** (OR 3.0, vs-chance p=0.003; honest matched-control caveat printed); **GDF5/GROW1 recovered blind at top 0.9%**.
- `bash code/run.sh` (v1 substitution-level backbone, MOCK) runs **end-to-end, exit 0**; `pytest tests/test_gdf5.py` → **11/11 pass**.
- Every load-bearing claim primary-source **fact-checked** (see `CHANGELOG.md`): AlphaGenome real (Nature Jan 2026), skeletal DNase tracks present (B1 = YES), benchmark data public (GSE298093), numbers corrected.
- Tested on Python 3.11, numpy 1.26, pandas 3.0. `pyBigWig`/`alphagenome` only needed for `--full` real-data runs.
- ⚠️ **Known residual:** the v1 code is substitution-level; the v2 `CANONICAL_SCHEMA.md` is element-level. `benchmark.py` is the v2 element-level centerpiece; unifying the rest of the pipeline to element-level is the top code task (see `CHANGELOG.md` residuals).

## How to use this in Claude Science (3 steps)
1. **Upload this whole folder** as project files.
2. **Paste `PROJECT_CONTEXT.md`** into the project instructions / system context. It is the source of truth for what SKELETOME is and how to behave while iterating (the seven locked decisions + the honest register). Keep `CANONICAL_SCHEMA.md` handy — every step reads/writes those exact columns.
3. **Paste the kickoff prompt below**, then work down `PROMPT_PACK.md` step by step.

### Kickoff prompt (paste into Claude Science)
```
You are continuing SKELETOME. Read PROJECT_CONTEXT.md (your standing instructions — honor
the seven locked decisions and the honest register) and CANONICAL_SCHEMA.md (the frozen
results-TSV contract). Then:

1. Run `bash code/run.sh` in MOCK mode and confirm it produces work/40_results.tsv with the
   canonical columns and that the blind GDF5/control validation block prints.
2. Run `pytest tests/test_gdf5.py` and confirm 11/11 pass.
3. Open OPEN_QUESTIONS.md and start on the four BLOCKERS in order — beginning with B1:
   verify whether AlphaGenome actually exposes a skeletal-lineage ATAC/DNASE track
   (limb / MSC / osteoblast). Enumerate the real biosamples/ontology terms live, and report
   back the LITERAL track names we are allowed to call "skeletal" before we score anything.

Do not relitigate the locked decisions. Assert the control set survives at every stage.
Never rename a cell type upward (bulk limb / MG63 / H1-MSC — never "chondrocyte").
Freeze thresholds and effect-direction predictions to disk BEFORE inspecting GDF5's rank.
```

## What's in the box
| File | What it is |
|---|---|
| **`PROJECT_CONTEXT.md`** | Standing project knowledge — paste as instructions. Thesis, 7 locked decisions, honest register, judging map, control policy. |
| **`CANONICAL_SCHEMA.md`** | The frozen results-TSV column contract. |
| **`DATA_MANIFEST.md`** | Every dataset: verified URL/accession, format, build, size, license, position-only load recipe. |
| **`RESEARCH_PLAN.md`** | The 6 phases as executable tasks with Definition-of-Done + open questions. Your living backlog. |
| **`PROMPT_PACK.md`** | Copy-paste prompts for each iteration step (0→7), each with acceptance criteria. |
| **`CAVEATS_AND_DEFENSES.md`** | Every reviewer kill-shot + the pre-baked honest answer. The trust layer. |
| **`OPEN_QUESTIONS.md`** | The 40 research questions the build surfaced, prioritized. **This is where "keep researching" lives.** |
| **`PROJECT_BRIEF.md`** | Human-readable master plan (day-by-day, demo script, judge scores). |
| **`code/`** | Runnable pipeline (mock-by-default). schema · substitutions (GDF5 unit-tested) · constraint (phyloP) · gbgc · AlphaGenome + ChromBPNet scorers · comparator · aggregate (permutation null, BH-FDR, blind GDF5 check) · run.sh · download.sh |
| **`tests/test_gdf5.py`** | The control-survival test (11 cases). |
| **`requirements.txt`** | Pinned deps. |

## The pipeline (what run.sh orchestrates)
```
make_demo_input → score_alphagenome (PRIMARY) → [score_chrombpnet, optional]
                → comparator (neural + skeletal_specific) → aggregate (null + FDR + BLIND GDF5)
```
`./run.sh` = mock (offline). `./run.sh --full` = real AlphaGenome (needs `ALPHAGENOME_API_KEY`). `--with-chrombpnet` adds the optional enrichment layer.

## The first thing to resolve
The single highest-leverage open question is **B1 in `OPEN_QUESTIONS.md`**: *does AlphaGenome actually expose a skeletal-lineage accessibility track, or is the "skeletal" readout a proxy tissue?* The answer decides whether `ag_atac_delta`/`ag_dnase_delta` can be labeled skeletal at all — and it's a live API query, not a literature question. Start there.

## Honest register (do not drift)
Predicted, not measured · gBGC ≠ selection · literal cell-type labels only · freeze before you look · constraint ≠ function · enrichment ≠ causality. These are what make the work trustworthy — see `CAVEATS_AND_DEFENSES.md`.
